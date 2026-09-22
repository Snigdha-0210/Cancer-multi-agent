import os


# Development mode allows us to test the complete application
# without making live OpenAI calls.
#
# Set:
#   APP_MODE=mock
#
# for offline development.
#
# Set:
#   APP_MODE=live
#
# when the OpenAI API is available again.

APP_MODE = os.getenv("APP_MODE", "mock").lower()


def is_mock_mode() -> bool:
    return APP_MODE == "mock"


def is_live_mode() -> bool:
    return APP_MODE == "live"