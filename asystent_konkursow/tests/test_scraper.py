import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import time # Will be needed to mock time.sleep

# Adjust path to import scraper from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Attempt to import the module or define a placeholder for TDD
try:
    from scraper import find_contests
except ImportError:
    def find_contests(search_phrase: str, scroll_count: int) -> list[dict]:
        raise NotImplementedError("scraper.find_contests is not yet implemented")

# Placeholder for browser_use.Browser if the library isn't available during test writing phase
# This helps in writing tests even if scraper.py itself can't import Browser yet.
# However, scraper.py will need `from browser_use import Browser`
# We will be patching 'scraper.Browser' or 'browser_use.Browser' depending on how it's imported in scraper.py
# For now, let's assume scraper.py does `from browser_use import Browser` and we'll patch `scraper.Browser`

class TestScraper(unittest.TestCase):

    @patch('scraper.time.sleep') # Patch time.sleep to speed up tests
    @patch('scraper.Browser')    # Patch Browser from the scraper module
    def test_successful_scraping_and_data_extraction(self, MockBrowser, mock_sleep):
        # Configure the mock browser instance
        mock_browser_instance = MockBrowser.return_value

        # Mock post elements
        # Element 1
        mock_post_element_1_link_element = MagicMock()
        mock_post_element_1_link_element.get_attribute.return_value = "https.facebook.com/post1"

        mock_post_element_1 = MagicMock()
        mock_post_element_1.text = "Content of post 1"
        # Simulate finding an 'a' tag within the post element for the link
        # This part depends heavily on how link extraction will be implemented in scraper.py
        # Option A: scraper.py does element.find_element_by_tag_name('a').get_attribute('href')
        # Option B: scraper.py does element.scrape_links() or similar if browser-use offers it
        # Option C: A more complex CSS selector on the post_element itself.
        # For now, let's assume a simple find_element_by_css_selector for an <a> tag.
        # We might need to adjust this mock if scraper.py's link extraction is different.
        mock_post_element_1.find_element_by_css_selector.return_value = mock_post_element_1_link_element


        # Element 2
        mock_post_element_2_link_element = MagicMock()
        mock_post_element_2_link_element.get_attribute.return_value = "https.facebook.com/post2"

        mock_post_element_2 = MagicMock()
        mock_post_element_2.text = "Content of post 2"
        mock_post_element_2.find_element_by_css_selector.return_value = mock_post_element_2_link_element

        mock_post_elements = [mock_post_element_1, mock_post_element_2]
        mock_browser_instance.scrape_elements_by_css_selector.return_value = mock_post_elements

        search_phrase = "konkurs"
        scroll_count = 1 # Keep it simple for this test

        expected_results = [
            {'content': "Content of post 1", 'link': "https.facebook.com/post1"},
            {'content': "Content of post 2", 'link': "https.facebook.com/post2"}
        ]

        actual_results = find_contests(search_phrase, scroll_count)
        self.assertEqual(actual_results, expected_results)

        # Assert browser interactions
        mock_browser_instance.go_to.assert_any_call("https://facebook.com")
        expected_search_url = f"https://www.facebook.com/search/posts/?q={search_phrase}"
        mock_browser_instance.go_to.assert_any_call(expected_search_url)

        self.assertEqual(mock_browser_instance.scroll_down.call_count, scroll_count)
        # The spec says time.sleep(20) for login and time.sleep(2) for scroll
        # mock_sleep should be called for login and for each scroll
        mock_sleep.assert_any_call(20) # For login
        mock_sleep.assert_any_call(2)  # For scroll

        # Assert that scrape_elements_by_css_selector was called with the correct selector
        mock_browser_instance.scrape_elements_by_css_selector.assert_called_once_with("div[role='article']")

        # Assert link extraction calls if using find_element_by_css_selector for links
        # This assumes a specific link extraction strategy that needs to be mirrored in scraper.py
        # For example, if scraper.py uses 'a[href*="/videos/"] a[href*="/photos/"] a[href*="/permalink/"]'
        # or some other common permalink patterns. For now, a generic 'a' is assumed for simplicity.
        # This part is highly dependent on the actual implementation in scraper.py for finding the link.
        # A more robust mock might involve mocking a specific helper if link extraction is complex.
        mock_post_element_1.find_element_by_css_selector.assert_called_with('a') # Example
        mock_post_element_1_link_element.get_attribute.assert_called_with('href')
        mock_post_element_2.find_element_by_css_selector.assert_called_with('a') # Example
        mock_post_element_2_link_element.get_attribute.assert_called_with('href')

    @patch('scraper.time.sleep')
    @patch('scraper.Browser')
    def test_scrolling_logic(self, MockBrowser, mock_sleep):
        mock_browser_instance = MockBrowser.return_value
        # Simulate no posts found to focus on scrolling
        mock_browser_instance.scrape_elements_by_css_selector.return_value = []

        search_phrase = "test_scroll"
        scroll_count = 3

        find_contests(search_phrase, scroll_count)

        self.assertEqual(mock_browser_instance.scroll_down.call_count, scroll_count)

        # Check that time.sleep(2) was called after each scroll_down
        # Expected calls: one for login (20s), and 'scroll_count' times for scrolling (2s each)
        expected_sleep_calls = [call(20)] # For login
        for _ in range(scroll_count):
            expected_sleep_calls.append(call(2)) # For each scroll

        # Check if all expected calls are present in actual calls.
        # This is more flexible than assert_has_calls if order doesn't strictly matter
        # or if other sleep calls could exist (though not expected here).
        # However, for this specific sequence, assert_has_calls with any_order=False (default) is good.
        mock_sleep.assert_has_calls(expected_sleep_calls)
        # Additionally, ensure the total number of sleep calls is as expected
        self.assertEqual(mock_sleep.call_count, scroll_count + 1) # +1 for the initial login sleep

    @patch('scraper.time.sleep')
    @patch('scraper.Browser')
    def test_navigation_logic(self, MockBrowser, mock_sleep):
        mock_browser_instance = MockBrowser.return_value
        mock_browser_instance.scrape_elements_by_css_selector.return_value = [] # No posts

        search_phrase = "test_navigation"
        scroll_count = 0 # No scrolling needed for this test focus

        find_contests(search_phrase, scroll_count)

        expected_fb_url = "https://facebook.com"
        expected_search_url = f"https://www.facebook.com/search/posts/?q={search_phrase}"

        # Check that go_to was called with the expected URLs in the correct order
        calls = [
            call.go_to(expected_fb_url),
            call.go_to(expected_search_url)
        ]
        mock_browser_instance.assert_has_calls(calls, any_order=False) # Check specific calls in order

        # Verify sleep after initial navigation
        mock_sleep.assert_any_call(20)

    @patch('scraper.time.sleep')
    @patch('scraper.Browser')
    def test_no_posts_found(self, MockBrowser, mock_sleep):
        mock_browser_instance = MockBrowser.return_value
        # Simulate scrape_elements_by_css_selector returning an empty list
        mock_browser_instance.scrape_elements_by_css_selector.return_value = []

        search_phrase = "no_results_phrase"
        scroll_count = 1

        actual_results = find_contests(search_phrase, scroll_count)

        self.assertEqual(actual_results, []) # Expect an empty list

        # Ensure basic navigation still happened
        mock_browser_instance.go_to.assert_any_call("https://facebook.com")
        expected_search_url = f"https://www.facebook.com/search/posts/?q={search_phrase}"
        mock_browser_instance.go_to.assert_any_call(expected_search_url)
        mock_browser_instance.scroll_down.assert_called_once() # Based on scroll_count = 1
        mock_browser_instance.scrape_elements_by_css_selector.assert_called_once_with("div[role='article']")

    @patch('scraper.time.sleep')
    @patch('scraper.Browser')
    @patch('scraper.logger') # Assuming scraper.py will have a logger named 'logger'
    def test_browser_operation_error(self, mock_logger, MockBrowser, mock_sleep):
        mock_browser_instance = MockBrowser.return_value
        # Simulate an error during a browser operation, e.g., go_to
        simulated_error_message = "Network Error"
        mock_browser_instance.go_to.side_effect = Exception(simulated_error_message)

        search_phrase = "error_case"
        scroll_count = 1

        # We expect find_contests to catch the exception, log it, and return an empty list.
        actual_results = find_contests(search_phrase, scroll_count)

        self.assertEqual(actual_results, [])

        # Verify that an error was logged.
        # This requires scraper.py to have `import logging; logger = logging.getLogger(__name__)`
        # or a similar logger setup.
        mock_logger.error.assert_called_once()
        # Optionally, check the content of the log message if it's predictable
        args, _ = mock_logger.error.call_args
        self.assertIn(simulated_error_message, args[0]) # Check if the error message is in the log

    # Test for error during scrape_elements_by_css_selector
    @patch('scraper.time.sleep')
    @patch('scraper.Browser')
    @patch('scraper.logger')
    def test_scrape_elements_error(self, mock_logger, MockBrowser, mock_sleep):
        mock_browser_instance = MockBrowser.return_value
        simulated_error_message = "Scrape Error"
        mock_browser_instance.scrape_elements_by_css_selector.side_effect = Exception(simulated_error_message)

        search_phrase = "scrape_error_case"
        scroll_count = 1

        actual_results = find_contests(search_phrase, scroll_count)
        self.assertEqual(actual_results, [])
        mock_logger.error.assert_called_once()
        args, _ = mock_logger.error.call_args
        self.assertIn(simulated_error_message, args[0])

    # Test for error during link extraction from a post element
    @patch('scraper.time.sleep')
    @patch('scraper.Browser')
    @patch('scraper.logger')
    def test_link_extraction_error(self, mock_logger, MockBrowser, mock_sleep):
        mock_browser_instance = MockBrowser.return_value

        mock_post_element_error = MagicMock()
        mock_post_element_error.text = "Content of post with link error"
        simulated_error_message = "Link not found"
        # Simulate find_element_by_css_selector for link raising an error
        mock_post_element_error.find_element_by_css_selector.side_effect = Exception(simulated_error_message)

        mock_browser_instance.scrape_elements_by_css_selector.return_value = [mock_post_element_error]

        search_phrase = "link_extraction_error_case"
        scroll_count = 1

        actual_results = find_contests(search_phrase, scroll_count)

        # Expect an empty list because if a post can't be fully processed (e.g. link missing),
        # it might be skipped, or the function might return partially successful ones.
        # For now, let's assume it tries to process and if one fails, it's logged and skipped.
        # If scraper.py is designed to return successfully processed items even if others fail,
        # this assertion would change. For now, let's assume an error in one post means it's not included.
        # A more robust design might return a list of successfully parsed items and log errors for others.
        # The current test assumes that an error in processing a post means it's skipped, so if only one post
        # is returned by the mock and it has an error, the result is an empty list.
        # If the design is to return an empty dict or a dict with an error field for that post, this test needs adjustment.
        # Let's assume a simple skip-on-error for now, resulting in an empty list if all posts have errors.
        # Or, if the post has content but link fails, perhaps it returns content and link=None/error_marker

        # For this test, let's assume the post is skipped if link extraction fails.
        self.assertEqual(actual_results, [])
        mock_logger.warning.assert_called_once() # Or error, depending on severity chosen in scraper.py
        args, _ = mock_logger.warning.call_args # or error
        self.assertIn(simulated_error_message, args[0])
        self.assertIn(mock_post_element_error.text, args[0]) # Log should include info about the post


if __name__ == '__main__':
    unittest.main()
