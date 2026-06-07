# lib/web_actions.py
import logging
from playwright.sync_api import Page, expect

logger = logging.getLogger(__name__)

class WebActions:
    def __init__(self, page: Page):
        self.page = page

    def navigate(self, url): 
        logger.info(f"Navigate to {url}")
        self.page.goto(url, wait_until="networkidle")

    def click(self, locator, timeout=30000):
        logger.info(f"Click: {locator}")
        self.page.click(locator, timeout=timeout)

    def fill(self, locator, text):
        logger.info(f"Fill {locator} = {text}")
        self.page.fill(locator, text)

    def get_text(self, locator): 
        return self.page.text_content(locator)

    def is_visible(self, locator, timeout=10000):
        try:
            self.page.wait_for_selector(locator, state="visible", timeout=timeout)
            return True
        except:
            return False

    def hover(self, locator):
        self.page.hover(locator)

    def scroll_into_view(self, locator):
        self.page.locator(locator).scroll_into_view_if_needed()

    def take_screenshot(self, path=None, full_page=True):
        path = path or f"screenshots/ss_{int(time.time())}.png"
        self.page.screenshot(path=path, full_page=full_page)
        return path

    # 可根据需要添加更多封装