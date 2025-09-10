"""
Log Management Utility
Command-line tool to manage log files in home directory
"""
import argparse
import os
from pathlib import Path
from datetime import datetime, timedelta

def list_logs():
    """List all social media job log files in home directory"""
    home_dir = Path.home()
    log_files = list(home_dir.glob('social_media_jobs_*.log'))
    
    if not log_files:
        print("No log files found in home directory")
        return
    
    print(f"\nSocial Media Jobs Log Files in {home_dir}:")
    print("=" * 60)
    
    # Sort by modification time (newest first)
    log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    for log_file in log_files:
        stat = log_file.stat()
        size = stat.st_size
        modified = datetime.fromtimestamp(stat.st_mtime)
        
        size_str = f"{size:,} bytes" if size > 0 else "Empty"
        print(f"{log_file.name}")
        print(f"  Size: {size_str}")
        print(f"  Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

def clean_old_logs(days: int = 7):
    """Clean log files older than specified days"""
    home_dir = Path.home()
    log_files = list(home_dir.glob('social_media_jobs_*.log'))
    
    if not log_files:
        print("No log files found to clean")
        return
    
    cutoff_date = datetime.now() - timedelta(days=days)
    deleted_count = 0
    
    for log_file in log_files:
        modified = datetime.fromtimestamp(log_file.stat().st_mtime)
        if modified < cutoff_date:
            try:
                log_file.unlink()
                print(f"Deleted: {log_file.name}")
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting {log_file.name}: {e}")
    
    print(f"\nCleaned {deleted_count} log files older than {days} days")

def show_latest_log(lines: int = 50):
    """Show the latest log file content"""
    home_dir = Path.home()
    log_files = list(home_dir.glob('social_media_jobs_*.log'))
    
    if not log_files:
        print("No log files found")
        return
    
    # Get the newest log file
    latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
    
    print(f"\nLatest log file: {latest_log.name}")
    print("=" * 60)
    
    try:
        with open(latest_log, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            
        # Show last N lines
        start_line = max(0, len(all_lines) - lines)
        for line in all_lines[start_line:]:
            print(line.rstrip())
            
    except Exception as e:
        print(f"Error reading log file: {e}")

def open_logs_folder():
    """Open the home directory in file explorer"""
    home_dir = Path.home()
    log_files = list(home_dir.glob('social_media_jobs_*.log'))
    
    if not log_files:
        print("No log files found")
        return
    
    try:
        os.startfile(str(home_dir))
        print(f"Opened {home_dir} in file explorer")
    except Exception as e:
        print(f"Error opening folder: {e}")

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description='Manage social media jobs log files')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all log files')
    
    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Clean old log files')
    clean_parser.add_argument('--days', type=int, default=7, 
                             help='Delete files older than N days (default: 7)')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show latest log content')
    show_parser.add_argument('--lines', type=int, default=50,
                            help='Number of lines to show (default: 50)')
    
    # Open command
    open_parser = subparsers.add_parser('open', help='Open logs folder in file explorer')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'list':
        list_logs()
    elif args.command == 'clean':
        clean_old_logs(args.days)
    elif args.command == 'show':
        show_latest_log(args.lines)
    elif args.command == 'open':
        open_logs_folder()

if __name__ == "__main__":
    main()
