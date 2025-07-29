import csv
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from io import StringIO
from datetime import datetime
from app.models.schemas import NewsItem, SearchResponse


def convert_to_csv(search_response: SearchResponse) -> str:
    """
    Convert search response to CSV format.
    
    Args:
        search_response: The search response to convert
        
    Returns:
        str: CSV formatted string
    """
    output = StringIO()
    
    # Define CSV headers
    fieldnames = ['title', 'link', 'source_name', 'snippet', 'published_date', 'scraped_timestamp']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    # Write header
    writer.writeheader()
    
    # Write data rows
    for item in search_response.results:
        writer.writerow({
            'title': item.title,
            'link': str(item.link),
            'source_name': item.source_name,
            'snippet': item.snippet,
            'published_date': item.published_date.isoformat() if item.published_date else None,
            'scraped_timestamp': item.scraped_timestamp.isoformat()
        })
    
    return output.getvalue()


def convert_to_xml(search_response: SearchResponse) -> str:
    """
    Convert search response to XML format.
    
    Args:
        search_response: The search response to convert
        
    Returns:
        str: XML formatted string
    """
    # Create root element
    root = ET.Element("search_results")
    
    # Add metadata
    metadata = ET.SubElement(root, "metadata")
    ET.SubElement(metadata, "query").text = search_response.query
    ET.SubElement(metadata, "item_count").text = str(search_response.item_count)
    ET.SubElement(metadata, "sources_searched").text = ",".join(search_response.sources_searched)
    
    # Add results
    results = ET.SubElement(root, "results")
    
    for item in search_response.results:
        result_elem = ET.SubElement(results, "news_item")
        
        ET.SubElement(result_elem, "title").text = item.title
        ET.SubElement(result_elem, "link").text = str(item.link)
        ET.SubElement(result_elem, "source_name").text = item.source_name
        ET.SubElement(result_elem, "snippet").text = item.snippet
        
        if item.published_date:
            ET.SubElement(result_elem, "published_date").text = item.published_date.isoformat()
        
        ET.SubElement(result_elem, "scraped_timestamp").text = item.scraped_timestamp.isoformat()
    
    # Convert to string with proper formatting
    ET.indent(root, space="  ", level=0)
    return ET.tostring(root, encoding='unicode', xml_declaration=True)


def clean_text(text: str) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text: Raw text to clean
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace and normalize
    text = ' '.join(text.split())
    
    # Remove common unwanted characters
    text = text.replace('\xa0', ' ')  # Non-breaking space
    text = text.replace('\u200b', '')  # Zero-width space
    
    return text.strip()


def format_markdown_content(title: str, author: str = None, date: str = None, content: str = "") -> str:
    """
    Format scraped content into markdown.
    
    Args:
        title: Article title
        author: Article author (optional)
        date: Publication date (optional)
        content: Main article content
        
    Returns:
        str: Formatted markdown content
    """
    markdown = f"# {title}\n\n"
    
    if author:
        markdown += f"**Author:** {author}\n"
    
    if date:
        markdown += f"**Date:** {date}\n"
    
    if author or date:
        markdown += "\n"
    
    markdown += content
    
    return markdown


def generate_filename(url: str, timestamp: datetime = None) -> str:
    """
    Generate a safe filename from URL and timestamp.
    
    Args:
        url: Source URL
        timestamp: Optional timestamp (defaults to current time)
        
    Returns:
        str: Safe filename
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    # Extract domain from URL
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
    except:
        domain = "scraped"
    
    # Create safe filename
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    filename = f"{domain}_{timestamp_str}.md"
    
    # Remove any unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    return filename
