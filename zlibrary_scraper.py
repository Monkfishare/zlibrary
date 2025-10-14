import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
from urllib.parse import urljoin, urlparse
import os

def fetch_working_zlib_links(url="https://zlibrary.st/new-z-library-official-website-links"):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        working_section = None
        headings = soup.find_all(['h2'])

        for heading in headings:
            if 'working' in heading.get_text().lower() and 'z-library' in heading.get_text().lower():
                working_section = heading
                break
        if not working_section:
            print("Could not find the working links section")
            return []
        current_element = working_section.find_next_sibling()
        working_links = []
        
        while current_element:
            if current_element.name == 'ul':
                list_items = current_element.find_all('li')
                for item in list_items:
                    text = item.get_text().lower()
                    exclusion_words = ['no ', 'not ', 'ano', 'direct', 'avoid', 'spam']
                    if any(word in text for word in exclusion_words):
                        continue
                    links = item.find_all('a')
                    for link in links:
                        href = link.get('href')
                        if href and href.startswith('http'):
                            href = href.rstrip('/')
                            working_links.append({
                                'url': href,
                                'description': item.get_text().strip()
                            })
                    url_pattern = r'https?://[^\s\(\)]+'
                    urls_in_text = re.findall(url_pattern, text)
                    for url_match in urls_in_text:
                        clean_url = re.sub(r'[^\w\-\./:]+$', '', url_match)
                        clean_url = clean_url.rstrip('/')
                        if clean_url not in [link['url'] for link in working_links]:
                            working_links.append({
                                'url': clean_url,
                                'description': item.get_text().strip()
                            })
                break
            current_element = current_element.find_next_sibling()
        
        filtered_links = []
        seen_urls = set()
        for link in working_links:
            url = link['url']
            if url in seen_urls:
                continue
            filtered_links.append(link)
            seen_urls.add(url)
        return filtered_links
        
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return []
    except Exception as e:
        print(f"Error parsing the webpage: {e}")
        return []

def save_links_to_json(links, filename="working_zlib_links.json"):
    try:
        data = {
            "generated_date": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
            "source": "https://zlibrary.st/new-z-library-official-website-links",
            "total_links": len(links),
            "links": links
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Links saved to {filename}")
    except Exception as e:
        print(f"Error saving to JSON: {e}")

def save_readme(links, filename="README.md"):
    if not links:
        print(f"Skipping README.md update - no links found")
        if os.path.exists(filename):
            print(f"Keeping existing {filename} file")
        return
    
    try:
        current_date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        source_url = "https://zlibrary.st/new-z-library-official-website-links"
        readme_content = f"""# Z-Library Working Links

"""
        for i, link in enumerate(links, 1):
            readme_content += f"{i}. {link['url']}\n"
        
        readme_content += f"""
---
**Last Updated:** {current_date}  
**Source:** [zlibrary.st]({source_url})

"""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"README.md updated with {len(links)} links")
    except Exception as e:
        print(f"Error saving README.md: {e}")

def display_links(links):
    if not links:
        print("No working links found at this time.")
        return
    print(f"Found {len(links)} working Z-Library links:\n")
    print("-" * 70)
    for i, link in enumerate(links, 1):
        print(f"{i}. {link['url']}")
        print(f"   Status: {link['description']}")
        print("-" * 70)

if __name__ == "__main__":
    print("Fetching working Z-Library links...")
    print("=" * 50)
    working_links = fetch_working_zlib_links()
    display_links(working_links)
    
    if working_links:
        save_links_to_json(working_links)
        save_readme(working_links)
        print("\nClean URL list:")
        for link in working_links:
            print(link['url'])
        print(f"\nProcess completed. Generated {len(working_links)} working links.")
    else:
        print("\nProcess completed. No links to save.")