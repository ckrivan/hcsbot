"""
Test script for web scraping pipeline
Tests scraping → processing → chunking → manifest tracking
"""

import sys
from web_scraper import HCSWebScraper
from article_manifest import ArticleManifest
from pdf_processor import PDFProcessor
from content_converter import ContentConverter

def test_full_pipeline():
    """Test the complete web scraping pipeline"""
    print("="*60)
    print("Testing Web Scraping Pipeline")
    print("="*60)

    # Initialize components
    print("\n[1/5] Initializing components...")
    scraper = HCSWebScraper()
    manifest = ArticleManifest()
    processor = PDFProcessor()
    converter = ContentConverter()
    print("✓ Components initialized")

    # Test single article scraping
    print("\n[2/5] Testing single article extraction...")
    test_url = "https://hcsonline.com/support/resources/blog/how-to-convince-microsoft-office-apps-to-save-files-on-your-mac"

    article = scraper.extract_article(test_url)
    if not article:
        print("✗ Failed to extract article")
        return False

    print(f"✓ Extracted article:")
    print(f"  - Title: {article['title']}")
    print(f"  - Date: {article['published_date']}")
    print(f"  - Section: {article['section']}")
    print(f"  - Content length: {len(article['content'])} chars")

    # Test content conversion
    print("\n[3/5] Testing content conversion...")
    rag_content = converter.prepare_for_rag(article)
    print(f"✓ Converted to RAG format ({len(rag_content)} chars)")
    print(f"\nFirst 300 chars:\n{rag_content[:300]}...")

    # Test chunking
    print("\n[4/5] Testing article chunking...")
    chunks = processor.process_web_article(article)
    if not chunks:
        print("✗ Failed to create chunks")
        return False

    print(f"✓ Created {len(chunks)} chunks")
    print(f"\nFirst chunk:")
    print(f"  - ID: {chunks[0]['chunk_id']}")
    print(f"  - Text length: {len(chunks[0]['text'])} chars")
    print(f"  - Metadata: {chunks[0]['metadata']}")
    print(f"\nFirst 200 chars of chunk:\n{chunks[0]['text'][:200]}...")

    # Test manifest tracking
    print("\n[5/5] Testing manifest tracking...")
    chunk_ids = [chunk['chunk_id'] for chunk in chunks]
    manifest.add_article(article, chunk_ids=chunk_ids)

    if manifest.article_exists(test_url):
        print("✓ Article added to manifest")

        # Test retrieval
        stored = manifest.get_article(test_url)
        print(f"  - Stored {len(stored['chunk_ids'])} chunk IDs")
        print(f"  - Content hash: {stored['content_hash']}")
    else:
        print("✗ Failed to add article to manifest")
        return False

    # Get stats
    print("\n" + "="*60)
    print("Manifest Statistics")
    print("="*60)
    stats = manifest.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

    # Cleanup test data
    print("\n[Cleanup] Removing test article from manifest...")
    manifest.remove_article(test_url)
    print("✓ Cleanup complete")

    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED")
    print("="*60)
    return True

def test_blog_discovery():
    """Test discovering articles from blog section"""
    print("\n" + "="*60)
    print("Testing Blog Discovery (First 5 Articles)")
    print("="*60)

    scraper = HCSWebScraper()

    # Discover blog articles
    print("\nDiscovering blog articles...")
    blog_urls = scraper.discover_articles("blog")

    print(f"\n✓ Discovered {len(blog_urls)} blog articles")
    print(f"\nFirst 5 articles:")
    for i, url in enumerate(blog_urls[:5], 1):
        print(f"{i}. {url}")

    return True

if __name__ == "__main__":
    print("\n🤖 HCSBot Web Scraping Test Suite\n")

    # Run tests
    try:
        test_full_pipeline()
        print("\n")
        test_blog_discovery()

        print("\n✅ Test suite completed successfully!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
