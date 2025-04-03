import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from datetime import datetime
import os
import concurrent.futures

def check_link_status(url, timeout=10):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except Exception:
        return False

def verify_links(links, max_workers=5):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(check_link_status, links))
    return [{"Link": link, "Verified Status": "Working" if status else "Not Working"} 
            for link, status in zip(links, results)]

def scrape_zlibrary_links(url="https://zlibrary.st/new-z-library-official-website-links", verify=True):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    one_month_ago = datetime.now().replace(month=datetime.now().month-1)
    links = []
    dates = []
    for li in soup.find('div', class_='entry-content').find_all('li'):
        text = li.get_text()
        url_match = re.search(r'https?://[^\s)]+', text)
        if url_match and "Working" in text:
            link = url_match.group(0)
            date_match = re.search(r'Working\s+([A-Za-z]+\s+\d{4})', text)
            date = date_match.group(1) if date_match else "Unknown"
            date_obj = datetime.strptime(date, "%B %Y") if date_match else None
            if date_obj and date_obj < one_month_ago:
                continue
            links.append(link)
            dates.append(date)
    df = pd.DataFrame({"Link": links, "Last Checked": dates})
    if verify and not df.empty:
        verified = pd.DataFrame(verify_links(links))
        df = pd.merge(df, verified, on="Link")
        df = df[df["Verified Status"] == "Working"]
    return df

def generate_markdown_table(df):
    if df.empty:
        return "No working links found in the last 30 days."
    markdown = "# Z-Library Working Links\n\n"
    markdown += f"*Last updated: {datetime.now().strftime('%Y-%m-%d')}*\n\n"
    markdown += "| Link | Status | Last Checked |\n|------|--------|-------------|\n"
    for _, row in df.iterrows():
        markdown += f"| [{row['Link']}]({row['Link']}) | ✅ Working | {row['Last Checked']} |\n"
    markdown += "\n**Note:** Data is sourced from [zlibrary.st](https://zlibrary.st/new-z-library-official-website-links) and verified by direct connection tests.\n"    
    return markdown

def main():
    df = scrape_zlibrary_links()
    markdown = generate_markdown_table(df)
    os.makedirs("output", exist_ok=True)
    df.to_csv("output/zlibrary_links.csv", index=False)
    with open("output/zlibrary_links.md", "w") as f:
        f.write(markdown)
    with open("README.md", "w") as f:
        f.write(markdown)

if __name__ == "__main__":
    main()