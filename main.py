import json
import requests
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from usp.tree import sitemap_tree_for_homepage, sitemap_from_str

USER_AGENT = "Sensebot"


robots_cache = {}
sitemaps_cache = {}

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


def get_robots_parser(url: str) -> RobotFileParser:
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
            parser = robots_cache[url_data.netloc] = RobotFileParser(robots_url)
            parser.read()
        else:
            parser = robots_cache[url_data.netloc] = None
    return parser


def can_crawl(url: str) -> bool:
    parser = get_robots_parser(url)
    if parser == None:
        return True
    else:
        return parser.can_fetch(USER_AGENT, url)


def get_robots_sitemaps_from(url: str) -> list[str]:
    parser = get_robots_parser(url)
    if parser == None:
        return None
    else:
        return parser.site_maps()


def get_links_from(url: str) -> set[str]:
    if not url.endswith("/"):
        url += "/"

    links = set()

    url_data = urlparse(url)
    if url_data.netloc in sitemaps_cache:
        sitemap_tree = sitemaps_cache[url_data.netloc]
    else:
        sitemap_tree = sitemap_tree_for_homepage(url, use_robots=False)
        sitemaps_cache[url_data.netloc] = sitemap_tree

    links = set()

    for page in sitemap_tree.all_pages():
        links.add(page.url)

    for sitemap in get_robots_sitemaps_from(url):
        if sitemap in sitemaps_cache:
            tree = sitemaps_cache[sitemap]
        else:
            response = requests.get(sitemap, headers={"User-Agent": USER_AGENT})
            if (
                response.status_code == 200
                and response.headers.get("content-type") == "text/xml"
            ):
                tree = sitemap_from_str(response.text)
                sitemaps_cache[sitemap] = tree
        for page in tree.all_pages():
            links.add(page.url)

    response = requests.get(url, headers={"User-Agent": USER_AGENT})

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("a"):
            link = urlparse(urljoin(url, link.get("href")))
            link = urlunparse(link._replace(query=""))
            if not link.endswith("/"):
                link += "/"
            if can_crawl(link):
                links.add(link)
    else:
        print(f"error: {response.status_code}")

    return links


links = get_links_from("https://www.google.com")
with open("links_to_crawl.txt", "w") as f:
    for url in links:
        f.write(url + "\n")
