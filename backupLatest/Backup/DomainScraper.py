import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Updated date patterns to include various formats including "August 26, 2024 / 08:28 PM IST"
date_patterns = [
    r'\b\d{4}-\d{2}-\d{2}\b',  
    r'\b\d{2}/\d{2}/\d{4}\b', 
    r'\b\d{2}-\d{2}-\d{4}\b',  
    r'\b\d{1,2} \w{3,9} \d{4}\b', 
    r'\b\w{3,9} \d{1,2}, \d{4}\b',
    r'\b\d{1,2} \w{3} \d{4} \d{2}:\d{2} [APM]{2}\b',
    r'\b\w{3,9} \d{1,2}, \d{4} / \d{2}:\d{2} [APM]{2} \w{3}\b',
    r'\b\w{3,9} \d{1,2}, \d{4} / \d{2}:\d{2} [APM]{2} [A-Z]{3}\b',
    r'\b\w{3,9} \d{1,2}, \d{4}\b',
    r'\b\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\b', 
    r'\b\w{3} \d{1,2} \d{4} \d{1,2}:\d{2}[apAP][mM]\b',
    r'\b[A-Z][a-z]+, \w{3,9} \d{1,2}[a-z]{2}, \d{4}\b',  # Pattern for 'Saturday, August 31st, 2024'
]

def is_valid_url(url):
    # Check if the URL is valid and not external
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def extract_author_and_date(text):
    # print("texting==?",text)
    # Try to find the date using the provided patterns
     # Try to find the date using the provided patterns
    author = None
    pub_date = None
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            pub_date = match.group(0)
            # Assuming author is just before the date
            author_candidate_list = text[:match.start()].strip().split()
            if author_candidate_list:
                author_candidate = author_candidate_list[-1]
                author = author_candidate if author_candidate.isalpha() else None
            break
    return author, pub_date

def scrape_page(url):
    # Send a GET request to the website
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None  # Return None if there's an error
    
    # Parse the content with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract title, content, and publication date from the page
    title_tag = soup.find('h1')
    if title_tag:
        title = title_tag.get_text(strip=True)
        if len(title) < 20:
            title = None
    else:
        title = None

    if not title:
        title_tag = soup.find('h2')
        title = title_tag.get_text(strip=True) if title_tag else 'No Title'

    content = ' '.join([p.get_text(strip=True) for p in soup.find_all('p')])
    
    # Look for author and publication date in the content
    body_text = soup.get_text(strip=True)
    print("checkingbody_text==?",body_text)
    author, pub_date = extract_author_and_date(body_text)
    
    # If author or date not found in content, try in meta tags
    if not pub_date:
        for meta_tag in soup.find_all('meta'):
            meta_content = meta_tag.get('content', '')
            author, pub_date = extract_author_and_date(meta_content)
            if pub_date:
                break
    
    return {
        "url": url,
        "title": title,
        "content": content,
        "author": author if author else 'Author not found',
        "publication_date": pub_date if pub_date else 'Date not found'
    }

def crawl_website(url):
    # Send a GET request to the website
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []
    
    # Parse the content with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract all the links
    links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        # Join the base URL with the href to get an absolute URL
        full_url = urljoin(url, href)
        if is_valid_url(full_url):
            links.add(full_url)
    
    return links

def main(initial_url):
    links = crawl_website(initial_url)
    all_data = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(scrape_page, link): link for link in links}
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                data = future.result()
                if data:
                    all_data.append(data)
            except Exception as e:
                print(f"Error processing {url}: {e}")
    
    with open('scraped_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
    
    print("Data saved to scraped_data.json")

if __name__ == "__main__":
    # Example URL to start crawling
    # initial_url = "https://10tv.in/"
    # initial_url = "https://www.yashbharat.com/"
    # initial_url = "https://worldnewsnetwork.co.in/"
    # initial_url = "https://worldnewsnetwork.co.in/"
    # initial_url = "https://www.indianeconomicobserver.com/"
    # initial_url = "https://www.indianeconomicobserver.com/"
    # initial_url = "https://www.indianewsnetwork.com/"
    # initial_url = "https://www.getnews.info/"
    # initial_url = "https://8pmnews.com/"
    # initial_url = "https://www.forpressrelease.com/"
    # initial_url = "https://www.inkhabar.com/"
    # initial_url = "https://www.mountaintoday.in/"
    # initial_url = "https://newsindialive.in/"
    # initial_url = "https://tv9telugu.com/"
    # initial_url = "https://rajasthanexpress.in/"
    # initial_url = "https://pharmawisdom.co.in/"
    # initial_url = "https://www.bhaskarhindi.com/"
    # initial_url = "https://www.tv9marathi.com/"
    # initial_url = "https://dailynews24.in/"
    # initial_url = "https://www.moneycontrol.com/"
    # initial_url = "https://www.zeebiz.com/"
    # initial_url = "https://www.uniindia.com/"
    # initial_url="https://tv9telugu.com/"
    # inital_url="https://www.tv9marathi.com/"
    # inital_url="https://biovoicenews.com/"
    # inital_url="https://tv9gujarati.com/"
    # inital_url="https://tv9kannada.com/"
    # inital_url="https://ntvtelugu.com/"
    # inital_url="https://indianexpress.com/"
    # inital_url="https://kannada.hindustantimes.com/"
    # inital_url="https://keralakaumudi.com/news/"
    # inital_url="https://indiaeducationdiary.in/"
    # inital_url="https://news7h.com/"
    # inital_url="https://www.lokmattimes.com/"
    # inital_url="https://glamsham.com/"
    # inital_url="https://bangalorebuzz.in/"
    # inital_url="https://shaktinews.in/"
    # initial_url = "https://www.jamshedpurreporter.in/"
    # initial_url = "https://www.realtimeindia.in/"
    # initial_url = "https://jantaserishta.com/"
    # initial_url="https://www.loksatta.com/"
    # initial_url="https://mediabulletins.com/"
    # initial_url="https://www.esakal.com/"
    # initial_url="https://consumerinfoline.com/"
    # initial_url="https://samacharcentral.com/"
    # initial_url="https://www.thelocalreport.in/"
    # initial_url="https://www.secunderabadchronicle.in/"
    # initial_url="https://ndtv.in/"
    # initial_url="https://justbureaucracy.com/"
    # initial_url="https://business-news-today.com/"
    # initial_url="https://fossbyte.in/"
    # initial_url="https://taxguru.in/"
    
    initial_url="https://investmentguruindia.com/"
    
    

    main(initial_url)
