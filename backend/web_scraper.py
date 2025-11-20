"""
Web Scraper for HCS Online Articles
Automatically discovers and extracts content from hcsonline.com
Filters for 2024+ articles only
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import time
import re
import pdfplumber
from io import BytesIO

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HCSWebScraper:
    """Scraper for HCS Technology Group website articles"""

    BASE_URL = "https://hcsonline.com"
    BLOG_PATH = "/support/resources/blog"
    WHITE_PAPERS_PATH = "/support/resources/white-papers"

    # Only include articles from 2024 and newer
    CUTOFF_YEAR = 2024

    # Be polite - delay between requests
    REQUEST_DELAY = 2  # seconds

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HCSBot/1.0 (Article Indexer; +https://hcsbot.hcsonline.com)'
        })

    def _make_request(self, url: str) -> Optional[BeautifulSoup]:
        """Make HTTP request with error handling and rate limiting"""
        try:
            time.sleep(self.REQUEST_DELAY)  # Polite scraping
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        try:
            # Handle formats like "Sunday, February 9, 2025" or "February 9, 2025"
            date_str = date_str.strip()

            # Remove day of week if present
            if ',' in date_str:
                parts = date_str.split(',', 1)
                if len(parts) > 1:
                    date_str = parts[1].strip()

            # Try different date formats
            for fmt in ['%B %d, %Y', '%b %d, %Y', '%Y-%m-%d']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue

            logger.warning(f"Could not parse date: {date_str}")
            return None
        except Exception as e:
            logger.error(f"Date parsing error: {e}")
            return None

    def _should_include_article(self, pub_date: Optional[datetime]) -> bool:
        """Check if article meets date filter criteria"""
        if not pub_date:
            return False  # Skip if no date

        return pub_date.year >= self.CUTOFF_YEAR

    def _extract_pdf_article(self, page_url: str, pdf_url: str, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """
        Extract content from a PDF-only white paper page

        Args:
            page_url: URL of the HTML page
            pdf_url: URL of the PDF file
            soup: BeautifulSoup object of the HTML page

        Returns:
            Article data dict or None
        """
        try:
            # Extract title from HTML page
            title_tag = soup.find('h1') or soup.find('title')
            title = title_tag.get_text().strip() if title_tag else "Untitled"

            # Extract publication date from HTML page
            pub_date = None
            date_patterns = [
                soup.find(string=re.compile(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}')),
                soup.find('time'),
                soup.find(class_=re.compile('date|published|time', re.I))
            ]

            for pattern in date_patterns:
                if pattern:
                    if hasattr(pattern, 'get_text'):
                        pub_date_str = pattern.get_text().strip()
                    else:
                        pub_date_str = str(pattern).strip()

                    pub_date = self._parse_date(pub_date_str)
                    if pub_date:
                        break

            # Check date filter
            if not self._should_include_article(pub_date):
                logger.info(f"Skipping PDF (date filter): {title}")
                return None

            # Download PDF
            logger.info(f"Downloading PDF: {pdf_url}")
            time.sleep(self.REQUEST_DELAY)

            response = requests.get(pdf_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
            response.raise_for_status()

            # Extract text from PDF
            pdf_content = []
            with pdfplumber.open(BytesIO(response.content)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        pdf_content.append(text)

            content = '\n\n'.join(pdf_content)

            # Determine section
            section = "blog" if "/blog/" in page_url else "white-paper"

            article_data = {
                'url': page_url,
                'title': title,
                'content': content,
                'published_date': pub_date.strftime('%Y-%m-%d') if pub_date else None,
                'section': section,
                'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'pdf_url': pdf_url
            }

            logger.info(f"Extracted PDF article: {title} ({len(content)} chars)")
            return article_data

        except Exception as e:
            logger.error(f"Error extracting PDF article: {e}")
            return None

    def _extract_article_links_from_page(self, soup: BeautifulSoup, base_path: str) -> List[str]:
        """Extract article URLs from listing page"""
        article_urls = []

        # Find all links that match the article pattern
        for link in soup.find_all('a', href=True):
            href = link['href']
            if base_path in href and href != base_path:
                full_url = href if href.startswith('http') else self.BASE_URL + href

                # Filter out pagination URLs and query parameters
                if '?' not in full_url and '#' not in full_url:
                    if full_url not in article_urls:
                        article_urls.append(full_url)

        return article_urls

    def _get_pagination_count(self, soup: BeautifulSoup) -> int:
        """Determine number of pages to scrape"""
        try:
            # Look for pagination links
            pagination = soup.find_all('a', href=re.compile(r'page=\d+'))
            if pagination:
                page_numbers = []
                for link in pagination:
                    match = re.search(r'page=(\d+)', link['href'])
                    if match:
                        page_numbers.append(int(match.group(1)))
                return max(page_numbers) if page_numbers else 1
            return 1
        except Exception as e:
            logger.error(f"Error determining pagination: {e}")
            return 1

    def discover_articles(self, section: str = "blog") -> List[str]:
        """
        Discover all article URLs from a section

        Args:
            section: "blog" or "white-papers"

        Returns:
            List of article URLs
        """
        base_path = self.BLOG_PATH if section == "blog" else self.WHITE_PAPERS_PATH
        base_url = self.BASE_URL + base_path

        logger.info(f"Discovering articles from {section}...")
        all_article_urls = []

        # Get first page to determine pagination
        soup = self._make_request(base_url)
        if not soup:
            return []

        # Extract articles from first page
        article_urls = self._extract_article_links_from_page(soup, base_path)
        all_article_urls.extend(article_urls)
        logger.info(f"Found {len(article_urls)} articles on page 1")

        # Get total pages
        total_pages = self._get_pagination_count(soup)
        logger.info(f"Total pages to scrape: {total_pages}")

        # Scrape remaining pages
        for page_num in range(2, total_pages + 1):
            page_url = f"{base_url}?page={page_num}"
            soup = self._make_request(page_url)
            if soup:
                article_urls = self._extract_article_links_from_page(soup, base_path)
                all_article_urls.extend(article_urls)
                logger.info(f"Found {len(article_urls)} articles on page {page_num}")

        # Remove duplicates
        all_article_urls = list(set(all_article_urls))
        logger.info(f"Discovered {len(all_article_urls)} unique articles from {section}")

        return all_article_urls

    def extract_article(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract article content and metadata
        Handles both HTML articles and PDF-only pages

        Returns:
            Dict with keys: url, title, content, published_date, section
        """
        soup = self._make_request(url)
        if not soup:
            return None

        try:
            # Check if this page contains a PDF download link
            pdf_link = soup.find('a', href=re.compile(r'\.pdf$', re.I))
            if pdf_link:
                pdf_url = pdf_link['href']
                if not pdf_url.startswith('http'):
                    pdf_url = self.BASE_URL + pdf_url

                logger.info(f"Found PDF link: {pdf_url}")
                return self._extract_pdf_article(url, pdf_url, soup)

            # Extract title
            title_tag = soup.find('h1') or soup.find('title')
            title = title_tag.get_text().strip() if title_tag else "Untitled"

            # Extract publication date
            pub_date_str = None
            pub_date = None

            # Look for date in various places
            date_patterns = [
                soup.find(string=re.compile(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}')),
                soup.find('time'),
                soup.find(class_=re.compile('date|published|time', re.I))
            ]

            for pattern in date_patterns:
                if pattern:
                    if hasattr(pattern, 'get_text'):
                        pub_date_str = pattern.get_text().strip()
                    else:
                        pub_date_str = str(pattern).strip()

                    pub_date = self._parse_date(pub_date_str)
                    if pub_date:
                        break

            # Check if article meets date criteria
            if not self._should_include_article(pub_date):
                logger.info(f"Skipping article (date filter): {title} ({pub_date_str if pub_date_str else 'no date'})")
                return None

            # Extract main content
            # Try to find main content area
            content_area = (
                soup.find('article') or
                soup.find('div', class_=re.compile('content|post|entry|article', re.I)) or
                soup.find('main')
            )

            if not content_area:
                content_area = soup

            # Get text content, removing scripts and styles
            for script_or_style in content_area(['script', 'style', 'nav', 'footer', 'header']):
                script_or_style.decompose()

            content = content_area.get_text(separator='\n', strip=True)

            # Clean up content
            content = re.sub(r'\n\s*\n', '\n\n', content)  # Remove excessive newlines
            content = content.strip()

            # Determine section
            section = "blog" if "/blog/" in url else "white-paper"

            article_data = {
                'url': url,
                'title': title,
                'content': content,
                'published_date': pub_date.strftime('%Y-%m-%d') if pub_date else None,
                'section': section,
                'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            logger.info(f"Extracted article: {title} ({pub_date.strftime('%Y-%m-%d') if pub_date else 'no date'})")
            return article_data

        except Exception as e:
            logger.error(f"Error extracting article from {url}: {e}")
            return None

    def scrape_all(self) -> List[Dict[str, Any]]:
        """
        Scrape all articles from both blog and white papers sections
        Only returns articles from 2024+

        Returns:
            List of article dictionaries
        """
        logger.info("Starting full website scrape...")
        all_articles = []

        # Scrape blog
        blog_urls = self.discover_articles("blog")
        for url in blog_urls:
            article = self.extract_article(url)
            if article:
                all_articles.append(article)

        # Scrape white papers
        white_paper_urls = self.discover_articles("white-papers")
        for url in white_paper_urls:
            article = self.extract_article(url)
            if article:
                all_articles.append(article)

        logger.info(f"Scraping complete. Collected {len(all_articles)} articles from {self.CUTOFF_YEAR}+")
        return all_articles


# Example usage
if __name__ == "__main__":
    scraper = HCSWebScraper()

    # Test with single article
    test_url = "https://hcsonline.com/support/resources/blog/how-to-convince-microsoft-office-apps-to-save-files-on-your-mac"
    article = scraper.extract_article(test_url)
    if article:
        print(f"\nTitle: {article['title']}")
        print(f"Date: {article['published_date']}")
        print(f"Content length: {len(article['content'])} characters")
        print(f"\nFirst 200 chars:\n{article['content'][:200]}...")
