"""
Add web articles to the MAIN vector database
Run from /var/www/hcsbot directory
"""

from backend.web_scraper import HCSWebScraper
from backend.article_manifest import ArticleManifest
from backend.pdf_processor import PDFProcessor
from backend.vector_db import VectorDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_web_articles():
    """Add recent web articles to main vector database"""

    print("\n" + "="*60)
    print("Adding Web Articles to Main Vector Database")
    print("="*60)

    # Initialize (will use /var/www/hcsbot/chroma_db)
    scraper = HCSWebScraper()
    manifest = ArticleManifest("./scraped_articles_manifest.json")
    processor = PDFProcessor()
    vector_db = VectorDatabase()  # Uses ./chroma_db

    print(f"\nCurrent vector DB has: {vector_db.collection.count()} documents")

    # Get just first page of recent articles
    print("\n[1/4] Discovering recent blog articles...")
    scraper.REQUEST_DELAY = 0.5  # Speed up
    blog_urls = scraper.discover_articles("blog")[:5]  # Just 5 for testing

    print(f"Will scrape {len(blog_urls)} articles")

    # Scrape them
    print("\n[2/4] Scraping articles...")
    articles = []
    for url in blog_urls:
        article = scraper.extract_article(url)
        if article:
            articles.append(article)
            manifest.add_article(article, store_content=True)
            print(f"  ✓ {article['title'][:60]}... ({article['published_date']})")

    if not articles:
        print("No articles scraped!")
        return

    # Process into chunks
    print(f"\n[3/4] Processing {len(articles)} articles into chunks...")
    all_chunks = []
    for article in articles:
        chunks = processor.process_web_article(article)
        all_chunks.extend(chunks)
        print(f"  ✓ {len(chunks)} chunks from: {article['title'][:50]}...")

    # Add to the MAIN vector DB
    print(f"\n[4/4] Adding {len(all_chunks)} chunks to MAIN vector database...")
    vector_db.add_documents(all_chunks)

    print(f"\n✅ Success! Vector DB now has: {vector_db.collection.count()} documents")
    print(f"   ({len(all_chunks)} chunks added from {len(articles)} web articles)")
    print("\n" + "="*60)

if __name__ == "__main__":
    add_web_articles()
