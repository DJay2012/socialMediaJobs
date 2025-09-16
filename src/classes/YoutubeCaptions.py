"""
Native YouTube Captions API implementation using Google API Client
Provides structured caption/transcript fetching for YouTube videos
"""

from typing import Dict, List, Optional, Any, Union
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import xml.etree.ElementTree as ET
import requests
import time
from urllib.parse import unquote

from config.CredentialManager import credential_manager
from log.logging import logger
from classes.Response import Response
from utils.text_clean import clean_text


class YoutubeCaptions:
    """
    Native YouTube Captions API client using googleapiclient
    Fetches captions/transcripts in a structured manner using official YouTube Data API v3
    """

    def __init__(self):
        self.logger = logger
        self.api_key = None
        self.youtube_service = None

        # Initialize with a working API key
        credential_manager.reactivate_keys()
        api_key = credential_manager.get_api_key(
            "youtube", test_func=self._test_api_key
        )

        if not api_key:
            raise Exception("No available YouTube API keys")

        self.api_key = api_key
        self._initialize_service()

    def _test_api_key(self, api_key: str) -> bool:
        """Test if an API key is valid"""
        try:
            test_service = build("youtube", "v3", developerKey=api_key)
            # Make a simple request to test the key
            request = test_service.search().list(
                q="test", part="snippet", type="video", maxResults=1
            )
            request.execute()
            return True
        except HttpError as e:
            self.logger.error(f"API key test failed: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"API key test failed with unexpected error: {str(e)}")
            return False

    def _initialize_service(self):
        """Initialize YouTube API service"""
        try:
            self.youtube_service = build("youtube", "v3", developerKey=self.api_key)
            masked_key = (
                self.api_key[:10] + "..." + self.api_key[-10:]
                if len(self.api_key) > 20
                else self.api_key
            )
            self.logger.success(
                f"YouTube Captions API service initialized with key: {masked_key}"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize YouTube Captions service: {e}")
            raise

    def _handle_api_error(self, error: HttpError) -> bool:
        """Handle API errors and report them to the API key manager"""
        if error.resp.status == 403:
            if "quotaExceeded" in str(error) or "quota" in str(error).lower():
                self.logger.warning("YouTube API quota exceeded")
                credential_manager.report_error(
                    "youtube", self.api_key, "quota_exceeded"
                )
                return True
            elif "blocked" in str(error).lower() or "forbidden" in str(error).lower():
                self.logger.warning(f"YouTube API request blocked: {str(error)}")
                credential_manager.report_error("youtube", self.api_key, "invalid_key")
                return True
            else:
                self.logger.warning(f"YouTube API 403 error: {str(error)}")
                credential_manager.report_error("youtube", self.api_key, "invalid_key")
                return True
        elif error.resp.status == 401:
            self.logger.error("YouTube API authentication failed")
            credential_manager.report_error("youtube", self.api_key, "invalid_key")
            return True
        elif error.resp.status == 429:
            self.logger.warning("YouTube API rate limit exceeded")
            credential_manager.report_error("youtube", self.api_key, "rate_limit")
            return True
        return False

    def _execute_with_retry(self, request_func, max_retries: int = 3):
        """Execute API request with automatic key rotation"""
        for attempt in range(max_retries):
            try:
                if not self.youtube_service:
                    self._initialize_service()

                return request_func(self.youtube_service)

            except HttpError as e:
                if self._handle_api_error(e):
                    # Try to get a new API key
                    credential_manager.reactivate_keys()
                    new_api_key = credential_manager.get_api_key(
                        "youtube", test_func=self._test_api_key
                    )

                    if new_api_key:
                        self.api_key = new_api_key
                        self.youtube_service = None  # Force re-initialization
                        self.logger.info(
                            f"Retrying with different API key (attempt {attempt + 1}/{max_retries})"
                        )
                        continue
                    else:
                        raise Exception("No more available YouTube API keys")
                else:
                    # Re-raise non-retryable errors
                    raise
            except Exception as e:
                self.logger.error(f"Unexpected error in API request: {e}")
                raise

        raise Exception("All API key retry attempts exhausted")

    def list_captions(self, video_id: str) -> Response:
        """
        List available captions for a video

        Args:
            video_id: YouTube video ID

        Returns:
            Response object containing caption track information
        """
        try:

            def request_func(service):
                return (
                    service.captions().list(part="snippet", videoId=video_id).execute()
                )

            response = self._execute_with_retry(request_func)

            captions_info = []
            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                captions_info.append(
                    {
                        "id": item.get("id"),
                        "language": snippet.get("language"),
                        "name": snippet.get("name"),
                        "track_kind": snippet.get(
                            "trackKind"
                        ),  # "standard" or "ASR" (auto-generated)
                        "is_auto_synced": snippet.get("isAutoSynced", False),
                        "is_cc": snippet.get("isCC", False),
                        "is_draft": snippet.get("isDraft", False),
                        "is_easy_reader": snippet.get("isEasyReader", False),
                        "is_large": snippet.get("isLarge", False),
                        "status": snippet.get("status"),
                        "audio_language": snippet.get("audioTrackType"),
                    }
                )

            return Response.success(
                status_code=200,
                message=f"Successfully retrieved caption list for video {video_id}",
                data={
                    "video_id": video_id,
                    "captions_count": len(captions_info),
                    "captions": captions_info,
                },
            )

        except HttpError as e:
            if e.resp.status == 404:
                return Response.not_found(
                    message=f"Video {video_id} not found or has no captions"
                )
            elif e.resp.status == 403:
                return Response.forbidden(
                    message=f"Access denied to captions for video {video_id}"
                )
            else:
                return Response.error(
                    status_code=e.resp.status,
                    message=f"Error listing captions for video {video_id}: {str(e)}",
                )
        except Exception as e:
            return Response.error(
                status_code=500,
                message=f"Unexpected error listing captions for video {video_id}: {str(e)}",
            )

    def _parse_ttml_transcript(self, ttml_content: str) -> List[Dict[str, Any]]:
        """
        Parse TTML (Timed Text Markup Language) format transcript

        Args:
            ttml_content: Raw TTML XML content

        Returns:
            List of transcript segments with timing information
        """
        try:
            root = ET.fromstring(ttml_content)

            # Define XML namespaces
            namespaces = {
                "ttml": "http://www.w3.org/ns/ttml",
                "ttm": "http://www.w3.org/ns/ttml#metadata",
                "ttp": "http://www.w3.org/ns/ttml#parameter",
                "tts": "http://www.w3.org/ns/ttml#styling",
            }

            transcript_data = []

            # Find all paragraph elements (caption segments)
            paragraphs = root.findall(".//ttml:p", namespaces)

            for p in paragraphs:
                # Extract timing information
                begin = p.get("begin", "0s")
                end = p.get("end", "0s")
                dur = p.get("dur")

                # Convert time format (e.g., "1.234s" to float seconds)
                start_time = self._parse_time_to_seconds(begin)
                end_time = self._parse_time_to_seconds(end)

                if dur:
                    duration = self._parse_time_to_seconds(dur)
                else:
                    duration = end_time - start_time if end_time > start_time else 0

                # Extract text content
                text_parts = []
                for elem in p.iter():
                    if elem.text:
                        text_parts.append(elem.text.strip())
                    if elem.tail:
                        text_parts.append(elem.tail.strip())

                text = " ".join(filter(None, text_parts))
                cleaned_text = clean_text(text)

                if cleaned_text:  # Only add non-empty segments
                    transcript_data.append(
                        {
                            "text": cleaned_text,
                            "start": start_time,
                            "duration": duration,
                            "end": end_time,
                        }
                    )

            return transcript_data

        except ET.ParseError as e:
            self.logger.error(f"Error parsing TTML content: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error parsing TTML: {e}")
            return []

    def _parse_time_to_seconds(self, time_str: str) -> float:
        """
        Convert time string to seconds
        Supports formats: "1.234s", "1:23.456", "1h2m3.456s"
        """
        try:
            time_str = time_str.strip()

            # Handle seconds format: "1.234s"
            if time_str.endswith("s"):
                return float(time_str[:-1])

            # Handle milliseconds format: "1234ms"
            if time_str.endswith("ms"):
                return float(time_str[:-2]) / 1000

            # Handle time format: "1:23.456" or "1:23:45.678"
            if ":" in time_str:
                parts = time_str.split(":")
                total_seconds = 0

                if len(parts) == 2:  # mm:ss.fff
                    minutes, seconds = parts
                    total_seconds = int(minutes) * 60 + float(seconds)
                elif len(parts) == 3:  # hh:mm:ss.fff
                    hours, minutes, seconds = parts
                    total_seconds = (
                        int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                    )

                return total_seconds

            # Default: try to parse as float (seconds)
            return float(time_str)

        except (ValueError, IndexError) as e:
            self.logger.warning(f"Could not parse time string '{time_str}': {e}")
            return 0.0

    def download_caption(self, caption_id: str, fmt: str = "ttml") -> Response:
        """
        Download caption content for a specific caption track

        Args:
            caption_id: Caption track ID from list_captions
            fmt: Format for caption download ("ttml", "srt", "vtt")

        Returns:
            Response object containing transcript data
        """
        try:

            def request_func(service):
                return service.captions().download(id=caption_id, tfmt=fmt).execute()

            # Get the download URL
            download_response = self._execute_with_retry(request_func)

            # The response should be the caption content directly
            if isinstance(download_response, bytes):
                caption_content = download_response.decode("utf-8")
            else:
                caption_content = str(download_response)

            # Parse the content based on format
            if fmt.lower() == "ttml":
                transcript_data = self._parse_ttml_transcript(caption_content)
            else:
                # For other formats, return raw content for now
                # You could implement SRT and VTT parsers here
                transcript_data = [
                    {
                        "text": caption_content,
                        "start": 0,
                        "duration": 0,
                        "end": 0,
                        "format": fmt,
                    }
                ]

            return Response.success(
                status_code=200,
                message=f"Successfully downloaded captions (format: {fmt})",
                data={
                    "caption_id": caption_id,
                    "format": fmt,
                    "transcript_count": len(transcript_data),
                    "transcript": transcript_data,
                    "raw_content": caption_content if fmt != "ttml" else None,
                },
            )

        except HttpError as e:
            if e.resp.status == 404:
                return Response.not_found(
                    message=f"Caption track {caption_id} not found"
                )
            elif e.resp.status == 403:
                return Response.forbidden(
                    message=f"Access denied to download caption {caption_id}"
                )
            else:
                return Response.error(
                    status_code=e.resp.status,
                    message=f"Error downloading caption {caption_id}: {str(e)}",
                )
        except Exception as e:
            return Response.error(
                status_code=500,
                message=f"Unexpected error downloading caption {caption_id}: {str(e)}",
            )

    def get_video_captions(
        self, video_id: str, language_preference: List[str] = None
    ) -> Response:
        """
        Get structured captions/transcript for a video with language preference

        Args:
            video_id: YouTube video ID
            language_preference: List of preferred languages (e.g., ["en", "en-US", "hi"])

        Returns:
            Response object containing structured transcript data
        """
        if language_preference is None:
            language_preference = ["en", "en-US", "en-GB"]

        # First, list available captions
        captions_response = self.list_captions(video_id)

        if captions_response.status_code != 200:
            return captions_response

        available_captions = captions_response.data.get("captions", [])

        if not available_captions:
            return Response.not_found(
                message=f"No captions available for video {video_id}"
            )

        # Find the best caption track based on language preference
        selected_caption = None

        # First priority: exact language match
        for lang in language_preference:
            for caption in available_captions:
                if caption.get("language") == lang:
                    selected_caption = caption
                    break
            if selected_caption:
                break

        # Second priority: any English variant if not found
        if not selected_caption:
            for caption in available_captions:
                if caption.get("language", "").startswith("en"):
                    selected_caption = caption
                    break

        # Third priority: first available caption
        if not selected_caption:
            selected_caption = available_captions[0]

        # Download the selected caption
        download_response = self.download_caption(
            selected_caption.get("id"), fmt="ttml"
        )

        if download_response.status_code != 200:
            return download_response

        # Combine caption info with transcript data
        result_data = {
            "video_id": video_id,
            "selected_caption": {
                "id": selected_caption.get("id"),
                "language": selected_caption.get("language"),
                "name": selected_caption.get("name"),
                "track_kind": selected_caption.get("track_kind"),
                "is_auto_generated": selected_caption.get("track_kind") == "ASR",
            },
            "available_languages": [cap.get("language") for cap in available_captions],
            "transcript_data": download_response.data.get("transcript", []),
            "total_segments": len(download_response.data.get("transcript", [])),
        }

        return Response.success(
            status_code=200,
            message=f"Successfully retrieved structured captions for video {video_id} in {selected_caption.get('language')}",
            data=result_data,
        )
