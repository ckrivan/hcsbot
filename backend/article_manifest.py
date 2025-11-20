"""
Article Manifest Manager
Tracks scraped web articles to avoid re-scraping and manage content lifecycle
"""

import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ArticleManifest:
    """Manages manifest of scraped articles"""

    def __init__(self, manifest_path: str = "./scraped_articles_manifest.json"):
        self.manifest_path = Path(manifest_path)
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> Dict[str, Any]:
        """Load manifest from disk or create new one"""
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    logger.info(f"Loaded manifest with {len(manifest.get('articles', []))} articles")
                    return manifest
            except Exception as e:
                logger.error(f"Error loading manifest: {e}")
                return self._create_empty_manifest()
        else:
            logger.info("Creating new manifest")
            return self._create_empty_manifest()

    def _create_empty_manifest(self) -> Dict[str, Any]:
        """Create empty manifest structure"""
        return {
            'created_date': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'total_articles': 0,
            'articles': {}
        }

    def _save_manifest(self):
        """Save manifest to disk"""
        try:
            self.manifest['last_updated'] = datetime.now().isoformat()
            self.manifest['total_articles'] = len(self.manifest['articles'])

            with open(self.manifest_path, 'w', encoding='utf-8') as f:
                json.dump(self.manifest, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved manifest with {self.manifest['total_articles']} articles")
        except Exception as e:
            logger.error(f"Error saving manifest: {e}")

    def _compute_content_hash(self, content: str) -> str:
        """Compute SHA256 hash of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

    def article_exists(self, url: str) -> bool:
        """Check if article URL is in manifest"""
        return url in self.manifest['articles']

    def get_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Get article entry from manifest"""
        return self.manifest['articles'].get(url)

    def needs_update(self, url: str, content: str) -> bool:
        """
        Check if article needs to be re-scraped
        Returns True if content has changed
        """
        if not self.article_exists(url):
            return True

        existing = self.get_article(url)
        current_hash = self._compute_content_hash(content)

        return existing.get('content_hash') != current_hash

    def add_article(self, article_data: Dict[str, Any], chunk_ids: List[str] = None, store_content: bool = True):
        """
        Add or update article in manifest

        Args:
            article_data: Dict with keys: url, title, content, published_date, section
            chunk_ids: List of ChromaDB chunk IDs for this article
            store_content: Whether to store full content in manifest (default: True)
        """
        url = article_data['url']
        content = article_data.get('content', '')
        content_hash = self._compute_content_hash(content)

        entry = {
            'url': url,
            'title': article_data['title'],
            'published_date': article_data.get('published_date'),
            'section': article_data.get('section', 'blog'),
            'content_hash': content_hash,
            'content_length': len(content),
            'scraped_date': article_data.get('scraped_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            'last_updated': datetime.now().isoformat(),
            'chunk_ids': chunk_ids or []
        }

        # Store content if requested (for processing into vector DB)
        if store_content and content:
            entry['content'] = content

        self.manifest['articles'][url] = entry
        self._save_manifest()

        logger.info(f"Added article to manifest: {article_data['title']}")

    def remove_article(self, url: str):
        """Remove article from manifest"""
        if url in self.manifest['articles']:
            del self.manifest['articles'][url]
            self._save_manifest()
            logger.info(f"Removed article from manifest: {url}")

    def get_all_articles(self) -> List[Dict[str, Any]]:
        """Get all articles in manifest"""
        return list(self.manifest['articles'].values())

    def get_articles_by_section(self, section: str) -> List[Dict[str, Any]]:
        """Get articles filtered by section (blog or white-paper)"""
        return [
            article for article in self.manifest['articles'].values()
            if article.get('section') == section
        ]

    def get_articles_by_date_range(self, start_date: str, end_date: str = None) -> List[Dict[str, Any]]:
        """
        Get articles within date range

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (defaults to today)
        """
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        filtered = []
        for article in self.manifest['articles'].values():
            pub_date = article.get('published_date')
            if pub_date and start_date <= pub_date <= end_date:
                filtered.append(article)

        return filtered

    def get_chunk_ids(self, url: str) -> List[str]:
        """Get chunk IDs associated with article"""
        article = self.get_article(url)
        return article.get('chunk_ids', []) if article else []

    def get_stats(self) -> Dict[str, Any]:
        """Get manifest statistics"""
        articles = self.get_all_articles()

        blog_count = len(self.get_articles_by_section('blog'))
        white_paper_count = len(self.get_articles_by_section('white-paper'))

        # Count by year
        year_counts = {}
        for article in articles:
            pub_date = article.get('published_date')
            if pub_date:
                year = pub_date[:4]
                year_counts[year] = year_counts.get(year, 0) + 1

        return {
            'total_articles': len(articles),
            'blog_articles': blog_count,
            'white_paper_articles': white_paper_count,
            'by_year': year_counts,
            'last_updated': self.manifest.get('last_updated'),
            'manifest_path': str(self.manifest_path)
        }

    def export_urls(self) -> List[str]:
        """Export list of all article URLs"""
        return list(self.manifest['articles'].keys())

    def clear(self):
        """Clear all articles from manifest"""
        self.manifest = self._create_empty_manifest()
        self._save_manifest()
        logger.info("Cleared manifest")


# Example usage
if __name__ == "__main__":
    manifest = ArticleManifest()

    # Test article
    test_article = {
        'url': 'https://hcsonline.com/test',
        'title': 'Test Article',
        'content': 'This is test content',
        'published_date': '2025-01-01',
        'section': 'blog'
    }

    # Add article
    manifest.add_article(test_article, chunk_ids=['test_chunk_1', 'test_chunk_2'])

    # Check if exists
    print(f"Article exists: {manifest.article_exists(test_article['url'])}")

    # Get stats
    stats = manifest.get_stats()
    print(f"\nManifest stats: {json.dumps(stats, indent=2)}")

    # Cleanup test
    manifest.remove_article(test_article['url'])
