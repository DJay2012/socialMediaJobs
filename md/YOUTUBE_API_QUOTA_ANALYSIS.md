# YouTube API Quota Usage Analysis

## Overview
Your system uses **9 YouTube API keys** with **10,000 units each** = **90,000 total daily quota units**.

## API Operations and Quota Costs

### 1. Search Operations (Most Expensive)
- **`search.list`**: **100 units per request**
- Used in: `_search_query()` and `_get_channel_videos()`
- **Pagination Impact**: Each page costs 100 units

### 2. Video Information Operations (Cheap)
- **`videos.list`**: **1 unit per request**
- Used in: `_get_video_info()`
- **Batch Processing**: Can request up to 50 video IDs per request

### 3. Channel Information Operations (Cheap)
- **`channels.list`**: **1 unit per request**
- Used in: `_get_channel_info()`
- **Batch Processing**: Can request multiple channel IDs per request

### 4. Transcript Operations (No Quota Cost)
- **Transcript fetching**: **0 units** (uses `youtube-transcript-api`, not YouTube Data API)

## Your Current Usage Pattern

### Per Keyword Processing:
1. **Channel Search** (`_get_channel_videos`):
   - 1 search request = **100 units**
   - If pagination occurs (e.g., 3 pages) = **300 units**

2. **Video Details** (`_get_video_info`):
   - 1 batch request for all videos = **1 unit**
   - Can handle up to 50 videos per request

3. **Channel Info** (`_get_channel_info`):
   - 1 batch request = **1 unit**

4. **Transcript Fetching**:
   - **0 units** (not using YouTube Data API)

### Total Per Keyword:
- **Minimum**: 102 units (1 search + 1 video + 1 channel)
- **With Pagination**: 102 + (100 × additional_pages)

## Quota Consumption Examples

### Scenario 1: Single Page Results
```
Per keyword: 102 units
With 9 keys: 9 × 10,000 = 90,000 units
Max keywords per day: 90,000 ÷ 102 = ~882 keywords
```

### Scenario 2: Multi-page Results (3 pages average)
```
Per keyword: 302 units (102 + 200 for 2 extra pages)
Max keywords per day: 90,000 ÷ 302 = ~298 keywords
```

### Scenario 3: Heavy Pagination (5 pages average)
```
Per keyword: 502 units (102 + 400 for 4 extra pages)
Max keywords per day: 90,000 ÷ 502 = ~179 keywords
```

## Optimization Recommendations

### 1. Reduce Search Quota Usage
```python
# Current: Each search costs 100 units
# Optimization: Use more specific date ranges to reduce pagination
def _search_query(self, q: str, type: str = "video", max_results: int = 50):
    # Reduce max_results to minimize pagination
    # Use more specific date ranges
    params = {
        "q": q,
        "type": type,
        "part": "snippet",
        "maxResults": 50,  # Reduced from 100
        "order": "relevance",
        "regionCode": "IN",
        "publishedAfter": self.start_date,
        "publishedBefore": self.end_date,
    }
```

### 2. Batch Video Information Requests
```python
# Current: Already optimized - 1 unit per batch
# Ensure you're batching all video IDs together
def _get_video_info(self, video_ids: List[str], max_results: int = 50):
    # This is already optimized - processes up to 50 videos per request
    video_ids = ",".join(video_ids)
```

### 3. Implement Quota Monitoring
```python
def get_quota_usage_stats(self):
    """Monitor quota usage across all API keys"""
    stats = {}
    for i, key in enumerate(self.api_keys):
        # Get usage from Google Cloud Console API
        usage = self._get_key_usage(key)
        stats[f"key_{i+1}"] = {
            "quota_used": usage,
            "quota_remaining": 10000 - usage
        }
    return stats
```

### 4. Smart Pagination Control
```python
def _pagination(self, fetch_func, max_results: int = 50, max_pages: int = 3):
    """Limit pagination to control quota usage"""
    all_items = []
    current_page_token = None
    page_count = 0
    
    while page_count < max_pages:  # Limit to 3 pages max
        response = fetch_func(max_results, current_page_token)
        # ... rest of pagination logic
        page_count += 1
```

## Current System Analysis

### Threading Impact
- **9 API keys** with round-robin distribution
- Each thread gets a different API key
- **No quota sharing** between keys (each key has independent 10K limit)

### Key Rotation Strategy
```python
# In Youtube.py - execute method
def execute(self, factory: FunctionType, total_attempts: int = 3):
    # Always gets next API key in round-robin
    self._initialize_build(force_new_key=True)
    # This ensures equal distribution across all 9 keys
```

## Quota Usage Summary

| Operation | Units per Request | Your Usage | Optimization |
|-----------|------------------|------------|--------------|
| `search.list` | 100 | High (main cost) | Reduce pagination, use specific date ranges |
| `videos.list` | 1 | Low (already optimized) | Already batched |
| `channels.list` | 1 | Low (already optimized) | Already batched |
| Transcripts | 0 | None | No quota impact |

## Daily Capacity Estimation

Based on your current implementation:
- **Conservative estimate**: ~300-500 keywords per day
- **Optimized estimate**: ~800-1000 keywords per day
- **Current bottleneck**: Search operations (100 units each)

## Recommendations for 10K Quota Usage

1. **Monitor pagination**: Track how many pages each search returns
2. **Optimize date ranges**: Use shorter, more specific date ranges
3. **Implement quota tracking**: Monitor usage per API key
4. **Consider caching**: Cache channel info and video details
5. **Batch operations**: Ensure all batchable operations are properly batched

Your current implementation is already quite optimized for the expensive operations. The main area for improvement is controlling pagination in search operations.
