import requests
from bs4 import BeautifulSoup
from urllib3 import Retry
from selenium import webdriver

class InvalidStatusCodeError(Exception):
    def __init__(self, status_code: int, body: str, *args: object) -> None:
        super().__init__(*args)
        self.status_code = status_code
        self.body = body

class BaseAdapter:
    def __init__(self, url: str, timeout: int = 10, redirects: bool = True, http: bool = True, browser: bool = False) -> None:
        self.url = url
        self.timeout = timeout
        self.redirects = redirects

        if http:
            self.session = requests.Session()
            self.session.mount("https://", requests.adapters.HTTPAdapter( # pyright: ignore[reportAttributeAccessIssue]
                max_retries=Retry(total=5, status_forcelist=[500, 502, 503, 504, 520, 524, 525])
                )
            )
        
        if browser:
            self.driver = webdriver.Chrome()
            self.driver.set_page_load_timeout(self.timeout)


    def scrape_site(self, url: str) -> BeautifulSoup:
        """
        Only call this method when http=True is set in __init__
        """
        r = self.session.get(url, allow_redirects=self.redirects, timeout=self.timeout)

        if r.status_code != 200:
            raise InvalidStatusCodeError(r.status_code, r.text)
        
        return BeautifulSoup(r.content, features='lxml')
    
    def scrape_site_with_selenium(self, url: str) -> BeautifulSoup:
        """
        Only call this method when browser=True is set in __init__

        This method doesn't check for error codes!
        """
        for _ in range(10):
            try:
                self.driver.get(url)
            except TimeoutError:
                pass
        
        if self.driver.current_url != url:
            raise TimeoutError
        
        return BeautifulSoup(self.driver.page_source, features='lxml')
