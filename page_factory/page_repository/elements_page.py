# page_factory/page_repository/elements_page.py
from playwright.sync_api import Page
from lib.web_actions import WebActions

class ElementsPage:
    def __init__(self, page: Page, web: WebActions):
        self.page = page
        self.web = web

    def navigate(self, base_url):
        self.web.navigate(f"{base_url}/elements")

    def fill_textbox(self, full_name, email, current_address, permanent_address):
        self.web.fill("#userName", full_name)
        self.web.fill("#userEmail", email)
        self.web.fill("#currentAddress", current_address)
        self.web.fill("#permanentAddress", permanent_address)
        self.web.click("#submit")

    def get_output_text(self):
        return self.web.get_text("#output")