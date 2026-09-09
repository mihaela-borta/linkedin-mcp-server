import re
import argparse
import requests


def extract_speakers_from_html(html_content):
    """
    Extract speaker names and session URLs from HTML content using regex.
    Returns a list of tuples (name, session_url).
    """
    speakers = []

    # First try to find any links containing 'speaker' in the URL
    speaker_links = re.findall(
        r'<a[^>]*href="([^"]*speaker[^"]*)"[^>]*>(.*?)</a>',
        html_content,
        re.DOTALL | re.IGNORECASE,
    )

    for session_url, content in speaker_links:
        # Try different patterns to extract the name
        name_patterns = [
            r"<h[1-6][^>]*>(.*?)</h[1-6]>",  # Any heading
            r'<div[^>]*class="[^"]*name[^"]*"[^>]*>(.*?)</div>',  # Div with name class
            r'<span[^>]*class="[^"]*name[^"]*"[^>]*>(.*?)</span>',  # Span with name class
            r"<strong>(.*?)</strong>",  # Strong tag
            r"<b>(.*?)</b>",  # Bold tag
        ]

        name = None
        for pattern in name_patterns:
            name_match = re.search(pattern, content, re.IGNORECASE)
            if name_match:
                name = name_match.group(1).strip()
                break

        # If no name found in content, try to extract from URL
        if not name:
            # Try to extract name from URL (e.g., /speakers/john-doe/ -> John Doe)
            url_name = re.search(r"/speakers/([^/]+)/", session_url)
            if url_name:
                name = url_name.group(1).replace("-", " ").title()

        if name and session_url:
            # Clean up the extracted text
            name = name.strip()
            session_url = session_url.strip()

            # Avoid duplicates
            if (name, session_url) not in speakers:
                speakers.append((name, session_url))

    # If no speakers found, try alternative patterns
    if not speakers:
        # Try to find any div containing speaker information
        speaker_divs = re.findall(
            r'<div[^>]*class="[^"]*speaker[^"]*"[^>]*>(.*?)</div>',
            html_content,
            re.DOTALL | re.IGNORECASE,
        )

        for div_content in speaker_divs:
            # Look for links and names in the div
            link_match = re.search(r'href="([^"]*)"', div_content)
            name_match = re.search(r"<h[1-6][^>]*>(.*?)</h[1-6]>", div_content)

            if link_match and name_match:
                session_url = link_match.group(1).strip()
                name = name_match.group(1).strip()

                if name and session_url and (name, session_url) not in speakers:
                    speakers.append((name, session_url))

    return speakers


def debug_html_structure(html_content, max_chars=1000):
    """
    Debug function to show relevant parts of the HTML structure.
    """
    print("=== HTML STRUCTURE DEBUG ===")

    # Look for speakers__person links
    person_links = re.findall(
        r"<a[^>]*speakers__person[^>]*>.*?</a>", html_content, re.DOTALL | re.IGNORECASE
    )
    print(f"Found {len(person_links)} speakers__person links")

    # Look for any links that might contain speaker information
    all_links = re.findall(
        r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html_content, re.DOTALL | re.IGNORECASE
    )
    print(f"\nFound {len(all_links)} total links")

    # Analyze first 5 links in detail
    print("\nAnalyzing first 5 links:")
    for i, (url, content) in enumerate(all_links[:5]):
        print(f"\nLink {i + 1}:")
        print(f"URL: {url}")
        print(f"Content (truncated): {content[:200]}...")

        # Look for any class names in this link
        classes = re.findall(r'class="([^"]*)"', content, re.IGNORECASE)
        if classes:
            print(f"Classes found: {classes}")

        # Look for any headings in this link
        headings = re.findall(r"<h[1-6][^>]*>(.*?)</h[1-6]>", content, re.IGNORECASE)
        if headings:
            print(f"Headings found: {headings}")

    # Look for any h2 tags that might contain names
    all_h2s = re.findall(r"<h2[^>]*>(.*?)</h2>", html_content, re.IGNORECASE)
    print(f"\nFound {len(all_h2s)} total h2 tags")

    # Look for any divs with speaker-related classes
    speaker_divs = re.findall(
        r'<div[^>]*class="[^"]*speaker[^"]*"[^>]*>', html_content, re.IGNORECASE
    )
    print(f"\nFound {len(speaker_divs)} divs with speaker-related classes")

    # Look for any class names containing 'speaker'
    speaker_classes = re.findall(
        r'class="[^"]*speaker[^"]*"', html_content, re.IGNORECASE
    )
    print(f"\nFound {len(speaker_classes)} class names containing 'speaker'")
    print("First 3 speaker classes:", speaker_classes[:3])

    # Look for any links containing 'speaker' in the URL
    speaker_urls = [url for url, _ in all_links if "speaker" in url.lower()]
    print(f"\nFound {len(speaker_urls)} links containing 'speaker' in URL")
    print("First 3 speaker URLs:", speaker_urls[:3])

    return len(person_links), len(all_h2s), len(speaker_divs)


def html_to_csv(html_content, output_file="speakers.csv"):
    """
    Convert HTML speaker data to CSV format with semicolon delimiter.
    """
    speakers = extract_speakers_from_html(html_content)

    # Write to CSV file
    with open(output_file, "w", encoding="utf-8") as f:
        # Write header
        f.write("name;url\n")

        # Write speaker data
        for name, speaker_url in speakers:
            # Escape semicolons in data if present
            name_escaped = name.replace(";", "\\;")
            speaker_url_escaped = speaker_url.replace(";", "\\;")
            f.write(f"{name_escaped};{speaker_url_escaped}\n")

    return speakers


def download_html_from_url(url):
    """
    Download HTML content from a URL.
    Returns the HTML content as a string.
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.text
    except requests.RequestException as e:
        print(f"Error downloading from {url}: {e}")
        return None


# Example usage
if __name__ == "__main__":
    # Sample HTML (you can replace this with your actual HTML content)
    # sample_html = """
    # <div class="site__centered">
    #     <div class="speakers__layout">
    #         <div class="speakers__item">
    #             <a href="https://groundswellag.com/speakers/matthew-adams/" class="speakers__person">
    #                 <div class="speakers__photo" style="background-image:url(https://groundswellag.com/wp-content/uploads/2021/05/Matthew-Adams-1-e1747994758923-295x305.jpg)"></div>
    #                 <div class="speakers__info">
    #                     <div>
    #                         <h2 class="speakers__name">Matthew Adams</h2>
    #                         <span class="speakers__post">2025</span>
    #                         <div class="speakers__icon"></div>
    #                     </div>
    #                 </div>
    #             </a>
    #         </div>
    #     </div>
    # </div>
    # """

    # # Method 1: Test with sample
    # speakers = html_to_csv(sample_html, "speakers_output.csv")
    # print(f"Extracted {len(speakers)} speakers to speakers_output.csv")

    parser = argparse.ArgumentParser(
        description="Extract speakers from website URL and convert to CSV"
    )
    parser.add_argument(
        "-u",
        "--url",
        default="https://groundswellag.com/2025-speakers/",
        help="URL to fetch speakers from (default: https://groundswellag.com/2025-speakers/)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="data/groundswellag_speaker_webpages.csv",
        help="Output CSV file path (default: data/groundswellag_speaker_webpages.csv)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output to analyze HTML structure",
    )

    args = parser.parse_args()

    print(f"Downloading HTML from {args.url}...")
    html_content = download_html_from_url(args.url)

    if html_content is None:
        print("Failed to download HTML content. Exiting.")
        exit(1)

    # Optionally save the downloaded HTML to a file
    html_filename = "data/groundswellag-2025-speakers.html"
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML content saved to {html_filename}")

    if args.debug:
        print("=== DEBUGGING HTML CONTENT ===")
        debug_html_structure(html_content)

    speakers = html_to_csv(html_content, args.output)
    print(
        f"Processed HTML from {args.url}: {len(speakers)} speakers extracted to {args.output}"
    )

    if not speakers:
        print(
            "\nNo speakers found. The HTML structure might be different than expected."
        )
        if args.debug:
            print("Check the debug output above to see what was found in the content.")
        else:
            print("Run with --debug to see what was found in the content.")
