#!/usr/bin/env python3

import os
import sys
import base64
import subprocess
from pathlib import Path

try:
    import markdown
    import jinja2
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "markdown", "jinja2", "pygments"])
    import markdown
    import jinja2

# HTML template with CSS for nice formatting
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        @page {
            size: A4;
            margin: 1.5cm;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 100%;
            padding: 0;
            margin: 0;
        }
        h1 {
            font-size: 24pt;
            color: #333;
            border-bottom: 1px solid #ddd;
            padding-bottom: 0.3cm;
        }
        h2 {
            font-size: 18pt;
            color: #444;
            margin-top: 1.5em;
            border-bottom: 1px solid #eee;
            padding-bottom: 0.2cm;
        }
        h3 {
            font-size: 14pt;
            color: #555;
        }
        h4, h5, h6 {
            color: #666;
        }
        p {
            text-align: justify;
            margin: 1em 0;
        }
        code {
            background-color: #f5f5f5;
            border-radius: 3px;
            font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 85%;
            padding: 0.2em 0.4em;
        }
        pre {
            background-color: #f5f5f5;
            border: 1px solid #ddd;
            border-radius: 3px;
            padding: 1em;
            overflow-x: auto;
            margin: 1em 0;
        }
        pre code {
            background-color: transparent;
            padding: 0;
        }
        blockquote {
            border-left: 4px solid #ddd;
            padding-left: 1em;
            color: #666;
            margin: 1em 0 1em 1em;
        }
        ul, ol {
            margin: 1em 0;
            padding-left: 2em;
        }
        li {
            margin-bottom: 0.5em;
        }
        li > ul, li > ol {
            margin: 0.5em 0;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        a {
            color: #0366d6;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        hr {
            border: 0;
            border-top: 1px solid #ddd;
            margin: 2em 0;
        }
        img {
            max-width: 100%;
            height: auto;
        }
        .toc {
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 1em;
            margin: 1em 0;
        }
        .toc ul {
            margin: 0.5em 0;
        }
        .toc-title {
            font-weight: bold;
            margin-bottom: 0.5em;
        }
        /* Code Highlighting */
        .codehilite .hll { background-color: #ffffcc }
        .codehilite .c { color: #408080; font-style: italic } /* Comment */
        .codehilite .k { color: #008000; font-weight: bold } /* Keyword */
        .codehilite .o { color: #666666 } /* Operator */
        .codehilite .ch { color: #408080; font-style: italic } /* Comment.Hashbang */
        .codehilite .cm { color: #408080; font-style: italic } /* Comment.Multiline */
        .codehilite .cp { color: #BC7A00 } /* Comment.Preproc */
        .codehilite .cpf { color: #408080; font-style: italic } /* Comment.PreprocFile */
        .codehilite .c1 { color: #408080; font-style: italic } /* Comment.Single */
        .codehilite .cs { color: #408080; font-style: italic } /* Comment.Special */
        .codehilite .gd { color: #A00000 } /* Generic.Deleted */
        .codehilite .ge { font-style: italic } /* Generic.Emph */
        .codehilite .gr { color: #FF0000 } /* Generic.Error */
        .codehilite .gh { color: #000080; font-weight: bold } /* Generic.Heading */
        .codehilite .gi { color: #00A000 } /* Generic.Inserted */
        .codehilite .go { color: #888888 } /* Generic.Output */
        .codehilite .gp { color: #000080; font-weight: bold } /* Generic.Prompt */
        .codehilite .gs { font-weight: bold } /* Generic.Strong */
        .codehilite .gu { color: #800080; font-weight: bold } /* Generic.Subheading */
        .codehilite .gt { color: #0044DD } /* Generic.Traceback */
        .codehilite .kc { color: #008000; font-weight: bold } /* Keyword.Constant */
        .codehilite .kd { color: #008000; font-weight: bold } /* Keyword.Declaration */
        .codehilite .kn { color: #008000; font-weight: bold } /* Keyword.Namespace */
        .codehilite .kp { color: #008000 } /* Keyword.Pseudo */
        .codehilite .kr { color: #008000; font-weight: bold } /* Keyword.Reserved */
        .codehilite .kt { color: #B00040 } /* Keyword.Type */
        .codehilite .m { color: #666666 } /* Literal.Number */
        .codehilite .s { color: #BA2121 } /* Literal.String */
    </style>
</head>
<body>
    <div class="container">
        {{ content }}
    </div>
</body>
</html>
"""

def create_pdf_from_html(html_content, output_path):
    """
    Convert HTML to PDF using Chrome or Firefox in headless mode
    """
    # First, try Chrome
    try:
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/usr/bin/google-chrome",
            "/usr/bin/chromium",
        ]
        chrome_path = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_path = path
                break
                
        if chrome_path:
            cmd = [
                chrome_path,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--print-to-pdf=" + output_path,
                "data:text/html;base64," + base64.b64encode(html_content.encode()).decode()
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✓ Created PDF using Chrome: {output_path}")
            return True
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print(f"Chrome conversion failed: {str(e)}")
    
    # Try using Firefox if Chrome failed
    try:
        if shutil.which("firefox"):
            with open("temp.html", "wb") as f:
                f.write(html_content.encode('utf-8'))
                
            cmd = [
                "firefox",
                "--headless",
                "--print-to-pdf=" + output_path,
                os.path.abspath("temp.html")
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            os.remove("temp.html")
            print(f"✓ Created PDF using Firefox: {output_path}")
            return True
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print(f"Firefox conversion failed: {str(e)}")
        os.remove("temp.html") if os.path.exists("temp.html") else None
    
    print("❌ Failed to convert HTML to PDF. Please install Chrome or Firefox.")
    return False

def convert_md_to_pdf(md_file_path, output_dir):
    """
    Convert markdown to PDF with proper formatting
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
        
        # Convert to HTML using Python Markdown
        extensions = [
            'markdown.extensions.tables',
            'markdown.extensions.fenced_code',
            'markdown.extensions.codehilite',
            'markdown.extensions.toc',
            'markdown.extensions.nl2br',
            'markdown.extensions.sane_lists',
            'markdown.extensions.smarty'
        ]
        
        html_body = markdown.markdown(md_content, extensions=extensions)
        
        # Render with template
        template = jinja2.Template(HTML_TEMPLATE)
        html = template.render(
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
        return False

def scan_and_convert(folder_path, output_dir):
    """
    Recursively scan for markdown files and convert them to PDFs
    """
    successful = 0
    failed = 0
    md_files = []
    
    # Find all markdown files
    for path in Path(folder_path).rglob('*.md'):
        md_files.append(str(path))
    
    print(f"Found {len(md_files)} markdown files in {folder_path}")
    
    # Convert all found files
    for md_file_path in md_files:
        if convert_md_to_pdf(md_file_path, output_dir):
            successful += 1
        else:
            failed += 1
    
    print(f"\nSummary: {successful} files converted successfully, {failed} files failed")
    return successful, failed

if __name__ == "__main__":
    # Top level directory to scan
    script_dir = os.path.dirname(os.path.abspath(__file__))
    top_level_dir = os.path.abspath(os.path.join(script_dir, '../..'))
    
    output_dir = script_dir
    
    print(f"Scanning for markdown files in: {top_level_dir}")
    print(f"Saving PDFs to: {output_dir}\n")
    
    scan_and_convert(top_level_dir, output_dir)
