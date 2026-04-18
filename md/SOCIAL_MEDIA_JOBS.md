# Social Media Jobs - Complete Documentation

A comprehensive social media data collection system with configurable job runners, API key management, and automated data processing.

## 📁 Project Structure

```
socialMediaJobs/
├── main.py                              # Main entry point (simple wrapper)
├── requirements.txt                     # Python dependencies
├── .env                                 # Environment variables
├── job_config.json                      # Job configuration
├── accounts.db                          # Database file
├── src/                                 # Source code directory
│   ├── socialMediaJobRunner.py         # Main job runner
│   ├── socialMediaConfig.py            # Configuration management
│   ├── baseSocialMediaScraper.py       # Base class for all scrapers
│   ├── apiKeysManager.py              # API key management
│   ├── manageApiKeys.py               # API key CLI
│   ├── manageLogs.py                  # Log management CLI
│   ├── youtube/                        # YouTube scrapers
│   │   ├── __init__.py
│   │   ├── youtubeScraper.py          # General YouTube scraper
│   │   ├── youtubeBmwScraper.py       # BMW-specific YouTube scraper
│   │   └── youtubeSearchScraper.py    # YouTube search scraper
│   ├── twitter/                        # Twitter scrapers
│   │   ├── __init__.py
│   │   ├── twitterScraper.py          # General Twitter scraper
│   │   └── modiTwitterScraper.py      # Modi family Twitter scraper
│   └── facebook/                       # Facebook scrapers
│       ├── __init__.py
│       └── facebookScraper.py         # Facebook scraper using Apify
├── backupLatest/                       # Original scripts backup
├── testing/                           # Test files and improved versions
└── logs/                              # Log files (stored in home directory)
```

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

Create a `.env` file with your API keys and database credentials:

```bash
# YouTube API Keys
YOUTUBE_API_KEY_1=your_youtube_api_key_1
YOUTUBE_API_KEY_2=your_youtube_api_key_2
YOUTUBE_API_KEY_3=your_youtube_api_key_3

# Twitter API Keys
TWITTER_BEARER_TOKEN_1=your_twitter_bearer_token_1
TWITTER_BEARER_TOKEN_2=your_twitter_bearer_token_2

# Apify API Keys
APIFY_API_TOKEN_1=your_apify_api_token_1
APIFY_API_TOKEN_2=your_apify_api_token_2

# MongoDB Configuration
MONGO_URI=mongodb://username:password@host:port/
DB_NAME=smFeeds

# Application Settings
MAX_RESULTS=50
RETRY_ATTEMPTS=3
RATE_LIMIT_DELAY=2
LOG_LEVEL=INFO
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

# Run with client filter
python main.py --job youtubeSearch --client client123
```

## 🔧 Features

### **Multi-Platform Support**
- **YouTube**: Search-based and channel-specific video collection
- **Twitter/X**: Tweet data collection with user filtering
- **Facebook**: Post data collection using Apify API

### **API Key Management**
- **Automatic Rotation**: Round-robin and error-based key switching
- **Error Handling**: Automatic key deactivation on errors
- **Reactivation**: Keys automatically reactivated after cooldown
- **Multiple Keys**: Support for multiple API keys per service

### **Data Processing**
- **MongoDB Integration**: Automatic data storage and updates
- **Duplicate Handling**: Smart duplicate detection and updates
- **Client Tagging**: Automatic client and company tagging
- **Data Validation**: Comprehensive data validation and cleaning

### **Error Handling & Reliability**
- **Retry Logic**: Exponential backoff for failed requests
- **Rate Limiting**: Automatic rate limiting and delays
- **Logging**: Comprehensive logging with home directory storage
- **Graceful Failures**: System continues running even if individual jobs fail

### **Configuration Management**
- **Environment Variables**: Secure configuration management
- **Centralized Settings**: Single configuration file for all settings
- **Validation**: Automatic configuration validation
- **Flexibility**: Easy to modify settings without code changes

## 📊 Available Jobs

### **YouTube Jobs**
- **youtubeSearch**: Search-based video collection using keywords
- **youtubeChannel**: Channel-specific video collection
- **youtubeBmw**: BMW-specific YouTube channel data collection

### **Twitter Jobs**
- **twitter**: General Twitter/X tweet data collection
- **modiTwitter**: Modi family Twitter data collection

### **Facebook Jobs**
- **facebook**: Facebook post data collection using Apify API

## 🛠️ Management Tools

### **API Key Management**
```bash
# List all API keys
python src/manageApiKeys.py list

# Test API keys
python src/manageApiKeys.py test

# Add new API key
python src/manageApiKeys.py add --service youtube --key YOUR_KEY

# Remove API key
python src/manageApiKeys.py remove --service youtube --key YOUR_KEY

# Reset error counts
python src/manageApiKeys.py reset

# Show key status
python src/manageApiKeys.py status
```

### **Log Management**
```bash
# List all log files
python src/manageLogs.py list

# Show latest log content
python src/manageLogs.py show --lines 50

# Clean old logs (older than 7 days)
python src/manageLogs.py clean --days 7

# Open logs folder in file explorer
python src/manageLogs.py open
```

## 🔑 API Key Configuration

### **Supported Services**
- **YouTube**: Google YouTube Data API v3
- **Twitter**: Twitter API v2
- **Apify**: Apify Facebook Scraper

### **Key Management Features**
- **Automatic Rotation**: Keys rotated based on usage and errors
- **Error Reporting**: Automatic error reporting and key deactivation
- **Reactivation**: Keys reactivated after cooldown period
- **Status Tracking**: Track key usage, errors, and availability

### **Adding API Keys**
```bash
# Add YouTube API key
python src/manageApiKeys.py add --service youtube --key "AIzaSyC..."

# Add Twitter Bearer Token
python src/manageApiKeys.py add --service twitter --key "Bearer AAAA..."

# Add Apify API Token
python src/manageApiKeys.py add --service apify --key "apify_api_..."
```

## 📝 Data Storage

### **MongoDB Collections**
- **searchKeywords**: Search keywords and queries
- **youtube**: YouTube video data
- **xtweets**: Twitter/X tweet data
- **facebook**: Facebook post data

### **Data Structure**
Each record includes:
- **Platform-specific data**: Video details, tweet content, post data
- **Metadata**: Timestamps, IDs, statistics
- **Client Tags**: Client and company information
- **Processing Info**: Source, processing time, errors

### **Data Updates**
- **Upsert Logic**: Smart insert/update based on record existence
- **Change Detection**: Only update when data has changed
- **Tag Management**: Add new client tags without duplicates
- **Statistics Updates**: Update metrics and follower counts

## 🔍 Logging

### **Log Storage**
- **Location**: Home directory (`C:\Users\[Username]\`)
- **Format**: `social_media_jobs_YYYYMMDD_HHMMSS.log`
- **Rotation**: New log file for each run
- **Retention**: Configurable log retention

### **Log Levels**
- **INFO**: General information and progress
- **WARNING**: Non-critical issues and missing data
- **ERROR**: Errors and failures
- **DEBUG**: Detailed debugging information

### **Log Management**
```bash
# View latest logs
python src/manageLogs.py show --lines 100

# Clean old logs
python src/manageLogs.py clean --days 14

# Open logs folder
python src/manageLogs.py open
```

## ⚙️ Configuration Options

### **Environment Variables**
```bash
# API Keys
YOUTUBE_API_KEY_1=key1
YOUTUBE_API_KEY_2=key2
TWITTER_BEARER_TOKEN_1=token1
APIFY_API_TOKEN_1=token1

# Database
MONGO_URI=mongodb://user:pass@host:port/
DB_NAME=smFeeds

# Application
MAX_RESULTS=50
RETRY_ATTEMPTS=3
RATE_LIMIT_DELAY=2
LOG_LEVEL=INFO
```

### **Job Configuration**
Jobs are configured in the main runner with:
- **Folder**: Source code location
- **Script**: Python file name
- **Class**: Scraper class name
- **Description**: Human-readable description
- **Search Type**: Database search type

## 🚨 Error Handling

### **API Errors**
- **Rate Limiting**: Automatic delays and retries
- **Quota Exceeded**: Key rotation and error reporting
- **Invalid Keys**: Automatic key deactivation
- **Network Issues**: Retry with exponential backoff

### **Database Errors**
- **Connection Issues**: Automatic reconnection attempts
- **Duplicate Keys**: Smart handling and logging
- **Validation Errors**: Data cleaning and retry

### **System Errors**
- **Missing Dependencies**: Clear error messages
- **Configuration Issues**: Validation and guidance
- **File System Errors**: Graceful handling and logging

## 🔄 Development

### **Adding New Scrapers**
1. Create new scraper class in appropriate folder
2. Inherit from `BaseSocialMediaScraper`
3. Implement `processSingleKeyword` method
4. Add job configuration to main runner
5. Test with sample data

### **Code Structure**
- **camelCase Naming**: All user-defined names use camelCase
- **Type Hints**: Comprehensive type annotations
- **Error Handling**: Robust error handling throughout
- **Logging**: Detailed logging for debugging
- **Documentation**: Clear docstrings and comments

### **Testing**
```bash
# Test individual scrapers
python src/youtube/youtubeScraper.py
python src/twitter/twitterScraper.py

# Test API key management
python src/manageApiKeys.py test

# Test log management
python src/manageLogs.py list
```

## 📈 Performance

### **Optimization Features**
- **Batch Processing**: Process multiple items efficiently
- **Rate Limiting**: Respect API rate limits
- **Connection Pooling**: Efficient database connections
- **Memory Management**: Optimized memory usage

### **Monitoring**
- **Progress Logging**: Real-time progress updates
- **Error Tracking**: Comprehensive error logging
- **Performance Metrics**: Processing time and success rates
- **Resource Usage**: Memory and CPU monitoring

## 🛡️ Security

### **API Key Security**
- **Environment Variables**: Keys stored in environment variables
- **No Hardcoding**: No API keys in source code
- **Rotation**: Regular key rotation and management
- **Error Reporting**: Secure error reporting without key exposure

### **Data Security**
- **Encrypted Connections**: MongoDB connections use encryption
- **Input Validation**: All inputs validated and sanitized
- **Error Handling**: Secure error handling without data exposure
- **Access Control**: Proper access control and permissions

## 🎯 Best Practices

### **Usage Guidelines**
1. **Monitor Logs**: Regularly check logs for errors
2. **Key Management**: Rotate API keys regularly
3. **Data Validation**: Verify data quality and completeness
4. **Error Handling**: Address errors promptly
5. **Performance**: Monitor system performance and resource usage

### **Maintenance**
1. **Regular Updates**: Keep dependencies updated
2. **Log Cleanup**: Clean old logs regularly
3. **Key Rotation**: Rotate API keys periodically
4. **Data Backup**: Regular database backups
5. **Monitoring**: Monitor system health and performance

## 📞 Support

### **Troubleshooting**
- **Check Logs**: Review logs for error details
- **Validate Configuration**: Ensure all environment variables are set
- **Test API Keys**: Verify API keys are working
- **Check Dependencies**: Ensure all packages are installed
- **Database Connection**: Verify MongoDB connection

### **Common Issues**
- **Missing API Keys**: Add keys using management tools
- **Database Connection**: Check MongoDB URI and credentials
- **Rate Limiting**: Increase delays or add more API keys
- **Memory Issues**: Reduce batch sizes or add more memory
- **Permission Errors**: Check file and folder permissions

## 🚀 Future Enhancements

### **Planned Features**
- **Additional Platforms**: Instagram, LinkedIn, TikTok
- **Real-time Processing**: WebSocket-based real-time updates
- **Advanced Analytics**: Data analysis and reporting
- **Web Interface**: Web-based management interface
- **Scheduling**: Advanced job scheduling and automation

### **Contributing**
- **Code Style**: Follow camelCase naming convention
- **Documentation**: Update documentation for new features
- **Testing**: Add tests for new functionality
- **Error Handling**: Implement robust error handling
- **Performance**: Optimize for performance and scalability

---

**Social Media Jobs** - A comprehensive, reliable, and scalable social media data collection system built with modern Python practices and camelCase naming conventions.
