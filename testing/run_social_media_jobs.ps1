# Improved Social Media Jobs Runner (PowerShell)
# Uses the new configuration system and improved scrapers

# Set script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Load environment variables from .env file
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

# Create logs directory if it doesn't exist
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

# Set log file with timestamp
$LogFile = "logs\social_media_jobs_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# Function to log messages
function Log-Message {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry
}

# Function to run a script with error handling
function Run-Script {
    param(
        [string]$ScriptName,
        [string]$ScriptPath
    )
    
    Log-Message "Starting $ScriptName..."
    
    if (Test-Path $ScriptPath) {
        try {
            $Output = python $ScriptPath 2>&1
            if ($LASTEXITCODE -eq 0) {
                Log-Message "✅ $ScriptName completed successfully"
                return $true
            } else {
                Log-Message "❌ $ScriptName failed - check logs for details"
                Log-Message "Error output: $Output"
                return $false
            }
        } catch {
            Log-Message "❌ Error running $ScriptName : $($_.Exception.Message)"
            return $false
        }
    } else {
        Log-Message "❌ Script not found: $ScriptPath"
        return $false
    }
}

# Main execution
function Main {
    Log-Message "🚀 Starting Social Media Jobs Pipeline"
    Log-Message "=========================================="
    
    # Check if .env file exists
    if (!(Test-Path ".env")) {
        Log-Message "❌ .env file not found. Please run setup.py first"
        exit 1
    }
    
    # Check if required environment variables are set
    $RequiredVars = @("YOUTUBE_API_KEY", "TWITTER_BEARER_TOKEN", "APIFY_API_TOKEN")
    $MissingVars = @()
    
    foreach ($Var in $RequiredVars) {
        if (![Environment]::GetEnvironmentVariable($Var)) {
            $MissingVars += $Var
        }
    }
    
    if ($MissingVars.Count -gt 0) {
        Log-Message "❌ Required API keys not set: $($MissingVars -join ', ')"
        exit 1
    }
    
    # Run improved scrapers
    Log-Message "📊 Running Social Media Scrapers..."
    
    # YouTube scraper
    Run-Script "YouTube Scraper" "youtube_scraper_improved.py"
    Start-Sleep -Seconds 30
    
    # Twitter scraper  
    Run-Script "Twitter Scraper" "twitter_scraper_improved.py"
    Start-Sleep -Seconds 30
    
    # Facebook scraper (using existing script for now)
    Run-Script "Facebook Scraper" "MainapifyFacebook.py"
    Start-Sleep -Seconds 30
    
    # Data migration scripts
    Log-Message "🔄 Running Data Migration..."
    Run-Script "X Feed Migration" "mongodbtocollectionpnqxfeed.py"
    Start-Sleep -Seconds 30
    
    Run-Script "YouTube Migration" "mongodbtocollectionpnqyoutube.py"
    Start-Sleep -Seconds 30
    
    Run-Script "Facebook Migration" "facebookdatatomongo.py"
    
    Log-Message "=========================================="
    Log-Message "✅ Social Media Jobs Pipeline completed"
    Log-Message "📋 Check $LogFile for detailed logs"
}

# Run main function
Main
