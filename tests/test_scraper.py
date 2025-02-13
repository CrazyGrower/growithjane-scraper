"""
Tests for the scraper module.
"""
import unittest
from unittest.mock import patch, MagicMock
from src.scraper import configure_driver, extract_plant_state

class TestScraper(unittest.TestCase):
    @patch('selenium.webdriver.Chrome')
    def test_configure_driver(self, mock_chrome):
        """Test driver configuration."""
        driver = configure_driver("/path/to/chromedriver")
        self.assertTrue(mock_chrome.called)
    
    def test_extract_plant_state(self):
        """Test plant state extraction."""
        mock_entry = MagicMock()
        mock_entry.find_element.return_value.get_attribute.return_value = "icon-seedling"
        
        state = extract_plant_state(mock_entry)
        self.assertEqual(state, "seedling")

if __name__ == '__main__':
    unittest.main()