import os
import sys
from unittest.mock import MagicMock

# Mock pydantic-settings
class MockBaseSettings:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    def __getattr__(self, name):
        # Handle default values defined in Settings class
        from app.config import Settings
        return getattr(Settings, name)

m = MagicMock()
m.BaseSettings = MockBaseSettings
m.SettingsConfigDict = lambda **kwargs: None
sys.modules["pydantic_settings"] = m

from app.config import Settings

def test_default_api_host():
    """Verify that the default API_HOST is set to 127.0.0.1 for security."""
    # Ensure environment variable is not set to interfere with the test
    if "API_HOST" in os.environ:
        del os.environ["API_HOST"]

    # We can't easily instantiate if we mock pydantic because it won't do the field processing
    # but we can check the class attribute if it is defined there
    assert Settings.API_HOST == "127.0.0.1"
