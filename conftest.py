# conftest.py
import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright
from config.test_config import TestConfig
from config.logging_config import setup_logging
from lib.web_actions import WebActions
from lib.api_actions import APIActions
from page_factory.page_repository.login_page import LoginPage
from page_factory.page_repository.elements_page import ElementsPage
from page_factory.page_repository.alerts_frame_windows_page import AlertsFrameWindowsPage
from page_factory.page_repository.widgets_page import WidgetsPage
from page_factory.page_repository.interactions_page import InteractionsPage


def pytest_sessionstart(session):
    """清理旧的报告目录，初始化日志"""
    setup_logging()
    for dir_name in ["allure-results", "test-results", "logs", "reports", "screenshots"]:
        Path(dir_name).mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def test_config():
    return TestConfig()


@pytest.fixture(scope="session")
def browser_name(request):
    val = request.config.getoption("--browser")
    return val[0] if isinstance(val, list) else val


@pytest.fixture(scope="session")
def context_kwargs(browser_name, test_config, playwright_instance):
    """不同浏览器/设备的上下文参数"""
    base = {
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": test_config.ignore_https_errors
    }
    if browser_name == "mobile-pixel4":
        base.update(**playwright_instance.devices["Pixel 4a 5G"])
    elif browser_name == "edge":
        base["channel"] = "msedge"
    return base


@pytest.fixture(scope="session")
def browser_type(playwright_instance, browser_name):
    if browser_name in ["chromium", "mobile-pixel4"]:
        return playwright_instance.chromium
    elif browser_name == "firefox":
        return playwright_instance.firefox
    elif browser_name == "webkit":
        return playwright_instance.webkit
    elif browser_name == "edge":
        return playwright_instance.chromium   # 使用 channel 区分
    else:
        return playwright_instance.chromium


@pytest.fixture(scope="session")
def browser_context(browser_type, context_kwargs):
    context = browser_type.launch(headless=True).new_context(**context_kwargs)
    yield context
    context.close()


@pytest.fixture
def page(browser_context):
    p = browser_context.new_page()
    yield p
    p.close()


@pytest.fixture
def web_actions(page):
    return WebActions(page)


# ---------- Page Object Fixtures ----------
@pytest.fixture
def login_page(page, web_actions, test_config):
    return LoginPage(page, web_actions, test_config)

@pytest.fixture
def elements_page(page, web_actions):
    return ElementsPage(page, web_actions)

@pytest.fixture
def alerts_page(page, web_actions):
    return AlertsFrameWindowsPage(page, web_actions)

@pytest.fixture
def widgets_page(page, web_actions):
    return WidgetsPage(page, web_actions)

@pytest.fixture
def interactions_page(page, web_actions):
    return InteractionsPage(page, web_actions)

# ---------- API Fixtures ----------
@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p

@pytest.fixture(scope="session")
def api_request_context(playwright_instance, test_config):
    ctx = playwright_instance.request.new_context(
        base_url=test_config.api_base_url,
        extra_http_headers={"Content-Type": "application/json"}
    )
    yield ctx
    ctx.dispose()

# ---------- 备用 DB Fixture（后期启用）----------
@pytest.fixture(scope="session")
def db_actions(test_config):
    from lib.db_actions import DBActions
    dba = DBActions(test_config)
    dba.connect()
    yield dba
    dba.disconnect()