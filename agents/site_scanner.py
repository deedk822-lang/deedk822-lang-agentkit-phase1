#!/usr/bin/env python3
"""
Site scanning agent that performs real security and performance analysis.
"""
import os
import json
import redis
import logging
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import ssl
import socket
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("site_scanner")

# ---------- Redis ----------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(REDIS_URL, decode_responses=True)

class SiteScanner:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 AgentKit Site Scanner'
        })
        
        # Setup headless Chrome for dynamic analysis
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            log.warning("Chrome driver not available, skipping dynamic analysis: %s", e)
            self.driver = None
    
    def scan_domain(self, domain: str) -> dict:
        """Perform comprehensive domain analysis"""
        if not domain.startswith(('http://', 'https://')):
            domain = f"https://{domain}"
        
        results = {
            'domain': domain,
            'scan_time': datetime.utcnow().isoformat(),
            'basic_info': {},
            'security': {},
            'performance': {},
            'seo': {},
            'technologies': [],
            'vulnerabilities': []
        }
        
        try:
            # Basic HTTP analysis
            results['basic_info'] = self._analyze_http(domain)
            
            # Security analysis
            results['security'] = self._analyze_security(domain)
            
            # Performance analysis
            results['performance'] = self._analyze_performance(domain)
            
            # SEO analysis
            results['seo'] = self._analyze_seo(domain)
            
            # Technology detection
            results['technologies'] = self._detect_technologies(domain)
            
            # Vulnerability scanning
            results['vulnerabilities'] = self._scan_vulnerabilities(domain)
            
        except Exception as e:
            log.error("Error scanning domain %s: %s", domain, e)
            results['error'] = str(e)
        
        return results
    
    def _analyze_http(self, domain: str) -> dict:
        """Basic HTTP response analysis"""
        try:
            response = self.session.get(domain, timeout=10, allow_redirects=True)
            
            return {
                'status_code': response.status_code,
                'final_url': response.url,
                'redirects': len(response.history),
                'response_time_ms': int(response.elapsed.total_seconds() * 1000),
                'content_length': len(response.content),
                'content_type': response.headers.get('content-type', ''),
                'server': response.headers.get('server', ''),
                'headers': dict(response.headers)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_security(self, domain: str) -> dict:
        """Security header and SSL analysis"""
        security_info = {
            'ssl_info': {},
            'security_headers': {},
            'score': 0
        }
        
        try:
            # SSL Certificate Analysis
            parsed = urlparse(domain)
            hostname = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            
            if parsed.scheme == 'https':
                context = ssl.create_default_context()
                with socket.create_connection((hostname, port), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()
                        security_info['ssl_info'] = {
                            'subject': dict(x[0] for x in cert['subject']),
                            'issuer': dict(x[0] for x in cert['issuer']),
                            'not_after': cert['notAfter'],
                            'not_before': cert['notBefore'],
                            'serial_number': cert['serialNumber'],
                            'version': cert['version']
                        }
            
            # Security Headers Analysis
            response = self.session.get(domain, timeout=10)
            headers = response.headers
            
            security_headers = {
                'strict_transport_security': headers.get('Strict-Transport-Security'),
                'content_security_policy': headers.get('Content-Security-Policy'),
                'x_frame_options': headers.get('X-Frame-Options'),
                'x_content_type_options': headers.get('X-Content-Type-Options'),
                'x_xss_protection': headers.get('X-XSS-Protection'),
                'referrer_policy': headers.get('Referrer-Policy')
            }
            
            security_info['security_headers'] = security_headers
            
            # Calculate security score
            score = 0
            if security_headers['strict_transport_security']:
                score += 20
            if security_headers['content_security_policy']:
                score += 25
            if security_headers['x_frame_options']:
                score += 15
            if security_headers['x_content_type_options']:
                score += 10
            if security_headers['x_xss_protection']:
                score += 10
            if security_headers['referrer_policy']:
                score += 10
            if security_info.get('ssl_info'):
                score += 10
            
            security_info['score'] = score
            
        except Exception as e:
            security_info['error'] = str(e)
        
        return security_info
    
    def _analyze_performance(self, domain: str) -> dict:
        """Performance analysis"""
        perf_info = {
            'load_times': {},
            'resource_analysis': {},
            'suggestions': []
        }
        
        try:
            # Basic load time
            start_time = time.time()
            response = self.session.get(domain, timeout=30)
            load_time = (time.time() - start_time) * 1000
            
            perf_info['load_times']['full_page'] = load_time
            
            # Analyze page size and resources
            soup = BeautifulSoup(response.content, 'html.parser')
            
            images = soup.find_all('img')
            scripts = soup.find_all('script')
            stylesheets = soup.find_all('link', rel='stylesheet')
            
            perf_info['resource_analysis'] = {
                'html_size': len(response.content),
                'image_count': len(images),
                'script_count': len(scripts),
                'stylesheet_count': len(stylesheets)
            }
            
            # Generate performance suggestions
            if len(images) > 20:
                perf_info['suggestions'].append('Consider optimizing images - high image count detected')
            if len(scripts) > 10:
                perf_info['suggestions'].append('Consider bundling JavaScript files - many scripts detected')
            if load_time > 3000:
                perf_info['suggestions'].append('Page load time is slow - consider optimization')
            
        except Exception as e:
            perf_info['error'] = str(e)
        
        return perf_info
    
    def _analyze_seo(self, domain: str) -> dict:
        """SEO analysis"""
        seo_info = {
            'meta_tags': {},
            'headings': {},
            'issues': [],
            'score': 0
        }
        
        try:
            response = self.session.get(domain, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Meta tags analysis
            title = soup.find('title')
            description = soup.find('meta', attrs={'name': 'description'})
            keywords = soup.find('meta', attrs={'name': 'keywords'})
            
            seo_info['meta_tags'] = {
                'title': title.text if title else None,
                'title_length': len(title.text) if title else 0,
                'description': description.get('content') if description else None,
                'description_length': len(description.get('content', '')) if description else 0,
                'keywords': keywords.get('content') if keywords else None
            }
            
            # Heading structure analysis
            headings = {}
            for i in range(1, 7):
                h_tags = soup.find_all(f'h{i}')
                headings[f'h{i}'] = len(h_tags)
            
            seo_info['headings'] = headings
            
            # SEO issues detection
            if not title:
                seo_info['issues'].append('Missing title tag')
            elif len(title.text) > 60:
                seo_info['issues'].append('Title tag too long')
            
            if not description:
                seo_info['issues'].append('Missing meta description')
            elif len(description.get('content', '')) > 160:
                seo_info['issues'].append('Meta description too long')
            
            if headings['h1'] == 0:
                seo_info['issues'].append('Missing H1 tag')
            elif headings['h1'] > 1:
                seo_info['issues'].append('Multiple H1 tags found')
            
            # Calculate SEO score
            score = 100
            score -= len(seo_info['issues']) * 15
            seo_info['score'] = max(0, score)
            
        except Exception as e:
            seo_info['error'] = str(e)
        
        return seo_info
    
    def _detect_technologies(self, domain: str) -> list:
        """Detect technologies used by the website"""
        technologies = []
        
        try:
            response = self.session.get(domain, timeout=10)
            headers = response.headers
            content = response.text.lower()
            
            # Server detection
            server = headers.get('Server', '')
            if server:
                technologies.append({'name': 'Server', 'value': server})
            
            # Framework detection
            if 'x-powered-by' in headers:
                technologies.append({'name': 'Powered By', 'value': headers['x-powered-by']})
            
            # Content Management System detection
            if 'wp-content' in content or 'wordpress' in content:
                technologies.append({'name': 'CMS', 'value': 'WordPress'})
            elif 'drupal' in content:
                technologies.append({'name': 'CMS', 'value': 'Drupal'})
            elif 'joomla' in content:
                technologies.append({'name': 'CMS', 'value': 'Joomla'})
            
            # JavaScript frameworks
            if 'react' in content:
                technologies.append({'name': 'JavaScript Framework', 'value': 'React'})
            elif 'angular' in content:
                technologies.append({'name': 'JavaScript Framework', 'value': 'Angular'})
            elif 'vue' in content:
                technologies.append({'name': 'JavaScript Framework', 'value': 'Vue.js'})
            
            # Analytics
            if 'google-analytics' in content or 'gtag' in content:
                technologies.append({'name': 'Analytics', 'value': 'Google Analytics'})
            
        except Exception as e:
            log.error("Error detecting technologies: %s", e)
        
        return technologies
    
    def _scan_vulnerabilities(self, domain: str) -> list:
        """Basic vulnerability scanning"""
        vulnerabilities = []
        
        try:
            response = self.session.get(domain, timeout=10)
            headers = response.headers
            
            # Check for common security issues
            if 'Server' in headers and any(old_server in headers['Server'].lower() 
                                         for old_server in ['apache/2.2', 'nginx/1.0', 'iis/6.0']):
                vulnerabilities.append({
                    'severity': 'medium',
                    'type': 'Outdated Server',
                    'description': f"Potentially outdated server: {headers['Server']}"
                })
            
            # Check for missing security headers
            if not headers.get('X-Frame-Options'):
                vulnerabilities.append({
                    'severity': 'low',
                    'type': 'Missing Security Header',
                    'description': 'X-Frame-Options header is missing (clickjacking protection)'
                })
            
            if not headers.get('Content-Security-Policy'):
                vulnerabilities.append({
                    'severity': 'medium',
                    'type': 'Missing Security Header',
                    'description': 'Content-Security-Policy header is missing'
                })
            
            # Check for directory listing
            try:
                dir_response = self.session.get(urljoin(domain, '/wp-admin/'), timeout=5)
                if 'Index of' in dir_response.text:
                    vulnerabilities.append({
                        'severity': 'medium',
                        'type': 'Directory Listing',
                        'description': 'Directory listing is enabled'
                    })
            except:
                pass
            
        except Exception as e:
            log.error("Error scanning vulnerabilities: %s", e)
        
        return vulnerabilities
    
    def handle_scan_task(self, task: dict):
        """Handle a SCAN_SITE task"""
        domain = task['params']['domain']
        log.info("Starting comprehensive scan of domain: %s", domain)
        
        # Perform the scan
        results = self.scan_domain(domain)
        
        # Store results in Redis
        result_key = f"scan_result:{task.get('id', 'unknown')}"
        r.setex(result_key, 3600, json.dumps(results, indent=2))  # Expire after 1 hour
        
        # Generate summary report
        summary = self._generate_summary(results)
        log.info("Scan complete for %s: %s", domain, summary)
        
        # Store summary for quick access
        summary_key = f"scan_summary:{task.get('id', 'unknown')}"
        r.setex(summary_key, 3600, summary)
        
        return results
    
    def _generate_summary(self, results: dict) -> str:
        """Generate a human-readable summary"""
        domain = results.get('domain', 'Unknown')
        
        if 'error' in results:
            return f"Scan failed for {domain}: {results['error']}"
        
        basic = results.get('basic_info', {})
        security = results.get('security', {})
        performance = results.get('performance', {})
        seo = results.get('seo', {})
        vulns = results.get('vulnerabilities', [])
        
        status = basic.get('status_code', 'Unknown')
        load_time = performance.get('load_times', {}).get('full_page', 0)
        security_score = security.get('score', 0)
        seo_score = seo.get('score', 0)
        vuln_count = len(vulns)
        
        return (
            f"Domain: {domain} | Status: {status} | "
            f"Load Time: {load_time:.0f}ms | "
            f"Security Score: {security_score}/100 | "
            f"SEO Score: {seo_score}/100 | "
            f"Vulnerabilities: {vuln_count}"
        )
    
    def loop(self):
        """Main loop to process scan tasks"""
        log.info("Site scanner waiting for SCAN_SITE tasks...")
        
        while True:
            try:
                _, raw = r.brpop("agent_tasks")
                task = json.loads(raw)
                
                if task.get("type") == "SCAN_SITE":
                    self.handle_scan_task(task)
                else:
                    # Put non-scan tasks back for other agents
                    r.lpush("agent_tasks", raw)
                    
            except Exception as e:
                log.error("Error processing scan task: %s", e)
                continue
    
    def __del__(self):
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan", help="Scan a specific domain directly")
    args = parser.parse_args()
    
    scanner = SiteScanner()
    
    if args.scan:
        results = scanner.scan_domain(args.scan)
        print(json.dumps(results, indent=2))
    else:
        scanner.loop()