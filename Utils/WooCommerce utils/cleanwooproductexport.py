###############################################################################################################################
# script to cleanup the exported product pages from woocommerce
# ✅ Uses the current working directory (no need to specify a folder).
# ✅ Renames old .txt files to .old before cleaning, if a backup doesn’t already exist.
# ✅ Removes the last remaining garbage, including:

# .orgLoading...
# WooFunnels UI elements
# UpdraftPlus backup references
# LSCache purge logs
# WordPress plugin notifications
# Extra JavaScript variables ✅ Keeps SKU, Price, and Product URL intact.
# ✅ Collapses multiple blank lines and removes stray CSS/JS content.
###############################################################################################################################

import os
import re
import html

def clean_text(content):
    """
    Cleans the text by removing HTML, CSS, JavaScript, and garbage content.
    Preserves Product URL, SKU, and Price.
    """

    # 1. Remove all HTML tags
    content = re.sub(r'<[^>]+>', '', content)

    # 2. Decode HTML entities (&amp; -> &, &nbsp; -> space)
    content = html.unescape(content)

    # 3. Remove inline JavaScript and CSS
    content = re.sub(r'<script.*?>.*?</script>', '', content, flags=re.DOTALL)
    content = re.sub(r'<style.*?>.*?</style>', '', content, flags=re.DOTALL)

    # 4. Keep "Product URL:" lines intact
    product_url_pattern = r"(Product URL:\s*https?://[^\s]+)"
    urls = re.findall(product_url_pattern, content)  # Extract valid URLs
    content = re.sub(product_url_pattern, '', content)  # Temporarily remove URLs

    # 5. Remove known garbage content (WooCommerce, WordPress UI junk, etc.)
    garbage_patterns = [
        r"TXT Product Download .* WordPress",  # WooCommerce Page Title
        r"Hostinger.*?AI Content Creator",  # Hostinger junk
        r"window\..*?;",  # JavaScript variables
        r"document\.body.*?;",  # JS-based UI handling
        r"wp-admin.*?",  # WordPress admin panel
        r"var ajaxurl = .*?",  # WordPress AJAX calls
        r"#adminmenu.*?",  # Admin menu references
        r"function .*?\(.*?\).*?\{.*?\}",  # Any JavaScript functions
        r"/\*.*?\*/",  # CSS comments
        r"\{.*?\}",  # Standalone CSS blocks
        r"\@media.*?\{.*?\}",  # Media queries
        r"body\..*?\{.*?\}",  # WordPress body styling
        r"\w+\s*\=\s*[\"'].*?[\"']",  # Random assignments from JS
        r"UpdraftPlus.*?Backup / Herstellen",  # UpdraftPlus backup plugin logs
        r"bwf-notice.*?",  # WooFunnels garbage
        r"bwf-message-content.*?",  # WooFunnels UI messages
        r"bwf-message-action.*?",  # WooFunnels button actions
        r"bwf-logo-wrapper.*?",  # WooFunnels logo section
        r"bwf-notice.notice.notice-success",  # WooFunnels notice
        r"\.orgLoading\.\.\.",  # Miscellaneous unwanted text
        r"Purge All.*?Gravatar Cache",  # LSCache cleanup references
        r"ManageSettings.*?Image Optimization",  # Miscellaneous WordPress settings references
        r"Hello, .*?Logout",  # WordPress user UI text
        r"window\.mailpoet.*?",  # MailPoet form garbage
        r"wpforms-menu-new.*?",  # WPForms UI elements
        r"woocommerce-site-visibility-badge.*?",  # WooCommerce UI notices
        r"woocommerce_page_txt-product-download.*?",  # WooCommerce junk references
        r"window\.locale.*?",  # Locale data garbage
        r"window\.bwf.*?",  # FunnelKit garbage
        r"\s*\.[a-zA-Z0-9_-]+ \{.*?\}",  # Any CSS class definitions
        r"\s*\/\*.*?\*\/",  # Block comments
        r"\s*//.*",  # Single-line comments
        r"Migreer / kloon.*?Profiel bewerkenUitloggen",  # Remove last garbage chunk
        r"notice, .*?upstroke",  # Unwanted WordPress notices
        r"\bnotice.notice-success\b",  # Remove empty notices
    ]

    for pattern in garbage_patterns:
        content = re.sub(pattern, '', content, flags=re.DOTALL)

    # 6. Restore the "Product URL:" lines back into the content
    if urls:
        content += "\n\n" + "\n".join(urls)

    # 7. Remove excessive blank lines and trim whitespace
    content = re.sub(r'\n\s*\n+', '\n\n', content.strip())

    return content


def clean_text_file(input_path, output_path):
    """
    Reads a .txt file, cleans it, and writes it to a new file.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    cleaned_content = clean_text(content)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)


def main():
    """
    Cleans all .txt files in the current directory.
    Old versions of files are renamed to .old if they don't already exist.
    """
    current_directory = os.getcwd()  # Use the current directory

    for filename in os.listdir(current_directory):
        if filename.lower().endswith(".txt"):
            file_path = os.path.join(current_directory, filename)

            # Create backup file (.old) if it doesn't exist
            old_file_path = file_path + ".old"
            if not os.path.exists(old_file_path):
                os.rename(file_path, old_file_path)

            # Define the cleaned file path
            cleaned_file_path = file_path  # Overwrite with cleaned version

            # Clean and save the new file
            clean_text_file(old_file_path, cleaned_file_path)

            print(f"✅ Cleaned: {filename}")

    print("\n✅ All .txt files have been cleaned and backed up as .old!")


if __name__ == "__main__":
    main()
