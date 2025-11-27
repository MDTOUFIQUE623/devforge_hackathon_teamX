"""
Unstructured Data Processor
----------------------------
Converts various unstructured data formats (HTML, Wiki, Markdown, URLs) 
into clean structured text files.
"""

import re
import html
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

# Try to import markdown, fallback to basic processing if not available
try:
    import markdown as md_lib
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    md_lib = None


class UnstructuredDataProcessor:
    """Process unstructured data into structured text format."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _is_json_like(self, text: str) -> bool:
        """
        Check if text looks like JSON data (to filter it out).
        
        Args:
            text: Text to check
            
        Returns:
            True if text looks like JSON
        """
        if not text or len(text.strip()) < 10:
            return False
        
        text = text.strip()
        
        # Check for JSON-like patterns
        # Starts with { or [ and contains common JSON patterns
        if (text.startswith('{') or text.startswith('[')) and (
            '"entityUrn"' in text or 
            '"$type"' in text or 
            '"lixTracking"' in text or
            '"data"' in text and '"elements"' in text or
            (text.count('"') > 5 and text.count(':') > 3)  # Multiple key-value pairs
        ):
            return True
        
        # Check for JSON-like structure with braces and quotes
        if text.count('{') > 2 and text.count('"') > 5:
            return True
        
        return False
    
    def _is_linkedin_ui_noise(self, text: str) -> bool:
        """
        Check if text is LinkedIn UI noise (navigation, notifications, etc.) to filter out.
        
        Args:
            text: Text to check
            
        Returns:
            True if text is LinkedIn UI noise
        """
        if not text or len(text.strip()) < 3:
            return False
        
        text_lower = text.lower().strip()
        
        # LinkedIn UI patterns to filter out
        ui_patterns = [
            r'^\d+\s+notifications?\s+total$',
            r'^suggested\s+for\s+you$',
            r'^stand\s+out\s+and\s+build',
            r'^analytics$',
            r'^activity$',
            r'^experience$',
            r'^education$',
            r'^skills$',
            r'^interests$',
            r'^who\s+your\s+viewers\s+also\s+viewed$',
            r'^unlock\s+the\s+full\s+list$',
            r'^people\s+you\s+may\s+know$',
            r'^you\s+might\s+like$',
            r'^show\s+recruiters',
            r'^get\s+started$',
            r'^share\s+that\s+you\'re\s+hiring',
            r'^showcase\s+your\s+services',
            r'^private\s+to\s+you$',
            r'^enhance\s+your\s+profile',
            r'^\d+\s+followers?$',
            r'^show\s+your\s+qualifications',
            r'^1-month\s+free\s+trial',
            r'^we\'ll\s+remind\s+you',
            r'^home$',
            r'^my\s+network$',
            r'^jobs$',
            r'^messaging$',
            r'^notifications$',
            r'^me$',
            r'^search$',
            r'^more$',
            r'^less$',
            r'^show\s+more$',
            r'^show\s+less$',
            r'^see\s+more$',
            r'^see\s+less$',
        ]
        
        for pattern in ui_patterns:
            if re.match(pattern, text_lower):
                return True
        
        # Check for very short UI-like text (1-3 words that are common UI elements)
        words = text_lower.split()
        if len(words) <= 3:
            ui_words = ['notifications', 'analytics', 'activity', 'experience', 'education', 
                       'skills', 'interests', 'followers', 'connections', 'views', 'likes',
                       'comments', 'shares', 'more', 'less', 'show', 'hide', 'close']
            if all(word in ui_words for word in words):
                return True
        
        return False
    
    def process_html(self, html_content: str, source_name: str = "html_content") -> str:
        """
        Process HTML content and extract clean text.
        Optimized for large HTML files and social media profiles (LinkedIn, etc.).
        Prioritizes content extraction over aggressive filtering.
        
        Args:
            html_content: Raw HTML string (outer HTML)
            source_name: Name for the source document
            
        Returns:
            Clean structured text
        """
        try:
            # Try lxml parser for better performance with large files, fallback to html.parser
            try:
                soup = BeautifulSoup(html_content, 'lxml')
            except:
                soup = BeautifulSoup(html_content, 'html.parser')
            
            # Step 1: Remove only truly unwanted elements (scripts, styles, etc.)
            # Don't be too aggressive - we want to preserve content
            unwanted_tags = ["script", "style", "noscript", "iframe", "svg", "canvas"]
            for tag in unwanted_tags:
                for element in soup.find_all(tag):
                    element.decompose()
            
            # Remove script tags with JSON data (LinkedIn often embeds JSON in script tags)
            for script in soup.find_all('script', type=re.compile('application/json|application/ld\+json', re.I)):
                script.decompose()
            
            # Remove elements with data attributes that contain JSON (common in LinkedIn)
            for element in soup.find_all(attrs={"data-json-key": True}):
                element.decompose()
            
            # Remove elements with JSON-like data attributes
            for element in soup.find_all(attrs={"data-json": True}):
                element.decompose()
            
            # Step 2: Remove navigation elements more carefully
            # Only remove obvious navigation, not everything with "nav" in class name
            for nav in soup.find_all(['nav']):
                # Check if it's actually navigation (has links, menu items, etc.)
                if nav.find_all('a') or 'menu' in (nav.get('class') or []) or 'navigation' in (nav.get('class') or []):
                    nav.decompose()
            
            # Remove header/footer tags but be careful
            for header in soup.find_all(['header', 'footer']):
                # Only remove if it looks like site header/footer (has nav links)
                if header.find_all('a', limit=3):
                    header.decompose()
            
            # Step 3: Focus on body content
            main_content = soup.find('body') or soup.find('main') or soup
            
            # Step 4: Extract text with a simpler, more aggressive approach
            # For large HTML like LinkedIn, we need to extract everything first, then clean
            
            # First, try to extract structured content (headings, paragraphs, lists)
            text_parts = []
            seen_texts = set()
            
            # Extract headings with their hierarchy
            for heading in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                text = heading.get_text(separator=' ', strip=True)
                if text and len(text.strip()) > 1:
                    # Filter out LinkedIn UI noise
                    if self._is_linkedin_ui_noise(text):
                        continue
                    
                    level = int(heading.name[1])
                    heading_text = f"{'#' * level} {text}"
                    # Use normalized text for duplicate detection
                    normalized = re.sub(r'\s+', ' ', text.lower().strip())
                    if normalized not in seen_texts:
                        text_parts.append(heading_text)
                        seen_texts.add(normalized)
            
            # Extract paragraphs
            for para in main_content.find_all('p'):
                text = para.get_text(separator=' ', strip=True)
                if text and len(text.strip()) > 5:
                    # Filter out LinkedIn UI noise and JSON
                    if self._is_linkedin_ui_noise(text) or self._is_json_like(text):
                        continue
                    
                    normalized = re.sub(r'\s+', ' ', text.lower().strip())
                    if normalized not in seen_texts:
                        text_parts.append(text)
                        seen_texts.add(normalized)
            
            # Extract list items
            for list_elem in main_content.find_all(['ul', 'ol']):
                list_items = []
                for li in list_elem.find_all('li', recursive=True):
                    item_text = li.get_text(separator=' ', strip=True)
                    if item_text and len(item_text.strip()) > 2:
                        normalized = re.sub(r'\s+', ' ', item_text.lower().strip())
                        if normalized not in seen_texts:
                            list_items.append(f"- {item_text}")
                            seen_texts.add(normalized)
                if list_items:
                    text_parts.append("\n".join(list_items))
            
            # Extract table content
            for table in main_content.find_all('table'):
                rows = []
                for tr in table.find_all('tr'):
                    cells = [td.get_text(separator=' ', strip=True) for td in tr.find_all(['td', 'th'])]
                    if cells and any(cell.strip() for cell in cells):
                        row_text = " | ".join(cells)
                        if row_text.strip():
                            rows.append(row_text)
                if rows:
                    text_parts.append("\n".join(rows))
            
            # Step 5: For LinkedIn and similar sites, extract text from divs and spans
            # This is important because LinkedIn uses lots of nested divs
            # Extract meaningful div content (not navigation)
            for div in main_content.find_all('div'):
                # Skip if it's navigation
                div_classes = ' '.join(div.get('class', [])).lower()
                if any(nav_term in div_classes for nav_term in ['nav', 'navbar', 'menu', 'sidebar', 'header', 'footer']):
                    continue
                
                # Skip if it contains only other block elements (already processed)
                if div.find(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'table']):
                    continue
                
                # Get text from div
                div_text = div.get_text(separator=' ', strip=True)
                if div_text and len(div_text.strip()) > 10:
                    # Filter out LinkedIn UI noise and JSON
                    if self._is_linkedin_ui_noise(div_text) or self._is_json_like(div_text):
                        continue
                    
                    normalized = re.sub(r'\s+', ' ', div_text.lower().strip())
                    # Filter out obvious non-content (single words, buttons, etc.)
                    if (normalized not in seen_texts and 
                        len(div_text.split()) > 2 and
                        not re.match(r'^(Home|About|Contact|Login|Sign|Menu|Search|Follow|Share|Like|Comment|Subscribe|Cookie|Accept|Decline|Close|×|←|→|↑|↓|More|Less|Show|Hide)$', div_text.strip(), re.I)):
                        text_parts.append(div_text)
                        seen_texts.add(normalized)
            
            # Extract meaningful span content (for inline text in divs)
            for span in main_content.find_all('span'):
                # Skip if in navigation or button
                if span.find_parent(['nav', 'button', 'a']):
                    continue
                
                span_text = span.get_text(separator=' ', strip=True)
                if span_text and len(span_text.strip()) > 15:
                    # Filter out LinkedIn UI noise and JSON
                    if self._is_linkedin_ui_noise(span_text) or self._is_json_like(span_text):
                        continue
                    
                    normalized = re.sub(r'\s+', ' ', span_text.lower().strip())
                    if (normalized not in seen_texts and 
                        len(span_text.split()) > 3):
                        text_parts.append(span_text)
                        seen_texts.add(normalized)
            
            # Step 6: If we have structured content, combine and clean it
            if text_parts:
                # Filter out any JSON-like content from text_parts before combining
                filtered_parts = []
                for part in text_parts:
                    # Check each line in the part
                    lines = part.split('\n')
                    filtered_lines = []
                    for line in lines:
                        line = line.strip()
                        if line and not self._is_json_like(line):
                            filtered_lines.append(line)
                    if filtered_lines:
                        filtered_parts.append('\n'.join(filtered_lines))
                
                if filtered_parts:
                    result = "\n\n".join(filtered_parts)
                    # Simple cleaning - don't be too aggressive
                    result = re.sub(r'\n{3,}', '\n\n', result)  # Max 2 newlines
                    result = re.sub(r' {2,}', ' ', result)  # Normalize spaces
                    result = result.strip()
                    
                    # If we got substantial content, return it
                    if result and len(result.strip()) > 20:
                        return result
            
            # Step 7: Fallback - extract all text if structured extraction didn't work
            # This is important for large, complex HTML
            all_text = main_content.get_text(separator='\n', strip=True)
            
            # Clean up the text
            # Remove excessive newlines
            all_text = re.sub(r'\n{3,}', '\n\n', all_text)
            # Normalize whitespace
            all_text = re.sub(r'[ \t]+', ' ', all_text)
            # Remove very short lines (likely noise) and JSON-like content
            lines = []
            for line in all_text.split('\n'):
                line = line.strip()
                if line and len(line) > 3 and not self._is_json_like(line):
                    lines.append(line)
            all_text = '\n'.join(lines)
            
            # If we have content, return it
            if all_text and len(all_text.strip()) > 10:
                return all_text.strip()
            
            # Step 8: Last resort - get everything from the entire document
            all_text = soup.get_text(separator=' ', strip=True)
            all_text = re.sub(r'\s+', ' ', all_text).strip()
            
            # Filter out JSON-like content from final extraction
            if self._is_json_like(all_text):
                # Try to extract lines that aren't JSON
                lines = all_text.split(' ')
                filtered_lines = [line for line in lines if not self._is_json_like(line) and len(line.strip()) > 3]
                all_text = ' '.join(filtered_lines)
            
            if all_text and len(all_text) > 10:
                return all_text
            
            return ""
            
        except Exception as e:
            # Exception fallback: try simple extraction
            try:
                soup_fallback = BeautifulSoup(html_content, 'html.parser')
                # Remove scripts and styles (including JSON scripts)
                for tag in soup_fallback(["script", "style", "noscript"]):
                    tag.decompose()
                
                # Remove JSON script tags
                for script in soup_fallback.find_all('script', type=re.compile('application/json|application/ld\+json', re.I)):
                    script.decompose()
                
                # Get all text
                text = soup_fallback.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text).strip()
                
                # Filter out JSON-like content
                if self._is_json_like(text):
                    # Try to extract non-JSON parts
                    lines = text.split(' ')
                    filtered_lines = [line for line in lines if not self._is_json_like(line) and len(line.strip()) > 3]
                    text = ' '.join(filtered_lines)
                
                if text and len(text) > 10:
                    return text
            except:
                pass
            
            # Final fallback: regex-based extraction
            text = re.sub(r'<[^>]+>', '', html_content)
            text = html.unescape(text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Filter out JSON-like content
            if self._is_json_like(text):
                lines = text.split(' ')
                filtered_lines = [line for line in lines if not self._is_json_like(line) and len(line.strip()) > 3]
                text = ' '.join(filtered_lines)
            
            return text if text and len(text) > 10 else ""
    
    def _clean_and_format_text(self, text: str) -> str:
        """
        Advanced text cleaning and formatting for professional output.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Clean, well-formatted text
        """
        # Remove excessive whitespace and normalize
        # First, normalize all whitespace within lines
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip empty lines (we'll add them back strategically)
            if not line.strip():
                continue
            
            # Clean the line: remove excessive spaces, normalize
            cleaned_line = re.sub(r'[ \t]+', ' ', line.strip())
            
            # Skip very short lines that are likely artifacts
            if len(cleaned_line) < 2:
                continue
            
            # Skip lines that are just punctuation or symbols
            if re.match(r'^[^\w\s]+$', cleaned_line):
                continue
            
            # Remove excessive leading/trailing whitespace from content
            cleaned_line = cleaned_line.strip()
            
            # Create a normalized version for duplicate detection (lowercase, no extra spaces)
            normalized = re.sub(r'\s+', ' ', cleaned_line.lower())
            
            # Skip duplicate consecutive lines
            if cleaned_lines and cleaned_line == cleaned_lines[-1].strip():
                continue
            
            # Skip if we've seen very similar content (fuzzy duplicate detection)
            # Check if this line is substantially similar to any previous line
            is_duplicate = False
            for prev_line in cleaned_lines:
                prev_normalized = re.sub(r'\s+', ' ', prev_line.lower())
                # If one is a substantial substring of the other (80% match)
                if len(normalized) > 30 and len(prev_normalized) > 30:
                    shorter = min(len(normalized), len(prev_normalized))
                    longer = max(len(normalized), len(prev_normalized))
                    if shorter / longer > 0.8:  # 80% similarity
                        # Check if they're very similar
                        if normalized[:int(shorter*0.8)] in prev_normalized or prev_normalized[:int(shorter*0.8)] in normalized:
                            is_duplicate = True
                            break
                elif normalized == prev_normalized:
                    is_duplicate = True
                    break
            
            if is_duplicate:
                continue
            
            cleaned_lines.append(cleaned_line)
        
        # Join lines with proper spacing
        result = '\n'.join(cleaned_lines)
        
        # Normalize multiple newlines (max 2 consecutive)
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        # Clean up spacing around headings
        result = re.sub(r'\n(#{1,6}\s+[^\n]+)\n+', r'\n\1\n\n', result)
        
        # Remove excessive spaces between words (but preserve single spaces)
        result = re.sub(r' {2,}', ' ', result)
        
        # Clean up list formatting
        result = re.sub(r'\n(- [^\n]+)\n+(- [^\n]+)', r'\n\1\n\2', result)
        
        # Remove trailing whitespace from each line
        lines = [line.rstrip() for line in result.split('\n')]
        result = '\n'.join(lines)
        
        # Final normalization: ensure proper paragraph spacing
        # Headings should have content after them, not just empty lines
        result = re.sub(r'(#{1,6}\s+[^\n]+)\n\n\n+', r'\1\n\n', result)
        
        # Remove leading/trailing newlines
        result = result.strip()
        
        return result
    
    def process_markdown(self, markdown_content: str, source_name: str = "markdown_content") -> str:
        """
        Process Markdown/Wiki content.
        
        Args:
            markdown_content: Markdown or Wiki formatted text
            source_name: Name for the source document
            
        Returns:
            Clean structured text (Markdown converted to plain text with structure)
        """
        try:
            # Convert markdown to HTML first, then extract text
            if MARKDOWN_AVAILABLE and md_lib:
                html_content = md_lib.markdown(markdown_content)
            else:
                # Fallback: treat as plain text with markdown structure
                html_content = markdown_content
                # Simple markdown to HTML conversion for basic elements
                html_content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
                html_content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
                html_content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)
                html_content = re.sub(r'^\* (.+)$', r'<li>\1</li>', html_content, flags=re.MULTILINE)
                html_content = re.sub(r'^- (.+)$', r'<li>\1</li>', html_content, flags=re.MULTILINE)
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract text while preserving structure
            text_parts = []
            
            # Process headings
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                level = int(heading.name[1])
                text = heading.get_text(strip=True)
                if text:
                    text_parts.append(f"\n{'#' * level} {text}\n")
            
            # Process paragraphs
            for para in soup.find_all('p'):
                text = para.get_text(separator=' ', strip=True)
                if text and len(text) > 5:  # Only substantial paragraphs
                    text_parts.append(text)
            
            # Process lists
            for list_elem in soup.find_all(['ul', 'ol']):
                list_items = []
                for li in list_elem.find_all('li', recursive=False):
                    item_text = li.get_text(separator=' ', strip=True)
                    if item_text:
                        list_items.append(f"- {item_text}")
                if list_items:
                    text_parts.append("\n".join(list_items))
            
            # Process code blocks (preserve as-is)
            for code in soup.find_all(['code', 'pre']):
                code_text = code.get_text()
                if code_text:
                    text_parts.append(f"\n```\n{code_text}\n```\n")
            
            # If no structured content found, try to extract all text and split by double newlines
            if not text_parts:
                all_text = soup.get_text(separator='\n', strip=True)
                # Split by double newlines to preserve paragraph structure
                paragraphs = [p.strip() for p in all_text.split('\n\n') if p.strip()]
                text_parts.extend(paragraphs)
            
            result = "\n\n".join(text_parts)
            # Clean up excessive whitespace
            result = re.sub(r'\n{3,}', '\n\n', result)
            
            # If conversion didn't work well, return original markdown with minimal processing
            if len(result.strip()) < len(markdown_content.strip()) * 0.3:
                # Just clean up the original markdown
                cleaned = re.sub(r'\n{3,}', '\n\n', markdown_content.strip())
                return cleaned
            
            return result.strip()
            
        except Exception as e:
            # Fallback: return original markdown
            return markdown_content.strip()
    
    def process_plain_text(self, text_content: str, source_name: str = "text_content") -> str:
        """
        Process plain text content.
        
        Args:
            text_content: Plain text
            source_name: Name for the source document
            
        Returns:
            Clean structured text
        """
        # Clean up the text
        text = text_content.strip()
        # Normalize whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        # Normalize line breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Remove excessive spaces
        text = re.sub(r' {2,}', ' ', text)
        
        return text.strip()
    
    def scrape_url(self, url: str) -> Optional[str]:
        """
        Scrape content from a URL.
        
        Args:
            url: URL to scrape
            
        Returns:
            Clean structured text or None if failed
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "meta", "link", "nav", "footer", "header"]):
                script.decompose()
            
            # Try to find main content area
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile('content|main|article', re.I))
            
            if main_content:
                html_content = str(main_content)
            else:
                html_content = str(soup)
            
            # Process the HTML
            return self.process_html(html_content, source_name=url)
            
        except Exception as e:
            return None
    
    def process_html_file(self, html_file_path: Path, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Process an HTML file and convert it to structured text.
        
        Args:
            html_file_path: Path to the HTML file
            output_dir: Directory to save the processed text file (default: same as HTML file)
            
        Returns:
            Dictionary with processing results including path to the processed .txt file
        """
        try:
            if not html_file_path.exists():
                return {
                    "success": False,
                    "error": f"HTML file not found: {html_file_path}",
                    "file_path": None,
                    "content_length": 0,
                    "paragraphs": 0,
                    "filename": None
                }
            
            # Read HTML content
            html_content = html_file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Validate that we read some content
            if not html_content or len(html_content.strip()) < 10:
                return {
                    "success": False,
                    "error": f"HTML file appears to be empty or too small ({len(html_content)} characters). Please check the file.",
                    "file_path": None,
                    "content_length": 0,
                    "paragraphs": 0,
                    "filename": None
                }
            
            # Process HTML
            processed_text = self.process_html(html_content, source_name=html_file_path.stem)
            
            # Validate that we got some content
            if not processed_text or len(processed_text.strip()) == 0:
                # Try a more aggressive extraction as fallback
                from bs4 import BeautifulSoup
                soup_fallback = BeautifulSoup(html_content, 'html.parser')
                # Remove scripts and styles
                for tag in soup_fallback(["script", "style", "meta", "link"]):
                    tag.decompose()
                # Get all text
                processed_text = soup_fallback.get_text(separator=' ', strip=True)
                # Clean up
                processed_text = re.sub(r'\s+', ' ', processed_text).strip()
                
                # If still empty, return error
                if not processed_text or len(processed_text.strip()) < 5:
                    return {
                        "success": False,
                        "error": "HTML file contains no extractable text content. The file may be empty or contain only scripts/styles.",
                        "file_path": None,
                        "content_length": 0,
                        "paragraphs": 0,
                        "filename": None
                    }
            
            # Determine output path
            if output_dir is None:
                output_dir = html_file_path.parent
            
            # Create output filename (same name, .txt extension)
            output_filename = html_file_path.stem + '.txt'
            output_path = output_dir / output_filename
            
            # Save processed text
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(processed_text)
            
            # Count paragraphs - improved logic
            # First try splitting by double newlines
            paragraphs = [p.strip() for p in processed_text.split('\n\n') if p.strip()]
            
            # If no double newlines, try single newlines for substantial content
            if not paragraphs:
                paragraphs = [p.strip() for p in processed_text.split('\n') if p.strip() and len(p.strip()) > 10]
            
            # If still no paragraphs but we have content, count by sentences or minimum length blocks
            if not paragraphs and processed_text.strip():
                # Split by periods and count substantial sentences
                sentences = [s.strip() for s in processed_text.split('.') if s.strip() and len(s.strip()) > 10]
                if sentences:
                    # Group sentences into paragraphs (roughly 2-3 sentences per paragraph)
                    para_count = max(1, len(sentences) // 2)
                    paragraphs = ['dummy'] * para_count  # Just for counting
                else:
                    # Last resort: if we have any content, count as 1 paragraph
                    paragraphs = ['dummy'] if len(processed_text.strip()) > 10 else []
            
            # Ensure we have at least 1 paragraph if content exists
            para_count = len(paragraphs) if paragraphs else (1 if len(processed_text.strip()) > 10 else 0)
            
            return {
                "success": True,
                "file_path": str(output_path),
                "filename": output_filename,
                "original_file": str(html_file_path),
                "content_length": len(processed_text),
                "paragraphs": para_count
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_path": None,
                "content_length": 0,
                "paragraphs": 0,
                "filename": None
            }
    
    def process_and_save(
        self, 
        content: str, 
        content_type: str, 
        filename: str,
        output_dir: Path,
        url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process content and save as structured text file.
        
        Args:
            content: The content to process
            content_type: Type of content ('html', 'markdown', 'text', 'url')
            filename: Output filename (without extension)
            output_dir: Directory to save the file
            url: Optional URL if content_type is 'url'
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Process based on type
            if content_type == 'html':
                # Validate input content first
                if not content or len(content.strip()) < 10:
                    return {
                        "success": False,
                        "error": "HTML content is too short or empty. Please provide valid HTML content.",
                        "file_path": None,
                        "content_length": 0,
                        "paragraphs": 0,
                        "filename": None
                    }
                
                processed_text = self.process_html(content, source_name=filename)
                # Validate HTML processing result - try multiple fallback strategies
                if not processed_text or len(processed_text.strip()) == 0:
                    # Fallback 1: try basic extraction with BeautifulSoup
                    try:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(content, 'html.parser')
                        for tag in soup(["script", "style", "meta", "link", "nav", "header", "footer"]):
                            tag.decompose()
                        processed_text = soup.get_text(separator=' ', strip=True)
                        processed_text = re.sub(r'\s+', ' ', processed_text).strip()
                    except Exception as e:
                        pass
                
                # Fallback 2: if still empty, try regex-based extraction
                if not processed_text or len(processed_text.strip()) < 10:
                    # Remove HTML tags with regex
                    text = re.sub(r'<[^>]+>', '', content)
                    text = html.unescape(text)
                    text = re.sub(r'\s+', ' ', text).strip()
                    if text and len(text) > 10:
                        processed_text = text
            elif content_type == 'markdown':
                processed_text = self.process_markdown(content, source_name=filename)
            elif content_type == 'url':
                processed_text = self.scrape_url(content)
                if processed_text is None:
                    raise ValueError(f"Failed to scrape URL: {content}")
            else:  # 'text' or default
                processed_text = self.process_plain_text(content, source_name=filename)
            
            # Validate processed text
            if not processed_text or len(processed_text.strip()) == 0:
                return {
                    "success": False,
                    "error": "No content could be extracted from the input. Please check that your input contains readable text.",
                    "file_path": None,
                    "content_length": 0,
                    "paragraphs": 0,
                    "filename": None
                }
            
            # Ensure filename is safe
            safe_filename = re.sub(r'[^\w\s-]', '', filename).strip()
            safe_filename = re.sub(r'[-\s]+', '_', safe_filename)
            if not safe_filename:
                safe_filename = f"processed_{content_type}"
            
            # Add .txt extension if not present
            if not safe_filename.endswith('.txt'):
                safe_filename += '.txt'
            
            # Save to file
            output_path = output_dir / safe_filename
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(processed_text)
            
            # Count paragraphs - improved logic
            # First try splitting by double newlines
            paragraphs = [p.strip() for p in processed_text.split('\n\n') if p.strip()]
            
            # If no double newlines, try single newlines for substantial content
            if not paragraphs:
                paragraphs = [p.strip() for p in processed_text.split('\n') if p.strip() and len(p.strip()) > 10]
            
            # If still no paragraphs but we have content, count by sentences or minimum length blocks
            if not paragraphs and processed_text.strip():
                # Split by periods and count substantial sentences
                sentences = [s.strip() for s in processed_text.split('.') if s.strip() and len(s.strip()) > 10]
                if sentences:
                    # Group sentences into paragraphs (roughly 2-3 sentences per paragraph)
                    para_count = max(1, len(sentences) // 2)
                    paragraphs = ['dummy'] * para_count  # Just for counting
                else:
                    # Last resort: if we have any content, count as 1 paragraph
                    paragraphs = ['dummy'] if len(processed_text.strip()) > 10 else []
            
            # Ensure we have at least 1 paragraph if content exists
            para_count = len(paragraphs) if paragraphs else (1 if len(processed_text.strip()) > 10 else 0)
            
            return {
                "success": True,
                "file_path": str(output_path),
                "filename": safe_filename,
                "content_length": len(processed_text),
                "paragraphs": para_count
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_path": None,
                "content_length": 0,
                "paragraphs": 0,
                "filename": None
            }

