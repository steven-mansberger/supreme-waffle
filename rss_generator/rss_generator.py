import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from urllib.parse import urljoin, urlparse
import time
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
    def __init__(self, base_url, output_dir='rss_feeds', max_pages=50, delay=1.0, config_file=None, feed_title=None, feed_description=None):
        self.base_url = base_url.rstrip('/')
        self.domain = urlparse(base_url).netloc
        self.output_dir = os.path.join(BASE_DIR, output_dir)
        self.max_pages = max_pages
        self.delay = delay
        self.config = self.load_config(config_file)
        self.feed_title = feed_title
        self.feed_description = feed_description
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(LOGS_DIR, exist_ok=True)
        self.db_path = os.path.join(self.output_dir, 'articles.db')
        self.init_db()

    def load_config(self, config_file):
        """Load site-specific selectors from a JSON config file."""
        default_config = {
            'default': {
                'article_selector': 'a[href*="/blog/"], article, .post, .entry, .blog-post, .blog-card',
                'title_selector': 'h1, .article-title, .post-title, .blog-card__title, h2, h3',
                'date_selectors': ['time[datetime]', 'meta[property="article:published_time"]', '.date, .blog-card__date', '.published-date'],
                'desc_selectors': ['meta[name="description"]', 'meta[property="og:description"]', '.summary, .excerpt, .blog-card__description, p']
            },
            'www.datacamp.com': {
                'article_selector': 'article.blog-card, a[href*="/blog/"]',
                'title_selector': 'h1, .blog-card__title',
                'date_selectors': ['time[datetime]', '.blog-card__date'],
                'desc_selectors': ['meta[name="description"]', '.blog-card__description, p']
            },
            'www.forbes.com': {
                'article_selector': 'article, .stream-item, a[href*="/sites/"], .article-card, .fbs-card',
                'title_selector': 'h1, .article-title, meta[property="og:title"], .fs-headline',
                'date_selectors': ['time[datetime]', 'meta[property="article:published_time"]', '.date, .publish-date'],
                'desc_selectors': ['meta[name="description"]', 'meta[property="og:description"]', '.article-body p:first-child, .intro']
            }
        }
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        return default_config

    def init_db(self):
        """Initialize SQLite database for article caching."""
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

    def cache_article(self, article):
        """Cache article in SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO articles (url, title, description, pub_date)
                VALUES (?, ?, ?, ?)
            ''', (article['url'], article['title'], article['description'], article['pub_date']))
            conn.commit()

    def get_cached_articles(self):
        """Retrieve cached articles."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT title, url, description, pub_date FROM articles')
            articles = [{'title': row[0], 'url': row[1], 'description': row[2], 'pub_date': row[3]} for row in cursor.fetchall()]
            filtered = [a for a in articles if self.domain in a['url']]
            logger.info(f"Retrieved {len(filtered)} cached articles for domain {self.domain}")
            return filtered

    def detect_blog_type(self, soup):
        """Detect CMS type based on HTML structure."""
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
        """Clean text by removing extra whitespace."""
        return re.sub(r'\s+', ' ', text.strip()) if text else ''

    def parse_article_date(self, article_soup):
        """Extract publication date from article page."""
        selectors = self.config.get(self.domain, self.config['default'])['date_selectors']
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
        """Fetch and parse article page for metadata."""
        try:
            headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
                'Referer': self.base_url,
                'Accept-Language': 'en-US,en;q=0.5'
            })
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')

            config = self.config.get(self.domain, self.config['default'])
            title_elem = soup.select_one(config['title_selector']) or soup.find('h1') or soup.title
            title = self.clean_text(title_elem.text if title_elem else 'Untitled')

            desc_elems = config['desc_selectors']
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
        """Fallback to detect article containers if config fails."""
        headers = soup.find_all(['h1', 'h2', 'h3'], class_=['title', 'post-title', 'entry-title', 'blog-card__title', 'fs-headline'])
        articles = []
        for header in headers:
            parent = header.parent
            for _ in range(3):
                if parent.name in ['article', 'div', 'section']:
                    link = parent.find('a', href=True)
                    if link:
                        articles.append(link)
                    break
                parent = parent.parent
                if parent is None:
                    break
        return articles

    def scrape(self, update_only=False, cache_first=False):
        """Scrape articles, optionally using cache or updating only new ones."""
        if cache_first:
            articles = self.get_cached_articles()
            if articles:
                logger.info(f"Using {len(articles)} cached articles for {self.base_url}")
                return articles

        articles = self.get_cached_articles() if update_only else []
        seen_urls = {a['url'] for a in articles}
        new_articles = []
        page_num = 1
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        while page_num <= self.max_pages:
            url = self.base_url if page_num == 1 else f"{self.base_url}/page/{page_num}"
            pagination_patterns = [
                url,
                f"{self.base_url}?page={page_num}",
                f"{self.base_url}/page/{page_num}/",
                f"{self.base_url}?p={page_num}",
                f"{self.base_url}?start={page_num * 10}"  # Forbes-specific
            ]

            soup = None
            for pattern in pagination_patterns:
                try:
                    response = requests.get(pattern, headers=headers, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'lxml')
                        url = pattern
                        break
                except:
                    continue

            if not soup:
                logger.warning(f"No valid page found for page {page_num}. Stopping.")
                break

            logger.info(f"Scraping page {page_num}: {url}")
            blog_type = self.detect_blog_type(soup)
            logger.info(f"Detected blog type: {blog_type}")

            article_selector = self.config.get(self.domain, self.config['default'])['article_selector']
            article_links = soup.select(article_selector)
            if not article_links:
                article_links = self.auto_detect_articles(soup)
                logger.info("Using auto-detected article links.")

            if not article_links:
                logger.warning(f"No articles found on page {page_num}.")
                break

            for link in article_links:
                href = link.get('href')
                if not href:
                    continue
                full_url = urljoin(self.base_url, href)
                if full_url in seen_urls:
                    continue

                article = self.scrape_article_details(full_url, headers)
                if article:
                    new_articles.append(article)
                    seen_urls.add(full_url)
                    self.cache_article(article)
                    logger.info(f"Added article: {article['title']}")

                time.sleep(self.delay)

            next_page = soup.select_one('a.next, a[rel="next"], .pagination a[href*="/page/"], a.next.page-numbers, a.load-more')
            if not next_page or page_num >= self.max_pages:
                logger.info("No more pages to scrape.")
                break
            page_num += 1
            time.sleep(self.delay)

        articles.extend(new_articles)
        return articles

    def generate_rss(self, articles, feed_title=None, feed_description=None):
        """Generate RSS feed from articles."""
        fg = FeedGenerator()
        fg.title(feed_title or self.feed_title or f"{self.domain} Blog")
        fg.link(href=self.base_url, rel='alternate')
        fg.description(feed_description or self.feed_description or f"Custom RSS feed for {self.base_url}")
        fg.language='en'

        for article in articles:
            fe = fg.add_entry()
            fe.title(article['title'])
            fe.link(href=article['url'])
            fe.guid(article['url'], permalink=True)
            fe.description(article['description'] or 'No description available.')
            fe.pubDate(article['pub_date'])

        output_file = os.path.join(self.output_dir, f"{self.domain.replace('.', '-')}-rss.xml")
        fg.rss_file(output_file, pretty=True)
        logger.info(f"RSS feed saved to {output_file}")
        return output_file, fg

# Flask Endpoints
def check_auth(username, password):
    return username == FLASK_USERNAME and password == FLASK_PASSWORD

@app.route('/generate-feed')
def rss_generator():
    target_url = request.args.get('url')
    if not target_url:
        return "Please provide a URL parameter", 400
    try:
        scraper = BlogScraper(target_url, output_dir='rss_feeds')
        articles = scraper.scrape(cache_first=True)
        if not articles:
            return "No articles found", 404
        _, fg = scraper.generate_rss(articles)
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

    feeds.append({
        "url": data['url'],
        "title": data['title'],
        "description": data['description']
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
        domain = urlparse(feed['url']).netloc.replace('.', '-')
        xml_url = f"http://{BIND_ADDRESS}/rss/{domain}-rss.xml"
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
    parser.add_argument('--max-pages', type=int, default=50, help="Maximum pages to scrape")
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

        feeds = load_feeds()
        if not feeds:
            logger.error("No feeds to process. Exiting.")
            return

        for feed in feeds:
            scraper = BlogScraper(
                feed['url'],
                args.output_dir,
                args.max_pages,
                args.delay,
                args.config,
                feed_title=feed['title'],
                feed_description=feed['description']
            )
            articles = scraper.scrape(args.update_only, args.cache_first)
            if articles:
                output_file, _ = scraper.generate_rss(articles)
                logger.info(f"Generated feed with {len(articles)} articles: {output_file}")
            else:
                logger.warning(f"No articles found for {feed['url']}")

        os.chdir(os.path.join(BASE_DIR, args.output_dir))
        Handler = http.server.SimpleHTTPRequestHandler
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