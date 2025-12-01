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
import os
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JamfNationScraper:
    """Scraper for Jamf, Apple documentation, and community content"""

    BASE_URL = "https://community.jamf.com"

    # Allowed domains for search
    ALLOWED_DOMAINS = [
        'community.jamf.com',
        'jamf.com',
        'support.apple.com',
        'developer.apple.com'
    ]

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
        Search Jamf Nation for relevant content using Google Custom Search API

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of article/discussion data dicts
        """
        try:
            # Get API credentials from environment
            api_key = os.getenv('GOOGLE_API_KEY')
            search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')

            if not api_key or not search_engine_id:
                logger.error("Google Custom Search API credentials not configured")
                return []

            logger.info(f"Searching Jamf/Apple docs via Google Custom Search for: {query}")

            # Google Custom Search API endpoint
            search_url = "https://www.googleapis.com/customsearch/v1"

            # Create site search filter for allowed domains
            site_filter = ' OR '.join([f'site:{domain}' for domain in self.ALLOWED_DOMAINS])

            params = {
                'key': api_key,
                'cx': search_engine_id,
                'q': f'{query} ({site_filter})',
                'num': min(max_results, 10)  # Google API max is 10 per request
            }

            response = requests.get(search_url, params=params, timeout=30)
            time.sleep(0.5)  # Brief delay to be polite

            if response.status_code != 200:
                logger.error(f"Google Custom Search API request failed with status {response.status_code}")
                logger.error(f"Response: {response.text}")
                return []

            data = response.json()

            # Extract search results
            results = []
            search_results = data.get('items', [])

            for result in search_results[:max_results]:
                try:
                    title = result.get('title', '')
                    url = result.get('link', '')
                    snippet = result.get('snippet', '')[:500]

                    # Only include URLs from allowed domains
                    if not any(domain in url for domain in self.ALLOWED_DOMAINS):
                        continue

                    # Skip non-discussion URLs (like user profiles, categories, etc.) for community.jamf.com
                    if 'community.jamf.com' in url:
                        if any(skip in url for skip in ['/user/', '/ct-p/', '/bd-p/', '/kudos/']):
                            continue

                    # Determine source type based on domain
                    source_type = 'external_docs'
                    if 'community.jamf.com' in url:
                        source_type = 'jamf_nation'
                    elif 'jamf.com' in url:
                        source_type = 'jamf_docs'
                    elif 'support.apple.com' in url:
                        source_type = 'apple_support'
                    elif 'developer.apple.com' in url:
                        source_type = 'apple_developer'

                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'published_date': datetime.now().strftime('%Y-%m-%d'),
                        'source_type': source_type
                    })

                    logger.info(f"  Found: {title[:60]}...")

                except Exception as e:
                    logger.error(f"Error parsing search result: {e}")
                    continue

            logger.info(f"Found {len(results)} results for query: {query}")
            return results

        except Exception as e:
            logger.error(f"Error searching Jamf Nation: {e}")
            return []

    def extract_article(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract full content from Jamf, Apple documentation, or community discussions

        Returns:
            Dict with keys: url, title, content, published_date, source_type
        """
        soup = self._make_request(url)
        if not soup:
            return None

        try:
            # Extract title
            title_elem = soup.find('h1')
            if not title_elem:
                title_elem = soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "Untitled"

            # Extract publication date (try various locations)
            date_elem = soup.find('time')
            if not date_elem:
                date_elem = soup.find('span', class_=re.compile('date', re.I))
            pub_date = None
            if date_elem:
                date_str = date_elem.get_text().strip()
                pub_date = self._parse_date(date_str)

            # Determine source type and extraction method based on URL
            source_type = 'external_docs'
            if 'community.jamf.com' in url:
                source_type = 'jamf_nation'
                content = self._extract_jamf_nation_content(soup)
            elif 'jamf.com' in url:
                source_type = 'jamf_docs'
                content = self._extract_generic_content(soup)
            elif 'support.apple.com' in url:
                source_type = 'apple_support'
                content = self._extract_generic_content(soup)
            elif 'developer.apple.com' in url:
                source_type = 'apple_developer'
                content = self._extract_generic_content(soup)
            else:
                content = self._extract_generic_content(soup)

            if not content or len(content) < 50:
                logger.warning(f"Extracted content too short for {url}")
                return None

            return {
                'url': url,
                'title': title,
                'content': content,
                'published_date': pub_date.strftime('%Y-%m-%d') if pub_date else None,
                'source_type': source_type,
                'section': source_type.replace('_', '-')
            }

        except Exception as e:
            logger.error(f"Error extracting article from {url}: {e}")
            return None

    def _extract_jamf_nation_content(self, soup: BeautifulSoup) -> str:
        """Extract content specifically from Jamf Nation community threads"""
        content_parts = []

        # Get all post content divs (original post + replies)
        # Jamf Nation uses post__content class for post bodies
        posts = soup.find_all('div', class_=re.compile('post__content', re.I))

        for idx, post in enumerate(posts[:5]):  # Get up to 5 posts (original + top 4 replies)
            # Remove script/style/nav elements
            for tag in post(['script', 'style', 'nav', 'header', 'footer', 'button']):
                tag.decompose()

            post_text = post.get_text(separator='\n', strip=True)

            if len(post_text) > 100:  # Only include substantial content
                if idx == 0:
                    content_parts.append(post_text)
                else:
                    content_parts.append(f"\n\n=== Community Reply {idx} ===\n{post_text[:1500]}")

        return '\n\n'.join(content_parts)

    def _extract_generic_content(self, soup: BeautifulSoup) -> str:
        """Extract content from generic documentation pages (Apple, Jamf docs)"""
        # Try to find the main content area
        content = None

        # Common content containers for documentation sites
        content_selectors = [
            ('article', {}),
            ('main', {}),
            ('div', {'class': re.compile('content|article|body|main', re.I)}),
            ('div', {'id': re.compile('content|article|body|main', re.I)})
        ]

        for tag, attrs in content_selectors:
            content_elem = soup.find(tag, attrs)
            if content_elem:
                # Remove unwanted elements
                for unwanted in content_elem(['script', 'style', 'nav', 'header', 'footer', 'aside', 'button']):
                    unwanted.decompose()

                content = content_elem.get_text(separator='\n', strip=True)
                if len(content) > 100:
                    break

        # Fallback: get body text
        if not content or len(content) < 100:
            body = soup.find('body')
            if body:
                for unwanted in body(['script', 'style', 'nav', 'header', 'footer', 'aside', 'button']):
                    unwanted.decompose()
                content = body.get_text(separator='\n', strip=True)

        # Limit to reasonable length
        if content and len(content) > 5000:
            content = content[:5000] + "\n\n[Content truncated for length]"

        return content if content else ""

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
