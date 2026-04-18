import requests
from bs4 import BeautifulSoup
import json
import re
import psycopg2
from concurrent.futures import ThreadPoolExecutor
import urllib.parse
from datetime import datetime

def extract_date(text):
    # Clean the text to remove any unwanted characters like 'more'
    text = re.sub(r'\bmore\b', '', text).strip()

    date_patterns = [
        r'\b\d{4}-\d{2}-\d{2}\b',  
        r'\b\d{2}/\d{2}/\d{4}\b', 
        r'\b\d{2}-\d{2}-\d{4}\b',  
        r'\b\d{1,2} \w{3,9} \d{4}\b', 
        r'\b\w{3,9} \d{1,2}, \d{4}\b' 
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            date_str = match.group(0)
            try:
                # Convert to a standardized format
                if '-' in date_str:  # 'YYYY-MM-DD' or 'DD-MM-YYYY'
                    return datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
                elif '/' in date_str:  # 'MM/DD/YYYY'
                    return datetime.strptime(date_str, '%m/%d/%Y').strftime('%Y-%m-%d')
                elif ',' in date_str:  # 'Month DD, YYYY'
                    return datetime.strptime(date_str, '%b %d, %Y').strftime('%Y-%m-%d')
                else:  # 'DD Month YYYY'
                    return datetime.strptime(date_str, '%d %B %Y').strftime('%Y-%m-%d')
            except ValueError:
                continue  # Skip if there's a parsing issue

    return None

def extract_time(text):
    time_patterns = [
        r'\b\d{1,2}:\d{2}(?:\s?[APM]{2})?\b',  
        r'\b\d{1,2} (?:hours?|minutes?) ago\b',  
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    
    return 'No date or time found'

def scrape_website(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        scraped_data = []

        base_url = '/'.join(url.split('/')[:3])

        for a_tag in soup.find_all('a'):
            title = a_tag.get_text(strip=True)
            link = a_tag.get('href')

            if link and link.startswith(base_url):
                scraped_data.append({'title': title, 'link': link})

        print(f'Initial data scraped from {url}, now fetching article details...')

        articles_with_details = []
        for article in scraped_data:
            print("Processing article:", article)
            article_details = scrape_article_details(article['link'])
            if article_details and article_details['title'] != 'No title' and article_details['publicationDate'] != 'No publication date':
                articles_with_details.append(article_details)

        # Insert articles into PostgreSQL
        insert_articles_into_postgresql(url, articles_with_details)
       
        return {
            'website': url,
            'articleCount': len(articles_with_details),
            'articles': articles_with_details
        }

    except requests.exceptions.RequestException as e:
        print(f'Error fetching the URL: {e}')
        return {
            'website': url,
            'articleCount': 0,
            'articles': []
        }


def scrape_article_details(article_url):
    try:
        response = requests.get(article_url)
        response.raise_for_status()

        try:
            soup = BeautifulSoup(response.text, 'lxml')
        except Exception as e:
            print(f'lxml parser failed for {article_url}: {e}, trying html.parser...')
            soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else 'No title'
        
        h1_tag = soup.find('h1')
        image_url = 'No image'
        title_sibling_text = ''
        if h1_tag:
            next_sibling = h1_tag.find_next_sibling()
            while next_sibling:
                if next_sibling.name == 'img':
                    image_url = next_sibling['src']
                  # Check for a p tag and its length
                elif next_sibling.name == 'p':
                    p_text = next_sibling.get_text(strip=True)
                    if len(p_text) < 20:
                        title_sibling_text = p_text
                    break

                next_sibling = next_sibling.find_next_sibling()

        content = title_sibling_text if title_sibling_text else '\n'.join([p.get_text(strip=True) for p in soup.find_all('p')])
        body_text = soup.get_text(strip=True)
        date = extract_date(body_text)
        
        article_details = {
            'title': title,
            'author': soup.find(class_='author').get_text(strip=True) if soup.find(class_='author') else 'No author',
            'publicationDate': date if date else 'No publication date',
            'content': content,
            'image': image_url,
            'link': article_url,
        }
        
        print("checkingarticle===>",article_details)
        

        return article_details

    except requests.exceptions.RequestException as e:
        print(f'Error fetching the article URL: {e}')
        return None
    except Exception as e:
        print(f'Error parsing article content from {article_url}: {e}')
        return None
    
def extract_domain(url):
    parsed_url = urllib.parse.urlparse(url)
    domain = parsed_url.netloc
    return domain

def insert_articles_into_postgresql(website_url, articles):
    conn = psycopg2.connect(
        dbname="prod_cirrus",
        user="prod_admin",
        password="Cir^Pnq@2023",
        host="51.68.220.77",
        port="5432"
    )
    cur = conn.cursor()
    
    publication_name = extract_domain(website_url)
    max_length = 4000
    
    for article in articles:
        
            print("main->",article['title'][:max_length])
            cur.execute("""
                INSERT INTO public."WEBSITES_LINK" (
                    "LINK", "FEEDDATETIME", "HEADLINE", "SUMMARY", 
                    "PUBLICATION", "PUBLICATIONID", "LANGUAGE", 
                    "IMAGE_URL", "CREATEDBY", "CREATEDON", "TAGGED"
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT ("LINK") DO NOTHING
            """, (
                
                article['link'],
                article['publicationDate'],
                article['title'][:max_length],
                article['content'][:max_length],
                publication_name,  # Publication name
                '',  # Publication ID (not provided in the script)
                'en',  # Language (you need to implement language detection)
                article['image'],
                'scraper',  # Created by (example value, modify as needed)
                None,  # Created on (you can add current timestamp if required)
                0  # Tagged
            ))

    conn.commit()
    cur.close()
    conn.close()
    

def scrape_all_websites(urls):
    results = []
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(scrape_website, urls))
    
    return results

urls = [
    # "https://tezzbuzz.com/",
    # "https://www.htsyndication.com/",
    # "http://smallnews.in/",
    # "https://www.yashbharat.com/",
    # "https://worldnewsnetwork.co.in/",
    # "https://www.indianeconomicobserver.com/",
    # "https://www.indianewsnetwork.com/",
    # "https://www.getnews.info/",
    # "https://thefreedompress.in/",
    # "https://www.realtimeindia.in/",
    # "https://hiindia.com/",
    # "http://weeklyvoice.com/",
    # "https://www.shiksha.com/",
    # "http://investmentguruindia.com/",
    # "https://jantaserishta.com/",
    # "https://www.apsense.com/",
    # "http://60secondsnow.com/",
    # "https://adkhabar.com/",
    # "https://inn24news.in/",
    # "http://eflip.in/",
    # "https://www.watchlistnews.com/",
    # "https://www.loksatta.com/",
    # "https://swapupdate.in/",
    # "https://mediabulletins.com/",
    # "https://samacharnama.com/",
    # "https://aplatestnews.com/default.php",
    # "https://www.esakal.com/",
    # "https://www.jalandhar-online.in/",
    # "https://www.haridwartoday.in/",
    # "https://www.jammuandkashmirheadlines.in/",
    # "https://consumerinfoline.com/",
    # "https://www.punjabsamachar.in/",
    # "https://www.varanasinewsmagazine.in/",
    # "https://www.jamshedpurreporter.in/",
    # "https://www.ranchinewsdesk.in/",
    # "https://www.vascodagamaonlinejournal.in/",
    # "https://www.guwahatimail.in/",
    # "https://samacharcentral.com/",
    # "https//www.punemagazine.in/",
    # "https://thelocalreport.in/",
    # "https://www.secunderabadchronicle.in/",
    # "https://www.nagalandnewstoday.in/",
    # "https://news89.com/",
    # "https://ndtv.in/",
    # "https://smartprix.com/",
    # "https://www.tv9hindi.com:443/",
    # "https://www.anandabazar.com/",
    # "https://www.nainitalnewsflash.in/",
    # "https://justbureaucracy.com/",
    # "https://cyberworldtechnologies.co.in/",
    # "https://www.bseindia.com/",
    # "https://aoplweb.in/",
    # "https://www.giridihjournal.in/",
    # "https://jayka.in/",
    # "https://redhot.sg/",
    # "https://www.itanagarnews.in/",
    # "https://lifecarenews.in/",
    # "https://business-news-today.com/",
    # "https://www.chandigarhherald.in/",
    # "https://fossbyte.in/",
    # "https://8pmnews.com/",
    # "https://jaipurherald.in/",
    # "https://www.forpressrelease.com/",
    # "https://www.twarak.com/",
    # "https://www.cochinreporter.in/",
    # "https://www.freelancer.in/",
    # "https://www.youthkiawaaz.com/",
    # "https://www.inkhabar.com/",
    # "https://www.mountaintoday.in/",
    # "https://newsindialive.in/",
    # "https://etradewire.com/",
    # "https://www.indiandefensenews.in/",
    # "https://www.marketquest.biz/",
    # "https://www.westernindiajournal.in/",
    # "https://www.freshersworld.com/",
    # "https://mrgaga.in/",
    # "https://www.forevernews.in/",
    # "https://purvanchaltoday.in/",
    # "https://www.thechhattisgarh.com/",
    # "https://www.marketsandmarkets.com/",
    # "https://www.tupaki.com/",
    # "https://tv9telugu.com/",
    # "https://udaipurkiran.in/",
    # "https://www.electronicsb2b.com/",
    # "https://www.pharmiweb.jobs/",
    # "https://varindia.com/",
    # "https://thehillstimes.in/",
    # "https://www.supermarketresearch.com/",
    # "https://24x7livenewz.com/",
    # "https://www.jansatta.com/",
    # "https://rajasthanexpress.in/",
    # "https://www.techgig.com/",
    # "https://asiannews.in/",
    # "https://pharmawisdom.co.in/",
    # "https://shifting-gears.com/",
    # "https://india-press-release.com/",
    # "https://lalluram.com/",
    # "https://www.realestateindia.com/",
    # "https://www.bhaskarhindi.com/",
    # "https://bull-leds.in/",
    # "https://aljazeera.co.in/",
    # "http://www.general.in/",
    # "https://www.tv9marathi.com/",
    # "https://bollyy.com/",
    # "https://ipfonline.com/",
    # "https://www.newsvoir.com/",
    # "https://www.newyorkindian.com/desi/",
    # "https://ssbcrackexams.com/",
    # "https://www.technobugg.com/",
    # "https://eximin.net/",
    # "https://www.telanganatribune.com/",
    # "https://emobilityplus.com/",
    # "https://pynr.in/",
    # "https://biovoicenews.com/",
    # "https://www.lybrate.com/",
    # "https://www.mediainfoline.com/",
    # "https://mobilityindia.com/",
    # "https://www.navarashtra.com/",
    # "https://startupreporter.in/",
    # "https://www.theindiadaily.com/",
    # "https://www.ntnews.com/",
    # "https://www.emsindia.com/",
    # "https://saverupee.in/",
    # "https://www.businessleague.in/",
    # "https://dailynews24.in/",
    # "https://educba.com/",
    # "https://examsdaily.in/",
    # "https://www.journeyline.in/",
    # "https://www.ournet.in/",
    # "https://prfeed.in/",
    # "https://www.salemonlinejournal.in/",
    # "https://www.commonfloor.com/",
    # "https://www.fmlive.in/",
    # "https://retailjewellerindia.com/",
    # "https://www.sfindian.com/desi/",
    # "https://asiainsurancepost.com/",
    # "https://www.broadcastandcablesat.co.in/",
    # "https://gstimes.in/",
    # "https://marketingmind.in/",
    # "https://startupcolleges.com/",
    # "https://thefactnews.in/",
    # "https://trinitymirror.net/news/",
    # "https://womenworld.eu/",
    # "https://cellit.in/",
    # "https://www.pioneeredge.in/",
    # "https://www.reportwire.in/",
    # "https://sightsinplus.com/",
    # "https://thenewsmen.co.in/",
    # "https://ukragroconsult.com/",
    # "https://bombaysamachar.com/",
    # "https://www.earlytimes.in/",
    # "http://industrialautomationindia.in/",
    # "https://newsjournals.in/",
    # "https://skilloutlook.com/",
    # "https://www.theceo.in/",
    # "https://www.aviation-defence-universe.com/",
    # "https://www.businessremedies.com/",
    # "https://drugtodayonline.com/",
    # "https://henryclubs.com/",
    # "https://maeeshat.in/",
    # "https://marketsandmarketsblog.com/",
    # "https://stylecity.in/",
    # "https://tv9gujarati.com/",
    # "https://capage.in/",
    # "https://www.chandigarhcitynews.com/",
    # "https://channeldrive.in/",
    # "https://www.eqmagpro.com/",
    # "https://www.generaldaily.com/",
    # "https://hyderabadtalks.com/",
    # "https://mybrandbook.co.in/",
    # "https://theheadlines.in/",
    # "https://andhraguide.com/",
    # "https://www.automotive-technology.com/",
    # "https://insightonlinenews.in/",
    # "https://www.ncnonline.net/",
    # "https://www.newjerseyindian.com/desi/",
    # "https://www.punjabijagran.com/",
    # "https://thepurbottar.in/",
    # "https://nrinews24x7.com/",
    # "https://prayukti.net/",
    # "https://www.todaystraveller.net/",
    # "https://tv9kannada.com/",
    # "https://ujjawalprabhat.com/",
    # "https://watsup.in/",
    # "https://aajkijandhara.com/",
    # "https://idreampost.com/",
    # "https://indiaoutbound.info/",
    # "https://indias.news/",
    # "https://ntvtelugu.com/",
    # "https://www.phonebunch.com/",
    # "https://www.sarvgyan.com/",
    # "https://streettimes.in/",
    
    
    
    
    
    # "https://techdeals.co.in/",
    # "https://www.thelallantop.com:443/",
    # "https://theonlinenews.in/",
    # "https://10tv.in/",
    # "https://www.autofans.in/",
    # "https://www.autoguideindia.com/",
    # "https://brainfeedmagazine.com/",
    # "https://chennaivision.com/",
    # "https://www.earthmagz.com/",
    # "https://eetindia.co.in/",
    # "http://eletimes.com/",
    # "https://fanfight.in/",
    # "https://glamsham.com/",
    # "https://happyeasygo.com/",
    # "https://icreateedutech.com/",
    # "https://jobs.icaneducate.in/",
    # "https://indiaincgroup.com/",
    # "https://indianexpress.com/",
    # "https://www.insidehighered.com/",
    # "http://intelligentinsurer.com/",
    # "https://kannada.hindustantimes.com/",
    # "https://kashmirstudentalerts.com/",
    # "https://matrubhumi.com/",
    # "https://money.rediff.com/",
    # "https://myogi.in/",
    # "https://psuwatch.com/",
    # "https://www.ragalahari.com/",
    # "https://shaktinews.in/",
    # "https://siliconcanals.com/",
    # "https://startupsuccessstories.in/",
    # "https://tennisuptodate.com/",
    # "https://www.thefintechbuzz.com/",
    # "https://www.theweekendleader.com/",
    # "https://tricksbystg.org/",
    # "https://www.uktech.news/",
    # "https://urduheadline.com/",
    # "https://urdupoint.com/",
    # "https://way2barak.com/",
    # "https://www.theweek.in/",
    # "https://www.theelablog.com/",
    # "https://tech.visionplusmag.com/",
    # "https://infosecurity.in/",
    # "https://karnatakamirror.com/",
    # "https://sportsmatik.com/",
    # "https://www.vanitynoapologies.com/",
    # "https://idrw.org/",
    # "https://www.enewscafe.com/",
    # "https://www.shilpaahuja.com/",
    # "https://www.madhyamam.com/",
    # "https://newzhook.com/",
    # "https://thestatesman.com/",
    # "https://bangalorebuzz.in/",
    
    
    
    # "https://therightnews.in/",
    # "https://theendnews.in/",
    # "https://webdeveloperpune.com/",
    # "https://amarujala.com/",
    # "https://computerhube.com/",
    # "https://latestly.com/",
    # "https://news.abplive.com/",
    # "https://www.revistaneon.net/",
    # "https://keralakaumudi.com/",
    # "https://vibesofindia.com/",
    # "https://indiapostlive.com/",
    # "https://www.crictracker.com/",
    # "https://leads.brandsynario.com/",
    # "https://www.idrw.org/",
    # "https://jaipurjournal.in/",
    # "https://www.devdiscourse.com/",
    # "https://www.apnnews.com/",
    # "https://tv9telugu.com/",
    # "https://www.keralatimes.in/",
    # "https://timesheadline.com/",
    # "https://policenama.com/",
    # "https://news7h.com/",
    # "https://www.chinamoneynetwork.com/",
    # "https://www.biospectrumindia.com/",
    # "https://timesofindia.indiatimes.com/",
    # "https://thecanarapost.com/",
    # "https://ukwire.com/",
    # "https://www.telanganaflashnews.com/",
    # "https://iguruji.in/",
    # "https://www.lokmattimes.com/",
    # "https://wionews.com/",
    # "https://www.tiptoptens.com/",
    # "https://www.indiantelevision.com/",
    # "https://breakingnewstoday.co.in/",
    # "https://www.agencefrancenationale.com/",
    # "https://www.bemoneyaware.com/",
    # "https://dronacharya.info/",
    # "https://asianmirror.us/",
    # "https://opoyi.com/",
    # "https://nyoooz.com/",
    # "https://mailislam.in/",
    # "https://www.thenewsminute.com/",
    # "https://indiaeducationdiary.in/",
    # "https://addprimes.com/",not working link error
    # "https://www.techsciresearch.com/",
    # "https://www.indiainfoline.com/",
    # "https://www.abplive.com/",
    # "https://www.mumbailive.com/",
    # "https://www.news18.com/",
    # "https://techobserver.in/",
    # "https://www.cardealerindia.com/", not working link error
    # "https://www.madhyamam.com/",
    # "https://www.uniindia.com/",
    # "https://www.newsdrops.in/",
    # "https://www.upes.ac.in/",
    # "https://news7h.com/",
    # "https://www.eseller365.com/",
    # "https://www.pharmafocusasia.com/",
    # "https://www.indiainfoline.com/",
    # "https://bangalorebuzz.in/",
    # "https://asiaone.co.in/",
    # "https://www.theweek.in/",
    # "https://taxguru.in/",
    # "https://www.zeebiz.com/",
    # "https://news.abplive.com/",
    # "http://www.uniindia.com/",
    # "https://www.zeebiz.com/",
    # "https://www.financialexpress.com/",
    # "https://www.business-standard.com/",
    # "https://www.deccanherald.com/",
    # "https://www.moneycontrol.com/",
    # "https://www.businesstoday.in/", no feedf
    # "https://www.punekarnews.in/",
    # "https://www.pressreleasepost.co.uk/" not working link error
]



results = scrape_all_websites(urls)

