import os
import unittest
from unittest.mock import patch, Mock

from src import playstore

class TestPlaystoreResolver(unittest.TestCase):

    def setUp(self):
        # Reset cache before each test
        playstore._exodus_cache = {}
        # Ensure API key is set for tests to pass auth check
        os.environ["EXODUS_API_KEY"] = "test_token"

    @patch('src.playstore.requests.get')
    def test_exact_match_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "com.instagram.android": {
                "reports": [
                    {"version": "2.371.0", "version_code": "29652157"},
                    {"version": "2.369.0", "version_code": "29633241"}
                ]
            }
        }
        mock_get.return_value = mock_response

        code = playstore.resolve_version_code("com.instagram.android", "2.371.0")
        self.assertEqual(code, 29652157)
        mock_get.assert_called_once()

    @patch('src.playstore.requests.get')
    def test_version_not_present(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "com.instagram.android": {
                "reports": [
                    {"version": "2.369.0", "version_code": "29633241"}
                ]
            }
        }
        mock_get.return_value = mock_response

        with self.assertRaises(playstore.VersionNotFound):
            playstore.resolve_version_code("com.instagram.android", "2.371.0")

    @patch('src.playstore.requests.get')
    def test_malformed_version_code(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "com.instagram.android": {
                "reports": [
                    {"version": "2.371.0", "version_code": "not_an_int"}
                ]
            }
        }
        mock_get.return_value = mock_response

        with self.assertRaises(ValueError):
            playstore.resolve_version_code("com.instagram.android", "2.371.0")

    @patch('src.playstore.requests.get')
    def test_http_error(self, mock_get):
        import requests
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.RequestException("HTTP 401")
        mock_get.return_value = mock_response

        with self.assertRaises(playstore.ExodusApiError):
            playstore.resolve_version_code("com.instagram.android", "2.371.0")

    @patch('src.playstore.requests.get')
    def test_missing_package_key(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"different.package": {}}
        mock_get.return_value = mock_response

        with self.assertRaises(playstore.ExodusApiError):
            playstore.resolve_version_code("com.instagram.android", "2.371.0")
            
    @patch('src.playstore.requests.get')
    def test_multiple_exact_matches(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "com.instagram.android": {
                "reports": [
                    {"version": "2.371.0", "version_code": "100"},
                    {"version": "2.371.0", "version_code": "200"}
                ]
            }
        }
        mock_get.return_value = mock_response

        # Should select max version code
        code = playstore.resolve_version_code("com.instagram.android", "2.371.0")
        self.assertEqual(code, 200)

    @patch('src.playstore.requests.get')
    def test_cli_version_code_precedence(self, mock_get):
        from src import utils
        utils.cli_version_codes[("au.com.shiftyjelly.pocketcasts", "8.16")] = {
            "arm64_v8a": 9441,
            "universal": 9441
        }
        code = playstore.resolve_version_code("au.com.shiftyjelly.pocketcasts", "8.16", "arm64-v8a")
        self.assertEqual(code, 9441)
        mock_get.assert_not_called()

    @patch('src.playstore.scrape_exodus_version_code')
    @patch('src.playstore.requests.get')
    def test_exodus_web_fallback_success(self, mock_get, mock_scrape):
        import requests
        # API returns 401 Unauthorized
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.RequestException("HTTP 401: Invalid token")
        mock_get.return_value = mock_response

        # Web scraper returns resolved version code
        mock_scrape.return_value = 14348020

        code = playstore.resolve_version_code("com.pinterest", "14.34.0")
        self.assertEqual(code, 14348020)
        mock_scrape.assert_called_once_with("com.pinterest", "14.34.0")

if __name__ == '__main__':
    unittest.main()
