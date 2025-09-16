# YouTube Native Captions API Usage Guide

This implementation provides a native Google API client solution for fetching YouTube captions/transcripts using the official YouTube Data API v3. It returns structured transcript data with proper timing information.

## Features

- ✅ Native Google API client using `googleapiclient`
- ✅ Structured transcript output with timing information
- ✅ Language preference support
- ✅ Automatic API key rotation and error handling
- ✅ Support for multiple caption formats (TTML, SRT, VTT)
- ✅ TTML parsing for structured transcript data
- ✅ Integration with existing Youtube class

## Classes

### 1. `YoutubeCaptions` (Direct Usage)

The main class that handles YouTube captions API interactions.

```python
from classes.YoutubeCaptions import YoutubeCaptions

# Initialize the captions API
captions_api = YoutubeCaptions()

# Get structured transcript for a video
video_id = "dQw4w9WgXcQ"
response = captions_api.get_video_captions(video_id, ["en", "en-US"])

if response.status_code == 200:
    data = response.data
    print(f"Language: {data['selected_caption']['language']}")
    print(f"Total segments: {data['total_segments']}")
    
    # Access transcript segments
    for segment in data['transcript_data']:
        print(f"[{segment['start']:.2f}s] {segment['text']}")
```

### 2. `Youtube` (Integrated Usage)

Enhanced Youtube class with integrated captions functionality.

```python
from classes.Youtube import Youtube

# Initialize YouTube client (includes captions API)
youtube = Youtube()

# Get transcript using integrated method
transcript_data = youtube.get_video_transcript(video_id, ["en", "en-US"])

if transcript_data:
    print(f"Selected language: {transcript_data['selected_caption']['language']}")
    print(f"Is auto-generated: {transcript_data['selected_caption']['is_auto_generated']}")
    
    # Process transcript segments
    for segment in transcript_data['transcript_data']:
        print(f"[{segment['start']:.2f}-{segment['end']:.2f}s] {segment['text']}")
```

## API Methods

### YoutubeCaptions Methods

#### `list_captions(video_id: str) -> Response`
Lists all available caption tracks for a video.

```python
response = captions_api.list_captions("VIDEO_ID")
if response.status_code == 200:
    for caption in response.data['captions']:
        print(f"Language: {caption['language']}, Kind: {caption['track_kind']}")
```

#### `download_caption(caption_id: str, fmt: str = "ttml") -> Response`
Downloads a specific caption track.

```python
# First list captions to get caption IDs
captions_response = captions_api.list_captions("VIDEO_ID")
caption_id = captions_response.data['captions'][0]['id']

# Download the caption
response = captions_api.download_caption(caption_id, "ttml")
if response.status_code == 200:
    transcript = response.data['transcript']
```

#### `get_video_captions(video_id: str, language_preference: List[str] = None) -> Response`
Gets structured captions with language preference (main method).

```python
response = captions_api.get_video_captions("VIDEO_ID", ["en", "hi", "es"])
```

### Youtube Integration Methods

#### `get_video_transcript(video_id: str, language_preference: list = None)`
Get structured transcript (integrated method).

#### `list_video_captions(video_id: str)`
List available captions (integrated method).

#### `download_specific_caption(caption_id: str, fmt: str = "ttml")`
Download specific caption track (integrated method).

## Response Structure

### Transcript Data Structure

```python
{
    "video_id": "dQw4w9WgXcQ",
    "selected_caption": {
        "id": "caption_track_id",
        "language": "en",
        "name": "English",
        "track_kind": "standard",  # or "ASR" for auto-generated
        "is_auto_generated": false
    },
    "available_languages": ["en", "en-US", "es", "fr"],
    "transcript_data": [
        {
            "text": "Never gonna give you up",
            "start": 0.0,
            "duration": 2.5,
            "end": 2.5
        },
        {
            "text": "Never gonna let you down",
            "start": 2.5,
            "duration": 2.8,
            "end": 5.3
        }
        // ... more segments
    ],
    "total_segments": 156
}
```

### Caption List Structure

```python
{
    "video_id": "dQw4w9WgXcQ",
    "captions_count": 3,
    "captions": [
        {
            "id": "caption_track_id_1",
            "language": "en",
            "name": "English",
            "track_kind": "standard",
            "is_auto_synced": false,
            "is_cc": false,
            "is_draft": false,
            "status": "serving"
        }
        // ... more caption tracks
    ]
}
```

## Language Preference

The API supports language preference with fallback logic:

1. **Exact match**: Tries to find exact language code match
2. **English variants**: Falls back to any English variant (en, en-US, en-GB)
3. **First available**: Uses the first available caption track

```python
# Priority order: Hindi, English US, any English, first available
transcript = youtube.get_video_transcript("VIDEO_ID", ["hi", "en-US", "en"])
```

## Error Handling

The implementation includes comprehensive error handling:

- **404**: Video not found or no captions available
- **403**: Access denied (private video, restricted captions)
- **401**: Invalid API key
- **429**: Rate limit exceeded
- **Quota exceeded**: Automatic API key rotation

```python
response = captions_api.get_video_captions("INVALID_VIDEO_ID")
if response.status_code == 404:
    print("Video not found or no captions available")
elif response.status_code == 403:
    print("Access denied to video captions")
```

## Testing

Run the test script to verify the implementation:

```bash
python test_youtube_captions.py [VIDEO_ID]
```

Example:
```bash
# Test with Rick Astley video (default)
python test_youtube_captions.py

# Test with specific video
python test_youtube_captions.py "dQw4w9WgXcQ"
```

## Requirements

Make sure these dependencies are installed:

```txt
google-api-python-client>=2.0.0
```

## Configuration

The implementation uses the existing credential management system:
- API keys are managed by `CredentialManager`
- Automatic key rotation on quota/rate limit errors
- Error reporting and key deactivation

## Advantages over youtube-transcript-api

1. **Official API**: Uses Google's official YouTube Data API v3
2. **Better Error Handling**: Comprehensive error responses and retry logic
3. **Structured Output**: Consistent response format with metadata
4. **API Key Management**: Integrated with existing key rotation system
5. **Language Selection**: Smart language preference with fallback
6. **Format Support**: Multiple caption formats (TTML, SRT, VTT)
7. **Timing Accuracy**: Precise timing information from TTML parsing

## Example Usage in Your Project

```python
# In your scraper class
from classes.Youtube import Youtube

class MyYouTubeScraper:
    def __init__(self):
        self.youtube = Youtube()
    
    def scrape_video_with_transcript(self, video_id):
        # Get video details using existing methods
        video_details = self.youtube.execute(
            lambda svc: svc.videos().list(part="snippet", id=video_id)
        )
        
        # Get transcript using new captions API
        transcript = self.youtube.get_video_transcript(video_id)
        
        return {
            "video_details": video_details,
            "transcript": transcript
        }
```
