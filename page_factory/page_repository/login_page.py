# page_factory/page_repository/login_page.py
import logging
from playwright.sync_api import Page
from lib.web_actions import WebActions
from config.test_config import TestConfig

logger = logging.getLogger(__name__)

class LoginPage:
    USERNAME = "#userName"
    PASSWORD = "#password"
    LOGIN_BTN = "#login"
    PROFILE = "text=Profile"
    USER_LABEL = "#userName-value"

    def __init__(self, page: Page, web: WebActions, config: TestConfig):
        self.page = page
        self.web = web
        self.config = config

    def navigate(self):
        self.web.navigate(f"{self.config.base_url}/login")

    def login(self, username, password):
        self.web.fill(self.USERNAME, username)
        self.web.fill(self.PASSWORD, password)
        self.web.click(self.LOGIN_BTN)

    def is_logged_in(self) -> bool:
        return self.web.is_visible(self.PROFILE)

    def get_username(self) -> str:
        return self.web.get_text(self.USER_LABEL)