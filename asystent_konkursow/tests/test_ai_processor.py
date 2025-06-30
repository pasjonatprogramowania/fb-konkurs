import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Adjust path to import ai_processor from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now try to import the module. This will fail if ai_processor.py doesn't exist
# or doesn't have the analyze_post function yet, but that's expected for TDD.
try:
    from ai_processor import analyze_post
except ImportError:
    # Define a placeholder if the import fails, so the test file can be written
    # without the ai_processor module being fully implemented yet.
    def analyze_post(post_content: str, api_key: str) -> dict:
        raise NotImplementedError("ai_processor.analyze_post is not yet implemented")


class TestAiProcessor(unittest.TestCase):

    @patch('ai_processor.genai.GenerativeModel')
    def test_successful_analysis(self, MockGenerativeModel):
        mock_model_instance = MockGenerativeModel.return_value
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "zadanie_konkursowe": "Opisz swoje ulubione wakacje",
            "miejsce_zgloszenia": "W komentarzu pod postem",
            "termin_zakonczenia": "2024-12-31"
        })
        mock_model_instance.generate_content.return_value = mock_response

        with patch('ai_processor.genai.configure') as mock_configure:
            api_key = "test_api_key"
            post_content = "To jest przykładowy post konkursowy."

            expected_result = {
                "zadanie_konkursowe": "Opisz swoje ulubione wakacje",
                "miejsce_zgloszenia": "W komentarzu pod postem",
                "termin_zakonczenia": "2024-12-31"
            }

            # Ensure no WARNING or ERROR logs are emitted during this successful test case
            if hasattr(self, 'assertNoLogs'): # Python 3.10+
                with self.assertNoLogs('ai_processor', level='WARNING'):
                    actual_result = analyze_post(post_content, api_key)
            else:
                actual_result = analyze_post(post_content, api_key) # Rely on overall clean output for older Pythons

            self.assertEqual(actual_result, expected_result)
            mock_configure.assert_called_once_with(api_key=api_key)
            MockGenerativeModel.assert_called_once_with('gemini-pro')
            mock_model_instance.generate_content.assert_called_once()

    @patch('ai_processor.genai.GenerativeModel')
    def test_handling_missing_information(self, MockGenerativeModel):
        mock_model_instance = MockGenerativeModel.return_value
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "zadanie_konkursowe": "Opisz swoje ulubione wakacje",
            "miejsce_zgloszenia": None,
            "termin_zakonczenia": "2024-12-31"
        })
        mock_model_instance.generate_content.return_value = mock_response

        with patch('ai_processor.genai.configure') as mock_configure:
            api_key = "test_api_key_missing_info"
            post_content = "Post z brakującymi informacjami."

            expected_result = {
                "zadanie_konkursowe": "Opisz swoje ulubione wakacje",
                "miejsce_zgloszenia": None,
                "termin_zakonczenia": "2024-12-31"
            }

            if hasattr(self, 'assertNoLogs'): # Python 3.10+
                with self.assertNoLogs('ai_processor', level='WARNING'):
                    actual_result = analyze_post(post_content, api_key)
            else:
                actual_result = analyze_post(post_content, api_key)

            self.assertEqual(actual_result, expected_result)
            mock_configure.assert_called_once_with(api_key=api_key)
            MockGenerativeModel.assert_called_once_with('gemini-pro')
            mock_model_instance.generate_content.assert_called_once()

    @patch('ai_processor.genai.GenerativeModel')
    def test_handling_invalid_json_response(self, MockGenerativeModel):
        mock_model_instance = MockGenerativeModel.return_value
        mock_response = MagicMock()
        invalid_json_text = "To nie jest poprawny JSON"
        mock_response.text = invalid_json_text
        mock_model_instance.generate_content.return_value = mock_response

        with patch('ai_processor.genai.configure') as mock_configure:
            api_key = "test_api_key_invalid_json"
            post_content = "Post który spowoduje błąd JSON."

            expected_error_result = {
                "zadanie_konkursowe": "Błąd parsowania JSON",
                "miejsce_zgloszenia": "Błąd parsowania JSON",
                "termin_zakonczenia": "Błąd parsowania JSON",
                "error": "Invalid JSON response"
            }

            # Use assertLogs to capture and verify log messages
            # ai_processor.logger is the logger instance in ai_processor.py
            # We need to make sure it's accessible or patch 'ai_processor.logger'
            # For now, assuming 'ai_processor.logger' is the correct path to the logger.
            # If ai_processor.py uses logging.getLogger(__name__), then the logger name is 'ai_processor'.
            with self.assertLogs('ai_processor', level='ERROR') as log_context:
                actual_result = analyze_post(post_content, api_key)

            self.assertIn("error", actual_result)
            self.assertEqual(actual_result.get("zadanie_konkursowe"), "Błąd parsowania JSON")
            self.assertEqual(actual_result.get("miejsce_zgloszenia"), "Błąd parsowania JSON")
            self.assertEqual(actual_result.get("termin_zakonczenia"), "Błąd parsowania JSON")
            self.assertEqual(actual_result.get("error"), "Invalid JSON response")

            # Verify log messages
            # The first log message comes from the attempt to find JSON with index()
            self.assertTrue(any(f"Could not find JSON in response: {invalid_json_text}" in record.getMessage() for record in log_context.records))
            # The second log message comes from the json.JSONDecodeError
            self.assertTrue(any(f"Error decoding JSON from AI response" in record.getMessage() and invalid_json_text in record.getMessage() for record in log_context.records))

            mock_configure.assert_called_once_with(api_key=api_key)
            MockGenerativeModel.assert_called_once_with('gemini-pro')
            mock_model_instance.generate_content.assert_called_once()

    @patch('ai_processor.genai.GenerativeModel')
    def test_handling_api_error(self, MockGenerativeModel):
        # Configure the mock to raise an exception when generate_content is called
        mock_model_instance = MockGenerativeModel.return_value
        simulated_error_message = "Simulated API Error"
        mock_model_instance.generate_content.side_effect = Exception(simulated_error_message)

        with patch('ai_processor.genai.configure') as mock_configure:
            api_key = "test_api_key_api_error"
            post_content = "Post który spowoduje błąd API."

            expected_error_result = {
                "zadanie_konkursowe": "Błąd API",
                "miejsce_zgloszenia": "Błąd API",
                "termin_zakonczenia": "Błąd API",
                "error": f"API Error: Exception('{simulated_error_message}')" # Match the actual error string
            }

            with self.assertLogs('ai_processor', level='ERROR') as log_context:
                actual_result = analyze_post(post_content, api_key)

            self.assertIn("error", actual_result)
            self.assertEqual(actual_result.get("zadanie_konkursowe"), "Błąd API")
            self.assertEqual(actual_result.get("miejsce_zgloszenia"), "Błąd API")
            self.assertEqual(actual_result.get("termin_zakonczenia"), "Błąd API")
            # The error message in the dict includes the string representation of the exception
            self.assertTrue(simulated_error_message in actual_result.get("error"))

            # Verify log messages
            self.assertTrue(any(f"Error calling Gemini API: {simulated_error_message}" in record.getMessage() for record in log_context.records))

            mock_configure.assert_called_once_with(api_key=api_key)
            MockGenerativeModel.assert_called_once_with('gemini-pro')
            mock_model_instance.generate_content.assert_called_once()

    @patch('ai_processor.genai.configure') # Patch configure
    @patch('ai_processor.genai.GenerativeModel') # Patch GenerativeModel
    def test_empty_post_content(self, MockGenerativeModel, mock_configure):
        # No API call should be made if post_content is empty, or it might return specific nulls.
        # Let's assume it should return a dict with all fields as None or a specific note.
        # This depends on the desired behavior defined in ai_processor.py.
        # Option 1: It tries to analyze and AI returns nulls (less likely for empty string)
        # Option 2: It short-circuits and returns nulls/error immediately.

        api_key = "test_api_key_empty_post"
        post_content = "" # Empty post content

        expected_result_empty_post = {
            "zadanie_konkursowe": None,
            "miejsce_zgloszenia": None,
            "termin_zakonczenia": None,
            "error": "Empty post content"
        }

        # Capture WARNING logs from 'ai_processor'
        with self.assertLogs('ai_processor', level='WARNING') as log_context:
            actual_result = analyze_post(post_content, api_key)

        self.assertEqual(actual_result, expected_result_empty_post)

        # Verify log messages
        self.assertTrue(any("Post content is empty. Skipping analysis." in record.getMessage() for record in log_context.records))

        # Ensure API was not called for generate_content, but configure might be.
        mock_configure.assert_called_once_with(api_key=api_key)
        MockGenerativeModel.return_value.generate_content.assert_not_called()

        # Alternative: If it does call the API, the test would be similar to test_successful_analysis
        # but expecting nulls or specific values for empty content.
        # For now, assuming it short-circuits.

    def test_missing_api_key(self):
        post_content = "Some post content"
        api_key = "" # Empty API key

        expected_error_result = {
            "zadanie_konkursowe": "Błąd konfiguracji",
            "miejsce_zgloszenia": "Błąd konfiguracji",
            "termin_zakonczenia": "Błąd konfiguracji",
            "error": "API key is missing"
        }

        with self.assertLogs('ai_processor', level='ERROR') as log_context:
            actual_result = analyze_post(post_content, api_key)

        self.assertEqual(actual_result, expected_error_result)
        self.assertTrue(any("API key is missing." in record.getMessage() for record in log_context.records))

    @patch('ai_processor.genai.configure')
    def test_genai_configure_error(self, mock_genai_configure):
        simulated_config_error_msg = "Simulated genai.configure() error"
        mock_genai_configure.side_effect = Exception(simulated_config_error_msg)

        api_key = "valid_api_key_but_config_fails"
        post_content = "Some post content"

        expected_error_result = {
            "zadanie_konkursowe": "Błąd konfiguracji API",
            "miejsce_zgloszenia": "Błąd konfiguracji API",
            "termin_zakonczenia": "Błąd konfiguracji API",
            "error": f"Error configuring Gemini API: {simulated_config_error_msg}" # Corrected expected error string
        }

        with self.assertLogs('ai_processor', level='ERROR') as log_context:
            actual_result = analyze_post(post_content, api_key)

        self.assertEqual(actual_result, expected_error_result)
        self.assertTrue(
            any(f"Error configuring Gemini API: {simulated_config_error_msg}" in record.getMessage()
                for record in log_context.records)
        )
        mock_genai_configure.assert_called_once_with(api_key=api_key)

if __name__ == '__main__':
    unittest.main()
