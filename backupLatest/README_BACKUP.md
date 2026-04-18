# Backup Latest - Old Scripts

This folder contains all the original scripts that were moved from the root directory to make way for the new organized structure.

## 📁 What's in this backup:

### **Original Python Scripts**
- `BmwYoutube.py` - Original BMW YouTube scraper
- `MainScriptXfeedNew.py` - Original Twitter scraper
- `MainapifyFacebook.py` - Original Facebook scraper
- `MainScriptyoutube.py` - Original YouTube scraper
- `MainScriptYoutubeAll.py` - Original YouTube all scraper
- `ModiXfeed.py` - Original Modi Twitter scraper
- `newtwitterapi.py` - Original new Twitter API scraper
- `facebookdatatomongo.py` - Facebook data migration script
- `mongodbtocollectionpnqxfeed.py` - X feed migration script
- `mongodbtocollectionpnqyoutube.py` - YouTube migration script

### **Shell Scripts**
- `new.sh` - New data collection script
- `onetime.sh` - One-time data collection script
- `social.sh` - Social media collection script

### **Other Files**
- `Backup/` - Original backup folder with additional scripts
- `newscheckerfile/` - News checking functionality
- `YOUTUBE_BMW.PY` - Alternative BMW YouTube script

## 🔄 Migration to New Structure

| **Old Script** | **New Location** | **Status** |
|----------------|------------------|------------|
| `MainScriptyoutube.py` | `youtube/youtube_scraper.py` | ✅ Migrated |
| `MainScriptXfeedNew.py` | `twitter/twitter_scraper.py` | ✅ Migrated |
| `MainapifyFacebook.py` | `facebook/facebook_scraper.py` | ✅ Migrated |
| `BmwYoutube.py` | `youtube/youtube_bmw_scraper.py` | ✅ Migrated |
| `ModiXfeed.py` | `twitter/modi_twitter_scraper.py` | ✅ Migrated |

## 🚀 New Usage

Instead of running individual scripts, use the new main runner:

```bash
# Old way
python MainScriptyoutube.py
python MainScriptXfeedNew.py
python MainapifyFacebook.py

# New way
python main.py --job youtube
python main.py --job twitter
python main.py --job facebook
python main.py --all
```

## 📊 Benefits of New Structure

- ✅ **Organized**: Each platform has its own folder
- ✅ **Configurable**: Easy to enable/disable specific jobs
- ✅ **Maintainable**: Clear separation of concerns
- ✅ **Secure**: All secrets in environment variables
- ✅ **Monitored**: Centralized logging and error handling

## 🔧 If You Need to Restore

If you need to use any of the old scripts temporarily:

1. Copy the script from this backup folder to the root directory
2. Make sure you have the required dependencies installed
3. Update any hardcoded paths or credentials

**Note**: The old scripts contain hardcoded API keys and database credentials, so use them carefully in production environments.

## 📅 Backup Date

Created: September 10, 2025
Reason: Reorganization to new folder structure with main.py runner
