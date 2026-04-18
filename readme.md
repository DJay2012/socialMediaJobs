# Social Media Jobs - Advanced Data Collection System

A comprehensive, enterprise-grade social media data collection system with intelligent API key management, automated scheduling, and robust error handling. Built for scalability and reliability.

## 🚀 Quick Start

### 1. Installation
```bash
# Clone the repository
git clone <repository-url>
cd socialMediaJobs

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file with your API keys:
```bash
# YouTube API Keys (supports multiple keys for load balancing)
YOUTUBE_API_KEY_1=your_youtube_api_key_1
YOUTUBE_API_KEY_2=your_youtube_api_key_2
YOUTUBE_API_KEY_3=your_youtube_api_key_3

# Twitter/X API Keys
TWITTER_BEARER_TOKEN_1=your_twitter_bearer_token_1

# Apify API Keys
APIFY_API_TOKEN_1=your_apify_api_token_1

# Database Configuration
MONGO_URI=mongodb://username:password@host:port/
DB_NAME=smFeeds
```

### 3. Run the System

#### YouTube Scheduler (Recommended)
```bash
# Run the automated YouTube scheduler
python youtube.py
```

#### Manual Job Execution
```bash
# Run specific YouTube jobs
python -c "from src.youtube.youtubeScraper import youtube_scraper; youtube_scraper('YOUTUBE_BMW')"

# Run Twitter jobs
python -c "from src.twitter.twitterScraper import twitter_scraper; twitter_scraper('TWITTER')"

# Run Facebook jobs
python -c "from src.facebook.facebookScraper import facebook_scraper; facebook_scraper('FACEBOOK')"
```

## 📁 Project Structure

```
socialMediaJobs/
├── youtube.py                              # YouTube scheduler entry point
├── requirements.txt                        # Python dependencies
├── .env                                    # Environment variables
├── cspell.json                            # Spell checking configuration
├── src/                                   # Source code directory
│   ├── classes/                          # Core classes and utilities
│   │   ├── BaseScraper.py                # Base scraper with common functionality
│   │   ├── Youtube.py                    # Centralized YouTube operations
│   │   ├── YoutubeApiClient.py           # YouTube API client with key rotation
│   │   ├── Transcript.py                 # YouTube transcript extraction
│   │   ├── DataMigration.py             # Data migration utilities
│   │   ├── IPManager.py                 # IP rotation management
│   │   └── Response.py                   # API response handling
│   ├── config/                           # Configuration management
│   │   ├── config.py                    # Main configuration
│   │   └── CredentialManager.py         # API key management
│   ├── enums/                            # Type definitions
│   │   └── types.py                     # Platform and entity types
│   ├── jobs/                             # Job schedulers
│   │   └── youtube_scheduler.py         # YouTube automated scheduler
│   ├── log/                              # Logging system
│   │   └── logging.py                   # Advanced logging with colors
│   ├── schema/                           # Data schemas
│   │   └── Youtube.py                   # YouTube data schema
│   ├── utils/                            # Utility functions
│   │   ├── helper.py                    # Helper functions
│   │   └── text_clean.py                # Text processing utilities
│   ├── youtube/                          # YouTube scrapers
│   │   ├── youtubeScraper.py            # Main YouTube scraper
│   │   └── channelResearch.py           # Channel research tools
│   ├── twitter/                          # Twitter scrapers
│   │   ├── twitterScraper.py            # General Twitter scraper
│   │   └── modiTwitterScraper.py        # Modi family Twitter scraper
│   ├── facebook/                         # Facebook scrapers
│   │   └── facebookScraper.py            # Facebook scraper
│   └── scripts/                          # Additional scripts
│       └── youtube/
│           └── channel.py                # Channel management scripts
├── md/                                    # Documentation
│   ├── JOB_OVERVIEW.md                  # Job overview documentation
│   ├── RESPONSE_CLASS_GUIDE.md          # Response class guide
│   ├── SOCIAL_MEDIA_JOBS.md             # Detailed job documentation
│   └── YOUTUBE_API_QUOTA_ANALYSIS.md    # API quota analysis
├── backupLatest/                          # Legacy scripts backup
│   ├── Backup/                          # Original script backups
│   └── newscheckerfile/                 # News checking utilities
└── temp/                                 # Temporary files
    └── ip_cooldown.json                 # IP rotation tracking
```

## 🔧 Available Jobs & Features

### YouTube Data Collection
- **Automated Scheduler**: Runs every 30 minutes during operating hours (6 AM - 9 PM)
- **Channel Research**: Comprehensive channel analysis and data collection
- **Playlist Processing**: Efficient playlist-based video collection
- **Transcript Extraction**: Automatic transcript retrieval for videos
- **Keyword & Influencer Search**: Advanced content filtering
- **API Quota Management**: Intelligent key rotation and quota optimization

### Twitter/X Data Collection
- **Tweet Collection**: Real-time tweet data gathering
- **Modi Family Tracking**: Specialized tracking for political figures
- **Content Analysis**: Advanced text processing and analysis

### Facebook Data Collection
- **Post Collection**: Facebook post data extraction
- **Content Processing**: Automated content analysis

## 🛠️ Advanced Features

### 🔑 Intelligent API Key Management
- **Multi-Key Support**: Automatic rotation across multiple API keys
- **Quota Monitoring**: Real-time quota tracking and optimization
- **Error Handling**: Automatic key switching on errors
- **Load Balancing**: Even distribution of requests across keys

### 📊 Data Processing
- **Smart Deduplication**: Intelligent duplicate detection and handling
- **Client Tagging**: Automatic client and company attribution
- **Data Migration**: Seamless data transfer between collections
- **Schema Validation**: Pydantic-based data validation

### 🕒 Scheduling & Automation
- **Operating Hours**: Configurable operating hours (6 AM - 9 PM)
- **Graceful Shutdown**: Ctrl+C interrupt handling
- **Error Recovery**: Robust error handling and retry logic
- **Status Monitoring**: Real-time job status tracking

### 📝 Advanced Logging
- **Color-Coded Logs**: Easy-to-read colored log output
- **Structured Logging**: JSON-formatted logs for analysis
- **Log Rotation**: Automatic log file management
- **Performance Metrics**: Detailed timing and quota usage

## 🚀 Usage Examples

### YouTube Scheduler
```bash
# Start the automated YouTube scheduler
python youtube.py

# The scheduler will:
# - Run every 30 minutes during operating hours
# - Handle Ctrl+C gracefully
# - Log all activities with timestamps
# - Manage API quotas automatically
```

### Manual YouTube Operations
```python
from src.classes.Youtube import Youtube

# Initialize YouTube client
youtube = Youtube()

# Set date range
youtube.set_date_range("2024-01-01T00:00:00Z", "2024-01-31T23:59:59Z")

# Search for videos
videos = youtube.search_query("BMW X5 review")

# Get channel videos
channel_videos = youtube.get_channel_videos("UC123456789")

# Process and get video details
processed_data = youtube.process_youtube_data(videos)
```

### API Key Management
```python
from src.config.CredentialManager import credential_manager

# Check key status
status = credential_manager.get_key_status("youtube")
print(f"Active keys: {status['active_keys']}")

# Get next available key
key = credential_manager.get_api_key("youtube", strategy="round_robin")
```

## 📊 Data Collection Schema

The system collects social media data based on keywords stored in MongoDB `searchKeywords` collection:

```javascript
{
  "type": "youtube",
  "query": "BMW X5 review",
  "playlistId": "PL123456789",
  "influencerName": "BMW Official",
  "keywords": ["BMW", "X5", "review"],
  "clientId": "client123",
  "clientName": "BMW India",
  "companyId": "company456",
  "companyName": "BMW Group"
}
```

## 🔧 Configuration Options

### Environment Variables
```bash
# Database
MONGO_URI=mongodb://localhost:27017/
DB_NAME=smFeeds

# YouTube API Keys (multiple keys supported)
YOUTUBE_API_KEY_1=your_key_1
YOUTUBE_API_KEY_2=your_key_2
YOUTUBE_API_KEY_3=your_key_3

# Twitter API
TWITTER_BEARER_TOKEN_1=your_twitter_token

# Apify API
APIFY_API_TOKEN_1=your_apify_token
```

### Scheduler Configuration
```python
# Operating hours (configurable in youtube_scheduler.py)
START_TIME = dt_time(6, 0)    # 6:00 AM
END_TIME = dt_time(21, 0)     # 9:00 PM
MINUTES_INTERVAL = 30         # Run every 30 minutes
```

## 🛡️ Error Handling & Reliability

### API Error Management
- **Automatic Key Rotation**: Switches keys on quota/error issues
- **Retry Logic**: Intelligent retry with exponential backoff
- **Rate Limiting**: Built-in rate limiting and request delays
- **Error Logging**: Comprehensive error tracking and reporting

### System Reliability
- **Graceful Shutdown**: Proper cleanup on Ctrl+C
- **Data Integrity**: Transaction-based data operations
- **Memory Management**: Efficient memory usage and cleanup
- **Thread Safety**: Thread-safe operations for concurrent access

## 📈 Performance & Monitoring

### Quota Management
- **Real-time Monitoring**: Live quota usage tracking
- **Load Balancing**: Even distribution across API keys
- **Usage Analytics**: Detailed usage statistics and reports

### Performance Metrics
- **Response Times**: API response time monitoring
- **Success Rates**: Request success rate tracking
- **Error Analysis**: Detailed error categorization and analysis

## 🔍 Troubleshooting

### Common Issues
1. **API Quota Exceeded**: System automatically switches to next available key
2. **Network Timeouts**: Built-in retry logic handles temporary network issues
3. **Database Connection**: Automatic reconnection on connection loss
4. **Memory Issues**: Efficient memory management prevents memory leaks

### Log Analysis
```bash
# Check recent logs
tail -f ~/logs/social_media_jobs.log

# Filter for errors
grep "ERROR" ~/logs/social_media_jobs.log

# Check API usage
grep "quota" ~/logs/social_media_jobs.log
```

## 📚 Documentation

- **Job Overview**: `md/JOB_OVERVIEW.md`
- **Response Classes**: `md/RESPONSE_CLASS_GUIDE.md`
- **Social Media Jobs**: `md/SOCIAL_MEDIA_JOBS.md`
- **API Quota Analysis**: `md/YOUTUBE_API_QUOTA_ANALYSIS.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For detailed documentation, see the `md/` directory.
For issues and troubleshooting, check logs in your home directory.
For API quota management, see `md/YOUTUBE_API_QUOTA_ANALYSIS.md`.