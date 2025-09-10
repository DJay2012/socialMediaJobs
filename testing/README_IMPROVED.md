# Social Media Jobs - Improved Version

This is an improved version of your social media data collection scripts with better security, error handling, and maintainability.

## 🚀 Quick Start

### 1. Setup
```bash
# Install dependencies and create configuration
python setup.py
```

### 2. Configure Environment
Edit the `.env` file with your actual API keys and database credentials:
```bash
# Copy the template and edit
cp environment_template.txt .env
# Edit .env with your actual values
```

### 3. Run the Jobs
```bash
# On Windows (PowerShell)
.\run_social_media_jobs.ps1

# On Linux/Mac
./run_social_media_jobs.sh
```

## 🔧 What's Improved

### ✅ Security
- **No more hardcoded API keys** - All secrets moved to environment variables
- **Secure configuration management** - Centralized config system
- **Environment-based deployment** - Easy to manage different environments

### ✅ Error Handling
- **Retry logic** - Automatic retry with exponential backoff
- **Better logging** - Detailed logs with timestamps
- **Graceful failures** - Scripts continue running even if one fails

### ✅ Code Quality
- **Base class** - Common functionality shared across all scrapers
- **Type hints** - Better code documentation and IDE support
- **Consistent structure** - All scripts follow the same pattern

### ✅ Maintainability
- **Single configuration file** - Easy to update settings
- **Modular design** - Easy to add new scrapers
- **Better documentation** - Clear comments and docstrings

## 📁 File Structure

```
socialMediaJobs/
├── config.py                          # Configuration management
├── base_social_media_scraper.py       # Base class for all scrapers
├── youtube_scraper_improved.py        # Improved YouTube scraper
├── twitter_scraper_improved.py        # Improved Twitter scraper
├── setup.py                           # Setup script
├── requirements.txt                   # Python dependencies
├── environment_template.txt           # Environment variables template
├── run_social_media_jobs.ps1         # Windows runner script
├── run_social_media_jobs.sh          # Linux/Mac runner script
└── README_IMPROVED.md                # This file
```

## 🔑 Environment Variables

Create a `.env` file with these variables:

```bash
# Database Configuration
MONGO_URI=mongodb://admin:password@localhost:27017/
DB_NAME=smFeeds

# API Keys (REQUIRED)
YOUTUBE_API_KEY=your_youtube_api_key_here
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here
APIFY_API_TOKEN=your_apify_api_token_here

# Application Settings
MAX_RESULTS=100
RETRY_ATTEMPTS=3
LOG_LEVEL=INFO
```

## 🛠️ Individual Scripts

### YouTube Scraper
```bash
python youtube_scraper_improved.py
```
- Searches YouTube for videos based on keywords
- Fetches video details, statistics, and channel info
- Handles pagination automatically
- Updates existing records with new data

### Twitter Scraper
```bash
python twitter_scraper_improved.py
```
- Searches Twitter for tweets based on keywords
- Fetches user details and media information
- Handles rate limiting and pagination
- Saves pagination tokens for resuming

## 🔄 Migration from Old Scripts

### Step 1: Backup Your Data
```bash
# Backup your existing data before switching
mongodump --uri="your_mongo_uri" --out=backup_$(date +%Y%m%d)
```

### Step 2: Test New Scripts
```bash
# Test individual scrapers first
python youtube_scraper_improved.py
python twitter_scraper_improved.py
```

### Step 3: Update Automation
Replace your existing cron jobs or shell scripts with the new runner:
```bash
# Old way
python MainScriptyoutube.py

# New way
python youtube_scraper_improved.py
```

## 🐛 Troubleshooting

### Common Issues

1. **Missing API Keys**
   ```
   Error: Missing required environment variables
   Solution: Check your .env file has all required keys
   ```

2. **Database Connection Failed**
   ```
   Error: Failed to connect to MongoDB
   Solution: Check MONGO_URI in .env file
   ```

3. **Rate Limiting**
   ```
   Error: API rate limit exceeded
   Solution: Scripts will retry automatically, or increase delays
   ```

### Logs
Check the logs directory for detailed error information:
```bash
ls logs/
tail -f logs/social_media_jobs_*.log
```

## 🔮 Next Steps

1. **Add More Scrapers** - Use the base class to create new scrapers
2. **Add Monitoring** - Set up alerts for failed jobs
3. **Add Data Validation** - Validate data before saving
4. **Add Metrics** - Track scraping performance and success rates

## 📞 Support

If you encounter issues:
1. Check the logs in the `logs/` directory
2. Verify your `.env` file configuration
3. Test individual scrapers before running the full pipeline
4. Check API quotas and rate limits

## 🔒 Security Notes

- Never commit your `.env` file to version control
- Rotate your API keys regularly
- Use environment-specific configurations for different deployments
- Monitor API usage to detect unauthorized access
