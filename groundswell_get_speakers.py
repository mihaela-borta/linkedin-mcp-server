import re


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
        f.write("name;session\n")

        # Write speaker data
        for name, session_url in speakers:
            # Escape semicolons in data if present
            name_escaped = name.replace(";", "\\;")
            session_escaped = session_url.replace(";", "\\;")
            f.write(f"{name_escaped};{session_escaped}\n")

    return speakers


def html_string_to_csv_string(html_content):
    """
    Convert HTML speaker data to CSV string format.
    """
    speakers = extract_speakers_from_html(html_content)

    lines = ["name;session"]
    for name, session_url in speakers:
        # Escape semicolons in data if present
        name_escaped = name.replace(";", "\\;")
        session_escaped = session_url.replace(";", "\\;")
        lines.append(f"{name_escaped};{session_escaped}")

    return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    # Sample HTML (you can replace this with your actual HTML content)
    sample_html = """
    <div class="site__centered">
        <div class="speakers__layout">
            <div class="speakers__item">
                <a href="https://groundswellag.com/speakers/matthew-adams/" class="speakers__person">
                    <div class="speakers__photo" style="background-image:url(https://groundswellag.com/wp-content/uploads/2021/05/Matthew-Adams-1-e1747994758923-295x305.jpg)"></div>
                    <div class="speakers__info">
                        <div>
                            <h2 class="speakers__name">Matthew Adams</h2>
                            <span class="speakers__post">2025</span>
                            <div class="speakers__icon"></div>
                        </div>
                    </div>
                </a>
            </div>
        </div>
    </div>
    """

    # Method 1: Save to file
    speakers = html_to_csv(sample_html, "speakers_output.csv")
    print(f"Extracted {len(speakers)} speakers to speakers_output.csv")

    # Method 2: Get as string
    csv_string = html_string_to_csv_string(sample_html)
    print("\nCSV Output:")
    print(csv_string)

    # Method 3: Read from file with debugging
    try:
        with open("data/groundswellag-2025-speakers.html", "r", encoding="utf-8") as f:
            html_content = f.read()

        print("=== DEBUGGING HTML FILE ===")
        debug_html_structure(html_content)

        speakers = html_to_csv(html_content, "data/groundswellag-2025-speakers.csv")
        print(f"\nProcessed HTML file: {len(speakers)} speakers extracted")

        if not speakers:
            print(
                "\nNo speakers found. The HTML structure might be different than expected."
            )
            print("Check the debug output above to see what was found in the file.")

    except FileNotFoundError:
        print(
            "\nTo process from file, save your HTML as 'groundswellag-2025-speakers.html' in the same directory"
        )
