"""One-time setup: log into Google and save the browser profile."""

from pathlib import Path

from playwright.sync_api import sync_playwright

from core.config_manager import ConfigManager

BASE_DIR = Path(__file__).resolve().parent


def main() -> None:
    config_manager = ConfigManager()
    config = config_manager.get_config()
    profile_dir = config_manager.resolve_path(config["browser"]["persistent_profile"])

    print("=" * 50)
    print("Google Login Setup")
    print("=" * 50)
    print(f"Profile directory: {profile_dir}")
    print()

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=False,
            channel="chrome",
        )
        page = context.new_page()
        page.goto("https://accounts.google.com")
        input("Log in completely, then press Enter...")
        context.close()

    print("Login saved. You can now run main.py.")


if __name__ == "__main__":
    main()
