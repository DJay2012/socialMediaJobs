import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dateutil import parser
import re

def is_new_article(url, days=10):
    try:
        # Fetch the webpage content
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse the content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Common meta tags and elements for publication dates
        date = None
        date_sources = [
            {"property": "article:published_time"},
            {"name": "datePublished"},
            {"name": "pubdate"},
            {"name": "publish-date"},
            {"name": "article:published_time"},
            {"name": "OriginalPublicationDate"},
            {"property": "og:updated_time"},
            {"name": "og:updated_time"},
            {"name": "dc.date"},
            {"name": "dcterms.date"},
            {"name": "date"},
            {"name": "dc.date.issued"},
            {"itemprop": "datePublished"},
            {"itemprop": "dateCreated"},
            {"itemprop": "dateModified"}
        ]
        
        # Search for publication date in meta tags
        for tag in date_sources:
            meta_tag = soup.find("meta", tag)
            if meta_tag and meta_tag.get("content"):
                date_str = meta_tag["content"]
                try:
                    # Parse the date string
                    date = parser.parse(date_str)
                    if date.tzinfo is not None:
                        date = date.replace(tzinfo=None)
                    break  # Exit loop if a date is successfully parsed
                except (parser.ParserError, ValueError):
                    continue  # Try the next tag if parsing fails

        # Search for publication date in <time> and other potential elements
        if date is None:
            time_elements = soup.find_all("time")
            for time_elem in time_elements:
                date_str = time_elem.get("datetime") or time_elem.text
                try:
                    date = parser.parse(date_str)
                    if date.tzinfo is not None:
                        date = date.replace(tzinfo=None)
                    break
                except (parser.ParserError, ValueError):
                    continue
        
        # Check for date in other common tag classes/ids if still not found
        if date is None:
            for elem in soup.find_all(["span", "p", "div"], {"class": ["date", "published", "pubdate", "post-date", "entry-date"]}):
                date_str = elem.text
                try:
                    date = parser.parse(date_str)
                    if date.tzinfo is not None:
                        date = date.replace(tzinfo=None)
                    break
                except (parser.ParserError, ValueError):
                    continue

        # If no date was parsed, check the URL path for news-related keywords as a fallback
        if date is None:
            print("datechecker==?",date)
            news_keywords = ["news", "latestnews", "breakingnews", "trendingnews", "article", "story"]
            url_path = url.split("://")[-1].split("/", 1)[-1]  # Get the path part of the URL
            if any(keyword in url_path.lower() for keyword in news_keywords):
                return "New article based on URL keywords"
            else:
                return "No publication date found and URL does not indicate news content."

        # Calculate if the date is within the threshold
        threshold_date = datetime.now().replace(tzinfo=None) - timedelta(days=days)
        is_new = date >= threshold_date
        return "New article" if is_new else "Not a new article"

    except requests.RequestException as e:
        return f"An error occurred while fetching the URL: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

# Example usage
url = "https://www.arthparkash.com/category/Business/"
print(is_new_article(url))
