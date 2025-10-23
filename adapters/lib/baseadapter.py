import requests
from bs4 import BeautifulSoup
from urllib3 import Retry

class InvalidStatusCodeError(Exception):
    def __init__(self, status_code: int, body: str, *args: object) -> None:
        super().__init__(*args)
        self.status_code = status_code
        self.body = body

class BaseAdapter:
    def __init__(self, url: str, timeout: int = 10, redirects: bool = True) -> None:
        self.url = url
        self.timeout = timeout
        self.redirects = redirects

        self.session = requests.Session()
        self.session.mount("https://", requests.adapters.HTTPAdapter( # pyright: ignore[reportAttributeAccessIssue]
            max_retries=Retry(total=5, status_forcelist=[500, 502, 503, 504, 520, 524, 525])
            )
        )

    def scrape_site(self, url: str) -> BeautifulSoup:
        r = self.session.get(url, allow_redirects=self.redirects, timeout=self.timeout)

        if r.status_code != 200:
            raise InvalidStatusCodeError(r.status_code, r.text)
        
        return BeautifulSoup(r.content, features='lxml')
