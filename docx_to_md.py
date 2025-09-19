import os
import sys

try:
    import pypandoc
except ImportError:
    print("Error: 'pypandoc' library not found. Please install it using 'pip install pypandoc'.")
    sys.exit(1)

def ensure_pandoc_installed():
    """
    Checks if pandoc is installed on the system.
    If not, prints an error message and exits.
    """
    try:
        pypandoc.get_pandoc_version()
    except OSError:
        print("Error: 'pandoc' is not installed or not in your system's PATH.")
        print("Please install pandoc from https://pandoc.org/installing.html")
        sys.exit(1)

def convert_docx_to_markdown(directory='.'):
    """
    Scans the specified directory for .docx files and converts them to Markdown.

    The output Markdown files will be saved in the same directory with the same
    base name.
    """
    print(f"Scanning for .docx files in '{os.path.abspath(directory)}'...")
    
    files_found = False
    for filename in os.listdir(directory):
        if filename.endswith(".docx"):
            files_found = True
            docx_path = os.path.join(directory, filename)
            base_name = os.path.splitext(filename)[0]
            # md_path = os.path.join(base_path, f"{base_name}.md")
            # Use the docx file path as the current path where this file is located
            md_path = os.path.join(directory, f"{base_name}.md")
            
            print(f"Converting '{docx_path}' to '{md_path}'...")
            
            try:
                # Using 'gfm' (GitHub-Flavored Markdown) for better table/strikethrough support.
                # '--wrap=none' helps preserve line breaks better.
                extra_args = ['--wrap=none']
                pypandoc.convert_file(docx_path, 'gfm', outputfile=md_path, extra_args=extra_args)
                print(f"Successfully converted '{filename}'.")
            except Exception as e:
                print(f"Error converting '{filename}': {e}")

    if not files_found:
        print("No .docx files found in the current directory.")

if __name__ == "__main__":
    ensure_pandoc_installed()
    # The script will convert .docx files located in its own directory.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Target directory for conversion: {script_dir}")
    convert_docx_to_markdown(script_dir)
