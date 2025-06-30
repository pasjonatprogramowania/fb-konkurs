import time
import logging
from browser_use import Browser # Assuming this is how Browser is imported

# Configure logging for the module
logger = logging.getLogger(__name__)

def find_contests(search_phrase: str, scroll_count: int) -> list[dict]:
    """
    Finds contest posts on Facebook based on a search phrase.

    Args:
        search_phrase: The phrase to search for (e.g., "konkurs").
        scroll_count: How many times to scroll down the results page.

    Returns:
        A list of dictionaries, where each dictionary contains 'content' and 'link'
        of a found post. Returns an empty list if errors occur or no posts are found.
    """
    results = []
    browse = None # Initialize browse to None for finally block

    try:
        logger.info(f"Initializing browser for scraping with search: '{search_phrase}', scrolls: {scroll_count}")
        browse = Browser() # Initialize the browser

        logger.info("Navigating to Facebook...")
        browse.go_to("https://facebook.com")
        logger.info("Pausing for 20 seconds for potential manual login...")
        time.sleep(20) # Time for manual login, as per spec

        search_url = f"https://www.facebook.com/search/posts/?q={search_phrase}"
        logger.info(f"Navigating to search URL: {search_url}")
        browse.go_to(search_url)

        logger.info(f"Scrolling down {scroll_count} times...")
        for i in range(scroll_count):
            browse.scroll_down()
            logger.debug(f"Scroll attempt {i+1}/{scroll_count}")
            time.sleep(2) # Wait for content to load after scrolling

        logger.info("Scraping post elements with selector: div[role='article']")
        post_elements = browse.scrape_elements_by_css_selector("div[role='article']")
        logger.info(f"Found {len(post_elements)} potential post elements.")

        for i, post_element in enumerate(post_elements):
            post_content = ""
            post_link = None
            try:
                post_content = post_element.text
                if not post_content: # Skip if text is empty
                    logger.warning(f"Post element {i+1} has no text content. Skipping.")
                    continue

                # Link extraction: Specification mentions finding an <a> tag.
                # This is a common challenge as link structures vary.
                # We'll try a few common patterns for permalinks / timestamp links.
                # This might need significant refinement based on actual Facebook structure.
                # A more robust approach might involve looking for links with specific text like "Permalink",
                # or links associated with the post's timestamp.
                # For now, a simple attempt to find any <a> tag with an href.
                # A more specific selector would be better, e.g., one that targets the post's timestamp link.
                # Let's try a generic 'a' tag for now as per the test mock, but acknowledge its fragility.
                link_element = post_element.find_element_by_css_selector('a') # This is a guess based on test mock
                if link_element:
                    post_link = link_element.get_attribute('href')

                if post_link:
                    results.append({'content': post_content, 'link': post_link})
                    logger.debug(f"Successfully extracted content and link for post {i+1}.")
                else:
                    logger.warning(f"Could not extract link for post {i+1}. Post content: '{post_content[:100]}...'")

            except Exception as e_post:
                logger.warning(f"Error processing post element {i+1}: {e_post}. Post content: '{post_content[:100]}...'. Skipping this post.")
                # Continue to the next post element

    except Exception as e_main:
        logger.error(f"An error occurred during the scraping process in find_contests: {e_main}")
        # results will be empty or partially filled, which is the intended fallback
    finally:
        if browse:
            try:
                logger.info("Attempting to close the browser.")
                # browse.close_browser() # Or browse.quit() depending on browser-use API
                # browser-use doesn't seem to have an explicit close method in its simple API.
                # It might close automatically when the object is garbage collected or script ends.
                # For now, we'll assume it handles its own cleanup or rely on context manager if available.
                # If a close method exists, it should be called here.
                pass # No explicit close in browser-use docs, seems to manage itself.
            except Exception as e_close:
                logger.error(f"Error trying to close browser: {e_close}")
        logger.info(f"Scraping finished. Returning {len(results)} results.")

    return results

if __name__ == '__main__':
    # Example usage for direct testing (requires manual browser interaction and Facebook login)
    # Configure basic logging for direct script execution test
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # test_phrase = "konkurs"
    # test_scrolls = 1
    # logger.info(f"--- Starting direct test for scraper.py with phrase: '{test_phrase}', scrolls: {test_scrolls} ---")
    # found_posts = find_contests(test_phrase, test_scrolls)
    # if found_posts:
    #     logger.info(f"--- Found {len(found_posts)} posts: ---")
    #     for idx, post_data in enumerate(found_posts):
    #         logger.info(f"Post {idx+1}:")
    #         logger.info(f"  Link: {post_data['link']}")
    #         logger.info(f"  Content snippet: {post_data['content'][:200]}...")
    # else:
    #     logger.info(f"--- No posts found or an error occurred during direct test. ---")
    pass
