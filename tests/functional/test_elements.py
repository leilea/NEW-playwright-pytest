import allure
import pytest

@allure.feature("Elements")
class TestElements:

    @allure.story("Text Box submit")
    def test_text_box(self, elements_page, test_config):
        elements_page.navigate(test_config.base_url)
        elements_page.fill_textbox("John Doe", "john@example.com", "Addr1", "Addr2")
        output = elements_page.get_output_text()
        assert "John Doe" in output