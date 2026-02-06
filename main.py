import requests
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser

USER_AGENT = "Sensebot"


robots_cache = {}


def can_crawl(url):
    url_data = urlparse(url)
    if url_data.netloc in robots_cache:
        parser = robots_cache[url_data.netloc]
    else:
        robots_url = urlunparse(url_data._replace(path="/robots.txt"))
        headers = requests.head(robots_url, headers={"User-Agent": USER_AGENT})
        if (
            headers.status_code == 200
            and headers.headers.get("content-type") == "text/plain"
        ):
            parser = RobotFileParser(robots_url)
            parser.read()
            robots_cache[url_data.netloc] = parser
        else:
            parser = True
            robots_cache[url_data.netloc] = True
    if parser == True:
        return True
    else:
        return parser.can_fetch(USER_AGENT, url)

url = "https://google.com"
response = requests.get(url, headers={"User-Agent": USER_AGENT})

if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    for link in soup.find_all("a"):
        url = urlparse(urljoin(url, link.get("href")))
        if url.path != None:
            url = url._replace(path=url.path.rstrip("/"))
        url = urlunparse(url._replace(query=""))
        if can_crawl(url):
            print("✔️  " + url)
        else:
            print("✖️  " + url)
else:
    print(f"error: {response.status_code}")
