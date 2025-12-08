
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, '/home/jules')


# Now, we can import and run the verification script
from verification.verify import run, setup_data
from playwright.sync_api import sync_playwright

if __name__ == '__main__':
    setup_data()
    with sync_playwright() as playwright:
        run(playwright)
