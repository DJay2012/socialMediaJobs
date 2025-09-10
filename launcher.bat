@echo off
REM Social Media Jobs Launcher - Batch File Version
REM Simple launcher for running social media scraping jobs

setlocal enabledelayedexpansion

:MAIN_MENU
cls
echo.
echo ============================================================
echo 🚀 SOCIAL MEDIA JOBS LAUNCHER
echo ============================================================
echo Available Jobs:
echo ------------------------------------------------------------
echo ✅ 1. youtubeSearch   - YouTube search-based video collection
echo ✅ 2. youtubeChannel  - YouTube channel-specific video collection
echo ✅ 3. youtubeBmw      - YouTube BMW channel data collection
echo ✅ 4. twitter         - Twitter/X tweet data collection
echo ✅ 5. facebook        - Facebook post data collection
echo ✅ 6. modiTwitter     - Modi family Twitter data collection
echo 📋 7. all            - Run all available jobs
echo 📋 8. list           - List all available jobs
echo ------------------------------------------------------------
echo Commands:
echo   q, quit, exit  - Exit launcher
echo   help          - Show this menu
echo   status        - Check job status
echo ============================================================
echo.

set /p choice="Enter your choice: "

if /i "%choice%"=="q" goto :EXIT
if /i "%choice%"=="quit" goto :EXIT
if /i "%choice%"=="exit" goto :EXIT
if /i "%choice%"=="help" goto :MAIN_MENU
if /i "%choice%"=="status" goto :CHECK_STATUS
if "%choice%"=="1" goto :RUN_YOUTUBE_SEARCH
if "%choice%"=="2" goto :RUN_YOUTUBE_CHANNEL
if "%choice%"=="3" goto :RUN_YOUTUBE_BMW
if "%choice%"=="4" goto :RUN_TWITTER
if "%choice%"=="5" goto :RUN_FACEBOOK
if "%choice%"=="6" goto :RUN_MODI_TWITTER
if "%choice%"=="7" goto :RUN_ALL
if "%choice%"=="8" goto :LIST_JOBS

echo ❌ Invalid choice: %choice%
echo Type 'help' to see available options
pause
goto :MAIN_MENU

:RUN_YOUTUBE_SEARCH
echo.
echo 🚀 Starting job: youtubeSearch
call :GET_CLIENT_FILTER
if "%client_filter%"=="" (
    python main.py --job youtubeSearch
) else (
    python main.py --job youtubeSearch --client %client_filter%
)
goto :PAUSE_AND_CONTINUE

:RUN_YOUTUBE_CHANNEL
echo.
echo 🚀 Starting job: youtubeChannel
call :GET_CLIENT_FILTER
if "%client_filter%"=="" (
    python main.py --job youtubeChannel
) else (
    python main.py --job youtubeChannel --client %client_filter%
)
goto :PAUSE_AND_CONTINUE

:RUN_YOUTUBE_BMW
echo.
echo 🚀 Starting job: youtubeBmw
call :GET_CLIENT_FILTER
if "%client_filter%"=="" (
    python main.py --job youtubeBmw
) else (
    python main.py --job youtubeBmw --client %client_filter%
)
goto :PAUSE_AND_CONTINUE

:RUN_TWITTER
echo.
echo 🚀 Starting job: twitter
call :GET_CLIENT_FILTER
if "%client_filter%"=="" (
    python main.py --job twitter
) else (
    python main.py --job twitter --client %client_filter%
)
goto :PAUSE_AND_CONTINUE

:RUN_FACEBOOK
echo.
echo 🚀 Starting job: facebook
call :GET_CLIENT_FILTER
if "%client_filter%"=="" (
    python main.py --job facebook
) else (
    python main.py --job facebook --client %client_filter%
)
goto :PAUSE_AND_CONTINUE

:RUN_MODI_TWITTER
echo.
echo 🚀 Starting job: modiTwitter
call :GET_CLIENT_FILTER
if "%client_filter%"=="" (
    python main.py --job modiTwitter
) else (
    python main.py --job modiTwitter --client %client_filter%
)
goto :PAUSE_AND_CONTINUE

:RUN_ALL
echo.
echo 🚀 Starting all jobs...
call :GET_CLIENT_FILTER
if "%client_filter%"=="" (
    python main.py --all
) else (
    python main.py --all --client %client_filter%
)
goto :PAUSE_AND_CONTINUE

:LIST_JOBS
echo.
echo 📋 Listing available jobs...
python main.py --list
goto :PAUSE_AND_CONTINUE

:CHECK_STATUS
echo.
echo 🔍 Checking system status...

if exist "main.py" (
    echo ✅ main.py found
) else (
    echo ❌ main.py not found
    goto :PAUSE_AND_CONTINUE
)

if exist "src" (
    echo ✅ src/ directory found
) else (
    echo ❌ src/ directory not found
    goto :PAUSE_AND_CONTINUE
)

if exist ".env" (
    echo ✅ .env file found
) else (
    echo ⚠️  .env file not found (may need configuration)
)

echo.
echo 📋 Available jobs:
python main.py --list
goto :PAUSE_AND_CONTINUE

:GET_CLIENT_FILTER
echo.
echo 📋 Client Filter (optional):
echo Enter client ID to filter jobs, or press Enter to skip:
set /p client_filter="Client ID: "
goto :EOF

:PAUSE_AND_CONTINUE
echo.
pause
goto :MAIN_MENU

:EXIT
echo.
echo 👋 Goodbye!
exit /b 0
