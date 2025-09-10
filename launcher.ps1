# Social Media Jobs Launcher - PowerShell Version
# Interactive launcher for running social media scraping jobs

param(
    [string]$Job = "",
    [string]$Client = "",
    [switch]$List,
    [switch]$All,
    [switch]$Help
)

# Set console encoding to UTF-8 for emoji support
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Show-Menu {
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "🚀 SOCIAL MEDIA JOBS LAUNCHER" -ForegroundColor Yellow
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "Available Jobs:" -ForegroundColor White
    Write-Host "-" * 40 -ForegroundColor Gray
    
    $jobs = @(
        @{Key="1"; Name="youtubeSearch"; Description="YouTube search-based video collection"},
        @{Key="2"; Name="youtubeChannel"; Description="YouTube channel-specific video collection"},
        @{Key="3"; Name="youtubeBmw"; Description="YouTube BMW channel data collection"},
        @{Key="4"; Name="twitter"; Description="Twitter/X tweet data collection"},
        @{Key="5"; Name="facebook"; Description="Facebook post data collection"},
        @{Key="6"; Name="modiTwitter"; Description="Modi family Twitter data collection"},
        @{Key="7"; Name="all"; Description="Run all available jobs"},
        @{Key="8"; Name="list"; Description="List all available jobs"}
    )
    
    foreach ($job in $jobs) {
        $status = if ($job.Key -in @("1","2","3","4","5","6")) { "✅" } else { "📋" }
        Write-Host "$status $($job.Key). $($job.Name.PadRight(15)) - $($job.Description)" -ForegroundColor Green
    }
    
    Write-Host "-" * 40 -ForegroundColor Gray
    Write-Host "Commands:" -ForegroundColor White
    Write-Host "  q, quit, exit  - Exit launcher" -ForegroundColor Yellow
    Write-Host "  help          - Show this menu" -ForegroundColor Yellow
    Write-Host "  status        - Check job status" -ForegroundColor Yellow
    Write-Host "=" * 60 -ForegroundColor Cyan
}

function Run-Job {
    param(
        [string]$JobName,
        [string]$ClientFilter = ""
    )
    
    try {
        Write-Host ""
        Write-Host "🚀 Starting job: $JobName" -ForegroundColor Yellow
        
        if ($ClientFilter) {
            Write-Host "📋 Client filter: $ClientFilter" -ForegroundColor Cyan
        }
        
        # Build command
        $cmd = "python", "main.py", "--job", $JobName
        if ($ClientFilter) {
            $cmd += "--client", $ClientFilter
        }
        
        # Run the job
        $result = & $cmd[0] $cmd[1..($cmd.Length-1)] 2>&1
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            Write-Host "✅ Job '$JobName' completed successfully!" -ForegroundColor Green
            if ($result) {
                Write-Host "Output: $result" -ForegroundColor White
            }
        } else {
            Write-Host "❌ Job '$JobName' failed!" -ForegroundColor Red
            if ($result) {
                Write-Host "Error: $result" -ForegroundColor Red
            }
        }
        
        return $exitCode -eq 0
        
    } catch {
        Write-Host "❌ Error running job '$JobName': $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Run-AllJobs {
    param([string]$ClientFilter = "")
    
    try {
        Write-Host ""
        Write-Host "🚀 Starting all jobs..." -ForegroundColor Yellow
        
        if ($ClientFilter) {
            Write-Host "📋 Client filter: $ClientFilter" -ForegroundColor Cyan
        }
        
        $cmd = "python", "main.py", "--all"
        if ($ClientFilter) {
            $cmd += "--client", $ClientFilter
        }
        
        $result = & $cmd[0] $cmd[1..($cmd.Length-1)] 2>&1
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            Write-Host "✅ All jobs completed successfully!" -ForegroundColor Green
        } else {
            Write-Host "❌ Some jobs failed!" -ForegroundColor Red
        }
        
        if ($result) {
            Write-Host "Output: $result" -ForegroundColor White
        }
        
        return $exitCode -eq 0
        
    } catch {
        Write-Host "❌ Error running all jobs: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function List-Jobs {
    try {
        Write-Host ""
        Write-Host "📋 Listing available jobs..." -ForegroundColor Yellow
        
        $result = python main.py --list 2>&1
        $exitCode = $LASTEXITCODE
        
        if ($result) {
            Write-Host $result -ForegroundColor White
        }
        
        return $exitCode -eq 0
        
    } catch {
        Write-Host "❌ Error listing jobs: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Check-Status {
    Write-Host ""
    Write-Host "🔍 Checking system status..." -ForegroundColor Yellow
    
    # Check if main.py exists
    if (Test-Path "main.py") {
        Write-Host "✅ main.py found" -ForegroundColor Green
    } else {
        Write-Host "❌ main.py not found" -ForegroundColor Red
        return $false
    }
    
    # Check if src directory exists
    if (Test-Path "src") {
        Write-Host "✅ src/ directory found" -ForegroundColor Green
    } else {
        Write-Host "❌ src/ directory not found" -ForegroundColor Red
        return $false
    }
    
    # Check if .env file exists
    if (Test-Path ".env") {
        Write-Host "✅ .env file found" -ForegroundColor Green
    } else {
        Write-Host "⚠️  .env file not found (may need configuration)" -ForegroundColor Yellow
    }
    
    # Try to list jobs
    Write-Host ""
    Write-Host "📋 Available jobs:" -ForegroundColor White
    List-Jobs
    
    return $true
}

function Get-ClientFilter {
    Write-Host ""
    Write-Host "📋 Client Filter (optional):" -ForegroundColor White
    Write-Host "Enter client ID to filter jobs, or press Enter to skip:" -ForegroundColor Gray
    $clientFilter = Read-Host "Client ID"
    return if ($clientFilter.Trim()) { $clientFilter.Trim() } else { "" }
}

# Main execution logic
if ($Help) {
    Write-Host "Social Media Jobs Launcher - PowerShell Version" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor White
    Write-Host "  .\launcher.ps1                    # Interactive mode" -ForegroundColor Gray
    Write-Host "  .\launcher.ps1 -Job youtubeBmw    # Run specific job" -ForegroundColor Gray
    Write-Host "  .\launcher.ps1 -All               # Run all jobs" -ForegroundColor Gray
    Write-Host "  .\launcher.ps1 -List              # List available jobs" -ForegroundColor Gray
    Write-Host "  .\launcher.ps1 -Client client123  # Filter by client" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor White
    Write-Host "  .\launcher.ps1 -Job youtubeBmw -Client bmw123" -ForegroundColor Gray
    Write-Host "  .\launcher.ps1 -All" -ForegroundColor Gray
    exit 0
}

# Handle direct command line execution
if ($Job -or $All -or $List) {
    if ($List) {
        List-Jobs
    } elseif ($All) {
        $clientFilter = if ($Client) { $Client } else { Get-ClientFilter }
        Run-AllJobs -ClientFilter $clientFilter
    } elseif ($Job) {
        $clientFilter = if ($Client) { $Client } else { Get-ClientFilter }
        Run-Job -JobName $Job -ClientFilter $clientFilter
    }
    exit 0
}

# Interactive mode
Write-Host "🚀 Social Media Jobs Launcher started!" -ForegroundColor Green

$availableJobs = @{
    "1" = "youtubeSearch"
    "2" = "youtubeChannel"
    "3" = "youtubeBmw"
    "4" = "twitter"
    "5" = "facebook"
    "6" = "modiTwitter"
    "7" = "all"
    "8" = "list"
}

while ($true) {
    Show-Menu
    
    try {
        $choice = (Read-Host "Enter your choice").Trim().ToLower()
        
        if ($choice -in @("q", "quit", "exit")) {
            Write-Host "👋 Goodbye!" -ForegroundColor Yellow
            break
        }
        elseif ($choice -eq "help") {
            continue  # Redisplay menu
        }
        elseif ($choice -eq "status") {
            Check-Status
            continue
        }
        elseif ($availableJobs.ContainsKey($choice)) {
            $jobName = $availableJobs[$choice]
            
            if ($jobName -eq "list") {
                List-Jobs
            }
            elseif ($jobName -eq "all") {
                $clientFilter = Get-ClientFilter
                Run-AllJobs -ClientFilter $clientFilter
            }
            else {
                $clientFilter = Get-ClientFilter
                Run-Job -JobName $jobName -ClientFilter $clientFilter
            }
            
            Read-Host "Press Enter to continue"
        }
        else {
            Write-Host "❌ Invalid choice: $choice" -ForegroundColor Red
            Write-Host "Type 'help' to see available options" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}
