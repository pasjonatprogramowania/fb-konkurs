import os

import google.generativeai as genai
import json
import logging

# Configure logging for the module
logger = logging.getLogger(__name__)

def analyze_post(post_content: str, api_key: str) -> dict:
    """
    Analyzes post content using Google Gemini to extract contest information.

    Args:
        post_content: The text content of the post to analyze.
        api_key: The Google Gemini API key.

    Returns:
        A dictionary containing extracted information:
        'zadanie_konkursowe', 'miejsce_zgloszenia', 'termin_zakonczenia'.
        Returns a dictionary with error information in case of failure.
    """
    if not api_key:
        logger.error("API key is missing.")
        return {
            "zadanie_konkursowe": "Błąd konfiguracji",
            "miejsce_zgloszenia": "Błąd konfiguracji",
            "termin_zakonczenia": "Błąd konfiguracji",
            "error": "API key is missing"
        }

    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        logger.error(f"Error configuring Gemini API: {e}")
        return {
            "zadanie_konkursowe": "Błąd konfiguracji API",
            "miejsce_zgloszenia": "Błąd konfiguracji API",
            "termin_zakonczenia": "Błąd konfiguracji API",
            "error": f"Error configuring Gemini API: {e}"
        }

    if not post_content or post_content.strip() == "":
        logger.warning("Post content is empty. Skipping analysis.")
        return {
            "zadanie_konkursowe": None,
            "miejsce_zgloszenia": None,
            "termin_zakonczenia": None,
            "error": "Empty post content"
        }

    prompt = f"""
    Jesteś ekspertem od analizy mediów społecznościowych. Twoim zadaniem jest przeanalizować poniższy tekst posta i wyodrębnić z niego informacje o konkursie. Zwróć odpowiedź wyłącznie w formacie JSON, używając następujących kluczy: 'zadanie_konkursowe', 'miejsce_zgloszenia', 'termin_zakonczenia'. Jeśli dana informacja nie jest dostępna, użyj wartości null. Przykład:
    {{
      "zadanie_konkursowe": "Opisz swoje ulubione wakacje",
      "miejsce_zgloszenia": "W komentarzu pod postem",
      "termin_zakonczenia": "2024-12-31"
    }}

    Tekst posta do analizy:
    {post_content}
    """

    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)

        # Attempt to find JSON block if the response contains other text like backticks
        # A simple heuristic: look for the first '{' and the last '}'
        try:
            json_start = response.text.index('{')
            json_end = response.text.rindex('}') + 1
            json_str = response.text[json_start:json_end]
            parsed_response = json.loads(json_str)
        except (ValueError, AttributeError) as e: # Handles cases where '{' or '}' not found or response.text is not string
             logger.error(f"Could not find JSON in response: {response.text}. Error: {e}")
             # Fallback to trying to parse the whole response.text if the above failed.
             # This might be needed if the AI returns *only* JSON without any surrounding text/markdown.
             parsed_response = json.loads(response.text)


        # Validate expected keys, even if they are null
        expected_keys = ['zadanie_konkursowe', 'miejsce_zgloszenia', 'termin_zakonczenia']
        result = {}
        for key in expected_keys:
            result[key] = parsed_response.get(key) # get() defaults to None if key is missing

        # Check if all expected keys were found, even if their value is None
        # This check is more about the structure of the JSON than the presence of data
        if not all(key in parsed_response for key in expected_keys):
             logger.warning(f"AI response missing some expected keys: {parsed_response}")
             # Decide if this is an error or just a partial result
             # For now, we return what we got, but add a note.
             # result['warning'] = "AI response missing some expected keys"


        return result

    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from AI response: {e}. Response text: {response.text if 'response' in locals() else 'N/A'}")
        return {
            "zadanie_konkursowe": "Błąd parsowania JSON",
            "miejsce_zgloszenia": "Błąd parsowania JSON",
            "termin_zakonczenia": "Błąd parsowania JSON",
            "error": "Invalid JSON response"
        }
    except Exception as e:
        # This will catch other errors from the API call itself (e.g., network, API internal error)
        logger.error(f"Error calling Gemini API: {e}")
        return {
            "zadanie_konkursowe": "Błąd API",
            "miejsce_zgloszenia": "Błąd API",
            "termin_zakonczenia": "Błąd API",
            "error": f"API Error: {e}"
        }

# Example usage (for testing purposes, not part of the module's public API)
if __name__ == '__main__':
    # Configure logging for direct script execution
    logging.basicConfig(level=logging.INFO)

    # This part requires a real API key to run.
    test_api_key = os.getenv('GEMINI_API_KEY')
    if test_api_key == "YOUR_GEMINI_API_KEY":
        logger.warning("Please replace YOUR_GEMINI_API_KEY with an actual API key to test.")
    else:
        sample_post_valid = "Wygraj super nagrody! Zadanie: polub post. Zgłoszenia w komentarzu. Czas do 20.03.2025."
        analysis_valid = analyze_post(sample_post_valid, test_api_key)
        logger.info(f"Analysis (Valid Post): {analysis_valid}")

        sample_post_missing_info = "Konkurs! Do wygrania książka. Zadanie: odpowiedz na pytanie."
        analysis_missing = analyze_post(sample_post_missing_info, test_api_key)
        logger.info(f"Analysis (Missing Info): {analysis_missing}")

        analysis_empty = analyze_post("", test_api_key)
        logger.info(f"Analysis (Empty Post): {analysis_empty}")

        analysis_no_key = analyze_post("Test post", "")
        logger.info(f"Analysis (No API Key): {analysis_no_key}")

    pass # Keep the example usage commented out or conditional