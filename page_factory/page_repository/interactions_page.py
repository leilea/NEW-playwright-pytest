from playwright.sync_api import Page
from lib.web_actions import WebActions

class InteractionsPage:
    def __init__(self, page: Page, web: WebActions):
        self.page = page
        self.web = web

    SORTABLE_LIST = ".list-group"
    DROPPABLE_SIMPLE = "#droppable"
    DRAGGABLE = "#draggable"

    def navigate(self, base_url):
        self.web.navigate(f"{base_url}/droppable")

    def drag_and_drop(self):
        self.page.drag_and_drop(self.DRAGGABLE, self.DROPPABLE_SIMPLE)

    def is_dropped(self) -> str:
        return self.web.get_text(self.DROPPABLE_SIMPLE)
