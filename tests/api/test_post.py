import allure
import pytest
from playwright.sync_api import APIRequestContext

@allure.feature("API POST")
class TestPostAPI:

    @allure.story("Create User")
    @pytest.mark.api
    def test_create_user(self, api_request_context: APIRequestContext, test_config):
        endpoint = f"{test_config.api_base_url}/Account/v1/User"
        payload = {
            "userName": "test_" + str(pytest.unique_id),
            "password": "Test@1234"
        }
        resp = api_request_context.post(endpoint, data=payload)
        assert resp.status == 201  # 或 200 根据 API 实际行为