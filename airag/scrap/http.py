import bs4
import requests

def get(url):
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.content, 'html.parser')
    return {
        'title': (soup.find('title') or bs4.element.Tag(name='title')).text or url,
        'content': response.content,
        'mimetype': response.headers.get('Content-Type'),
        'source': url
    }

# pip install playwright
# playwright install
from playwright.sync_api import sync_playwright

def browse(url='https://google.com/'):
    with sync_playwright() as p:
        # TODO: Pass bot checks using playwright-stealth: https://www.zenrows.com/blog/playwright-stealth#how-to
        browser = p.chromium.launch() #headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url)
        # return page.inner_html('body')
        # return page.content()
        soup = bs4.BeautifulSoup(page.content(), 'html.parser')
        return {
            'title': (soup.find('title') or bs4.element.Tag(name='title')).text or url,
            'content': str(soup),
            'mimetype': requests.get(url).headers.get('Content-Type'),  # FIXME: Using requests because cannot get response headers from `page`
            'source': url
        }

# url='http://google.com/'
# with sync_playwright() as p:
#     browser = p.chromium.launch() #headless=False)
#     context = browser.new_context()
#     page = context.new_page()
#     page.goto(url)
