from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import random
from datetime import datetime


class EbayScraper:
    def __init__(self, headless=True):
        self.items_list = []
        self.driver = None
        self.headless = headless
        
    def setup_driver(self):
        options = webdriver.ChromeOptions()
        
        #Anti bot detection measures
        options.add_argument('--disable-bots')
        options.add_argument('--disable-automation')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        
        if self.headless:
            options.add_argument('--headless=new')

        #Sets use agent, anti bot detection
        options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        print("Initializing Chrome driver...")
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(30)
        self.driver.set_window_size(1920, 1080)
        
        print("✓ Driver initialized successfully")
        
    def build_search_url(self, search_query, items_per_page=100, listing_type="all", category=None):

        base_url = "https://www.ebay.com/sch/i.html"
        
        params = []
        params.append(f"_nkw={search_query.replace(' ', '+')}")
        params.append(f"_ipg={items_per_page}")
        if listing_type == "auction":
            params.append("LH_Auction=1")
        elif listing_type == "buynow":
            params.append("LH_BIN=1")
            
        if category:
            params.append(f"_dcat={category}")
            
        url = f"{base_url}?{'&'.join(params)}"
        return url
        
        #Mimics human behavior through scrolling patterns and delays
    def human_delay(self, min_seconds=2, max_seconds=5):
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
        
    def scroll_page(self):
        #Scrolls to middle
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(random.uniform(0.5, 1.5))
        
        #Scrolls to bottom
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(0.5, 1.5))
        
        #Scrolls back up a bit
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
        time.sleep(random.uniform(0.3, 0.8))
        
    def scrape_page(self):
        #Tries multiple selectors because eBay changes these frequently
        possible_selectors = [
            (By.CSS_SELECTOR, "li.s-card"),  #Current eBay structure (October 2025)
            (By.CSS_SELECTOR, "li.s-item"),  #Older structure
            (By.CSS_SELECTOR, "div.s-item__info"),
        ]
        
        items = []
        for selector_type, selector_value in possible_selectors:
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((selector_type, selector_value))
                )
                items = self.driver.find_elements(selector_type, selector_value)
                if len(items) > 0:
                    break
            except TimeoutException:
                continue
        
        if len(items) == 0:
            print("  ⚠ No items found")
            with open('ebay_debug.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            print("  → Saved page source to ebay_debug.html")
            return 0
            
        #Scrolls to load lazy images
        self.scroll_page()
        
        #Filters out empty/separator items to avoid breaks
        valid_items = []
        for item in items:
            text = item.text or ''
            if len(text.strip()) > 30:
                valid_items.append(item)
        
        scraped_count = 0
        
        for idx, item in enumerate(valid_items, 1):
            try:
                if not item.text or len(item.text.strip()) < 30:
                    continue

                title = None
                title_selectors = [
                    ".su-card-container__header",
                    ".su-card-container__content",
                    "div.s-item__title",
                    "h3.s-item__title",
                    ".s-item__title",
                ]
                
                for selector in title_selectors:
                    try:
                        title_elem = item.find_element(By.CSS_SELECTOR, selector)
                        title = title_elem.text.strip()
                        #Removes hidden "Opens in a new window or tab" suffix for cleaner data
                        if "Opens in a new window" in title:
                            title = title.split("Opens in a new window")[0].strip()
                        if title and title not in ["Shop on eBay", "", "New Listing"]:
                            break
                    except NoSuchElementException:
                        continue
                
                if not title or title in ["Shop on eBay", "", "New Listing"]:
                    continue

                price = "N/A"
                price_selectors = [
                    "span.s-card__price",
                    ".su-styled-text.s-card__price",
                    ".s-item__price",
                    "span.s-item__price",
                ]
                for selector in price_selectors:
                    try:
                        price_elem = item.find_element(By.CSS_SELECTOR, selector)
                        price = price_elem.text.strip()
                        if price:
                            break
                    except NoSuchElementException:
                        continue
                
                #Extracts link
                link = "N/A"
                try:
                    #Tries current ebay structure first
                    link_elem = item.find_element(By.CSS_SELECTOR, "a.image-treatment")
                    link = link_elem.get_attribute("href")
                    if link:
                        link = link.split('?')[0]
                except NoSuchElementException:
                    try:
                        #Fallback to former structure
                        link_elem = item.find_element(By.CSS_SELECTOR, "a.s-item__link")
                        link = link_elem.get_attribute("href")
                        if link:
                            link = link.split('?')[0]
                    except NoSuchElementException:
                        pass
                
                image_url = "N/A"
                try:
                    img_selectors = [
                        "img.s-card__image",
                        ".s-item__image-wrapper img",
                        "img",
                    ]
                    for selector in img_selectors:
                        try:
                            img_element = item.find_element(By.CSS_SELECTOR, selector)
                            image_url = img_element.get_attribute("src")
                            if not image_url:
                                image_url = img_element.get_attribute("data-src")
                            if image_url and ("ebayimg" in image_url or "http" in image_url):
                                break
                        except NoSuchElementException:
                            continue
                except:
                    pass
                
                shipping = "N/A"
                shipping_selectors = [
                    ".s-card__shipping",
                    ".s-item__shipping",
                    "span.s-item__shipping",
                ]
                for selector in shipping_selectors:
                    try:
                        shipping_elem = item.find_element(By.CSS_SELECTOR, selector)
                        shipping = shipping_elem.text.strip()
                        if shipping:
                            break
                    except NoSuchElementException:
                        continue
                
                #For auctions: extracts time left
                time_left = "N/A"
                time_selectors = [
                    ".s-card__time-left",
                    ".s-item__time-left",
                    "span.s-item__time-left",
                ]
                for selector in time_selectors:
                    try:
                        time_elem = item.find_element(By.CSS_SELECTOR, selector)
                        time_left = time_elem.text.strip()
                        if time_left:
                            break
                    except NoSuchElementException:
                        continue

                item_dict = {
                    'Title': title,
                    'Price': price,
                    'Shipping': shipping,
                    'Time Left': time_left,
                    'Link': link,
                    'Image URL': image_url,
                    'Scraped At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                self.items_list.append(item_dict)
                scraped_count += 1
                
            except Exception as e:
                #Silently skips items with errors for consistency and avoiding breaks
                continue
        
        return scraped_count
        
    def has_next_page(self):
        try:
            next_button = self.driver.find_element(By.CSS_SELECTOR, "a.pagination__next")
            classes = next_button.get_attribute("class")
            aria_disabled = next_button.get_attribute("aria-disabled")
            
            if "disabled" in classes or aria_disabled == "true":
                return False
            return True
            
        except NoSuchElementException:
            return False
            
    def click_next_page(self):
        try:
            next_button = self.driver.find_element(By.CSS_SELECTOR, "a.pagination__next")
            
            #Scroll to center
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
            time.sleep(1)

            #Uses JS to click to bypass overlay blocking
            self.driver.execute_script("arguments[0].click();", next_button)
            
            time.sleep(2)
            return True
            
        except Exception as e:
            print(f"  ✗ Error clicking next page: {e}")
            return False
            
    def scrape(self, search_query, max_pages=10, items_per_page=60, 
               listing_type="all", category=None, output_file='ebay_results.csv'):
        print("="*60)
        print(f"eBay Scraper - Starting")
        print("="*60)
        print(f"Search Query: {search_query}")
        print(f"Max Pages: {max_pages}")
        print(f"Items Per Page: {items_per_page}")
        print("="*60 + "\n")
        
        try:
            self.setup_driver()
            
            url = self.build_search_url(search_query, items_per_page, listing_type, category)
            print(f"Search URL: {url}\n")
            
            print("Loading first page...")
            self.driver.get(url)
            self.human_delay(3, 5)
        
            page_number = 1
            
            while page_number <= max_pages:
                print(f"\n{'─'*60}")
                print(f"Scraping Page {page_number}/{max_pages}")
                print(f"{'─'*60}")

                scraped = self.scrape_page()
                print(f"  ✓ Scraped {scraped} items from page {page_number}")
                print(f"  Total items collected: {len(self.items_list)}")
                
                if page_number < max_pages and self.has_next_page():
                    print(f"  → Moving to page {page_number + 1}...")
                    
                    #Delay before clicking to mimic human behavior
                    self.human_delay(3, 6)
                    
                    if self.click_next_page():
                        page_number += 1
                        self.human_delay(2, 4)
                    else:
                        print("  ✗ Could not navigate to next page")
                        break
                else:
                    if page_number >= max_pages:
                        print(f"\n  Reached maximum page limit ({max_pages})")
                    else:
                        print("\n  No more pages available")
                    break
            
            print("\n" + "="*60)
            print("SCRAPING COMPLETE")
            print("="*60)
            print(f"Total items scraped: {len(self.items_list)}")
            print(f"Pages scraped: {page_number}")
            
            if self.items_list:
                df = pd.DataFrame(self.items_list)
                
                csv_file = output_file
                excel_file = output_file.replace('.csv', '.xlsx')
                
                df.to_csv(csv_file, index=False)
                print(f"✓ Data saved to CSV: {csv_file}")
                
                try:
                    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='eBay Results')
                        worksheet = writer.sheets['eBay Results']
                        for idx, col in enumerate(df.columns):
                            max_length = max(
                                df[col].astype(str).apply(len).max(),
                                len(col)
                            )
                            max_length = min(max_length, 50)
                            worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2
                    
                    print(f"✓ Data saved to Excel: {excel_file}")
                except ImportError:
                    print("⚠ openpyxl not installed. Install with: pip install openpyxl")
                    print("  CSV file was still saved successfully.")
                return df
            else:
                print("⚠ No items were collected")
                return None
                
        except Exception as e:
            print(f"\n✗ Fatal error: {e}")
            return None
            
        finally:
            #Closes the browser to limit resource use
            if self.driver:
                print("\nClosing browser...")
                self.driver.quit()
                print("✓ Browser closed")


def main():

    """
    Main function - handles user input and runs the scraper
    
    Prompts user for:
    -Search query
    -Listing type (auction/buynow/all)
    
    Outputs:
    -CSV file with results
    -Excel file with formatted data
    -Statistics summary
    """

    scraper = EbayScraper(headless=True)  #Set to True to hide browser for efficiency (set to False to see browser)

    search_query = input("What do you want to search for?")
    if not search_query:
        print("Error: Search query cannot be empty!")
        return
    print("\nListing Type:")
    print("  [A] Auctions only")
    print("  [B] Buy Now only")
    print("  [Anything other than A or B] All listings")
    choice = input("Enter choice: ").strip().upper()
    if choice == "A":
        listing_type = "auction"
    elif choice == "B":
        listing_type = "buynow"
    else:
        listing_type = "all"  #Default
    print(f"Selected: {listing_type}")

    max_pages = 10
    items_per_page = 100 
    safe_filename = search_query.replace(' ', '_')
    safe_filename = safe_filename.replace('/', '-')
    safe_filename = safe_filename.replace(':', '')
    safe_filename = safe_filename.replace('?', '')
    safe_filename = safe_filename.replace('*', '')
    safe_filename = safe_filename.lower()
    output_file = f"{safe_filename}.csv"
    
    df = scraper.scrape(
        search_query=search_query,
        max_pages=max_pages,
        items_per_page=items_per_page,
        listing_type=listing_type,
        output_file=output_file
    )

    if df is not None:
        print("\n" + "="*60)
        print("STATISTICS")
        print("="*60)
        print(f"Total items: {len(df)}")
        print(f"Unique titles: {df['Title'].nunique()}")
        try:
            #Clean price column
            df['Price_Numeric'] = df['Price'].str.replace('$', '').str.replace(',', '')
            df['Price_Numeric'] = pd.to_numeric(df['Price_Numeric'], errors='coerce')
            if df['Price_Numeric'].notna().any():
                print(f"\nPrice Range:")
                print(f"  Min: ${df['Price_Numeric'].min():.2f}")
                print(f"  Max: ${df['Price_Numeric'].max():.2f}")
                print(f"  Average: ${df['Price_Numeric'].mean():.2f}")
                print(f"  Median: ${df['Price_Numeric'].median():.2f}")
        except:
            pass

if __name__ == "__main__":
    main()
