# Jobs Overview - Social Media Data Collection

## 🎯 **What This System Does**

This is a **multi-client social media intelligence platform** that automatically collects and processes social media data across multiple platforms for various clients.

## 🔍 **Search Mechanics**

### **Data Source**
The system gets search instructions from MongoDB `searchKeywords` collection:

```javascript
// Example search configuration
{
  "_id": "keyword1",
  "type": "youtubeBmw",
  "query": "BMW X5 review",
  "channelName": "BMW Official",
  "influencerName": "CarReviewer123",
  "clientId": "client123",
  "clientName": "BMW India",
  "companyId": "company456",
  "companyName": "BMW Group"
}
```

### **Search Types**

#### **1. YouTube Search (`youtubeSearch`)**
- **What**: General YouTube videos based on search queries
- **How**: Uses YouTube Data API v3 search endpoint
- **Example**: Searches for "BMW X5 review" → finds all videos about BMW X5 reviews
- **Data**: Video title, description, statistics, transcripts, location

#### **2. YouTube Channel (`youtubeChannel`)**
- **What**: All videos from specific YouTube channels
- **How**: Gets channel ID, then fetches all videos from that channel
- **Example**: Channel "BMW Official" → gets all videos from BMW's official channel
- **Data**: Complete channel video library with metadata

#### **3. BMW YouTube (`youtubeBmw`)**
- **What**: BMW-specific influencer monitoring
- **How**: Searches BMW channels for specific influencer mentions
- **Example**: BMW Official channel + "CarReviewer123" → finds BMW videos mentioning CarReviewer123
- **Data**: Video content, statistics, transcripts, client tagging

#### **4. Twitter Search (`twitter`)**
- **What**: Twitter/X tweets containing keywords
- **How**: Uses Twitter API v2 search endpoint
- **Example**: "artificial intelligence" → finds tweets about AI
- **Data**: Tweet content, engagement metrics, user information

#### **5. Facebook Search (`facebook`)**
- **What**: Facebook posts using Apify scraper
- **How**: Uses Apify Facebook Scraper API
- **Example**: "BMW" → finds Facebook posts about BMW
- **Data**: Post content, engagement, page information

#### **6. Modi Twitter (`modiTwitter`)**
- **What**: Specific Twitter users (Modi family members)
- **How**: Gets user timeline from Twitter API v2
- **Example**: "@narendramodi" → gets all tweets from Narendra Modi
- **Data**: User tweets, engagement metrics, timestamps

## 🔄 **Business Workflow**

### **Step 1: Keyword Configuration**
- Clients provide search keywords, channels, and influencer names
- Keywords stored in MongoDB `searchKeywords` collection
- Each keyword tagged with client information for billing

### **Step 2: Automated Data Collection**
- System runs jobs based on configured schedules
- Each job processes all keywords for its search type
- Uses API key rotation to avoid rate limits

### **Step 3: Data Processing & Storage**
- Smart duplicate detection and updates
- Additional metadata collection (statistics, transcripts, location)
- Automatic client and company tagging
- Organized data storage in platform-specific collections

## 💰 **Business Model**

### **Multi-Client Architecture**
- Each data record tagged with client information
- Enables serving multiple clients simultaneously
- Accurate billing and attribution per client

### **Service Tiers**
- **Basic**: Standard keyword monitoring
- **Premium**: Advanced analytics and reporting
- **Enterprise**: Custom integrations and dedicated resources

## 🎯 **Real-World Examples**

### **BMW Brand Monitoring**
```javascript
// Search Configuration
{
  "type": "youtubeBmw",
  "channelName": "BMW Official",
  "influencerName": "CarReviewer123",
  "query": "BMW X5 review"
}

// What it does:
// 1. Finds "BMW Official" channel
// 2. Gets all videos from that channel
// 3. Filters for videos mentioning "CarReviewer123"
// 4. Collects video data, statistics, transcripts
// 5. Tags with BMW client information
```

### **General Social Listening**
```javascript
// Search Configuration
{
  "type": "xfeed",
  "query": "artificial intelligence",
  "clientId": "client456"
}

// What it does:
// 1. Searches Twitter for "artificial intelligence"
// 2. Gets recent tweets (up to 100)
// 3. Collects tweet data and engagement metrics
// 4. Tags with client information
```

## 🔧 **Technical Features**

### **API Key Management**
- Multiple API keys per service for redundancy
- Automatic rotation to avoid rate limits
- Error-based key switching
- Usage tracking and cost optimization

### **Data Quality**
- Smart duplicate detection
- Statistics update only when changed
- Comprehensive data validation
- Client-specific data attribution

### **Error Handling**
- Robust retry logic with exponential backoff
- Automatic API key switching on errors
- Comprehensive logging and monitoring
- Graceful failure handling

## 📊 **Data Collections**

### **MongoDB Collections**
- **searchKeywords**: Search instructions and client configuration
- **youtube**: YouTube video data and metadata
- **xtweets**: Twitter/X tweet data and engagement
- **facebook**: Facebook post data and metrics

### **Data Structure**
Each record includes:
- Platform-specific data (video details, tweet content, post data)
- Metadata (timestamps, IDs, statistics)
- Client tags (client and company information)
- Processing info (source, processing time, errors)

## 🚀 **Usage Commands**

### **Job Execution**
```bash
# List all available jobs
python main.py --list

# Run specific jobs
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

### **Management Tools**
```bash
# API key management
python src/manageApiKeys.py list
python src/manageApiKeys.py test
python src/manageApiKeys.py add --service youtube --key YOUR_KEY

# Log management
python src/manageLogs.py list
python src/manageLogs.py show --lines 50
python src/manageLogs.py clean --days 7
```

## 🎯 **Key Business Value**

- **Automated Data Collection**: Minimal manual intervention required
- **Multi-Platform Coverage**: YouTube, Twitter/X, Facebook
- **Client Attribution**: Accurate billing and data ownership
- **Scalable Architecture**: Easy to add new clients and platforms
- **Reliable Operation**: Robust error handling and API management
- **Comprehensive Data**: Rich metadata and analytics

**This system essentially acts as a B2B social media intelligence platform that can be configured to search for any content across multiple platforms for multiple clients simultaneously!** 🚀📊
