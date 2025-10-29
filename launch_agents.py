#!/usr/bin/env python3
"""
AgentKit Phase-1 Agent Launcher
Starts all agents with proper process management and monitoring.
"""
import os
import sys
import time
import signal
import logging
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict
from multiprocessing import Process

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("launcher")

class AgentLauncher:
    def __init__(self):
        self.agents = {
            'command_poller': 'agents.command_poller',
            'content_distribution': 'agents.content_distribution_agent', 
            'site_scanner': 'agents.site_scanner',
            'report_generator': 'agents.report_generator'
        }
        self.processes: Dict[str, Process] = {}
        self.shutdown = False
    
    def check_environment(self) -> bool:
        """Check if environment is properly configured"""
        log.info("Checking environment configuration...")
        
        # Check if .env file exists
        env_file = Path('.env')
        if not env_file.exists():
            log.warning(".env file not found. Copy .env.template to .env and configure it.")
            return False
        
        # Load environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            log.warning("python-dotenv not installed. Install with: pip install python-dotenv")
        
        # Check Redis connection
        try:
            import redis
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            r = redis.from_url(redis_url, decode_responses=True)
            r.ping()
            log.info("✓ Redis connection successful")
        except Exception as e:
            log.error("✗ Redis connection failed: %s", e)
            log.error("Start Redis with: docker run --rm -d -p 6379:6379 redis:7-alpine")
            return False
        
        # Check Google credentials
        google_creds_path = os.getenv('GOOGLE_CREDENTIALS_PATH')
        google_creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        if google_creds_path and Path(google_creds_path).exists():
            log.info("✓ Google credentials file found")
        elif google_creds_json:
            log.info("✓ Google credentials JSON configured")
        else:
            log.warning("⚠ Google credentials not configured (will use fallback mode)")
        
        # Check API keys (non-blocking warnings)
        api_checks = [
            ('Twitter', 'TWITTER_API_KEY'),
            ('LinkedIn', 'LINKEDIN_USERNAME'),
            ('Facebook', 'FACEBOOK_ACCESS_TOKEN'),
            ('Reddit', 'REDDIT_CLIENT_ID'),
            ('Email', 'EMAIL_USERNAME'),
            ('Notion', 'NOTION_TOKEN')
        ]
        
        for service, env_var in api_checks:
            if os.getenv(env_var) and not os.getenv(env_var).startswith(('your_', 'secret_')):
                log.info("✓ %s API configured", service)
            else:
                log.warning("⚠ %s API not configured (will simulate posts)", service)
        
        return True
    
    def start_agent(self, name: str, module: str) -> bool:
        """Start a single agent"""
        try:
            log.info("Starting %s agent...", name)
            
            def run_agent():
                import importlib
                agent_module = importlib.import_module(module)
                # Run the agent's main loop
                if hasattr(agent_module, 'main'):
                    agent_module.main()
                elif name == 'command_poller':
                    from agents.command_poller import Poller
                    Poller().run_forever()
                elif name == 'content_distribution':
                    from agents.content_distribution_agent import Distributor
                    Distributor().loop()
                elif name == 'site_scanner':
                    from agents.site_scanner import SiteScanner
                    SiteScanner().loop()
                elif name == 'report_generator':
                    from agents.report_generator import ReportGenerator
                    ReportGenerator().loop()
            
            process = Process(target=run_agent, name=f"agent-{name}")
            process.start()
            self.processes[name] = process
            
            log.info("✓ %s agent started (PID: %d)", name, process.pid)
            return True
            
        except Exception as e:
            log.error("✗ Failed to start %s agent: %s", name, e)
            return False
    
    def stop_agent(self, name: str) -> bool:
        """Stop a single agent"""
        if name in self.processes:
            process = self.processes[name]
            if process.is_alive():
                log.info("Stopping %s agent (PID: %d)...", name, process.pid)
                process.terminate()
                process.join(timeout=5)
                
                if process.is_alive():
                    log.warning("Force killing %s agent", name)
                    process.kill()
                    process.join()
                
                log.info("✓ %s agent stopped", name)
            
            del self.processes[name]
            return True
        
        return False
    
    def start_all(self, agents: List[str] = None) -> bool:
        """Start all or specified agents"""
        if not self.check_environment():
            log.error("Environment check failed. Please fix configuration and try again.")
            return False
        
        agents_to_start = agents or list(self.agents.keys())
        
        log.info("Starting AgentKit Phase-1 with %d agents...", len(agents_to_start))
        
        success_count = 0
        for agent_name in agents_to_start:
            if agent_name in self.agents:
                if self.start_agent(agent_name, self.agents[agent_name]):
                    success_count += 1
                    time.sleep(1)  # Stagger startup
            else:
                log.error("Unknown agent: %s", agent_name)
        
        log.info("Started %d/%d agents successfully", success_count, len(agents_to_start))
        return success_count > 0
    
    def stop_all(self):
        """Stop all agents"""
        log.info("Stopping all agents...")
        
        for name in list(self.processes.keys()):
            self.stop_agent(name)
        
        log.info("All agents stopped")
    
    def status(self):
        """Show status of all agents"""
        log.info("Agent Status:")
        
        if not self.processes:
            log.info("  No agents running")
            return
        
        for name, process in self.processes.items():
            status = "RUNNING" if process.is_alive() else "STOPPED"
            pid = process.pid if process.is_alive() else "N/A"
            log.info("  %s: %s (PID: %s)", name.upper(), status, pid)
    
    def monitor(self):
        """Monitor agents and restart if they crash"""
        log.info("Monitoring agents... (Press Ctrl+C to stop)")
        
        def signal_handler(signum, frame):
            log.info("Received shutdown signal")
            self.shutdown = True
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            while not self.shutdown:
                for name, process in list(self.processes.items()):
                    if not process.is_alive():
                        log.warning("%s agent crashed, restarting...", name)
                        del self.processes[name]
                        self.start_agent(name, self.agents[name])
                
                time.sleep(5)  # Check every 5 seconds
                
        except KeyboardInterrupt:
            log.info("Monitoring interrupted")
        
        finally:
            self.stop_all()

def main():
    parser = argparse.ArgumentParser(description='AgentKit Phase-1 Launcher')
    parser.add_argument('command', choices=['start', 'stop', 'status', 'monitor', 'test'], 
                       help='Command to execute')
    parser.add_argument('--agents', nargs='*', 
                       choices=['command_poller', 'content_distribution', 'site_scanner', 'report_generator'],
                       help='Specific agents to start (default: all)')
    parser.add_argument('--check-env', action='store_true', help='Only check environment')
    
    args = parser.parse_args()
    
    launcher = AgentLauncher()
    
    if args.check_env:
        success = launcher.check_environment()
        sys.exit(0 if success else 1)
    
    if args.command == 'start':
        success = launcher.start_all(args.agents)
        if success:
            launcher.monitor()
        sys.exit(0 if success else 1)
    
    elif args.command == 'stop':
        launcher.stop_all()
    
    elif args.command == 'status':
        launcher.status()
    
    elif args.command == 'monitor':
        if launcher.processes:
            launcher.monitor()
        else:
            log.error("No agents running. Start them first.")
    
    elif args.command == 'test':
        # Test mode: run each agent briefly to check for import errors
        log.info("Testing agent imports...")
        
        try:
            from agents.command_poller import Poller
            log.info("✓ Command poller imports OK")
        except Exception as e:
            log.error("✗ Command poller import failed: %s", e)
        
        try:
            from agents.content_distribution_agent import Distributor
            log.info("✓ Content distribution agent imports OK")
        except Exception as e:
            log.error("✗ Content distribution agent import failed: %s", e)
        
        try:
            from agents.site_scanner import SiteScanner
            log.info("✓ Site scanner imports OK")
        except Exception as e:
            log.error("✗ Site scanner import failed: %s", e)
        
        try:
            from agents.report_generator import ReportGenerator
            log.info("✓ Report generator imports OK")
        except Exception as e:
            log.error("✗ Report generator import failed: %s", e)

if __name__ == '__main__':
    main()