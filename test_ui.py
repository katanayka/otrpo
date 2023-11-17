import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By

# URL of your Flask application
BASE_URL = 'http://localhost:5000'  # Update with your actual URL

# Sample test class using pytest and Selenium
class TestFlaskApp:
    @classmethod
    def setup_class(cls):
        # Set up the WebDriver (use the appropriate webdriver for your browser)
        cls.driver = webdriver.Chrome()

    @classmethod
    def teardown_class(cls):
        # Close the WebDriver after all tests
        cls.driver.quit()

    def test_homepage_loads(self):
        # Test that the homepage loads successfully
        self.driver.get(BASE_URL)
        assert "" in self.driver.title

    def test_search_functionality(self):
        # Test the search functionality on the homepage
        self.driver.get(BASE_URL)

        # Enter a search term in the search input
        search_input = self.driver.find_element(By.ID, 'param')
        search_input.send_keys('charizard')

        # Click the "БУМ" button to submit the search
        search_button = self.driver.find_element(By.XPATH, '//input[@value="БУМ"]')
        search_button.click()

        # Wait for the search results to load
        time.sleep(2)

        # Verify that the search result contains the expected Pokemon (Charizard)
        result_name = self.driver.find_element(By.CLASS_NAME, 'pokemon-name').text
        assert "charizard" in result_name

    def test_battle_button_redirect(self):
        # Test that clicking the "battle" button redirects to the battle page
        self.driver.get(BASE_URL)

        # Click the first "battle" button
        battle_button = self.driver.find_element(By.CLASS_NAME, 'battle-button')
        battle_button.click()

        # Wait for the battle page to load
        time.sleep(2)

        # Verify that the URL has changed to the expected battle URL
        assert "fight" in self.driver.current_url

# Run the tests using pytest
if __name__ == "__main__":
    pytest.main()
