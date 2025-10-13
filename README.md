## eBay Web Scraper
- A web scraper that extracts eBay listing data with anti-detection measures and exports to CSV/Excel.

## Features
- Searches ebay listings with custom search query
- Multi-page pagination support
- Can filter for listing type (auction, buy now or all)
- Anti bot detection measures (random delays, humanlike interaction and scrolling)
- Saves data into CSV and Excel file
- Robust error handling with fallbacks (swaps to old ebay html structure if needed)

## Technologies used
- Python 3.x
- Selenium for web automation
- Pandas
- openpyxl for excel support

## Installation
```bash
git clone <https://github.com/Crukzz/ebay-scraper.git>
cd ebay-scraper
pip install -r requirements.txt
```

## How to run
```bash
python ebay_scraper.py
```

## Example output:
```bash
============================================================
eBay Scraper - Starting
============================================================
Search Query: pokemon prismatic evolutions etb
Max Pages: 10

Scraping Page 1/10... ✓ 120 items
Scraping Page 2/10... ✓ 120 items
Scraping Page 3/10... ✓ 120 items
...
Scraping Page 7/10... ✓ 120 items

============================================================
SCRAPING COMPLETE
============================================================
Total items scraped: 840
Pages scraped: 7

STATISTICS
Price Range: $2.00 - $35,698.27
Average: $574.74
Median: $200.00

✓ Data saved to: pokemon_prismatic_evolutions_etb.csv
✓ Data saved to: pokemon_prismatic_evolutions_etb.xlsx
```