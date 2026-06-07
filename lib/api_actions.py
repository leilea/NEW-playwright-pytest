# lib/api_actions.py
import logging
from playwright.sync_api import APIRequestContext, APIResponse

logger = logging.getLogger(__name__)

class APIActions:
    def __init__(self, request_context: APIRequestContext):
        self.context = request_context

    def get(self, endpoint, params=None, headers=None):
        logger.info(f"GET {endpoint}")
        resp = self.context.get(endpoint, params=params, headers=headers)
        logger.info(f"Status: {resp.status}")
        return resp

    def post(self, endpoint, data=None, headers=None):
        logger.info(f"POST {endpoint} body={data}")
        resp = self.context.post(endpoint, data=data, headers=headers)
        logger.info(f"Status: {resp.status}")
        return resp

    def assert_status(self, response: APIResponse, expected: int):
        assert response.status == expected, f"Expected {expected}, got {response.status}"

    def assert_json_path(self, response: APIResponse, json_path, expected_value):
        # 支持点号路径 "books.0.isbn"
        json_data = response.json()
        keys = json_path.split(".")
        value = json_data
        for k in keys:
            if k.isdigit():
                value = value[int(k)]
            else:
                value = value.get(k)
        assert value == expected_value, f"Expected {expected_value} at {json_path}, got {value}"