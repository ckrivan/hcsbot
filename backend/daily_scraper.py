"""
Daily Web Article Scraper
Automatically scrapes new articles from hcsonline.com and adds to vector database
Runs daily at 2:00 AM
"""

import sys
import os
import time
from datetime import datetime
import schedule
import logging
from pathlib import Path

# Set up paths
sys.path.insert(0, '/var/www/hcsbot/backend')
os.chdir('/var/www/hcsbot')

from web_scraper import HCSWebScraper
from article_manifest import ArticleManifest
from pdf_processor import PDFProcessor
from vector_db import VectorDatabase

# Configure logging
LOG_DIR = Path('/var/www/hcsbot/logs')
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'daily_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DailyScraper:
    """Manages daily scraping of web articles"""

    def __init__(self):
        self.scraper = HCSWebScraper()
        self.manifest = ArticleManifest('/var/www/hcsbot/scraped_articles_manifest.json')
        self.processor = PDFProcessor()
        self.vector_db = None  # Lazy load to avoid issues

        # Stats
        self.last_run = None
        self.articles_scraped = 0
        self.chunks_added = 0

    def run_daily_scrape(self):
        """Execute daily scraping routine"""
        try:
            logger.info("="*60)
            logger.info("Starting daily web article scrape")
            logger.info("="*60)

            start_time = time.time()
            self.articles_scraped = 0
            self.chunks_added = 0

            # Initialize vector DB
            logger.info("Initializing vector database...")
            self.vector_db = VectorDatabase()
            current_docs = self.vector_db.collection.count()
            logger.info(f"Vector DB currently has {current_docs} documents")

            # Scrape blog articles
            logger.info("\n[1/4] Discovering blog articles...")
            self.scraper.REQUEST_DELAY = 1  # Be polite
            blog_urls = self.scraper.discover_articles("blog")
            logger.info(f"Found {len(blog_urls)} blog article URLs")

            # Scrape white papers
            logger.info("\n[2/4] Discovering white paper articles...")
            wp_urls = self.scraper.discover_articles("white-papers")
            logger.info(f"Found {len(wp_urls)} white paper URLs")

            all_urls = blog_urls + wp_urls
            logger.info(f"Total URLs to check: {len(all_urls)}")

            # Filter for new/updated articles only
            logger.info("\n[3/4] Checking for new or updated articles...")
            new_articles = []

            for url in all_urls:
                # Check if already in manifest
                if self.manifest.article_exists(url):
                    # Check if has chunks (already in DB)
                    existing = self.manifest.get_article(url)
                    if existing.get('chunk_ids'):
                        continue  # Already processed, skip

                    logger.info(f"Re-processing article without chunks: {url}")

                # Scrape the article
                article = self.scraper.extract_article(url)
                if article:
                    new_articles.append(article)
                    logger.info(f"  ✓ New: {article['title'][:60]}... ({article['published_date']})")

            if not new_articles:
                logger.info("No new articles found. Database is up to date!")
                self.last_run = datetime.now()
                elapsed = time.time() - start_time
                logger.info(f"Scrape completed in {elapsed:.1f} seconds")
                logger.info("="*60)
                return

            logger.info(f"Found {len(new_articles)} new articles to process")

            # Process into chunks
            logger.info("\n[4/4] Processing articles into vector database...")
            all_chunks = []

            for article in new_articles:
                # Add to manifest
                self.manifest.add_article(article, store_content=True)

                # Process into chunks
                chunks = self.processor.process_web_article(article)
                if chunks:
                    all_chunks.extend(chunks)
                    self.articles_scraped += 1
                    logger.info(f"  ✓ Processed: {article['title'][:50]}... ({len(chunks)} chunks)")

            # Add to vector database
            if all_chunks:
                logger.info(f"\nAdding {len(all_chunks)} chunks to vector database...")
                self.vector_db.add_documents(all_chunks)
                self.chunks_added = len(all_chunks)

                # Update manifest with chunk IDs
                for article in new_articles:
                    article_chunks = [c for c in all_chunks if c['metadata']['url'] == article['url']]
                    chunk_ids = [c['chunk_id'] for c in article_chunks]
                    self.manifest.add_article(article, chunk_ids=chunk_ids, store_content=True)

                new_total = self.vector_db.collection.count()
                logger.info(f"Vector DB now has {new_total} documents (was {current_docs})")

            # Summary
            elapsed = time.time() - start_time
            self.last_run = datetime.now()

            logger.info("\n" + "="*60)
            logger.info("Daily scrape completed successfully!")
            logger.info(f"  - Articles scraped: {self.articles_scraped}")
            logger.info(f"  - Chunks added: {self.chunks_added}")
            logger.info(f"  - Time elapsed: {elapsed:.1f} seconds")
            logger.info(f"  - Next run: Tomorrow at 2:00 AM")
            logger.info("="*60)

        except Exception as e:
            logger.error(f"Error during daily scrape: {e}")
            import traceback
            traceback.print_exc()
            logger.error("Daily scrape failed! Will retry tomorrow.")

    def get_stats(self):
        """Get scraper statistics"""
        return {
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'articles_scraped': self.articles_scraped,
            'chunks_added': self.chunks_added,
            'manifest_articles': len(self.manifest.get_all_articles())
        }


def main():
    """Main scheduler loop"""
    logger.info("Starting Daily Web Article Scraper Service")
    logger.info("Schedule: Every day at 2:00 AM")

    scraper = DailyScraper()

    # Schedule daily scraping at 2:00 AM
    schedule.every().day.at("02:00").do(scraper.run_daily_scrape)

    # Optional: Run immediately on startup (for testing)
    run_on_startup = os.getenv('SCRAPER_RUN_ON_STARTUP', 'false').lower() == 'true'
    if run_on_startup:
        logger.info("Running initial scrape on startup...")
        scraper.run_daily_scrape()

    logger.info("Scheduler started. Waiting for scheduled time...")

    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nScheduler stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Scheduler crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
