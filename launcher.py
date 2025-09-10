#!/usr/bin/env python3
"""
Social Media Jobs Launcher
Interactive launcher for running social media scraping jobs
"""
import sys
import os
import subprocess
from pathlib import Path
from typing import Dict, List

class SocialMediaLauncher:
    """Interactive launcher for social media jobs"""
    
    def __init__(self):
        self.projectRoot = Path(__file__).parent
        self.availableJobs = {
            '1': {'name': 'youtubeSearch', 'description': 'YouTube search-based video collection'},
            '2': {'name': 'youtubeChannel', 'description': 'YouTube channel-specific video collection'},
            '3': {'name': 'youtubeBmw', 'description': 'YouTube BMW channel data collection'},
            '4': {'name': 'twitter', 'description': 'Twitter/X tweet data collection'},
            '5': {'name': 'facebook', 'description': 'Facebook post data collection'},
            '6': {'name': 'modiTwitter', 'description': 'Modi family Twitter data collection'},
            '7': {'name': 'all', 'description': 'Run all available jobs'},
            '8': {'name': 'list', 'description': 'List all available jobs'}
        }
    
    def displayMenu(self):
        """Display the main menu"""
        print("\n" + "="*60)
        print("🚀 SOCIAL MEDIA JOBS LAUNCHER")
        print("="*60)
        print("Available Jobs:")
        print("-" * 40)
        
        for key, job in self.availableJobs.items():
            status = "✅" if key in ['1', '2', '3', '4', '5', '6'] else "📋"
            print(f"{status} {key}. {job['name']:<15} - {job['description']}")
        
        print("-" * 40)
        print("Commands:")
        print("  q, quit, exit  - Exit launcher")
        print("  help          - Show this menu")
        print("  status        - Check job status")
        print("="*60)
    
    def runJob(self, jobName: str, clientFilter: str = None):
        """Run a specific job"""
        try:
            print(f"\n🚀 Starting job: {jobName}")
            if clientFilter:
                print(f"📋 Client filter: {clientFilter}")
            
            # Build command
            cmd = [sys.executable, "main.py", "--job", jobName]
            if clientFilter:
                cmd.extend(["--client", clientFilter])
            
            # Run the job
            result = subprocess.run(cmd, cwd=self.projectRoot, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Job '{jobName}' completed successfully!")
                if result.stdout:
                    print("Output:", result.stdout)
            else:
                print(f"❌ Job '{jobName}' failed!")
                if result.stderr:
                    print("Error:", result.stderr)
                if result.stdout:
                    print("Output:", result.stdout)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Error running job '{jobName}': {e}")
            return False
    
    def runAllJobs(self, clientFilter: str = None):
        """Run all available jobs"""
        try:
            print(f"\n🚀 Starting all jobs...")
            if clientFilter:
                print(f"📋 Client filter: {clientFilter}")
            
            cmd = [sys.executable, "main.py", "--all"]
            if clientFilter:
                cmd.extend(["--client", clientFilter])
            
            result = subprocess.run(cmd, cwd=self.projectRoot, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ All jobs completed successfully!")
            else:
                print("❌ Some jobs failed!")
                if result.stderr:
                    print("Error:", result.stderr)
            
            if result.stdout:
                print("Output:", result.stdout)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Error running all jobs: {e}")
            return False
    
    def listJobs(self):
        """List all available jobs"""
        try:
            print(f"\n📋 Listing available jobs...")
            
            cmd = [sys.executable, "main.py", "--list"]
            result = subprocess.run(cmd, cwd=self.projectRoot, capture_output=True, text=True)
            
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print("Error:", result.stderr)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Error listing jobs: {e}")
            return False
    
    def checkStatus(self):
        """Check the status of the system"""
        print(f"\n🔍 Checking system status...")
        
        # Check if main.py exists
        mainFile = self.projectRoot / "main.py"
        if mainFile.exists():
            print("✅ main.py found")
        else:
            print("❌ main.py not found")
            return False
        
        # Check if src directory exists
        srcDir = self.projectRoot / "src"
        if srcDir.exists():
            print("✅ src/ directory found")
        else:
            print("❌ src/ directory not found")
            return False
        
        # Check if .env file exists
        envFile = self.projectRoot / ".env"
        if envFile.exists():
            print("✅ .env file found")
        else:
            print("⚠️  .env file not found (may need configuration)")
        
        # Try to list jobs
        print("\n📋 Available jobs:")
        self.listJobs()
        
        return True
    
    def getClientFilter(self):
        """Get client filter from user"""
        print("\n📋 Client Filter (optional):")
        print("Enter client ID to filter jobs, or press Enter to skip:")
        clientFilter = input("Client ID: ").strip()
        return clientFilter if clientFilter else None
    
    def run(self):
        """Main launcher loop"""
        print("🚀 Social Media Jobs Launcher started!")
        
        while True:
            self.displayMenu()
            
            try:
                choice = input("\nEnter your choice: ").strip().lower()
                
                if choice in ['q', 'quit', 'exit']:
                    print("👋 Goodbye!")
                    break
                
                elif choice == 'help':
                    continue  # Redisplay menu
                
                elif choice == 'status':
                    self.checkStatus()
                    continue
                
                elif choice in self.availableJobs:
                    jobName = self.availableJobs[choice]['name']
                    
                    if jobName == 'list':
                        self.listJobs()
                    elif jobName == 'all':
                        clientFilter = self.getClientFilter()
                        self.runAllJobs(clientFilter)
                    else:
                        clientFilter = self.getClientFilter()
                        self.runJob(jobName, clientFilter)
                    
                    input("\nPress Enter to continue...")
                
                else:
                    print(f"❌ Invalid choice: {choice}")
                    print("Type 'help' to see available options")
            
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main entry point"""
    launcher = SocialMediaLauncher()
    launcher.run()

if __name__ == "__main__":
    main()
