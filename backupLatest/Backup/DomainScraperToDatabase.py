import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import urllib.parse
import psycopg2
from concurrent.futures import ThreadPoolExecutor, as_completed


conn = psycopg2.connect(
    dbname="prod_cirrus",
    user="prod_admin",
    password="Cir^Pnq@2023",
    host="51.68.220.77",
    port="5432"
)
cur = conn.cursor()

date_patterns = [
    r'\b\d{4}-\d{2}-\d{2}\b',  
    r'\b\d{2}/\d{2}/\d{4}\b', 
    r'\b\d{4}-\d{2}-\d{2}\b',
    r'\b\d{2}-\d{2}-\d{4}\b',  
    r'\b\d{1,2} \w{3,9} \d{4}\b', 
    r'\b\w{3,9} \d{1,2}, \d{4}\b',
    r'\b\d{1,2} \w{3} \d{4} \d{2}:\d{2} [APM]{2}\b',
    r'\b\w{3,9} \d{1,2}, \d{4} / \d{2}:\d{2} [APM]{2} \w{3}\b',
    r'\b\w{3,9} \d{1,2}, \d{4} / \d{2}:\d{2} [APM]{2} [A-Z]{3}\b',
    r'\b\w{3,9} \d{1,2}, \d{4}\b',
    r'\b\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\b', 
    r'\b\w{3} \d{1,2} \d{4} \d{1,2}:\d{2}[apAP][mM]\b'
]

def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def extract_author_and_date(text):
    pub_date = None
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            pub_date = match.group(0)
            break
    return pub_date

def scrape_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
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
    
    body_text = soup.get_text(strip=True)
    pub_date = extract_author_and_date(body_text)
    
    if not pub_date:
        for meta_tag in soup.find_all('meta'):
            meta_content = meta_tag.get('content', '')
            pub_date = extract_author_and_date(meta_content)
            if pub_date:
                break
    
    return {
        "url": url,
        "title": title,
        "content": content,
        "publication_date": pub_date if pub_date else 'Date not found'
    }


def extract_domain(url):
    parsed_url = urllib.parse.urlparse(url)
    domain = parsed_url.netloc
    return domain

def crawl_website(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        full_url = urljoin(url, href)
        if is_valid_url(full_url):
            links.add(full_url)
    
    return links

def process_url(url):
    domain = urlparse(url).netloc
    publication_name = extract_domain(url)
    
    domain_name = domain.replace('www.', '')  # Re
    links = crawl_website(url)

    for link in links:
        print(f"Scraping: {link}")
        data = scrape_page(link)
        if data and data['title'] and data['publication_date'] != 'Date not found':
            try:
                cur.execute("""
                    INSERT INTO public."WEBSITES_LINK" (
                        "LINK", "FEEDDATETIME", "HEADLINE", "SUMMARY", 
                        "PUBLICATION", "PUBLICATIONID", "LANGUAGE", 
                        "IMAGE_URL", "CREATEDBY", "CREATEDON", "TAGGED"
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT ("LINK") DO NOTHING
                """, (
                    data['url'],
                    data['publication_date'],  
                    data['title'],
                    data['content'][:500], 
                    publication_name,
                    '',  
                    'en',  
                    '',  
                    'scraper',  
                    None,  
                    0  # TAGGED
                ))
                conn.commit()
            except Exception as e:
                print(f"Error inserting data for {link}: {e}")
                conn.rollback()
def main(urls):
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_url, url) for url in urls]
        for future in as_completed(futures):
            try:
                future.result()  
            except Exception as e:
                print(f"Error processing a URL: {e}")

if __name__ == "__main__":
    urls = [
        "https://10tv.in/",
        "https://www.yashbharat.com/",
        "https://worldnewsnetwork.co.in/",
        "https://www.indianeconomicobserver.com/",
        "https://www.indianewsnetwork.com/",
        "https://www.getnews.info/",
        "https://8pmnews.com/",
        "https://www.forpressrelease.com/",
        "https://www.inkhabar.com/",
        "https://www.mountaintoday.in/",
        "https://newsindialive.in/",
        "https://tv9telugu.com/",
        "https://rajasthanexpress.in/",
        "https://pharmawisdom.co.in/",
        "https://www.bhaskarhindi.com/",
        "https://www.tv9marathi.com/",
        "https://dailynews24.in/",
        "https://www.jamshedpurreporter.in/",
        "https://www.moneycontrol.com/",
        "https://www.zeebiz.com/",
        "https://www.jamshedpurreporter.in/",
        "https://24x7livenewz.com/",
        "https://www.tv9marathi.com/",
        "https://biovoicenews.com/",
        "https://tv9gujarati.com/",
        "https://tv9kannada.com/",
        "https://ntvtelugu.com/",
        "https://kannada.hindustantimes.com/",
        "https://keralakaumudi.com/news/",
        "https://indiaeducationdiary.in/",
        "https://www.lokmattimes.com/",
        "https://glamsham.com/",
        "https://bangalorebuzz.in/",
        "https://shaktinews.in/",
        "https://www.realtimeindia.in/",
        "https://jantaserishta.com/",
        "https://www.loksatta.com/",
        "https://mediabulletins.com/",
        "https://www.esakal.com/",
        "https://consumerinfoline.com/",
        "https://samacharcentral.com/",
        "https://thelocalreport.in/",
        "https://ndtv.in/",
        "https://www.tv9hindi.com/",
        "https://justbureaucracy.com/",
        "https://business-news-today.com/",
        "https://fossbyte.in/",
        "https://8pmnews.com/",
        "https://thehillstimes.in/",
        "https://www.jansatta.com/",
        "https://rajasthanexpress.in/",
        "https://www.techgig.com/",
        "https://www.newsvoir.com/",
        "https://www.technobugg.com/",
        "https://www.telanganatribune.com/",
        "https://pynr.in/",
        "https://biovoicenews.com/",
        "https://www.navarashtra.com/",
        "https://www.ntnews.com/",
        "https://www.businessleague.in/",
        "https://thefactnews.in/",
        "https://www.pioneeredge.in/",
        "https://thenewsmen.co.in/",
        "https://skilloutlook.com/",
        "https://www.aviation-defence-universe.com/",
        "https://maeeshat.in/",
        "https://stylecity.in/",
        "https://www.chandigarhcitynews.com/",
        "https://channeldrive.in/",
        "https://www.generaldaily.com/",
        "https://insightonlinenews.in/",
        "https://www.ncnonline.net/",
        "https://www.punjabijagran.com/",
        "https://ujjawalprabhat.com/",
        "https://aajkijandhara.com/",
        "https://www.sarvgyan.com/",
        "https://www.abplive.com/",
        "https://www.news18.com/",
        "https://www.deccanherald.com/",
        "https://www.theweek.in/",
        "https://bangalorebuzz.in/",
        "https://therightnews.in/",
        "https://www.amarujala.com/",
        "https://www.latestly.com/",
        "https://news.abplive.com/",
        "https://keralakaumudi.com/news/",
        "https://vibesofindia.com/",
        "https://indiapostlive.com/",
        "https://www.crictracker.com/",
        "https://www.devdiscourse.com/",
        "https://www.chinamoneynetwork.com/",
        "https://timesofindia.indiatimes.com/",
        "https://thecanarapost.com/",
        "https://www.lokmattimes.com/",
        "https://opoyi.com/",
        "https://www.thenewsminute.com/",
        "https://www.theweek.in/",
        "https://theonlinenews.in/",
        "https://10tv.in/",
        "https://brainfeedmagazine.com/",
        "https://glamsham.com/",
        "https://kannada.hindustantimes.com/",
        "https://kashmirstudentalerts.com/",
        "https://money.rediff.com/",
        "https://psuwatch.com/",
        "https://www.ragalahari.com/",
        "https://shaktinews.in/",
        "https://siliconcanals.com/",
        "https://startupsuccessstories.in/",
        "https://tennisuptodate.com/",
        "https://www.thefintechbuzz.com/",
        "https://tricksbystg.org/",
        "https://urduheadline.com/",
        "https://urdupoint.com/",
        "https://www.theweek.in/",
        "https://www.vanitynoapologies.com/",
        "https://idrw.org/",
        "https://thestatesman.com/",
        "https://therightnews.in/",
        "https://latestly.com/",
        "https://keralakaumudi.com/",
        "https://vibesofindia.com/",
        "https://indiapostlive.com/",
        "https://www.songoti.in/",
        "https://www.thehighereducationreview.com/",
        "https://ajhindidaily.com/",
        "https://www.bikes4sale.in/",
        "https://hindupad.com/",
        "https://www.inextlive.com/",
        "https://ajhindidaily.com/",
        "https://tricitytoday.com/"
        
        
        "https://gadgetsnow.indiatimes.com/",
        "https://www.techgig.com/"
    ]

    main(urls)


cur.close()
conn.close()
