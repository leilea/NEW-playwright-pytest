import allure
import pytest

@allure.feature("Login")
class TestLogin:

    @allure.story("Successful Login")
    @pytest.mark.smoke
    def test_valid_login(self, login_page):
        with allure.step("Navigate to login"):
            login_page.navigate()
        with allure.step("Enter valid credentials"):
            # 使用测试环境预置账号，这里硬编码仅示例，实际应来自 config 或 fixture
            login_page.login("testuser", "Test@123")
        with allure.step("Verify login success"):
            assert login_page.is_logged_in(), "Login should succeed"

    @allure.story("Failed Login")
    def test_invalid_login(self, login_page):
        login_page.navigate()
        login_page.login("invalid", "wrong")
        assert not login_page.is_logged_in(), "Should not be logged in"