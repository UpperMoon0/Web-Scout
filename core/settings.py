import json
import os
from typing import Dict, Any

SETTINGS_FILE = "/app/data/settings.json"

DEFAULT_SETTINGS = {
    "max_content_length": 5000,
    "search_mode": "summary",
    "safe_search": True,
    "max_results": 10,
    "max_cache_size": 20,
    "gemini_api_keys": [],
    "gemini_model": "gemini-2.0-flash",
    "summary_prompt_template": """Based on the following search results for the query: "{query}"

Please provide a concise summary of the key findings in 2-3 paragraphs. Focus on the most relevant and important information.

Search Results:
{results_text}

Summary:""",
    "detailed_prompt_template": """Based on the following search results for the query: "{query}"

Please provide a detailed analysis in 4-5 paragraphs, covering:
1. Main themes and topics found
2. Key insights and important details
3. Different perspectives if available
4. Any notable trends or patterns

Cite specific sources when relevant.

Search Results:
{results_text}

Detailed Analysis:"""
}


def mask_api_key(key: str) -> str:
    """Mask an API key for display (show last 4 characters)."""
    if len(key) <= 4:
        return "****"
    return f"...{key[-4:]}"


def mask_api_keys(keys: list) -> list:
    """Mask a list of API keys for display."""
    return [mask_api_key(key) for key in keys]


class SettingsManager:
    def __init__(self):
        self.settings = self._load_settings()
        self._current_key_index = 0

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from JSON file or return defaults."""
        if not os.path.exists(SETTINGS_FILE):
            return DEFAULT_SETTINGS.copy()
        
        try:
            with open(SETTINGS_FILE, "r") as f:
                saved_settings = json.load(f)
                # Merge with defaults to ensure all keys exist
                return {**DEFAULT_SETTINGS, **saved_settings}
        except Exception as e:
            print(f"Error loading settings: {e}")
            return DEFAULT_SETTINGS.copy()

    def save_settings(self, new_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update and save settings to JSON file."""
        # Only update known keys to prevent pollution
        for key in DEFAULT_SETTINGS.keys():
            if key in new_settings:
                self.settings[key] = new_settings[key]
        
        try:
            os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
            with open(SETTINGS_FILE, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")
            
        return self.settings

    def get_settings(self) -> Dict[str, Any]:
        """Get current settings with masked API keys."""
        # Return a copy with masked API keys
        settings = self.settings.copy()
        settings["gemini_api_keys"] = mask_api_keys(settings.get("gemini_api_keys", []))
        return settings

    def get_raw_api_keys(self) -> list:
        """Get raw (unmasked) API keys for internal use."""
        return self.settings.get("gemini_api_keys", [])

    def get_api_key_count(self) -> int:
        """Get the number of configured API keys."""
        return len(self.settings.get("gemini_api_keys", []))

    def get_current_api_key_index(self) -> int:
        """Get the current API key index for round-robin."""
        return self._current_key_index % max(1, self.get_api_key_count())

    def advance_api_key(self) -> None:
        """Advance to the next API key in round-robin."""
        self._current_key_index = (self._current_key_index + 1) % max(1, self.get_api_key_count())

    def get(self, key: str) -> Any:
        """Get a specific setting value."""
        return self.settings.get(key, DEFAULT_SETTINGS.get(key))

# Global instance
settings_manager = SettingsManager()
