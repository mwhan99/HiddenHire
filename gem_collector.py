import requests

# Test Gem with Avoca
identifier = "avoca"

url = f"https://jobs.gem.com/{identifier}"

response = requests.get(url)

print("Status Code:", response.status_code)
print("Final URL:", response.url)
print("Content length:", len(response.text))
print("\nFirst 500 characters:")
print(response.text[:500])

# Search the HTML for useful job-related content

html = response.text

keywords = [
    "jobPostings",
    "job_postings",
    "jobs",
    "openings",
    "positions",
    "Avoca"
]

print("\nKeyword check:")

for keyword in keywords:
    print(keyword, ":", keyword.lower() in html.lower())

import re

print("\nPossible API URLs:")

urls = re.findall(r'https?://[^"\'\s<>]+', html)

for u in urls:
    if "api" in u.lower() or "job" in u.lower():
        print(u[:300])

import re

print("\nSearching page for Gem data...")

patterns = [
    r'8480b8e7-[a-zA-Z0-9\-]+',
    r'job_board[^<]{0,200}',
    r'jobBoard[^<]{0,200}',
]

for pattern in patterns:
    matches = re.findall(pattern, html, re.IGNORECASE)
    print(f"\nPattern: {pattern}")
    print(matches[:10])

board_id = "8480b8e7-0274-4b78-a696-5a1b17124aa8"

position = html.find(board_id)

print("\nContext around Gem board ID:")
print(html[max(0, position - 1000):position + 1000])

from bs4 import BeautifulSoup

soup = BeautifulSoup(html, "html.parser")

links = soup.find_all("a", href=True)

print("\nTotal links:", len(links))

print("\nPossible job links:")
for link in links:
    href = link.get("href", "")
    text = link.get_text(" ", strip=True)

    if text:
        print(text[:100], "|", href)