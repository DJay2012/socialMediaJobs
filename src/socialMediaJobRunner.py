"""
Main Social Media Jobs Runner
Configurable job runner that can execute specific social media scrapers
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from socialMediaConfig import config

class SocialMediaJobRunner:
    """Main job runner for social media scrapers"""
    
    def __init__(self):
        self.setupLogging()
        self.logger = logging.getLogger(__name__)
        self.availableJobs = self.discoverJobs()
    
    def setupLogging(self):
        """Setup logging configuration"""
        # Log to home directory instead of separate logs folder
        home_dir = Path.home()
        log_file = home_dir / f'social_media_jobs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def discoverJobs(self) -> Dict[str, Dict]:
        """Discover available jobs from folder structure"""
        jobs = {}
        
        # Define job configurations
        jobConfigs = {
            'youtubeSearch': {
                'folder': 'src/youtube',
                'script': 'youtubeSearchScraper.py',
                'class': 'YouTubeSearchScraper',
                'description': 'YouTube search-based video collection',
                'search_type': 'youtube'
            },
            'youtubeChannel': {
                'folder': 'src/youtube',
                'script': 'youtubeScraper.py',
                'class': 'YouTubeScraper',
                'description': 'YouTube channel-specific video collection',
                'search_type': 'youtube'
            },
            'youtubeBmw': {
                'folder': 'src/youtube',
                'script': 'youtubeBmwScraper.py',
                'class': 'YouTubeBmwScraper', 
                'description': 'YouTube BMW channel data collection',
                'search_type': 'youtubeBmw'
            },
            'twitter': {
                'folder': 'src/twitter', 
                'script': 'twitterScraper.py',
                'class': 'TwitterScraper',
                'description': 'Twitter/X tweet data collection',
                'search_type': 'xfeed'
            },
            'facebook': {
                'folder': 'src/facebook',
                'script': 'facebookScraper.py', 
                'class': 'FacebookScraper',
                'description': 'Facebook post data collection',
                'search_type': 'facebook'
            },
            'modiTwitter': {
                'folder': 'src/twitter',
                'script': 'modiTwitterScraper.py',
                'class': 'ModiTwitterScraper',
                'description': 'Modi family Twitter data collection',
                'search_type': 'modi'
            }
        }
        
        # Check which jobs are available
        for jobName, jobConfig in jobConfigs.items():
            folderPath = Path(jobConfig['folder'])
            scriptPath = folderPath / jobConfig['script']
            
            if folderPath.exists() and scriptPath.exists():
                jobs[jobName] = jobConfig
                self.logger.info(f"Discovered job: {jobName}")
            else:
                self.logger.warning(f"Job not available: {jobName} (missing {scriptPath})")
        
        return jobs
    
    def listJobs(self):
        """List all available jobs"""
        print("\nAvailable Social Media Jobs:")
        print("=" * 50)
        
        if not self.availableJobs:
            print("No jobs available. Check folder structure and scripts.")
            return
        
        for jobName, jobConfig in self.availableJobs.items():
            status = "OK" if self.isJobReady(jobName) else "WARN"
            print(f"{status} {jobName:15} - {jobConfig['description']}")
        
        print("\nUsage: python socialMediaJobRunner.py --job <job_name>")
        print("Example: python socialMediaJobRunner.py --job youtube")
    
    def isJobReady(self, jobName: str) -> bool:
        """Check if a job is ready to run"""
        if jobName not in self.availableJobs:
            return False
        
        jobConfig = self.availableJobs[jobName]
        scriptPath = Path(jobConfig['folder']) / jobConfig['script']
        
        return scriptPath.exists()
    
    def runJob(self, jobName: str, clientFilter: Optional[str] = None):
        """Run a specific job"""
        if jobName not in self.availableJobs:
            self.logger.error(f"Job '{jobName}' not found")
            self.listJobs()
            return False
        
        jobConfig = self.availableJobs[jobName]
        
        if not self.isJobReady(jobName):
            self.logger.error(f"Job '{jobName}' is not ready")
            return False
        
        try:
            self.logger.info(f"Starting job: {jobName}")
            self.logger.info(f"Description: {jobConfig['description']}")
            
            # Import and run the job
            scriptPath = Path(jobConfig['folder']) / jobConfig['script']
            
            # Add the folder to Python path
            folderPath = str(Path(jobConfig['folder']).absolute())
            if folderPath not in sys.path:
                sys.path.insert(0, folderPath)
            
            # Import the module
            moduleName = jobConfig['script'].replace('.py', '')
            module = __import__(moduleName)
            
            # Get the scraper class
            scraperClass = getattr(module, jobConfig['class'])
            
            # Create and run the scraper
            scraper = scraperClass()
            
            if hasattr(scraper, 'run'):
                scraper.run(jobConfig['search_type'], clientFilter)
            else:
                self.logger.error(f"Scraper class {jobConfig['class']} doesn't have a 'run' method")
                return False
            
            self.logger.info(f"Job '{jobName}' completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Job '{jobName}' failed: {e}")
            return False
    
    def runAllJobs(self, clientFilter: Optional[str] = None):
        """Run all available jobs"""
        self.logger.info("Starting all available jobs")
        
        results = {}
        for jobName in self.availableJobs:
            self.logger.info(f"\n{'='*50}")
            results[jobName] = self.runJob(jobName, clientFilter)
        
        # Summary
        self.logger.info(f"\n{'='*50}")
        self.logger.info("Job Execution Summary:")
        
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        for jobName, success in results.items():
            status = "SUCCESS" if success else "FAILED"
            self.logger.info(f"{status} {jobName}")
        
        self.logger.info(f"\nCompleted: {successful}/{total} jobs")
        return successful == total

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Social Media Jobs Runner')
    parser.add_argument('--job', type=str, help='Specific job to run')
    parser.add_argument('--list', action='store_true', help='List available jobs')
    parser.add_argument('--all', action='store_true', help='Run all available jobs')
    parser.add_argument('--client', type=str, help='Filter by client ID')
    
    args = parser.parse_args()
    
    runner = SocialMediaJobRunner()
    
    if args.list:
        runner.listJobs()
    elif args.job:
        success = runner.runJob(args.job, args.client)
        sys.exit(0 if success else 1)
    elif args.all:
        success = runner.runAllJobs(args.client)
        sys.exit(0 if success else 1)
    else:
        # Default: show help and list jobs
        parser.print_help()
        print()
        runner.listJobs()

if __name__ == "__main__":
    main()