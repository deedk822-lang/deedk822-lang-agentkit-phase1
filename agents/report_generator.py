#!/usr/bin/env python3
"""
Report generation agent that creates real PDF and Excel reports.
"""
import os
import json
import redis
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from jinja2 import Template
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("report_generator")

# ---------- Redis ----------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(REDIS_URL, decode_responses=True)

class ReportGenerator:
    def __init__(self):
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        self.styles = getSampleStyleSheet()
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.darkblue
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        )
    
    def generate_report(self, client: str, dataset: str, format_type: str) -> str:
        """Generate a comprehensive report"""
        log.info("Generating %s report for client: %s, dataset: %s", format_type, client, dataset)
        
        # Gather data from Redis and create sample dataset
        report_data = self._gather_report_data(client, dataset)
        
        if format_type.lower() == 'pdf':
            return self._generate_pdf_report(client, dataset, report_data)
        elif format_type.lower() == 'csv':
            return self._generate_csv_report(client, dataset, report_data)
        elif format_type.lower() == 'excel':
            return self._generate_excel_report(client, dataset, report_data)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _gather_report_data(self, client: str, dataset: str) -> dict:
        """Gather data for the report from various sources"""
        data = {
            'client': client,
            'dataset': dataset,
            'generated_at': datetime.now().isoformat(),
            'scan_results': [],
            'distribution_results': [],
            'performance_metrics': {},
            'summary_stats': {}
        }
        
        # Gather scan results from Redis
        scan_keys = r.keys('scan_result:*')
        for key in scan_keys[:10]:  # Limit to last 10 scans
            try:
                scan_data = json.loads(r.get(key))
                data['scan_results'].append(scan_data)
            except:
                continue
        
        # Gather distribution results
        dist_keys = r.keys('distribution_result:*')
        for key in dist_keys[:20]:  # Limit to last 20 distributions
            try:
                dist_data = json.loads(r.get(key))
                data['distribution_results'].append(dist_data)
            except:
                continue
        
        # Generate performance metrics
        if data['scan_results']:
            load_times = []
            security_scores = []
            
            for scan in data['scan_results']:
                perf = scan.get('performance', {})
                if 'load_times' in perf:
                    load_times.append(perf['load_times'].get('full_page', 0))
                
                security = scan.get('security', {})
                if 'score' in security:
                    security_scores.append(security['score'])
            
            if load_times:
                data['performance_metrics'] = {
                    'avg_load_time': sum(load_times) / len(load_times),
                    'min_load_time': min(load_times),
                    'max_load_time': max(load_times),
                    'total_scans': len(load_times)
                }
            
            if security_scores:
                data['summary_stats'] = {
                    'avg_security_score': sum(security_scores) / len(security_scores),
                    'min_security_score': min(security_scores),
                    'max_security_score': max(security_scores)
                }
        
        return data
    
    def _generate_pdf_report(self, client: str, dataset: str, data: dict) -> str:
        """Generate a comprehensive PDF report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{client}_{dataset}_{timestamp}.pdf"
        filepath = self.reports_dir / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(str(filepath), pagesize=A4)
        story = []
        
        # Title
        title = f"AgentKit Report - {client.title()}"
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.heading_style))
        summary_text = f"""
        This report provides a comprehensive analysis of the {dataset} dataset for {client}.
        Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}.
        
        Key Findings:
        • Total scans performed: {len(data.get('scan_results', []))}
        • Total distributions executed: {len(data.get('distribution_results', []))}
        • Average security score: {data.get('summary_stats', {}).get('avg_security_score', 'N/A')}
        • Average load time: {data.get('performance_metrics', {}).get('avg_load_time', 'N/A')} ms
        """
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Performance Metrics
        if data.get('performance_metrics'):
            story.append(Paragraph("Performance Analysis", self.heading_style))
            
            perf_data = [
                ['Metric', 'Value'],
                ['Average Load Time', f"{data['performance_metrics'].get('avg_load_time', 0):.2f} ms"],
                ['Minimum Load Time', f"{data['performance_metrics'].get('min_load_time', 0):.2f} ms"],
                ['Maximum Load Time', f"{data['performance_metrics'].get('max_load_time', 0):.2f} ms"],
                ['Total Scans', str(data['performance_metrics'].get('total_scans', 0))]
            ]
            
            perf_table = Table(perf_data)
            perf_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(perf_table)
            story.append(Spacer(1, 20))
        
        # Security Analysis
        if data.get('summary_stats'):
            story.append(Paragraph("Security Analysis", self.heading_style))
            
            sec_data = [
                ['Security Metric', 'Score'],
                ['Average Security Score', f"{data['summary_stats'].get('avg_security_score', 0):.1f}/100"],
                ['Minimum Security Score', f"{data['summary_stats'].get('min_security_score', 0):.1f}/100"],
                ['Maximum Security Score', f"{data['summary_stats'].get('max_security_score', 0):.1f}/100"]
            ]
            
            sec_table = Table(sec_data)
            sec_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(sec_table)
            story.append(Spacer(1, 20))
        
        # Recent Scan Results
        if data.get('scan_results'):
            story.append(Paragraph("Recent Scan Results", self.heading_style))
            
            scan_data = [['Domain', 'Status', 'Load Time (ms)', 'Security Score']]
            for scan in data['scan_results'][:5]:  # Show last 5 scans
                domain = scan.get('domain', 'Unknown')
                status = scan.get('basic_info', {}).get('status_code', 'N/A')
                load_time = scan.get('performance', {}).get('load_times', {}).get('full_page', 0)
                sec_score = scan.get('security', {}).get('score', 0)
                
                scan_data.append([domain, str(status), f"{load_time:.0f}", f"{sec_score}/100"])
            
            scan_table = Table(scan_data)
            scan_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(scan_table)
        
        # Build PDF
        doc.build(story)
        
        log.info("PDF report generated: %s", filepath)
        return str(filepath)
    
    def _generate_csv_report(self, client: str, dataset: str, data: dict) -> str:
        """Generate CSV report with structured data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{client}_{dataset}_{timestamp}.csv"
        filepath = self.reports_dir / filename
        
        # Prepare data for CSV
        csv_data = []
        
        # Add scan results
        for scan in data.get('scan_results', []):
            row = {
                'type': 'scan',
                'client': client,
                'dataset': dataset,
                'timestamp': scan.get('scan_time', ''),
                'domain': scan.get('domain', ''),
                'status_code': scan.get('basic_info', {}).get('status_code', ''),
                'load_time_ms': scan.get('performance', {}).get('load_times', {}).get('full_page', 0),
                'security_score': scan.get('security', {}).get('score', 0),
                'seo_score': scan.get('seo', {}).get('score', 0),
                'vulnerability_count': len(scan.get('vulnerabilities', [])),
                'technology_count': len(scan.get('technologies', []))
            }
            csv_data.append(row)
        
        # Add distribution results
        for i, dist in enumerate(data.get('distribution_results', [])):
            row = {
                'type': 'distribution',
                'client': client,
                'dataset': dataset,
                'timestamp': datetime.now().isoformat(),
                'distribution_id': i,
                'platforms_total': len(dist),
                'platforms_success': len([p for p in dist.values() if 'success' in p]),
                'platforms_failed': len([p for p in dist.values() if 'fail' in p])
            }
            csv_data.append(row)
        
        # Create DataFrame and save
        if csv_data:
            df = pd.DataFrame(csv_data)
            df.to_csv(filepath, index=False)
        else:
            # Create empty CSV with headers
            df = pd.DataFrame(columns=['type', 'client', 'dataset', 'timestamp'])
            df.to_csv(filepath, index=False)
        
        log.info("CSV report generated: %s", filepath)
        return str(filepath)
    
    def _generate_excel_report(self, client: str, dataset: str, data: dict) -> str:
        """Generate Excel report with multiple sheets"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{client}_{dataset}_{timestamp}.xlsx"
        filepath = self.reports_dir / filename
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                'Metric': ['Total Scans', 'Total Distributions', 'Average Security Score', 'Average Load Time (ms)'],
                'Value': [
                    len(data.get('scan_results', [])),
                    len(data.get('distribution_results', [])),
                    data.get('summary_stats', {}).get('avg_security_score', 0),
                    data.get('performance_metrics', {}).get('avg_load_time', 0)
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Scan results sheet
            if data.get('scan_results'):
                scan_records = []
                for scan in data['scan_results']:
                    record = {
                        'Domain': scan.get('domain', ''),
                        'Scan Time': scan.get('scan_time', ''),
                        'Status Code': scan.get('basic_info', {}).get('status_code', ''),
                        'Load Time (ms)': scan.get('performance', {}).get('load_times', {}).get('full_page', 0),
                        'Security Score': scan.get('security', {}).get('score', 0),
                        'SEO Score': scan.get('seo', {}).get('score', 0),
                        'Vulnerabilities': len(scan.get('vulnerabilities', [])),
                        'Technologies': len(scan.get('technologies', []))
                    }
                    scan_records.append(record)
                
                scan_df = pd.DataFrame(scan_records)
                scan_df.to_excel(writer, sheet_name='Scan Results', index=False)
            
            # Distribution results sheet
            if data.get('distribution_results'):
                dist_records = []
                for i, dist in enumerate(data['distribution_results']):
                    record = {
                        'Distribution ID': i,
                        'Platforms Total': len(dist),
                        'Platforms Success': len([p for p in dist.values() if 'success' in p]),
                        'Platforms Failed': len([p for p in dist.values() if 'fail' in p]),
                        'Success Rate': len([p for p in dist.values() if 'success' in p]) / len(dist) if dist else 0
                    }
                    dist_records.append(record)
                
                dist_df = pd.DataFrame(dist_records)
                dist_df.to_excel(writer, sheet_name='Distribution Results', index=False)
        
        log.info("Excel report generated: %s", filepath)
        return str(filepath)
    
    def handle_report_task(self, task: dict) -> str:
        """Handle a PUBLISH_REPORT task"""
        client = task['params']['client']
        dataset = task['params']['dataset']
        format_type = task['params']['format']
        
        log.info("Generating %s report for %s - %s", format_type, client, dataset)
        
        try:
            report_path = self.generate_report(client, dataset, format_type)
            
            # Store report info in Redis
            report_info = {
                'client': client,
                'dataset': dataset,
                'format': format_type,
                'path': report_path,
                'generated_at': datetime.now().isoformat(),
                'file_size': os.path.getsize(report_path) if os.path.exists(report_path) else 0
            }
            
            result_key = f"report_result:{task.get('id', 'unknown')}"
            r.setex(result_key, 7200, json.dumps(report_info))  # Expire after 2 hours
            
            log.info("Report generated successfully: %s", report_path)
            return report_path
            
        except Exception as e:
            log.error("Failed to generate report: %s", e)
            raise
    
    def loop(self):
        """Main loop to process report generation tasks"""
        log.info("Report generator waiting for PUBLISH_REPORT tasks...")
        
        while True:
            try:
                _, raw = r.brpop("agent_tasks")
                task = json.loads(raw)
                
                if task.get("type") == "PUBLISH_REPORT":
                    self.handle_report_task(task)
                else:
                    # Put non-report tasks back for other agents
                    r.lpush("agent_tasks", raw)
                    
            except Exception as e:
                log.error("Error processing report task: %s", e)
                continue

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", help="Client name")
    parser.add_argument("--dataset", help="Dataset name")
    parser.add_argument("--format", choices=['pdf', 'csv', 'excel'], help="Report format")
    args = parser.parse_args()
    
    generator = ReportGenerator()
    
    if args.client and args.dataset and args.format:
        report_path = generator.generate_report(args.client, args.dataset, args.format)
        print(f"Report generated: {report_path}")
    else:
        generator.loop()