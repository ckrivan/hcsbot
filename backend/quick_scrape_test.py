"""
Quick test to scrape just a few recent articles and add to database
"""

import sys
sys.path.insert(0, '/var/www/hcsbot/backend')

from web_scraper import HCSWebScraper
from article_manifest import ArticleManifest
from pdf_processor import PDFProcessor
from vector_db import VectorDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def quick_test():
    """Scrape just 3-5 recent articles and add to DB"""

    print("\n" + "="*60)
    print("Quick Scrape Test - Adding Recent Articles to Vector DB")
    print("="*60)

    # Initialize
    scraper = HCSWebScraper()
    manifest = ArticleManifest()
    processor = PDFProcessor()

    # Get just first page of blog articles
    print("\n[1/4] Discovering recent blog articles...")
    scraper.REQUEST_DELAY = 0.5  # Speed up for test
    blog_urls = scraper.discover_articles("blog")

    # Take just first 5
    test_urls = blog_urls[:5]
    print(f"Testing with {len(test_urls)} articles")

    # Scrape them
    print("\n[2/4] Scraping articles...")
    articles = []
    for url in test_urls:
        article = scraper.extract_article(url)
        if article:
            articles.append(article)
            print(f"  ✓ {article['title']} ({article['published_date']})")

    if not articles:
        print("No articles scraped!")
        return

    # Add to manifest
    print(f"\n[3/4] Adding {len(articles)} articles to manifest...")
    for article in articles:
        manifest.add_article(article, store_content=True)

    # Process and add to vector DB
    print("\n[4/4] Processing articles and adding to vector database...")
    vector_db = VectorDatabase()

    all_chunks = []
    for article in articles:
        chunks = processor.process_web_article(article)
        all_chunks.extend(chunks)
        print(f"  ✓ Processed: {article['title']} ({len(chunks)} chunks)")

    # Add to vector DB
    vector_db.add_documents(all_chunks)
    print(f"\n✅ Successfully added {len(all_chunks)} chunks from {len(articles)} articles to vector database!")

    # Show stats
    stats = vector_db.get_stats()
    print(f"\nVector DB now contains: {stats['total_documents']} total documents")

    print("\n" + "="*60)

if __name__ == "__main__":
    quick_test()
