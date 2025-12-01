"""
Jamf Nation Community Scraper
Scrapes relevant articles, discussions, and knowledge base entries from Jamf Nation
Used as a fallback source when HCS documentation doesn't have the answer
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import time
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JamfNationScraper:
    """Scraper for Jamf Nation community content"""

    BASE_URL = "https://community.jamf.com"

    # Focus on high-quality content areas
    KNOWLEDGE_BASE_PATH = "/t5/jamf-pro/ct-p/jamf-pro-knowledge-base"
    DISCUSSIONS_PATH = "/t5/jamf-pro/bd-p/jamf-pro-discussions"

    # Be polite - delay between requests
    REQUEST_DELAY = 2  # seconds

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HCSBot/1.0 (Knowledge Base Indexer; +https://hcsbot.hcsonline.com)'
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
            date_str = date_str.strip()

            # Handle relative dates like "2 days ago", "1 week ago"
            if 'ago' in date_str.lower():
                # Return current date for recent posts
                return datetime.now()

            # Try different date formats
            for fmt in ['%m-%d-%Y', '%Y-%m-%d', '%B %d, %Y', '%b %d, %Y']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue

            logger.warning(f"Could not parse date: {date_str}")
            return datetime.now()  # Default to current date if can't parse
        except Exception as e:
            logger.error(f"Date parsing error: {e}")
            return datetime.now()

    def search_jamf_nation(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search Jamf Nation for relevant content using Google search with site restriction

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of article/discussion data dicts
        """
        try:
            # Use Google search with site restriction for Jamf Nation
            # This is more reliable than scraping Jamf Nation's JS-based search
            search_query = f"site:community.jamf.com {query}"
            google_url = "https://www.google.com/search"
            params = {
                'q': search_query,
                'num': min(max_results, 10)
            }

            logger.info(f"Searching Jamf Nation via Google for: {query}")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = self.session.get(google_url, params=params, headers=headers, timeout=30)
            time.sleep(self.REQUEST_DELAY)

            if response.status_code != 200:
                logger.error(f"Google search request failed with status {response.status_code}")
                return []

            soup = BeautifulSoup(response.content, 'lxml')

            # Extract Google search results
            results = []
            search_results = soup.find_all('div', class_='g')

            for result in search_results[:max_results]:
                try:
                    # Extract title and link
                    title_elem = result.find('h3')
                    link_elem = result.find('a')

                    if not title_elem or not link_elem:
                        continue

                    title = title_elem.get_text().strip()
                    url = link_elem.get('href', '')

                    # Only include Jamf Nation URLs
                    if 'community.jamf.com' not in url:
                        continue

                    # Extract snippet from Google's search result
                    snippet_elem = result.find('div', class_=re.compile('VwiC3b', re.I))
                    if not snippet_elem:
                        snippet_elem = result.find('span', class_=re.compile('aCOpRe', re.I))
                    snippet = snippet_elem.get_text().strip()[:500] if snippet_elem else ""

                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'published_date': datetime.now().strftime('%Y-%m-%d'),
                        'source_type': 'jamf_nation'
                    })

                    logger.info(f"  Found: {title[:60]}...")

                except Exception as e:
                    logger.error(f"Error parsing search result: {e}")
                    continue

            logger.info(f"Found {len(results)} Jamf Nation results for query: {query}")
            return results

        except Exception as e:
            logger.error(f"Error searching Jamf Nation: {e}")
            return []

    def extract_article(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract full content from a Jamf Nation article or discussion

        Returns:
            Dict with keys: url, title, content, published_date, source_type
        """
        soup = self._make_request(url)
        if not soup:
            return None

        try:
            # Extract title
            title_elem = soup.find('h1', class_=re.compile('lia-message-subject', re.I))
            if not title_elem:
                title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "Untitled"

            # Extract publication date
            date_elem = soup.find('span', class_=re.compile('DateTime', re.I))
            pub_date = None
            if date_elem:
                date_str = date_elem.get_text().strip()
                pub_date = self._parse_date(date_str)

            # Extract main content
            content_parts = []

            # Get original post content
            main_content = soup.find('div', class_=re.compile('lia-message-body-content', re.I))
            if main_content:
                # Remove script/style elements
                for tag in main_content(['script', 'style', 'nav', 'header', 'footer']):
                    tag.decompose()

                content_text = main_content.get_text(separator='\n', strip=True)
                content_parts.append(content_text)

            # Also get accepted solution if it exists
            solution = soup.find('div', class_=re.compile('lia-accepted-solution', re.I))
            if solution:
                solution_text = solution.get_text(separator='\n', strip=True)
                content_parts.append("\n\n=== Accepted Solution ===\n" + solution_text)

            # Get top replies (up to 3) for additional context
            replies = soup.find_all('div', class_=re.compile('lia-linear-display-message-view', re.I))[:3]
            for idx, reply in enumerate(replies):
                reply_body = reply.find('div', class_=re.compile('lia-message-body-content', re.I))
                if reply_body:
                    reply_text = reply_body.get_text(separator='\n', strip=True)
                    if len(reply_text) > 100:  # Only include substantial replies
                        content_parts.append(f"\n\n=== Community Reply {idx+1} ===\n{reply_text[:1000]}")

            content = '\n\n'.join(content_parts)

            if not content or len(content) < 50:
                logger.warning(f"Extracted content too short for {url}")
                return None

            return {
                'url': url,
                'title': title,
                'content': content,
                'published_date': pub_date.strftime('%Y-%m-%d') if pub_date else None,
                'source_type': 'jamf_nation',
                'section': 'jamf-nation'
            }

        except Exception as e:
            logger.error(f"Error extracting article from {url}: {e}")
            return None

    def get_popular_articles(self, category: str = "jamf-pro", limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get popular/featured articles from Jamf Nation

        Args:
            category: Category to scrape (e.g., "jamf-pro", "jamf-connect")
            limit: Maximum number of articles to retrieve

        Returns:
            List of article data dicts
        """
        try:
            # Get the main Jamf Pro discussions page
            url = f"{self.BASE_URL}/t5/jamf-pro/bd-p/jamf-pro-discussions"
            soup = self._make_request(url)

            if not soup:
                return []

            articles = []
            discussion_links = soup.find_all('a', class_=re.compile('lia-link-navigation', re.I))

            for link in discussion_links[:limit]:
                try:
                    url = link.get('href', '')
                    if not url or url == '#':
                        continue

                    if not url.startswith('http'):
                        url = self.BASE_URL + url

                    # Skip non-article links
                    if '/bd-p/' in url or '/ct-p/' in url or '/user/' in url:
                        continue

                    title = link.get_text().strip()
                    if not title or len(title) < 10:
                        continue

                    articles.append({
                        'url': url,
                        'title': title,
                        'source_type': 'jamf_nation'
                    })

                except Exception as e:
                    logger.error(f"Error parsing article link: {e}")
                    continue

            logger.info(f"Found {len(articles)} Jamf Nation articles")
            return articles

        except Exception as e:
            logger.error(f"Error getting popular articles: {e}")
            return []
