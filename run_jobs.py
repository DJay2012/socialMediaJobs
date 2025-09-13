#!/usr/bin/env python3
"""
Simple Social Media Jobs Runner
Direct command-line interface for running social media scraping jobs
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_job(job_name, client_filter=None):
    """Run a specific job"""
    try:
        print(f"🚀 Starting job: {job_name}")
        if client_filter:
            print(f"📋 Client filter: {client_filter}")

        cmd = [sys.executable, "main.py", "--job", job_name]
        if client_filter:
            cmd.extend(["--client", client_filter])

        print(cmd)
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ Job '{job_name}' completed successfully!")
            if result.stdout:
                print("Output:", result.stdout)
        else:
            print(f"❌ Job '{job_name}' failed!")
            if result.stderr:
                print("Error:", result.stderr)
            if result.stdout:
                print("Output:", result.stdout)

        # Also show stderr as info (since logging goes to stderr)
        if result.stderr and result.returncode == 0:
            print("Logs:", result.stderr)

        return result.returncode == 0

    except Exception as e:
        print(f"❌ Error running job '{job_name}': {e}")
        return False


def run_all_jobs(client_filter=None):
    """Run all available jobs"""
    try:
        print(f"🚀 Starting all jobs...")
        if client_filter:
            print(f"📋 Client filter: {client_filter}")

        cmd = [sys.executable, "main.py", "--all"]
        if client_filter:
            cmd.extend(["--client", client_filter])

        result = subprocess.run(cmd, capture_output=True, text=True)

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


def list_jobs():
    """List all available jobs"""
    try:
        print(f"📋 Listing available jobs...")

        cmd = [sys.executable, "main.py", "--list"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            # For list command, stderr contains logging info, not errors
            if result.returncode == 0:
                print("Logs:", result.stderr)
            else:
                print("Error:", result.stderr)

        return result.returncode == 0

    except Exception as e:
        print(f"❌ Error listing jobs: {e}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Social Media Jobs Runner - Simple Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_jobs.py youtubeBmw                    # Run YouTube BMW job
  python run_jobs.py youtubeBmw --client bmw123   # Run with client filter
  python run_jobs.py --all                        # Run all jobs
  python run_jobs.py --list                       # List available jobs
  python run_jobs.py --interactive                # Interactive mode
        """,
    )

    parser.add_argument(
        "job",
        nargs="?",
        help="Job name to run (youtubeSearch, youtubeChannel, youtubeBmw, twitter, facebook, modiTwitter)",
    )
    parser.add_argument("--client", "-c", help="Client ID filter")
    parser.add_argument(
        "--all", "-a", action="store_true", help="Run all available jobs"
    )
    parser.add_argument(
        "--list", "-l", action="store_true", help="List all available jobs"
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Interactive mode"
    )

    args = parser.parse_args()

    # Interactive mode
    if args.interactive:
        print("🚀 Social Media Jobs Runner - Interactive Mode")
        print("=" * 50)

        while True:
            print("\nAvailable commands:")
            print("1. youtubeSearch   - YouTube search-based video collection")
            print("2. youtubeChannel  - YouTube channel-specific video collection")
            print("3. youtubeBmw      - YouTube BMW channel data collection")
            print("4. twitter         - Twitter/X tweet data collection")
            print("5. facebook        - Facebook post data collection")
            print("6. modiTwitter     - Modi family Twitter data collection")
            print("7. all            - Run all available jobs")
            print("8. list           - List all available jobs")
            print("q. quit           - Exit")

            choice = input("\nEnter your choice: ").strip().lower()

            if choice in ["q", "quit", "exit"]:
                print("👋 Goodbye!")
                break
            elif choice == "1":
                run_job("youtubeSearch", args.client)
            elif choice == "2":
                run_job("youtubeChannel", args.client)
            elif choice == "3":
                run_job("youtubeBmw", args.client)
            elif choice == "4":
                run_job("twitter", args.client)
            elif choice == "5":
                run_job("facebook", args.client)
            elif choice == "6":
                run_job("modiTwitter", args.client)
            elif choice == "7":
                run_all_jobs(args.client)
            elif choice == "8":
                list_jobs()
            else:
                print("❌ Invalid choice. Please try again.")

            input("\nPress Enter to continue...")

    # Command line mode
    elif args.list:
        list_jobs()
    elif args.all:
        run_all_jobs(args.client)
    elif args.job:
        run_job(args.job, args.client)
    else:
        parser.print_help()
        print("\n💡 Tip: Use --interactive for a menu-driven interface")


if __name__ == "__main__":
    main()
