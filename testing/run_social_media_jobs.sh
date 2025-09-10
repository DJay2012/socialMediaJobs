#!/bin/bash

# Improved Social Media Jobs Runner
# Uses the new configuration system and improved scrapers

# Set script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Set log file with timestamp
LOG_FILE="logs/social_media_jobs_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to run a script with error handling
run_script() {
    local script_name="$1"
    local script_path="$2"
    
    log_message "Starting $script_name..."
    
    if [ -f "$script_path" ]; then
        if python3 "$script_path" >> "$LOG_FILE" 2>&1; then
            log_message "✅ $script_name completed successfully"
        else
            log_message "❌ $script_name failed - check logs for details"
            return 1
        fi
    else
        log_message "❌ Script not found: $script_path"
        return 1
    fi
}

# Main execution
main() {
    log_message "🚀 Starting Social Media Jobs Pipeline"
    log_message "=========================================="
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        log_message "❌ .env file not found. Please run setup.py first"
        exit 1
    fi
    
    # Check if required environment variables are set
    if [ -z "$YOUTUBE_API_KEY" ] || [ -z "$TWITTER_BEARER_TOKEN" ] || [ -z "$APIFY_API_TOKEN" ]; then
        log_message "❌ Required API keys not set in .env file"
        exit 1
    fi
    
    # Run improved scrapers
    log_message "📊 Running Social Media Scrapers..."
    
    # YouTube scraper
    run_script "YouTube Scraper" "youtube_scraper_improved.py"
    sleep 30
    
    # Twitter scraper  
    run_script "Twitter Scraper" "twitter_scraper_improved.py"
    sleep 30
    
    # Facebook scraper (using existing script for now)
    run_script "Facebook Scraper" "MainapifyFacebook.py"
    sleep 30
    
    # Data migration scripts
    log_message "🔄 Running Data Migration..."
    run_script "X Feed Migration" "mongodbtocollectionpnqxfeed.py"
    sleep 30
    
    run_script "YouTube Migration" "mongodbtocollectionpnqyoutube.py"
    sleep 30
    
    run_script "Facebook Migration" "facebookdatatomongo.py"
    
    log_message "=========================================="
    log_message "✅ Social Media Jobs Pipeline completed"
    log_message "📋 Check $LOG_FILE for detailed logs"
}

# Handle script interruption
trap 'log_message "⚠️  Script interrupted by user"; exit 1' INT TERM

# Run main function
main "$@"
