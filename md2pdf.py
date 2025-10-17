#!/usr/bin/env python3

import os
import sys
import re
import subprocess
import tempfile
import hashlib
from pathlib import Path

# Check and install required packages
try:
    import markdown
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "markdown", "playwright", "pygments"])
    print("Installing playwright browsers...")
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    import markdown
    from playwright.sync_api import sync_playwright

# HTML template with CSS for nice formatting and Mermaid support
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ 
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }}
        }});
    </script>
    <style>
        @page {{
            size: A4;
            margin: 1.5cm;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 100%;
            padding: 20px;
            margin: 0;
        }}
        h1 {{
            font-size: 24pt;
            color: #333;
            border-bottom: 2px solid #ddd;
            padding-bottom: 0.3cm;
            margin-top: 0;
        }}
        h2 {{
            font-size: 18pt;
            color: #444;
            margin-top: 1.5em;
            border-bottom: 1px solid #eee;
            padding-bottom: 0.2cm;
        }}
        h3 {{
            font-size: 14pt;
            color: #555;
            margin-top: 1.2em;
        }}
        h4, h5, h6 {{
            color: #666;
            margin-top: 1em;
        }}
        p {{
            text-align: justify;
            margin: 1em 0;
        }}
        code {{
            background-color: #f5f5f5;
            border-radius: 3px;
            font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 85%;
            padding: 0.2em 0.4em;
        }}
        pre {{
            background-color: #f5f5f5;
            border: 1px solid #ddd;
            border-radius: 3px;
            padding: 1em;
            overflow-x: auto;
            margin: 1em 0;
            page-break-inside: avoid;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        blockquote {{
            border-left: 4px solid #ddd;
            padding-left: 1em;
            color: #666;
            margin: 1em 0 1em 1em;
        }}
        ul, ol {{
            margin: 1em 0;
            padding-left: 2em;
        }}
        li {{
            margin-bottom: 0.5em;
        }}
        li > ul, li > ol {{
            margin: 0.5em 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
            page-break-inside: avoid;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        a {{
            color: #0366d6;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        hr {{
            border: 0;
            border-top: 1px solid #ddd;
            margin: 2em 0;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
        /* Mermaid diagram styling */
        .mermaid {{
            text-align: center;
            margin: 2em 0;
            page-break-inside: avoid;
        }}
        .mermaid svg {{
            max-width: 100%;
            height: auto;
        }}
        /* Code Highlighting */
        .codehilite .hll {{ background-color: #ffffcc }}
        .codehilite .c {{ color: #408080; font-style: italic }}
        .codehilite .k {{ color: #008000; font-weight: bold }}
        .codehilite .o {{ color: #666666 }}
        .codehilite .s {{ color: #BA2121 }}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>
"""

def extract_mermaid_blocks(md_content):
    """
    Extract Mermaid code blocks from markdown and replace with HTML div placeholders
    Returns: (modified_markdown, list_of_mermaid_codes)
    """
    mermaid_pattern = re.compile(r'```mermaid\s*\n(.*?)\n```', re.DOTALL)
    mermaid_blocks = []
    
    def replace_mermaid(match):
        mermaid_code = match.group(1).strip()
        mermaid_blocks.append(mermaid_code)
        # Create a unique placeholder that will be replaced with rendered diagram
        placeholder = f'<div class="mermaid">\n{mermaid_code}\n</div>'
        return placeholder
    
    modified_content = mermaid_pattern.sub(replace_mermaid, md_content)
    return modified_content, mermaid_blocks


def create_pdf_from_html(html_content, output_path):
    """
    Convert HTML to PDF using Playwright with Chromium
    This ensures Mermaid diagrams are properly rendered
    """
    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Set content and wait for Mermaid to render
            page.set_content(html_content)
            
            # Wait for Mermaid diagrams to render
            # Check if there are any mermaid elements
            try:
                page.wait_for_selector('.mermaid svg', timeout=10000)
                # Give extra time for all diagrams to render
                page.wait_for_timeout(2000)
            except:
                # No mermaid diagrams or they rendered quickly
                page.wait_for_timeout(500)
            
            # Generate PDF with proper settings
            page.pdf(
                path=output_path,
                format='A4',
                margin={
                    'top': '1.5cm',
                    'right': '1.5cm',
                    'bottom': '1.5cm',
                    'left': '1.5cm'
                },
                print_background=True,
                prefer_css_page_size=True
            )
            
            browser.close()
            return True
            
    except Exception as e:
        print(f"❌ Error creating PDF: {str(e)}")
        return False

def convert_md_to_pdf(md_file_path, output_dir):
    """
    Convert markdown to PDF with proper formatting and Mermaid diagram rendering
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Output PDF path
        base_name = os.path.splitext(os.path.basename(md_file_path))[0]
        pdf_path = os.path.join(output_dir, base_name + ".pdf")
        
        # Read markdown content
        with open(md_file_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        
        # Extract and process Mermaid blocks
        md_content, mermaid_blocks = extract_mermaid_blocks(md_content)
        
        if mermaid_blocks:
            print(f"  Found {len(mermaid_blocks)} Mermaid diagram(s) in {os.path.basename(md_file_path)}")
        
        # Convert to HTML using Python Markdown
        extensions = [
            'markdown.extensions.tables',
            'markdown.extensions.fenced_code',
            'markdown.extensions.codehilite',
            'markdown.extensions.toc',
            'markdown.extensions.nl2br',
            'markdown.extensions.sane_lists',
            'markdown.extensions.smarty',
            'markdown.extensions.attr_list'
        ]
        
        html_body = markdown.markdown(md_content, extensions=extensions)
        
        # Render with template
        html = HTML_TEMPLATE.format(
            title=base_name,
            content=html_body
        )
        
        # Convert to PDF
        result = create_pdf_from_html(html, pdf_path)
        if result:
            print(f"✓ Converted {os.path.basename(md_file_path)} to {pdf_path}")
            return True
        return False
        
    except Exception as e:
        print(f"✗ Error converting {md_file_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def scan_and_convert(folder_path, output_dir):
    """
    Scan for markdown files in current directory (non-recursive) and convert them to PDFs
    """
    successful = 0
    failed = 0
    md_files = []
    
    # Find all markdown files in current directory only (not recursive)
    for path in Path(folder_path).glob('*.md'):
        md_files.append(str(path))
    
    if not md_files:
        print(f"No markdown files found in {folder_path}")
        return 0, 0
    
    print(f"Found {len(md_files)} markdown file(s) in {folder_path}\n")
    
    # Convert all found files
    for md_file_path in md_files:
        print(f"\nProcessing: {os.path.basename(md_file_path)}")
        if convert_md_to_pdf(md_file_path, output_dir):
            successful += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Summary: {successful} file(s) converted successfully, {failed} file(s) failed")
    print(f"{'='*60}")
    return successful, failed

if __name__ == "__main__":
    # Current directory to scan
    script_dir = os.path.dirname(os.path.abspath(__file__))
    current_dir = script_dir
    
    # Output directory for PDFs
    output_dir = os.path.join(script_dir, "pdfs")
    
    print("="*60)
    print("Markdown to PDF Converter with Mermaid Support")
    print("="*60)
    print(f"Scanning for markdown files in: {current_dir}")
    print(f"Saving PDFs to: {output_dir}")
    print("="*60 + "\n")
    
    scan_and_convert(current_dir, output_dir)
