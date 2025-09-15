# Social Media Jobs - Main README

A comprehensive social media data collection system with configurable job runners, API key management, and automated data processing.

## 🚀 Quick Start

### 1. Installation
```bash
# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file with your API keys:
```bash
YOUTUBE_API_KEY_1=your_youtube_api_key_1
TWITTER_BEARER_TOKEN_1=your_twitter_bearer_token_1
APIFY_API_TOKEN_1=your_apify_api_token_1
MONGO_URI=mongodb://username:password@host:port/
DB_NAME=smFeeds
```

### 3. Run the System
```bash
# List available jobs
python main.py --list

# Run specific job
python main.py --job youtubeSearch
python main.py --job youtubeChannel
python main.py --job youtubeBmw
python main.py --job twitter
python main.py --job facebook
python main.py --job modiTwitter

# Run all jobs
python main.py --all
```

## 📁 Project Structure

```
socialMediaJobs/
├── main.py                              # Main entry point
├── requirements.txt                     # Python dependencies
├── .env                                 # Environment variables
├── src/                                 # Source code directory
│   ├── socialMediaJobRunner.py         # Main job runner
│   ├── socialMediaConfig.py            # Configuration management
│   ├── baseSocialMediaScraper.py       # Base class for all scrapers
│   ├── apiKeysManager.py              # API key management
│   ├── manageApiKeys.py               # API key CLI
│   ├── manageLogs.py                  # Log management CLI
│   ├── youtube/                        # YouTube scrapers
│   ├── twitter/                        # Twitter scrapers
│   └── facebook/                       # Facebook scrapers
├── backupLatest/                       # Original scripts backup
└── testing/                           # Test files and improved versions
```

## 🔧 Available Jobs

- **youtubeSearch**: YouTube search-based video collection
- **youtubeChannel**: YouTube channel-specific video collection
- **youtubeBmw**: YouTube BMW channel data collection
- **twitter**: Twitter/X tweet data collection
- **facebook**: Facebook post data collection
- **modiTwitter**: Modi family Twitter data collection

## 🛠️ Management Tools

### API Key Management
```bash
python src/manageApiKeys.py list
python src/manageApiKeys.py test
python src/manageApiKeys.py add --service youtube --key YOUR_KEY
```

### Log Management
```bash
python src/manageLogs.py list
python src/manageLogs.py show --lines 50
python src/manageLogs.py clean --days 7
```

## 📊 Data Collection

The system collects social media data based on keywords stored in MongoDB `searchKeywords` collection:

```javascript
{
  "type": "youtube",
  "query": "BMW X5 review",
  "clientId": "client123",
  "clientName": "BMW India",
  "companyId": "company456",
  "companyName": "BMW Group"
}
```

## 🔑 Features

- **Multi-Platform Support**: YouTube, Twitter/X, Facebook
- **API Key Management**: Automatic rotation and error handling
- **Client Tagging**: Automatic client and company attribution
- **Data Processing**: Smart duplicate detection and updates
- **Error Handling**: Robust error recovery and retry logic
- **Logging**: Comprehensive logging with home directory storage

## 📞 Support

For detailed documentation, see `jobsOverview.md`
For issues and troubleshooting, check logs in your home directory
