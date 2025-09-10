# Social Media Jobs - New Folder Structure

This is the improved version with organized folder structure and a main.py runner.

## 📁 Project Structure

```
socialMediaJobs/
├── main.py                              # Main job runner
├── config.py                            # Configuration management
├── base_social_media_scraper.py         # Base class for all scrapers
├── job_config.json                      # Job configuration file
├── requirements.txt                     # Python dependencies
├── environment_template.txt             # Environment variables template
├── test_new_structure.py               # Test script
├── README_NEW_STRUCTURE.md             # This file
│
├── youtube/                             # YouTube scrapers
│   ├── __init__.py
│   ├── youtube_scraper.py              # General YouTube scraper
│   └── youtube_bmw_scraper.py          # BMW-specific YouTube scraper
│
├── twitter/                             # Twitter scrapers
│   ├── __init__.py
│   ├── twitter_scraper.py              # General Twitter scraper
│   └── modi_twitter_scraper.py         # Modi family Twitter scraper
│
├── facebook/                            # Facebook scrapers
│   ├── __init__.py
│   └── facebook_scraper.py             # Facebook scraper using Apify
│
└── logs/                               # Log files (auto-created)
    └── main_*.log
```

## 🚀 Quick Start

### 1. Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Create environment file
cp environment_template.txt .env
# Edit .env with your actual API keys
```

### 2. Test the Structure
```bash
python test_new_structure.py
```

### 3. Run Jobs

#### List Available Jobs
```bash
python main.py --list
```

#### Run Specific Job
```bash
# YouTube scraper
python main.py --job youtube

# Twitter scraper
python main.py --job twitter

# Facebook scraper
python main.py --job facebook

# YouTube BMW scraper
python main.py --job youtube_bmw

# Modi Twitter scraper
python main.py --job modi_twitter
```

#### Run All Jobs
```bash
python main.py --all
```

#### Filter by Client
```bash
python main.py --job youtube --client MHADA11
```

## 🔧 Configuration

### Job Configuration (job_config.json)
```json
{
  "jobs": {
    "youtube": {
      "enabled": true,
      "description": "YouTube video data collection",
      "schedule": "0 */6 * * *",
      "max_results": 100,
      "retry_attempts": 3
    }
  }
}
```

### Environment Variables (.env)
```bash
# Database Configuration
MONGO_URI=mongodb://admin:password@localhost:27017/
DB_NAME=smFeeds

# API Keys (REQUIRED)
YOUTUBE_API_KEY=your_youtube_api_key_here
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here
APIFY_API_TOKEN=your_apify_api_token_here
```

## 📊 Available Jobs

| Job Name | Description | Search Type | Folder |
|----------|-------------|-------------|---------|
| `youtube` | General YouTube video collection | `youtube` | `youtube/` |
| `youtube_bmw` | BMW-specific YouTube channels | `youtubeBmw` | `youtube/` |
| `twitter` | General Twitter/X tweet collection | `xfeed` | `twitter/` |
| `modi_twitter` | Modi family Twitter accounts | `modi` | `twitter/` |
| `facebook` | Facebook post collection via Apify | `facebook` | `facebook/` |

## 🛠️ Adding New Scrapers

### 1. Create Scraper Class
```python
# In appropriate folder (e.g., instagram/instagram_scraper.py)
from base_social_media_scraper import BaseSocialMediaScraper

class InstagramScraper(BaseSocialMediaScraper):
    def __init__(self):
        super().__init__("Instagram")
    
    def process_single_keyword(self, keyword_data):
        # Your scraper logic here
        pass
```

### 2. Update main.py
Add your scraper to the `_discover_jobs()` method:
```python
'instagram': {
    'folder': 'instagram',
    'script': 'instagram_scraper.py',
    'class': 'InstagramScraper',
    'description': 'Instagram post data collection',
    'search_type': 'instagram'
}
```

### 3. Update job_config.json
```json
{
  "jobs": {
    "instagram": {
      "enabled": true,
      "description": "Instagram post data collection",
      "schedule": "0 */4 * * *",
      "max_results": 50,
      "retry_attempts": 3
    }
  }
}
```

## 🔍 Monitoring and Logs

### Log Files
- Main runner logs: `logs/main_YYYYMMDD_HHMMSS.log`
- Individual scraper logs: `social_media_jobs.log`

### Job Status
```bash
# Check available jobs
python main.py --list

# Run with verbose logging
python main.py --job youtube --client MHADA11
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'config'
   ```
   **Solution**: Make sure you're running from the project root directory

2. **Job Not Found**
   ```
   Job 'instagram' not found
   ```
   **Solution**: Check that the scraper file exists in the correct folder

3. **API Key Errors**
   ```
   Missing required environment variables
   ```
   **Solution**: Check your .env file has all required API keys

### Debug Mode
```bash
# Run with debug logging
LOG_LEVEL=DEBUG python main.py --job youtube
```

## 🔄 Migration from Old Structure

### Old Scripts → New Structure
- `MainScriptyoutube.py` → `youtube/youtube_scraper.py`
- `MainScriptXfeedNew.py` → `twitter/twitter_scraper.py`
- `MainapifyFacebook.py` → `facebook/facebook_scraper.py`
- `BmwYoutube.py` → `youtube/youtube_bmw_scraper.py`
- `ModiXfeed.py` → `twitter/modi_twitter_scraper.py`

### Benefits of New Structure
- ✅ **Organized**: Each platform has its own folder
- ✅ **Configurable**: Easy to enable/disable specific jobs
- ✅ **Maintainable**: Clear separation of concerns
- ✅ **Extensible**: Easy to add new scrapers
- ✅ **Secure**: All secrets in environment variables
- ✅ **Monitored**: Centralized logging and error handling

## 📞 Support

If you encounter issues:
1. Run `python test_new_structure.py` to check setup
2. Check logs in the `logs/` directory
3. Verify your `.env` file configuration
4. Test individual scrapers before running the full pipeline
