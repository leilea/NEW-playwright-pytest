import allure
import pytest
from playwright.sync_api import APIRequestContext

@allure.feature("API GET")
class TestGetAPI:

    @allure.story("Get Books")
    @pytest.mark.api
    def test_get_books(self, api_request_context: APIRequestContext, test_config):
        resp = api_request_context.get(f"{test_config.api_base_url}/BookStore/v1/Books")
        assert resp.status == 200
        json_data = resp.json()
        assert "books" in json_data
        assert len(json_data["books"]) > 0

    @allure.story("Response Headers")
    @pytest.mark.api
    def test_response_headers(self, api_request_context: APIRequestContext, test_config):
        resp = api_request_context.get(f"{test_config.api_base_url}/BookStore/v1/Books")
        content_type = resp.headers.get("content-type", "")
        assert "application/json" in content_type