"""
PDF Publication Date Mapping
Maps PDF filenames to their actual publication dates for recency-based search prioritization
"""

# PDFs with known recent publication dates (2024+)
RECENT_PDF_DATES = {
    'Jamf_Connect_Entra_2025.pdf': '2025-10-03',
    # Add more recent PDFs here as they're published
}

def get_pdf_date(filename: str) -> str:
    """
    Get publication date for a PDF

    Args:
        filename: PDF filename

    Returns:
        ISO date string (YYYY-MM-DD) or 'pre-2024' for older content
    """
    return RECENT_PDF_DATES.get(filename, 'pre-2024')

def is_recent_pdf(filename: str) -> bool:
    """Check if PDF is from 2024 or later"""
    date = get_pdf_date(filename)
    if date == 'pre-2024':
        return False
    try:
        year = int(date.split('-')[0])
        return year >= 2024
    except:
        return False
