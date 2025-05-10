import os
import time
import json
import requests
from tqdm import tqdm
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def fetch_article_urls(query, max_results=5):
    with DDGS() as ddgs:
        try:
            response = ddgs.text(
                query,
                timelimit="d",
                max_results=max_results
            )
        except RatelimitException as e:
            print("DDGS Rate Limit Error")
            pass
        except Exception as e:
            print(f"Unexpected error in DDGS: {e}")
    
    return [r["href"] for r in response]

    
def extract_content_bs4(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return {"url": url, "error": f"Status code: {resp.status_code}"}
        
        soup = BeautifulSoup(resp.text, "html.parser")

        # Try to get the title
        title = soup.title.string.strip() if soup.title else ""

        # Attempt to extract main article content heuristically
        paragraphs = soup.find_all("p")
        content = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text()) > 40)

        return {
            "url": url,
            "title": title,
            "text": content
        }
    except Exception as e:
        return {"url": url, "error": str(e)}
    


def main():
    query = "technology"
    urls = fetch_article_urls(query, max_results=10)

    articles = []
    for url in tqdm(urls, desc="Scraping URLs"):
        article = extract_content_bs4(url)
        articles.append(article)
        time.sleep(1)  # rate limit to avoid blocks
    
    os.makedirs("data/", exist_ok=True)
    with open("data/scraped_articles.json", "w") as f:
        json.dump(articles, f, indent=2)
    

if __name__ == "__main__":
    main()
