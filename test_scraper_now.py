"""
Test the daily scraper manually (without waiting for scheduled time)
"""

import sys
sys.path.insert(0, '/var/www/hcsbot/backend')

import os
os.chdir('/var/www/hcsbot')

from backend.daily_scraper import DailyScraper

print("Testing daily scraper manually...")
print("This will scrape for new articles and add them to the database.")
print()

scraper = DailyScraper()
scraper.run_daily_scrape()

print("\nTest complete!")
print("Stats:", scraper.get_stats())
