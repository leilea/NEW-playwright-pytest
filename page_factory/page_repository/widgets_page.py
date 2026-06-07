from playwright.sync_api import Page
from lib.web_actions import WebActions

class WidgetsPage:
    def __init__(self, page: Page, web: WebActions):
        self.page = page
        self.web = web

    PROGRESS_BAR = "#progressBar"
    START_STOP_BTN = "#startStopButton"
    RESET_BTN = "#resetButton"
    TOOLTIP_BTN = "#toolTipButton"
    TOOLTIP_TEXT = ".tooltip-inner"

    def navigate(self, base_url):
        self.web.navigate(f"{base_url}/progress-bar")

    def click_start_stop(self):
        self.web.click(self.START_STOP_BTN)

    def is_progress_complete(self) -> bool:
        return self.web.get_text(self.PROGRESS_BAR) == "100%"

    def hover_tooltip_button(self):
        self.web.hover(self.TOOLTIP_BTN)

    def get_tooltip_text(self) -> str:
        return self.web.get_text(self.TOOLTIP_TEXT)
