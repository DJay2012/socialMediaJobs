import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json


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
    r'\b[A-Z][a-z]+, \w{3,9} \d{1,2}[a-z]{2}, \d{4}\b',  
]


html_date_patterns = [
    r'\b\d{1,2} \w{3,9} \d{4}\b',  
    r'\b\d{2}/\d{2}/\d{4}\b',      
    r'\b\d{2}-\d{2}-\d{4}\b',      
    r'\b\w{3,9} \d{1,2}, \d{4}\b',  
    r'\b\w{3,9} \d{1,2}, \d{4} \d{2}:\d{2} [APM]{2}\b', 
    r'\b\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\b',  
]



date_pattern = r'''
    (\b(?:\d{1,2}\s[A-Z][a-z]{2,8}\s\d{4}|\b[A-Z]{3}\s\d{1,2}\s,\s\d{4}\b))|            
    (\b\d{1,2}-\d{1,2}-\d{4}\b\s\d{1,2}:\d{2}\s(?:AM|PM)\b)|                             
    (\b(?:\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\b|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}))| 
    (\b[A-Za-z]+\s\d{1,2}[a-z]{2},\s\d{4}\b)|                                            
    (\b\d{1,2}\s[A-Z][a-z]{2,8}\s\d{4},\s\d{2}:\d{2}\s(?:AM|PM)\b)|                      
    (\b[A-Z][a-z]{2,8}\s\d{1,2},\s\d{4}\b)                                               
'''

def setup_driver():
    options = Options()
    options.headless = True
    options.add_argument("--window-size=1920x1080")
    driver = webdriver.Chrome(options=options)
    return driver

def scrape_page_with_selenium(driver, url):
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else 'No Title'
    
    content = ' '.join([p.get_text(strip=True) for p in soup.find_all('p')])
    body_text = soup.get_text(strip=True)
    publication_date = find_publication_date(body_text)
    

    if publication_date == 'Date not found':
        soup_text = soup.get_text()  # Extract text from the BeautifulSoup object
        matches = re.findall(date_pattern, soup_text, re.VERBOSE)
        # Flatten and filter out empty strings
        publication_date = [match for group in matches for match in group if match]
    
    return {
        "url": url,
        "title": title,
        "content": content,
        "body": body_text,
        "author": 'Author not found',  
        "publication_date": publication_date
    }

def find_publication_date(content):
    for pattern in date_patterns:
        match = re.search(pattern, content)
        if match:
            return match.group()
    return 'Date not found'

def find_date_in_html_tags(soup):
    # Extract text from all relevant tags
    relevant_tags = ['div', 'span', 'time']
    text_content = ' '.join(
        tag.get_text(strip=True) for tag in soup.find_all(relevant_tags)
    )
    
    for pattern in html_date_patterns:
        match = re.search(pattern, text_content)
        if match:
            return match.group()
    
    return 'Date not found'

def crawl_website(driver, initial_url):
    driver.get(initial_url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if href.startswith("http"):
            links.append(href)
        else:
            links.append(f"{initial_url.rstrip('/')}/{href.lstrip('/')}")
    
    return list(set(links))

def main_with_selenium(initial_url):
    driver = setup_driver()
    
    links = crawl_website(driver, initial_url)
    
    all_data = []
    for link in links:
        data = scrape_page_with_selenium(driver, link)
        if data:
            all_data.append(data)
    
    with open('scraped_data_selenium.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
    
    print("Data saved to scraped_data_selenium.json")
    
    driver.quit()

if __name__ == "__main__":
    initial_url = "https://outlookhindi.com/" 
    main_with_selenium(initial_url)