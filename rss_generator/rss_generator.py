import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from urllib.parse import urljoin, urlparse
import time
import random
from datetime import datetime
from dateutil.parser import parse as parse_date
import re
import os
import http.server
import socketserver
import argparse
import logging
import sqlite3
import json
from flask import Flask, request, Response, abort
import threading
import socket
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth

# Load environment variables from .env file
load_dotenv()

# Load sensitive data from environment variables
BIND_ADDRESS = os.getenv("BIND_ADDRESS", "0.0.0.0")
FLASK_USERNAME = os.getenv("FLASK_USERNAME", "admin")
FLASK_PASSWORD = os.getenv("FLASK_PASSWORD", "defaultpassword")

# Set up logging
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'rss_generator.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class BlogScraper:
    def __init__(self, base_url, config_key, output_dir='rss_feeds', max_pages=None, delay=1.0, config_file=None, feed_title=None, feed_description=None):
        self.base_url = base_url.rstrip('/')
        self.config_key = config_key
        self.domain = urlparse(base_url).netloc
        self.output_dir = os.path.join(BASE_DIR, output_dir)
        self.max_pages = max_pages
        self.delay = delay
        self.config = self.load_config(config_file)
        self.site_config = self.config.get(self.config_key, None)
        if not self.site_config:
            logger.error(f"No configuration found for {self.config_key} in config.json. Skipping.")
            raise ValueError(f"No configuration found for {self.config_key}")
        self.feed_title = feed_title or self.site_config.get('feed_title', f"{self.config_key} Feed")
        self.feed_description = feed_description or f"RSS feed for {self.base_url}"
        os.makedirs(self.output_dir, exist_ok=True)
        self.site_log_dir = os.path.join(LOGS_DIR, self.config_key.replace('/', '-').replace('.', '-'))
        os.makedirs(self.site_log_dir, exist_ok=True)
        self.db_path = os.path.join(self.output_dir, f"{self.config_key.replace('/', '-').replace('.', '-')}.db")
        self.init_db()

    def load_config(self, config_file):
        config_path = config_file or os.path.join(BASE_DIR, 'config.json')
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file {config_path} not found. Please create it with site configurations.")
            raise
        except Exception as e:
            logger.error(f"Error loading config file {config_path}: {e}")
            raise

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    url TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    pub_date TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
        logger.info(f"Initialized database at {self.db_path}")

    def cache_article(self, article):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO articles (url, title, description, pub_date)
                VALUES (?, ?, ?, ?)
            ''', (article['url'], article['title'], article['description'], article['pub_date']))
            conn.commit()

    def get_cached_articles(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT title, url, description, pub_date FROM articles WHERE scraped_at > datetime("now", "-7 days")')
            articles = [{'title': row[0], 'url': row[1], 'description': row[2], 'pub_date': row[3]} for row in cursor.fetchall()]
            filtered = [a for a in articles if self.domain in a['url']]
            logger.info(f"Retrieved {len(filtered)} cached articles for domain {self.domain} from {self.db_path}")
            return filtered

    def detect_blog_type(self, soup):
        try:
            if soup.find('meta', {'name': 'generator', 'content': lambda x: x and 'WordPress' in x}):
                return 'wordpress'
            elif soup.find('meta', {'name': 'blogger-template'}):
                return 'blogger'
            elif 'medium.com' in self.base_url or soup.find('meta', {'property': 'al:android:app_name', 'content': 'Medium'}):
                return 'medium'
            elif soup.find('meta', {'name': 'generator', 'content': lambda x: x and 'Ghost' in x}):
                return 'ghost'
            return 'generic'
        except Exception as e:
            logger.error(f"Error detecting blog type: {e}")
            return 'generic'

    def clean_text(self, text):
        return re.sub(r'\s+', ' ', text.strip()) if text else ''

    def parse_article_date(self, article_soup):
        selectors = self.site_config['date_selectors']
        try:
            for selector in selectors:
                date_elem = article_soup.select_one(selector)
                if date_elem:
                    date_str = date_elem.get('datetime') or date_elem.get('content') or date_elem.text
                    if date_str:
                        return parse_date(date_str, fuzzy=True).strftime('%a, %d %b %Y %H:%M:%S GMT')
            return datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        except Exception as e:
            logger.warning(f"Failed to parse date: {e}")
            return datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    def scrape_article_details(self, url, headers):
        try:
            logger.info(f"Fetching article {url} with requests")
            headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9'
            })
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')

            title_elem = soup.select_one(self.site_config['title_selector']) or soup.find('h1') or soup.title
            logger.debug(f"Title element found: {title_elem}")  # Debug log
            if not title_elem:
                html_path = os.path.join(self.site_log_dir, f"{self.domain}_{url.split('/')[-1]}_debug.html")
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                logger.warning(f"No title found for {url}. Saved debug HTML to {html_path}")
            title = self.clean_text(title_elem.text if title_elem else 'Untitled')

            desc_elems = self.site_config['desc_selectors']
            description = ''
            for selector in desc_elems:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    description = self.clean_text(desc_elem.get('content') or desc_elem.text)
                    if len(description) > 20:
                        break

            pub_date = self.parse_article_date(soup)

            return {
                'title': title,
                'url': url,
                'description': description[:500],
                'pub_date': pub_date
            }
        except Exception as e:
            logger.error(f"Failed to scrape article {url}: {e}")
            return None

    def auto_detect_articles(self, soup):
        article_links = soup.find_all('a', href=True)
        articles = []
        include_patterns = [re.compile(p) for p in self.site_config['url_filters'].get('include_patterns', [])]
        exclude_patterns = [re.compile(p) for p in self.site_config['url_filters'].get('exclude_patterns', [])]

        logger.info(f"Auto-detecting articles: found {len(article_links)} links")
        for link in article_links:
            href = link.get('href', '')
            matches_include = not include_patterns or any(p.search(href) for p in include_patterns)
            matches_exclude = any(p.search(href) for p in exclude_patterns)
            full_url = urljoin(self.base_url, href)
            if matches_include and not matches_exclude:
                logger.debug(f"Included article link: {full_url}")
                if full_url not in articles:
                    articles.append(link)
            else:
                logger.debug(f"Excluded link: {full_url} (include={matches_include}, exclude={matches_exclude})")
        logger.info(f"Auto-detected {len(articles)} article links")
        return articles

    def scrape(self, update_only=False, cache_first=False):
        if cache_first:
            articles = self.get_cached_articles()
            if articles:
                logger.info(f"Using {len(articles)} cached articles for {self.base_url}")
                return articles

        # Default to using cached articles unless update_only is False
        articles = self.get_cached_articles() if not update_only else []
        seen_urls = {a['url'] for a in articles}
        new_articles = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://www.google.com/',
            'Accept-Language': 'en-US,en;q=0.9'
        }

        if self.site_config.get('use_selenium', False):
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f'user-agent={headers["User-Agent"]}')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            driver = webdriver.Chrome(options=options)
            stealth(driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
            )

            try:
                logger.info(f"Fetching {self.base_url} with Selenium")
                driver.get(self.base_url)

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(1, 3))

                cookie_button_xpath = self.site_config.get('selenium_cookie_button')
                if cookie_button_xpath:
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, cookie_button_xpath))
                        ).click()
                        logger.info("Accepted cookies")
                    except Exception as e:
                        logger.debug(f"No cookie button found or error: {e}")

                max_loads = self.site_config.get('selenium_max_loads', float('inf'))
                load_count = 0
                while load_count < max_loads:
                    try:
                        load_more = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='variants'] | //button[contains(text(), 'More Articles')]"))
                        )
                        load_more.click()
                        time.sleep(random.uniform(1, 3))
                        load_count += 1
                        logger.info("Clicked 'Load More'")
                    except Exception:
                        logger.info("No more 'Load More' buttons found")
                        break

                soup = BeautifulSoup(driver.page_source, 'lxml')
                html_path = os.path.join(self.site_log_dir, f"{self.domain}_full.html")
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                logger.info(f"Saved full page source to {html_path}")

                if "Access denied (403)" in driver.page_source:
                    logger.error("Access denied (403) by Forbes. Bot detection triggered. Falling back to requests.")
                    driver.quit()
                    try:
                        logger.info(f"Fetching {self.base_url} with requests as fallback")
                        response = requests.get(self.base_url, headers=headers, timeout=10)
                        response.raise_for_status()
                        soup = BeautifulSoup(response.text, 'lxml')
                        html_path = os.path.join(self.site_log_dir, f"{self.domain}_fallback.html")
                        with open(html_path, 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        logger.info(f"Saved fallback page source to {html_path}")
                    except Exception as e:
                        logger.error(f"Fallback requests failed: {e}")
                        return articles
                else:
                    section_selector = self.site_config.get('section_selector')
                    if section_selector:
                        section = soup.select_one(section_selector)
                        if section:
                            article_links = section.select(self.site_config['article_selector'])
                        else:
                            logger.warning(f"Section {section_selector} not found")
                            article_links = soup.select(self.site_config['article_selector'])
                    else:
                        article_links = soup.select(self.site_config['article_selector'])

                    if not article_links:
                        article_links = self.auto_detect_articles(soup)
                        logger.info("Using auto-detected article links")

                    exclude_patterns = [re.compile(p) for p in self.site_config['url_filters'].get('exclude_patterns', [])]
                    for link in article_links:
                        href = link.get('href')
                        if not href:
                            continue
                        full_url = urljoin(self.base_url, href)
                        if any(p.search(full_url) for p in exclude_patterns):
                            continue
                        if full_url in seen_urls:
                            cached_article = next((a for a in articles if a['url'] == full_url), None)
                            if cached_article and (not cached_article.get('title') or cached_article.get('title') == 'Untitled'):
                                logger.info(f"Re-scraping {full_url} due to missing title")
                                article = self.scrape_article_details(full_url, headers)
                                if article:
                                    new_articles.append(article)
                                    self.cache_article(article)
                                    logger.info(f"Updated article: {article['title']}")
                            continue
                        article = self.scrape_article_details(full_url, headers)
                        if article:
                            new_articles.append(article)
                            seen_urls.add(full_url)
                            self.cache_article(article)
                            logger.info(f"Added article: {article['title']}")
                        time.sleep(self.delay)

            finally:
                if 'driver' in locals():
                    driver.quit()
        else:
            # Existing requests-based scraping logic
            page_num = 1
            while True:
                pagination_pattern = self.site_config.get('pagination_pattern', 'page/{page_num}')
                url = self.base_url if page_num == 1 else self.base_url + pagination_pattern.format(page_num=page_num)

                pagination_patterns = [
                    url,
                    f"{self.base_url}?page={page_num}",
                    f"{self.base_url}/page/{page_num}/",
                    f"{self.base_url}/page/{page_num}",
                    f"{self.base_url}?p={page_num}",
                ]

                soup = None
                for pattern in pagination_patterns:
                    try:
                        logger.info(f"Fetching {pattern} with requests")
                        response = requests.get(pattern, headers=headers, timeout=10, allow_redirects=True)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'lxml')
                            url = pattern
                            html_path = os.path.join(self.site_log_dir, f"{self.domain}_page_{page_num}.html")
                            with open(html_path, 'w', encoding='utf-8') as f:
                                f.write(response.text)
                            logger.info(f"Saved {self.domain} page source to {html_path}")
                            break
                        else:
                            logger.warning(f"Failed to fetch {pattern}: Status code {response.status_code}")
                    except Exception as e:
                        logger.error(f"Error fetching {pattern}: {e}")
                        continue

                if not soup:
                    logger.warning(f"No valid page found for page {page_num}. Stopping.")
                    break

                logger.info(f"Scraping page {page_num}: {url}")
                blog_type = self.detect_blog_type(soup)
                logger.info(f"Detected blog type: {blog_type}")

                article_selector = self.site_config['article_selector']
                article_links = soup.select(article_selector)
                if not article_links:
                    article_links = self.auto_detect_articles(soup)
                    logger.info("Using auto-detected article links.")

                if not article_links:
                    logger.warning(f"No articles found on page {page_num}.")

                exclude_patterns = [re.compile(p) for p in self.site_config['url_filters'].get('exclude_patterns', [])]
                for link in article_links:
                    href = link.get('href')
                    if not href:
                        continue
                    full_url = urljoin(self.base_url, href)
                    if any(p.search(full_url) for p in exclude_patterns):
                        logger.info(f"Skipping unwanted link: {full_url}")
                        continue
                    if full_url in seen_urls:
                        continue

                    article = self.scrape_article_details(full_url, headers)
                    if article:
                        new_articles.append(article)
                        seen_urls.add(full_url)
                        self.cache_article(article)
                        logger.info(f"Added article: {article['title']}")

                    time.sleep(self.delay)

                next_page = soup.select_one(self.site_config['next_page_selector'])
                logger.info(f"Next page element: {next_page}")

                if not next_page or (self.max_pages and page_num >= self.max_pages):
                    logger.info("No more pages to scrape.")
                    break
                page_num += 1
                time.sleep(self.delay)

        articles.extend(new_articles)
        logger.info(f"Total articles scraped: {len(articles)}")
        return articles

    def generate_rss(self):
        fg = FeedGenerator()
        fg.title(self.feed_title)
        fg.link(href=self.base_url, rel='alternate')
        fg.description(self.feed_description)
        fg.language='en'

        articles = self.get_cached_articles()
        # Sort articles by publication date (oldest first)
        articles.sort(key=lambda x: parse_date(x['pub_date']), reverse=False)

        for article in articles:
            fe = fg.add_entry()
            fe.title(article['title'])
            fe.link(href=article['url'])
            fe.guid(article['url'], permalink=True)
            fe.description(article['description'] or 'No description available.')
            fe.pubDate(article['pub_date'])

        output_file = os.path.join(self.output_dir, f"{self.config_key.replace('/', '-').replace('.', '-')}-rss.xml")
        fg.rss_file(output_file, pretty=True)
        logger.info(f"Generated feed with {len(articles)} articles: {output_file}")
        return output_file, fg

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.generate_index_page().encode('utf-8'))
        else:
            super().do_GET()

    def generate_index_page(self):
        feeds = load_feeds()
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>RSS Feeds</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                ul { list-style-type: none; padding: 0; }
                li { margin: 10px 0; }
                a { color: #007bff; text-decoration: none; }
                a:hover { text-decoration: underline; }
                p { color: #666; }
            </style>
        </head>
        <body>
            <h1>Available RSS Feeds</h1>
            <ul>
        """
        for feed in feeds:
            config_key = feed['config_key']
            feed_url = f"/rss/{config_key.replace('/', '-').replace('.', '-')}-rss.xml"
            html += f"""
                <li>
                    <a href="{feed_url}">{feed['title']}</a>
                    <p>{feed['description']}</p>
                </li>
            """
        html += """
            </ul>
        </body>
        </html>
        """
        return html

def check_auth(username, password):
    return username == FLASK_USERNAME and password == FLASK_PASSWORD

@app.route('/generate-feed')
def rss_generator():
    target_url = request.args.get('url')
    if not target_url:
        return "Please provide a URL parameter", 400
    try:
        config_key = target_url.replace('https://', '').replace('http://', '').rstrip('/')
        scraper = BlogScraper(target_url, config_key, output_dir='rss_feeds')
        articles = scraper.scrape(cache_first=True)
        if not articles:
            return "No articles found", 404
        _, fg = scraper.generate_rss()
        return Response(fg.rss_str(pretty=True), mimetype='application/rss+xml')
    except Exception as e:
        return f"Error generating feed: {str(e)}", 500

@app.route('/add-feed', methods=['POST'])
def add_feed():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        abort(401)
    data = request.get_json()
    if not data or 'url' not in data or 'title' not in data or 'description' not in data:
        return "Missing required fields: url, title, description", 400

    feed_config_path = os.path.join(BASE_DIR, 'feeds.json')
    try:
        with open(feed_config_path, 'r') as f:
            feeds = json.load(f)
    except FileNotFoundError:
        feeds = []

    if any(feed['url'] == data['url'] for feed in feeds):
        return "Feed already exists", 400

    config_key = data['url'].replace('https://', '').replace('http://', '').rstrip('/')
    feeds.append({
        "url": data['url'],
        "title": data['title'],
        "description": data['description'],
        "config_key": config_key,
        "enabled": True
    })

    with open(feed_config_path, 'w') as f:
        json.dump(feeds, f, indent=4)

    return "Feed added successfully", 200

@app.route('/remove-feed', methods=['POST'])
def remove_feed():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        abort(401)
    data = request.get_json()
    if not data or 'url' not in data:
        return "Missing required field: url", 400

    feed_config_path = os.path.join(BASE_DIR, 'feeds.json')
    try:
        with open(feed_config_path, 'r') as f:
            feeds = json.load(f)
    except FileNotFoundError:
        return "No feeds configured", 404

    feeds = [feed for feed in feeds if feed['url'] != data['url']]
    with open(feed_config_path, 'w') as f:
        json.dump(feeds, f, indent=4)

    return "Feed removed successfully", 200

@app.route('/generate-opml')
def generate_opml():
    feed_config_path = os.path.join(BASE_DIR, 'feeds.json')
    try:
        with open(feed_config_path, 'r') as f:
            feeds = json.load(f)
    except FileNotFoundError:
        return "No feeds configured", 404

    opml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    opml += '<opml version="1.0">\n'
    opml += '  <head>\n'
    opml += '    <title>RSS Feeds</title>\n'
    opml += '  </head>\n'
    opml += '  <body>\n'

    for feed in feeds:
        if not feed.get('enabled', True):
            continue
        config_key = feed['config_key']
        xml_url = f"http://{BIND_ADDRESS}/rss/{config_key.replace('/', '-').replace('.', '-')}-rss.xml"
        opml += f'    <outline text="{feed["title"]}" type="rss" xmlUrl="{xml_url}" htmlUrl="{feed["url"]}" description="{feed["description"]}"/>\n'

    opml += '  </body>\n'
    opml += '</opml>\n'

    return Response(opml, mimetype='application/xml')

def run_flask(bind_address='0.0.0.0'):
    app.run(host=bind_address, port=5001, debug=False)

def load_feeds():
    feed_config_path = os.path.join(BASE_DIR, 'feeds.json')
    try:
        with open(feed_config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("feeds.json not found. Please create it with a list of feeds.")
        return []

def main():
    parser = argparse.ArgumentParser(description="Generate and serve RSS feeds from blogs.")
    parser.add_argument('--output-dir', default='rss_feeds', help="Directory to save RSS files")
    parser.add_argument('--http-port', type=int, default=8080, help="Port for HTTP server")
    parser.add_argument('--max-pages', type=int, help="Maximum pages to scrape (optional, overridden by feeds.json)")
    parser.add_argument('--delay', type=float, default=1.0, help="Delay between requests (seconds)")
    parser.add_argument('--config', help="Path to JSON config file")
    parser.add_argument('--update-only', action='store_true', help="Only scrape new articles")
    parser.add_argument('--cache-first', action='store_true', help="Use cached articles if available")
    parser.add_argument('--no-flask', action='store_true', help="Disable Flask web interface")
    parser.add_argument('--bind-address', default=BIND_ADDRESS, help="IP address to bind servers")
    args = parser.parse_args()

    try:
        if not args.no_flask:
            flask_thread = threading.Thread(target=run_flask, args=(args.bind_address,), daemon=True)
            flask_thread.start()
            logger.info(f"Flask server running at http://{args.bind_address}:5001")
            time.sleep(3)

        feeds = [feed for feed in load_feeds() if feed.get('enabled', True)]
        if not feeds:
            logger.error("No enabled feeds to process. Exiting.")
            return

        # Load config to check which sites are allowed
        config_path = args.config or os.path.join(BASE_DIR, 'config.json')
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file {config_path} not found. Exiting.")
            return

        allowed_config_keys = set(config.keys()) - {'default'}

        for feed in feeds:
            config_key = feed.get('config_key')
            if config_key not in allowed_config_keys:
                logger.info(f"Skipping {feed['url']} as its config_key '{config_key}' is not defined in config.json.")
                continue

            try:
                max_pages = feed.get('max_pages', args.max_pages)
                scraper = BlogScraper(
                    feed['url'],
                    config_key,
                    args.output_dir,
                    max_pages,
                    args.delay,
                    args.config,
                    feed_title=feed['title'],
                    feed_description=feed['description']
                )
                articles = scraper.scrape(args.update_only, args.cache_first)
                if articles:
                    output_file, _ = scraper.generate_rss()
                    logger.info(f"Generated feed with {len(articles)} articles: {output_file}")
                else:
                    logger.warning(f"No articles found for {feed['url']}")
            except ValueError as e:
                logger.error(f"Failed to initialize scraper for {feed['url']}: {e}")
                continue

        os.chdir(os.path.join(BASE_DIR, args.output_dir))
        Handler = CustomHTTPRequestHandler
        for port in [args.http_port, 8080, 8081]:
            try:
                with socketserver.TCPServer((args.bind_address, port), Handler) as httpd:
                    httpd.allow_reuse_address = True
                    httpd.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    logger.info(f"Serving RSS feeds at http://{args.bind_address}:{port}")
                    httpd.serve_forever()
                break
            except OSError as e:
                logger.warning(f"Port {port} failed: {e}")
                if port == 8081:
                    raise Exception("All ports failed")

    except KeyboardInterrupt:
        logger.info("Stopped by user.")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()
