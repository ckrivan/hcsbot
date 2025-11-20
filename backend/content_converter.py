"""
Content Converter
Converts HTML content to clean Markdown format for storage and processing
"""

import html2text
import re
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ContentConverter:
    """Convert web article content to clean markdown"""

    def __init__(self):
        # Configure html2text
        self.converter = html2text.HTML2Text()
        self.converter.ignore_links = False
        self.converter.ignore_images = False
        self.converter.ignore_emphasis = False
        self.converter.body_width = 0  # Don't wrap lines
        self.converter.unicode_snob = True  # Use unicode characters
        self.converter.skip_internal_links = True

    def html_to_markdown(self, html_content: str) -> str:
        """
        Convert HTML to markdown

        Args:
            html_content: Raw HTML string

        Returns:
            Clean markdown string
        """
        try:
            # Convert HTML to markdown
            markdown = self.converter.handle(html_content)

            # Clean up the markdown
            markdown = self._clean_markdown(markdown)

            return markdown
        except Exception as e:
            logger.error(f"Error converting HTML to markdown: {e}")
            return html_content  # Fallback to original

    def _clean_markdown(self, markdown: str) -> str:
        """Clean up markdown text"""

        # Remove excessive newlines (more than 2)
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)

        # Remove markdown link artifacts
        markdown = re.sub(r'\[\s*\]', '', markdown)

        # Remove excessive spaces
        markdown = re.sub(r' {2,}', ' ', markdown)

        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in markdown.split('\n')]
        markdown = '\n'.join(lines)

        # Remove navigation breadcrumbs
        markdown = re.sub(r'Home\s*>\s*[^\n]+\n', '', markdown)

        # Remove social sharing text
        markdown = re.sub(r'(Share on|Follow us on|Connect with us)\s*:?\s*(Facebook|Twitter|LinkedIn|Instagram|YouTube)', '', markdown, flags=re.IGNORECASE)

        # Remove "Read More" links
        markdown = re.sub(r'\[?Read More\]?.*\n?', '', markdown, flags=re.IGNORECASE)

        # Remove email subscription prompts
        markdown = re.sub(r'Subscribe to our (newsletter|email|updates).*\n?', '', markdown, flags=re.IGNORECASE)

        return markdown.strip()

    def prepare_for_rag(self, article_data: Dict[str, Any]) -> str:
        """
        Prepare article content for RAG system

        Combines title, metadata, and content into a structured format

        Args:
            article_data: Dict with keys: title, content, published_date, url, section

        Returns:
            Formatted string ready for chunking
        """
        title = article_data.get('title', 'Untitled')
        pub_date = article_data.get('published_date', 'Unknown date')
        section = article_data.get('section', 'article')
        content = article_data.get('content', '')
        url = article_data.get('url', '')

        # Build structured content
        formatted = f"""# {title}

**Source:** HCS Technology Group - {section.replace('-', ' ').title()}
**Published:** {pub_date}
**URL:** {url}

---

{content}
"""

        return formatted

    def clean_text_content(self, text: str) -> str:
        """
        Clean plain text content (for non-HTML sources)

        Args:
            text: Plain text string

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove repeated punctuation
        text = re.sub(r'([.!?])\1+', r'\1', text)

        # Fix spacing around punctuation
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)
        text = re.sub(r'([,.!?;:])\s*', r'\1 ', text)

        # Remove URLs (optional)
        # text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)

        return text.strip()

    def extract_summary(self, content: str, max_length: int = 200) -> str:
        """
        Extract a summary from content

        Args:
            content: Full article content
            max_length: Maximum characters for summary

        Returns:
            Summary text
        """
        # Get first paragraph or first max_length characters
        paragraphs = content.split('\n\n')
        summary = paragraphs[0] if paragraphs else content

        if len(summary) > max_length:
            summary = summary[:max_length].rsplit(' ', 1)[0] + '...'

        return summary


# Example usage
if __name__ == "__main__":
    converter = ContentConverter()

    # Test HTML to markdown
    sample_html = """
    <h1>Test Article</h1>
    <p>This is a <strong>test</strong> article with <a href="https://example.com">a link</a>.</p>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
    </ul>
    """

    markdown = converter.html_to_markdown(sample_html)
    print("Markdown output:")
    print(markdown)
    print("\n" + "="*50 + "\n")

    # Test RAG preparation
    article_data = {
        'title': 'Test Article',
        'content': markdown,
        'published_date': '2025-01-15',
        'section': 'blog',
        'url': 'https://example.com/test'
    }

    rag_content = converter.prepare_for_rag(article_data)
    print("RAG-formatted content:")
    print(rag_content)
