from playwright.sync_api import Page
from lib.web_actions import WebActions

class AlertsFrameWindowsPage:
    def __init__(self, page: Page, web: WebActions):
        self.page = page
        self.web = web

    ALERT_BTN = "#alertButton"
    TIMER_ALERT_BTN = "#timerAlertButton"
    CONFIRM_BTN = "#confirmButton"
    PROMPT_BTN = "#promtButton"
    CONFIRM_RESULT = "#confirmResult"
    PROMPT_RESULT = "#promptResult"

    def navigate(self, base_url):
        self.web.navigate(f"{base_url}/alertsWindows")

    def click_alert(self):
        self.web.click(self.ALERT_BTN)

    def click_timer_alert(self):
        self.web.click(self.TIMER_ALERT_BTN)

    def click_confirm(self):
        self.web.click(self.CONFIRM_BTN)

    def get_confirm_result(self) -> str:
        return self.web.get_text(self.CONFIRM_RESULT)

    def click_prompt(self):
        self.web.click(self.PROMPT_BTN)

    def get_prompt_result(self) -> str:
        return self.web.get_text(self.PROMPT_RESULT)
