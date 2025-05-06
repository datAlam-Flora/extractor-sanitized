import tempfile
import platform
import shutil
import zipfile
import json
import time
import calendar
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.support.expected_conditions import any_of
from selenium.webdriver.common.action_chains import ActionChains
from dagster import MaterializeResult, MetadataValue
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from urllib.parse import urlparse
from pathlib import Path
import sys
import threading
import itertools
import time
import math
import os
import colorsys
from colorama import Fore, Back, Style, init

current_directory = os.getcwd()  # Get current working directory
utils_dir = os.path.join(current_directory, "scripts", "utils")  # Assuming "scripts" is the folder

if utils_dir not in sys.path:
    sys.path.append(utils_dir)

creds_dir = os.path.join(current_directory, ".key", "credentials.json")

### **Step 1: Load Data from JSON Files**
def load_credentials():
    """Load credentials from JSON file."""
    with open(creds_dir, "r") as file:
        return json.load(file)

def initialize_driver():
    """Initialize and return Selenium WebDriver with download handling."""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--mute-audio")  # ✅ Mutes audio in Chrome
    options.add_argument("--headless")  # Run Chrome in headless mode
    options.add_argument("--disable-gpu")
    # options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920, 1080")
    options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    options.add_argument("--log-level=3")  # Suppress all logs (ERROR level only)
    options.add_argument("--disable-logging")  # Disable logging
    options.add_argument("--disable-webgl")  # Disable WebGL

    # ✅ Get the current directory and set "Downloads" folder
    current_directory = os.getcwd()  # Get current working directory
    download_dir = os.path.join(current_directory, "downloads", "ss")
    os.makedirs(download_dir, exist_ok=True)   

    # ✅ Prevents "Save As" window and auto-downloads files
    prefs = {
        "download.default_directory": download_dir,  # ✅ Sets default download folder
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_settings.popups": 0
    }

    options.add_experimental_option("prefs", prefs)

    # ✅ Create WebDriver instance and return it
    driver = webdriver.Chrome(options=options)

    # ✅ Move window to Screen 2
    try:
        driver.set_window_position(-1920, 0)  # Move to second screen (assuming 1920px width for first screen)
        time.sleep(0.5) # Allow time for window to move
        driver.set_window_size(1920, 1080)
        print("✅ Moved browser to right-side screen.")
    except Exception as e:
        print(f"❌ Failed to move browser window: {e}")

    return driver, download_dir  # <-- Fix: return the driver instance


def login(driver, url, creds):
    """Perform login on the given URL using credentials."""
    try:
        driver.get(url)
        print(f"🌍 Attempting to log in: Superswan")

        # Wait for the login page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#password-input"))
        )

        # Fill in Username
        username_field = driver.find_element(By.CSS_SELECTOR, "div.form-control > input:nth-child(1)")
        username_field.clear()
        username_field.send_keys(creds["username"])

        # Fill in Password
        password_field = driver.find_element(By.CSS_SELECTOR, "#password-input")
        password_field.clear()
        password_field.send_keys(creds["password"])

        # Click Login Button
        login_button = driver.find_element(By.CSS_SELECTOR, ".btn-submit")
        login_button.click()
        print("✅ Login form submitted")

        wait_for_browser_to_load(driver)

        dashboard_url = f"{url}/#/home"

        WebDriverWait(driver, 10).until(
            any_of(
                EC.url_to_be(dashboard_url)  # ✅ Detects redirection immediately
            )
        )

        wait_for_browser_to_load(driver)

        print(f"✅ Successfully logged into Superswan.\n")
    
    except Exception as e:
        print(f"❌ Error logging into {url}: {str(e)}")

def deposit(driver, url, creds, download_dir):
    """Clicks on '3. Transaction', then '3.3. Member Deposit', handles currency selection per brand, and prepares for export."""
    
    wait_for_browser_to_load(driver)

    # ✅ Check for the popup and click "Close" if it appears
    try:
        close_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-submit') and normalize-space(text())='Close']"))
        )
        close_button.click()
        print("✅ Popup detected and closed.")
        time.sleep(1)  # ✅ Small delay after closing popup
    except (TimeoutException, NoSuchElementException):
        print("✅ No popup detected, continuing...")

    # ✅ Click "3. Transaction"
    try:
        transaction_menu = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#left-menu-body > jhi-sub-left-menu-component > ul > li:nth-child(4) > div > div.row.parent-row.h-auto > a > ul > li:nth-child(2)"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", transaction_menu)  # ✅ Ensure it's in view
        ActionChains(driver).move_to_element(transaction_menu).click().perform()
        print("✅ Clicked '3. Transaction' menu.")
        time.sleep(1)  # ✅ Allow dropdown to expand
    except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
        print("❌ Failed to find or click '3. Transaction' menu.")
        return

    # ✅ Click "3.3. Member Deposit"
    try:
        member_deposit_menu = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#left-menu-body > jhi-sub-left-menu-component > ul > li:nth-child(4) > div > div.row.children-row.expand > jhi-sub-left-menu-component > ul > li:nth-child(1) > div > div > a > ul > li:nth-child(2)"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", member_deposit_menu)  # ✅ Ensure it's in view
        ActionChains(driver).move_to_element(member_deposit_menu).click().perform()
        print("🌍 Clicked '3.3. Member Deposit' menu.")
        time.sleep(1)  # ✅ Allow page to load
    except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
        print("\n❌ Failed to find or click '3.3. Member Deposit' menu.")
        return

    time.sleep(1)  # ✅ Retain original delay before proceeding
    wait_for_browser_to_load(driver)
    time.sleep(3)

    deposit_nav(driver, creds, download_dir)


def withdrawal(driver, url, creds, download_dir):
    """Clicks on '3. Transaction', then '3.4. Member Withdraw', handles currency selection per brand, and prepares for export."""
    
    wait_for_browser_to_load(driver)

        # ✅ Click "3. Transaction"
    try:
        transaction_menu = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#left-menu-body > jhi-sub-left-menu-component > ul > li:nth-child(4) > div > div.row.parent-row.h-auto > a > ul > li:nth-child(2)"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", transaction_menu)  # ✅ Ensure it's in view
        ActionChains(driver).move_to_element(transaction_menu).click().perform()
        print("✅ Clicked '3. Transaction' menu.")
        time.sleep(1)  # ✅ Allow dropdown to expand
    except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
        print("❌ Failed to find or click '3. Transaction' menu.")
        return

        # ✅ Click "3.4. Member Withdraw"
    try:
        member_withdraw_menu = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#left-menu-body > jhi-sub-left-menu-component > ul > li:nth-child(4) > div > div.row.children-row.expand > jhi-sub-left-menu-component > ul > li:nth-child(2) > div > div > a > ul > li:nth-child(2)"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", member_withdraw_menu)  # ✅ Ensure it's in view
        ActionChains(driver).move_to_element(member_withdraw_menu).click().perform()
        print("🌍 Clicked '3.4. Member Withdraw' menu.")
        time.sleep(1)  # ✅ Allow page to load
    except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
        print("\n❌ Failed to find or click '3.4. Member Withdraw' menu.")
        return

    time.sleep(1)  # ✅ Retain original delay before proceeding
    wait_for_browser_to_load(driver)

    withdrawal_nav(driver, creds, download_dir)

def deposit_nav(driver, creds, download_dir):
    """Handles the deposit form by selecting values based on credentials.json."""

    actions = ActionChains(driver)  # Create an ActionChains instance

    # Get yesterday's UTC datetime range
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_dt = {
        "start": yesterday.replace(hour=0, minute=0, second=0, microsecond=0),
        "end": yesterday.replace(hour=23, minute=59, second=59, microsecond=0)
    }
    
    # ✅ Iterate over each brand in the creds dictionary
    for brand in creds.get("brand", []):
        if brand not in creds:
            print(f"⚠️ No data for {brand}, skipping...")
            continue
        
        brand_name = creds[brand][0]  # e.g., "Acewin8", "Ivip9", "UEABET"
        country = creds[brand][1]     # e.g., "Cambodia", "Singapore"
        time_offset = int(creds[brand][2])  # Time offset (if needed)

        # Calculate country-specific datetime range
        country_dt = {
            "start": yesterday_dt["start"] + timedelta(hours=time_offset),
            "end": yesterday_dt["end"] + timedelta(hours=time_offset)
        }

        print(f"\n🔍 Selecting values for brand: {brand} ({brand_name}, {country})")

        # **Step 1: Click the dropdown to select the brand**
        try:
            brand_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".search-navbar-nav > li:nth-child(1) > jhi-single-select-shared-component:nth-child(1) > div:nth-child(1) > div:nth-child(2)"))
            )
            
            # Retry mechanism for handling click interception
            attempts = 0
            max_attempts = 69
            while attempts < max_attempts:
                try:
                    # Scroll into view and click
                    driver.execute_script("arguments[0].scrollIntoView(true);", brand_dropdown)
                    actions.move_to_element(brand_dropdown).perform()
                    brand_dropdown.click()  # Click to open dropdown
                    print(f"✅ Opened brand selection dropdown.")
                    break
                except ElementClickInterceptedException:
                    print(f"⚠️ Element click intercepted! Retrying... {attempts + 1}/{max_attempts}")
                    attempts += 1  # Wait before retrying
            else:
                print(f"❌ Failed to open brand dropdown for {brand}.")
                continue  # Skip to the next brand if dropdown cannot be clicked

        except (TimeoutException, NoSuchElementException):
            print(f"❌ Failed to open brand dropdown for {brand}.")
            continue  # Skip to the next brand if dropdown cannot be clicked

        # **Step 2: Wait for the dropdown list and select the appropriate option**
        try:
            # Wait for dropdown items to appear
            dropdown_items = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ng-dropdown-panel-items.scroll-host .ng-option"))
            )

            # Loop through the options and select the matching brand
            for item in dropdown_items:
                if brand_name in item.text:  # Match the brand name (e.g., "Acewin8", "Ivip9")
                    ActionChains(driver).move_to_element(item).click().perform()
                    print(f"✅ Selected '{brand_name}' from dropdown.")
                    break
            else:
                print(f"❌ '{brand_name}' option not found in the dropdown.")
                continue  # Skip to the next brand if the option is not found
        except (TimeoutException, NoSuchElementException):
            print(f"❌ Failed to find or select the brand option for {brand}.")
            continue

        # **Step 3: Click the dropdown to select the country**
        try:
            country_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".search-navbar-nav > li:nth-child(2) > jhi-single-select-shared-component:nth-child(1) > div:nth-child(1) > div:nth-child(2)"))
            )
            
            # Retry mechanism for handling click interception
            attempts = 0
            max_attempts = 69
            while attempts < max_attempts:
                try:
                    # Scroll into view and click
                    driver.execute_script("arguments[0].scrollIntoView(true);", country_dropdown)
                    actions.move_to_element(brand_dropdown).perform()
                    country_dropdown.click()  # Click to open dropdown
                    print(f"✅ Opened country selection dropdown.")
                    break
                except ElementClickInterceptedException:
                    print(f"⚠️ Element click intercepted! Retrying... {attempts + 1}/{max_attempts}")
                    attempts += 1  # Wait before retrying
            else:
                print(f"❌ Failed to open country dropdown for {brand}.")
                continue  # Skip to the next brand if dropdown cannot be clicked

        except (TimeoutException, NoSuchElementException):
            print(f"❌ Failed to open country dropdown for {brand}.")
            continue  # Skip to the next brand if dropdown cannot be clicked

        # **Step 4: Wait for the dropdown list and select the appropriate option**
        try:
            # Wait for dropdown items to appear
            dropdown_items = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ng-dropdown-panel-items.scroll-host .ng-option"))
            )

            # Loop through the options and select the matching brand
            for item in dropdown_items:
                if country in item.text:  # Match the brand name (e.g., "Acewin8", "Ivip9")
                    ActionChains(driver).move_to_element(item).click().perform()
                    print(f"✅ Selected '{country}' from dropdown.")
                    break
            else:
                print(f"❌ '{country}' option not found in the dropdown.")
                continue  # Skip to the next brand if the option is not found
        except (TimeoutException, NoSuchElementException):
            print(f"❌ Failed to find or select the country for {brand}.")
            continue
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".block-ui-spinner"))
            )
        except TimeoutException:
            print("⚠️ No loading spinner detected, proceeding.")

       # ✅ Wait for the spinner to disappear
        WebDriverWait(driver, 300).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, ".block-ui-spinner"))
        )

        # **Step 5: Select "All" (status)**
        try:
            status_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "jhi-multiple-select-shared-component.col"))
            )

            # ✅ Handle intercepted clicks using retry mechanism
            attempts = 0
            max_attempts = 5  # Limit retry attempts
            while attempts < max_attempts:
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", status_dropdown)
                    ActionChains(driver).move_to_element(status_dropdown).click().perform()
                    print("✅ Opened 'Status' dropdown.")
                    break
                except ElementClickInterceptedException:
                    print(f"⚠️ Click intercepted! Retrying... {attempts + 1}/{max_attempts}")
                    attempts += 1
                    time.sleep(0.5)
            else:
                print("❌ Failed to open 'Status' dropdown.")
                raise Exception("Dropdown not clickable after multiple attempts.")

            # ✅ Wait for the "All" button inside the dropdown
            all_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".ng-dropdown-header button"))
            )

            # ✅ Click the "All" button
            ActionChains(driver).move_to_element(all_button).click().perform()
            print("✅ Selected 'All' from dropdown.")

        except (TimeoutException, NoSuchElementException, Exception) as e:
            print(f"❌ Failed to select 'All': {e}")


        # **Step 6: Select "Processing Time" from dropdown**
        try:
            processing_time_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "li.nav-item:nth-child(11) > jhi-single-select-shared-component:nth-child(1)"))
            )

            # ✅ Handle intercepted clicks using retry mechanism
            attempts = 0
            max_attempts = 5  # Limit retry attempts
            while attempts < max_attempts:
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", processing_time_dropdown)
                    actions.move_to_element(processing_time_dropdown).perform()
                    processing_time_dropdown.click()  # Click to open dropdown
                    print("✅ Opened 'Date By' dropdown.")
                    break
                except ElementClickInterceptedException:
                    print(f"⚠️ Click intercepted! Retrying... {attempts + 1}/{max_attempts}")
                    attempts += 1
                    time.sleep(0.5)
            else:
                print("❌ Failed to open 'Date By' dropdown.")
                raise Exception("Dropdown not clickable after multiple attempts.")

            # ✅ Wait for dropdown options to appear
            dropdown_options = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ng-dropdown-panel-items.scroll-host .ng-option"))
            )

            # ✅ Select "Processing Time"
            for option in dropdown_options:
                if "Processing Time" in option.text:
                    ActionChains(driver).move_to_element(option).click().perform()
                    print("✅ Selected 'Processing Time' from dropdown.")
                    break
            else:
                print("❌ 'Processing Time' option not found.")
                raise Exception("Processing Time option not found.")

        except (TimeoutException, NoSuchElementException, Exception) as e:
            print(f"❌ Failed to select 'Processing Time': {e}")

        # **Step 7: Select start datetime in dropdown**
        try:
            start_dt_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "li.nav-item:nth-child(19) > jhi-date-time-shared-component:nth-child(1) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > a:nth-child(1)"))
            )

            # ✅ First attempt normal click
            try:
                start_dt_dropdown.click()
            except ElementClickInterceptedException:
                print(f"⚠️ Click intercepted, using JavaScript click.")
                driver.execute_script("arguments[0].click();", start_dt_dropdown)

            print(f"✅ Opened start datetime selection dropdown.")
            time.sleep(1)  # ✅ Small delay before selecting datetime

            # ✅ Select start datetime
            select_day(driver, country_dt["start"].year, country_dt["start"].month, country_dt["start"].day)
            select_time(driver, country_dt["start"].hour, country_dt["start"].minute, country_dt["start"].second)

        except (TimeoutException, NoSuchElementException) as e:
            print(f"❌ Failed to open start datetime dropdown for {brand}: {e}")
            continue  # Skip to the next brand if dropdown cannot be clicked
        
        # **Step 8: Select end datetime in dropdown**
        try:
            end_dt_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "li.nav-item:nth-child(20) > jhi-date-time-shared-component:nth-child(1) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > a:nth-child(1)"))
            )

            # ✅ First attempt normal click
            try:
                end_dt_dropdown.click()
            except ElementClickInterceptedException:
                print(f"⚠️ Click intercepted, using JavaScript click.")
                driver.execute_script("arguments[0].click();", end_dt_dropdown)

            print(f"✅ Opened end datetime selection dropdown.")
            time.sleep(1)  # ✅ Small delay before selecting datetime

            # ✅ Select end datetime
            select_day(driver, country_dt["end"].year, country_dt["end"].month, country_dt["end"].day)
            select_time(driver, country_dt["end"].hour, country_dt["end"].minute, country_dt["end"].second)

        except (TimeoutException, NoSuchElementException) as e:
            print(f"❌ Failed to open end datetime dropdown for {brand}: {e}")
            continue  # Skip to the next brand if dropdown cannot be clicked

        # ** Step 9: Click on Search button and wait for results **
        try:
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-search"))
            )

            # ✅ First attempt normal click
            try:
                search_button.click()
            except ElementClickInterceptedException:
                print(f"⚠️ Click intercepted, using JavaScript click.")
                driver.execute_script("arguments[0].click();", search_button)
            
            print(f"✅ Loading data for {brand}...")
            
            # ✅ Wait for the loading spinner to appear (optional: ensures spinner exists before waiting for it to disappear)
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".block-ui-spinner"))
                )
            except TimeoutException:
                print("⚠️ No loading spinner detected, proceeding.")

            # ✅ Wait for the spinner to disappear
            WebDriverWait(driver, 300).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".block-ui-spinner"))
            )
            print(f"✅ Data successfully loaded!")

        except (TimeoutException, NoSuchElementException) as e:
            print(f"❌ Failed to load data for {brand}: {e}")
            continue  # Skip to the next brand if search cannot be clicked
        
        # ** Step 10: Check if "No Data" is displayed on the page **
        try:
            no_data_element = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, '//tr[contains(@class, "no-data-container")]//span[text()="No Data"]'))
            )
            if no_data_element:
                print(f"⚠️ No data available for {brand}. Skipping export.")
                continue  # Skip export_report() if no data is found
        except TimeoutException:
            print(f"✅ Data found for {brand}, proceeding with export.")

        print(Fore.GREEN + f"✅ Completed form navigation, exporting data for {brand}...")

        # ✅ Call `export_report()` only if data is available
        export_report(driver, creds, brand, download_dir)


def withdrawal_nav(driver, creds, download_dir):
    """Handles the withdrawal form by selecting values based on credentials.json."""

    actions = ActionChains(driver)  # Create an ActionChains instance

    # Get yesterday's datetime range UTC+8
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_dt = {
        "start": yesterday.replace(hour=0, minute=0, second=0, microsecond=0),
        "end": yesterday.replace(hour=23, minute=59, second=59, microsecond=0)
    }
    
    # ✅ Iterate over each brand in the creds dictionary
    for brand in creds.get("brand", []):
        if brand not in creds:
            print(f"⚠️ No data for {brand}, skipping...")
            continue
        
        brand_name = creds[brand][0] 
        country = creds[brand][1]     # e.g., "Cambodia", "Singapore"
        time_offset = int(creds[brand][2])  # Time offset (if needed)

        # Calculate country-specific datetime range
        country_dt = {
            "start": yesterday_dt["start"] + timedelta(hours=time_offset),
            "end": yesterday_dt["end"] + timedelta(hours=time_offset)
        }

        print(f"\n🔍 Selecting values for brand: {brand} ({brand_name}, {country})")

        # **Step 1: Click the dropdown to select the brand**
        try:
            brand_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".search-navbar-nav > li:nth-child(1) > jhi-single-select-shared-component:nth-child(1) > div:nth-child(1) > div:nth-child(2)"))
            )
            
            # Retry mechanism for handling click interception
            attempts = 0
            max_attempts = 69
            while attempts < max_attempts:
                try:
                    # Scroll into view and click
                    driver.execute_script("arguments[0].scrollIntoView(true);", brand_dropdown)
                    actions.move_to_element(brand_dropdown).perform()
                    brand_dropdown.click()  # Click to open dropdown
                    print(f"✅ Opened brand selection dropdown.")
                    break
                except ElementClickInterceptedException:
                    print(f"⚠️ Element click intercepted! Retrying... {attempts + 1}/{max_attempts}")
                    attempts += 1  # Wait before retrying
            else:
                print(f"❌ Failed to open brand dropdown for {brand}.")
                continue  # Skip to the next brand if dropdown cannot be clicked

        except (TimeoutException, NoSuchElementException):
            print(f"❌ Failed to open brand dropdown for {brand}.")
            continue  # Skip to the next brand if dropdown cannot be clicked

        # **Step 2: Wait for the dropdown list and select the appropriate option**
        try:
            # Wait for dropdown items to appear
            dropdown_items = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ng-dropdown-panel-items.scroll-host .ng-option"))
            )

            # Loop through the options and select the matching brand
            for item in dropdown_items:
                if brand_name in item.text:  # Match the brand name (e.g., "Acewin8", "Ivip9")
                    ActionChains(driver).move_to_element(item).click().perform()
                    print(f"✅ Selected '{brand_name}' from dropdown.")
                    break
            else:
                print(f"❌ '{brand_name}' option not found in the dropdown.")
                continue  # Skip to the next brand if the option is not found
        except (TimeoutException, NoSuchElementException):
            print(f"❌ Failed to find or select the brand option for {brand}.")
            continue

        # **Step 3: Click the dropdown to select the country**
        try:
            country_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".search-navbar-nav > li:nth-child(2) > jhi-single-select-shared-component:nth-child(1) > div:nth-child(1) > div:nth-child(2)"))
            )
            
            # Retry mechanism for handling click interception
            attempts = 0
            max_attempts = 69
            while attempts < max_attempts:
                try:
                    # Scroll into view and click
                    driver.execute_script("arguments[0].scrollIntoView(true);", country_dropdown)
                    actions.move_to_element(brand_dropdown).perform()
                    country_dropdown.click()  # Click to open dropdown
                    print(f"✅ Opened country selection dropdown.")
                    break
                except ElementClickInterceptedException:
                    print(f"⚠️ Element click intercepted! Retrying... {attempts + 1}/{max_attempts}")
                    attempts += 1  # Wait before retrying
            else:
                print(f"❌ Failed to open country dropdown for {brand}.")
                continue  # Skip to the next brand if dropdown cannot be clicked

        except (TimeoutException, NoSuchElementException):
            print(f"❌ Failed to open country dropdown for {brand}.")
            continue  # Skip to the next brand if dropdown cannot be clicked

        # **Step 4: Wait for the dropdown list and select the appropriate option**
        try:
            # Wait for dropdown items to appear
            dropdown_items = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ng-dropdown-panel-items.scroll-host .ng-option"))
            )

            # Loop through the options and select the matching brand
            for item in dropdown_items:
                if country in item.text:  # Match the brand name (e.g., "Acewin8", "Ivip9")
                    ActionChains(driver).move_to_element(item).click().perform()
                    print(f"✅ Selected '{country}' from dropdown.")
                    break
            else:
                print(f"❌ '{country}' option not found in the dropdown.")
                continue  # Skip to the next brand if the option is not found
        except (TimeoutException, NoSuchElementException):
            print(f"❌ Failed to find or select the country for {brand}.")
            continue
                # ✅ Wait for the loading spinner to appear (optional: ensures spinner exists before waiting for it to disappear)
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".block-ui-spinner"))
            )
        except TimeoutException:
            print("⚠️ No loading spinner detected, proceeding.")

       # ✅ Wait for the spinner to disappear
        WebDriverWait(driver, 300).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, ".block-ui-spinner"))
        )

        # **Step 5: Select "All" (status)**
        try:
            status_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "jhi-multiple-select-shared-component.col"))
            )

            # ✅ Handle intercepted clicks using retry mechanism
            attempts = 0
            max_attempts = 5  # Limit retry attempts
            while attempts < max_attempts:
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", status_dropdown)
                    ActionChains(driver).move_to_element(status_dropdown).click().perform()
                    print("✅ Opened 'Status' dropdown.")
                    break
                except ElementClickInterceptedException:
                    print(f"⚠️ Click intercepted! Retrying... {attempts + 1}/{max_attempts}")
                    attempts += 1
                    time.sleep(0.5)
            else:
                print("❌ Failed to open 'Status' dropdown.")
                raise Exception("Dropdown not clickable after multiple attempts.")

            # ✅ Wait for the "All" button inside the dropdown
            all_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".ng-dropdown-header button"))
            )

            # ✅ Click the "All" button
            ActionChains(driver).move_to_element(all_button).click().perform()
            print("✅ Selected 'All' from dropdown.")

        except (TimeoutException, NoSuchElementException, Exception) as e:
            print(f"❌ Failed to select 'All': {e}")


        # **Step 6: Select "Processing Time" from dropdown**
        try:
            processing_time_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "li.nav-item:nth-child(11) > jhi-single-select-shared-component:nth-child(1)"))
            )

            # ✅ Handle intercepted clicks using retry mechanism
            attempts = 0
            max_attempts = 5  # Limit retry attempts
            while attempts < max_attempts:
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", processing_time_dropdown)
                    actions.move_to_element(processing_time_dropdown).perform()
                    processing_time_dropdown.click()  # Click to open dropdown
                    print("✅ Opened 'Date By' dropdown.")
                    break
                except ElementClickInterceptedException:
                    print(f"⚠️ Click intercepted! Retrying... {attempts + 1}/{max_attempts}")
                    attempts += 1
                    time.sleep(0.5)
            else:
                print("❌ Failed to open 'Date By' dropdown.")
                raise Exception("Dropdown not clickable after multiple attempts.")

            # ✅ Wait for dropdown options to appear
            dropdown_options = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ng-dropdown-panel-items.scroll-host .ng-option"))
            )

            # ✅ Select "Processing Time"
            for option in dropdown_options:
                if "Processing Time" in option.text:
                    ActionChains(driver).move_to_element(option).click().perform()
                    print("✅ Selected 'Processing Time' from dropdown.")
                    break
            else:
                print("❌ 'Processing Time' option not found.")
                raise Exception("Processing Time option not found.")

        except (TimeoutException, NoSuchElementException, Exception) as e:
            print(f"❌ Failed to select 'Processing Time': {e}")

        # **Step 7: Select start datetime in dropdown**
        try:
            start_dt_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "li.nav-item:nth-child(20) > jhi-date-time-shared-component:nth-child(1)"))
            )

            # ✅ First attempt normal click
            try:
                start_dt_dropdown.click()
            except ElementClickInterceptedException:
                print(f"⚠️ Click intercepted, using JavaScript click.")
                driver.execute_script("arguments[0].click();", start_dt_dropdown)

            print(f"✅ Opened start datetime selection dropdown.")
            time.sleep(1)  # ✅ Small delay before selecting datetime

            # ✅ Select start datetime
            select_day(driver, country_dt["start"].year, country_dt["start"].month, country_dt["start"].day)
            select_time(driver, country_dt["start"].hour, country_dt["start"].minute, country_dt["start"].second)

        except (TimeoutException, NoSuchElementException) as e:
            print(f"❌ Failed to open start datetime dropdown for {brand}: {e}")
            continue  # Skip to the next brand if dropdown cannot be clicked
        
        # **Step 8: Select end datetime in dropdown**
        try:
            end_dt_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "li.nav-item:nth-child(21) > jhi-date-time-shared-component:nth-child(1)"))
            )

            # ✅ First attempt normal click
            try:
                end_dt_dropdown.click()
            except ElementClickInterceptedException:
                print(f"⚠️ Click intercepted, using JavaScript click.")
                driver.execute_script("arguments[0].click();", end_dt_dropdown)

            print(f"✅ Opened end datetime selection dropdown.")
            time.sleep(1)  # ✅ Small delay before selecting datetime

            # ✅ Select end datetime
            select_day(driver, country_dt["end"].year, country_dt["end"].month, country_dt["end"].day)
            select_time(driver, country_dt["end"].hour, country_dt["end"].minute, country_dt["end"].second)

        except (TimeoutException, NoSuchElementException) as e:
            print(f"❌ Failed to open end datetime dropdown for {brand}: {e}")
            continue  # Skip to the next brand if dropdown cannot be clicked

        # ** Step 9: Click on Search button and wait for results **
        try:
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-search"))
            )

            # ✅ First attempt normal click
            try:
                search_button.click()
            except ElementClickInterceptedException:
                print(f"⚠️ Click intercepted, using JavaScript click.")
                driver.execute_script("arguments[0].click();", search_button)
            
            print(f"✅ Loading data for {brand}...")
            
            # ✅ Wait for the loading spinner to appear (optional: ensures spinner exists before waiting for it to disappear)
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".block-ui-spinner"))
                )
            except TimeoutException:
                print("⚠️ No loading spinner detected, proceeding.")

            # ✅ Wait for the spinner to disappear
            WebDriverWait(driver, 300).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".block-ui-spinner"))
            )
            print(f"✅ Data successfully loaded!")

        except (TimeoutException, NoSuchElementException) as e:
            print(f"❌ Failed to load data for {brand}: {e}")
            continue  # Skip to the next brand if search cannot be clicked
        
        # ** Step 10: Check if "No Data" is displayed on the page **
        try:
            no_data_element = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, '//tr[contains(@class, "no-data-container")]//span[text()="No Data"]'))
            )
            if no_data_element:
                print(f"⚠️ No data available for {brand}. Skipping export.")
                continue  # Skip export_report() if no data is found
        except TimeoutException:
            print(f"✅ Data found for {brand}, proceeding with export.")

        print(Fore.GREEN + f"✅ Completed form navigation, exporting data for {brand}...")

        # ✅ Call `export_report()` only if data is available
        export_report(driver, creds, brand, download_dir)

def export_report(driver, creds, brand, download_dir):
       # ** Step 9: Click on Search button and wait for results **
        try:
            # ✅ Wait for any of the Export buttons to be clickable
            export_button = WebDriverWait(driver, 10).until(
                any_of(
                    EC.element_to_be_clickable((By.XPATH, '//button[text()="Export"]')),
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "li.nav-item:nth-child(27) jhi-export-shared-component ul li button")),
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "li.nav-item:nth-child(28) jhi-export-shared-component ul li button"))
                )
            )

            # ✅ First attempt normal click
            try:
                export_button.click()
                export_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"✅ Export started at {export_time}")

            except ElementClickInterceptedException:
                print(f"⚠️ Click intercepted, using JavaScript click.")
                driver.execute_script("arguments[0].click();", export_button)
                export_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            time.sleep(1)
            # ✅ Wait for the export to be loaded
            WebDriverWait(driver, 300).until(
                EC.invisibility_of_element_located((By.XPATH, '//li[contains(text(),"Yesterday")]'))
            )
            print(f"📂 Report download initiated for {brand}.")

            # **Step 6: Wait for the downloaded file to appear in the download directory**
            print(f"⏳ Waiting for the report file for {brand} to finish downloading...")
            download_complete = False
            start_time = time.time()
            timeout = 90  # ✅ Increase timeout for larger downloads
            export_time_dt = datetime.strptime(export_time, "%Y-%m-%d %H:%M:%S")

            while not download_complete and time.time() - start_time < timeout:
                recent_file = get_most_recent_file(download_dir)

                if recent_file and recent_file.exists():
                    # ✅ Ignore temporary download files (`.crdownload` and `.tmp`)
                    if recent_file.suffix.lower() in [".crdownload", ".tmp"]:
                        print(f"⚠️ File '{recent_file.name}' is still downloading. Waiting...")
                        time.sleep(1)  # ✅ Wait and retry
                        continue  
                    
                    # ✅ Convert file's modified time to string format for comparison
                    file_modified_time = datetime.fromtimestamp(recent_file.stat().st_mtime)
                    file_modified_time_str = file_modified_time.strftime("%Y-%m-%d %H:%M:%S")

                    if file_modified_time >= export_time_dt:
                        # ✅ Check if the file has a valid extension
                        if recent_file.suffix.lower() in [".zip"]:
                            download_complete = True
                            print(f"✅ Download completed for {brand}! File saved as: {recent_file.name}")

                            # ✅ Unpack .zip and extract .csv
                            extract_and_move_csv(download_dir)
                            # ✅ Rename and move the file
                            rename_and_move_file(driver, download_dir, brand)
                            break
                        else:
                            print(f"⚠️ Found file '{recent_file.name}', but it is not a valid .zip file. Retrying...")
                    else:
                        print(f"⚠️ Found file '{recent_file.name}', but modified at {file_modified_time_str}, which is before {export_time}. Retrying...")
                        time.sleep(1)
                else:
                    time.sleep(0.5)

            if not download_complete:
                print(f"❌ Error: File download did not complete within the expected time for {brand}.")

        except (TimeoutException, NoSuchElementException) as e:
            print(f"❌ Failed to load data for {brand}: {e}")

def rename_and_move_file(driver, download_dir, brand):
    """Renames the latest downloaded file and moves it to the correct folder based on the current URL, overwriting if duplicate exists."""
    try:
        # ✅ Get yesterday's date in YYYY-MM-DD format
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        # ✅ Get the most recent valid file
        recent_file = get_most_recent_file(download_dir)
        if not recent_file or not recent_file.exists():
            print(f"❌ No valid file found to rename for {brand}.")
            return

        # ✅ Ensure file is a valid CSV or Excel file
        if recent_file.suffix.lower() not in [".csv", ".xlsx"]:
            print(f"⚠️ Skipping rename: {recent_file.name} is not a CSV or Excel file.")
            return

        # ✅ Extract the current URL fragment (after `#`)
        current_url = driver.current_url
        parsed_url = urlparse(current_url)
        url_fragment = parsed_url.fragment  # Extracts everything after `#`
        
        # ✅ Get the last segment (e.g., "deposit" or "withdraw")
        path_segments = url_fragment.split("/")
        last_segment = path_segments[-1] if len(path_segments) > 1 else ""

        # ✅ Ensure 'ss' directory exists
        ss_folder = os.path.join(download_dir)
        os.makedirs(ss_folder, exist_ok=True)

        # ✅ Determine the folder based on the last segment
        folder_mapping = {
            "deposit": "deposit",
            "withdraw": "withdrawal"
        }
        target_folder = os.path.join(ss_folder, folder_mapping.get(last_segment, ""))

        if not target_folder:
            print(f"⚠️ Unknown URL segment '{last_segment}', keeping file in default Downloads folder.")
            return  # ✅ Exit without moving if URL is unknown

        # ✅ Ensure the target folder exists before moving
        os.makedirs(target_folder, exist_ok=True)

        # ✅ Construct new file name with brand and date
        new_filename = f"{brand} {yesterday}{recent_file.suffix}"
        new_filepath = os.path.join(target_folder, new_filename)

        # ✅ If a file with the same name exists, delete it before moving
        if os.path.exists(new_filepath):
            os.remove(new_filepath)
            print(f"⚠️ Existing file '{new_filename}' found. Overwriting...")

        # ✅ Move and rename the file
        shutil.move(str(recent_file), new_filepath)
        print(Fore.GREEN + f"✅ File renamed and moved to: {new_filepath}\n")

        moved_files.append(new_filepath)

    except Exception as e:
        print(f"❌ Error renaming/moving file for {brand}: {e}")

def extract_and_move_csv(download_dir):
    """Unpacks the ZIP file in `download_dir`, moves CSV to `download_dir`, and deletes the ZIP."""
    time.sleep(1)
    
    # ✅ Find the latest ZIP file in `download_dir`
    zip_files = [f for f in os.listdir(download_dir) if f.endswith('.zip')]
    if not zip_files:
        print("❌ No ZIP files found in download directory.")
        return

    latest_zip = max(zip_files, key=lambda f: os.path.getctime(os.path.join(download_dir, f)))
    zip_path = os.path.join(download_dir, latest_zip)
    
    # ✅ Create a temp folder for extraction
    extract_path = os.path.join(download_dir, "temp_extracted")
    os.makedirs(extract_path, exist_ok=True)
    
    try:
        # ✅ Extract the ZIP file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        print(f"✅ Extracted: {latest_zip}")

        # ✅ Find the CSV file(s) inside the extracted folder
        csv_files = [f for f in os.listdir(extract_path) if f.endswith('.csv')]
        if not csv_files:
            print("❌ No CSV files found in extracted folder.")
            return
        
        # ✅ Move all CSV files to `download_dir`
        for csv_file in csv_files:
            csv_src = os.path.join(extract_path, csv_file)
            csv_dest = os.path.join(download_dir, csv_file)
            shutil.move(csv_src, csv_dest)
            print(f"✅ Moved: {csv_file} to {download_dir}")

        # ✅ Confirm CSV is in `download_dir` before deleting ZIP
        extracted_csvs = [f for f in os.listdir(download_dir) if f.endswith('.csv')]
        if all(f in extracted_csvs for f in csv_files):
            os.remove(zip_path)
            print(f"✅ Deleted ZIP file: {latest_zip}")
        else:
            print("⚠️ CSV extraction incomplete, ZIP not deleted.")

    except Exception as e:
        print(f"❌ Error extracting ZIP: {e}")

    finally:
        # ✅ Clean up temp extraction folder
        shutil.rmtree(extract_path, ignore_errors=True)


def get_most_recent_file(download_dir, timeout=300):
    """Returns the most recently modified file in download_dir, ignoring folders. Displays a loading animation while waiting."""
    try:
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # ✅ List all valid files (ignore folders)
            files = [f for f in Path(download_dir).iterdir() if f.is_file()]
            
            if files:
                return max(files, key=lambda f: f.stat().st_mtime)

            time.sleep(1)  # ✅ Wait and retry
        print("⚠️ No valid files found after waiting.")

    except Exception as e:
        print(f"❌ Error finding most recent file: {e}")

    return None

def close_first_tab(driver):
    # closes first navigation tab    

    close_tab_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "a.active > ul:nth-child(1) > li:nth-child(3)"))
    )
    
    # ✅ Handle intercepted clicks using retry mechanism
    attempts = 0
    max_attempts = 5  # Limit retry attempts
    while attempts < max_attempts:
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", close_tab_button)
            ActionChains(driver).move_to_element(close_tab_button).click().perform()
            print("✅ Closed deposit tab.")
            break
        except ElementClickInterceptedException:
            print(f"⚠️ Click intercepted! Retrying... {attempts + 1}/{max_attempts}")
            attempts += 1
            time.sleep(0.5)
    else:
        print("❌ Failed to close deposit tab.")
        raise Exception("Failed to close deposit tab after multiple attempts.")    

def select_day(driver, year, month, day):
    """Selects the correct date from the currently active date picker."""
    try:
        # ✅ Ensure we are selecting from the visible date picker
        datepicker = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".dropdown-menu.show ngb-datepicker"))
        )

        # ✅ Open the year dropdown **inside** the currently active date picker
        year_dropdown = datepicker.find_element(By.CSS_SELECTOR, "select[aria-label='Select year']")
        year_dropdown.click()

        # ✅ Select the correct year
        year_option = datepicker.find_element(By.XPATH, f".//select[@aria-label='Select year']/option[@value='{year}']")
        year_option.click()
        print(f"✅ Selected Year: {year}")

        # ✅ Open the month dropdown **inside** the currently active date picker
        month_dropdown = datepicker.find_element(By.CSS_SELECTOR, "select[aria-label='Select month']")
        month_dropdown.click()

        # ✅ Select the correct month
        month_option = datepicker.find_element(By.XPATH, f".//select[@aria-label='Select month']/option[@value='{month}']")
        month_option.click()
        print(f"✅ Selected Month: {month}")

        # ✅ Convert date to aria-label format with correct platform-specific formatting
        day_format = "%#d" if platform.system() == "Windows" else "%-d"  # Fix for Windows/Linux/Mac
        date_str = datetime(year, month, day).strftime(f"%A, %B {day_format}, %Y")

        # ✅ Find and click the correct day using `aria-label`
        day_element = datepicker.find_element(By.XPATH, f".//div[contains(@class, 'ngb-dp-day')][@aria-label='{date_str}']")
        day_element.click()
        print(f"✅ Selected Day: {date_str}")

    except Exception as e:
        print(f"❌ Failed to select date: {e}")

def select_time(driver, hour, minute, second):
    """Selects the correct time in the currently active time picker."""
    try:
        # ✅ Ensure we are selecting from the visible time picker
        timepicker = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".dropdown-menu.show ngb-timepicker"))
        )

        # ✅ Locate time input fields **inside** the active time picker
        hour_element = timepicker.find_element(By.CSS_SELECTOR, "input[aria-label='Hours']")
        minute_element = timepicker.find_element(By.CSS_SELECTOR, "input[aria-label='Minutes']")
        second_element = timepicker.find_element(By.CSS_SELECTOR, "input[aria-label='Seconds']")

        # ✅ Properly clear fields using Ctrl+A + Backspace
        for elem, value in zip([hour_element, minute_element, second_element], [hour, minute, second]):
            elem.send_keys(Keys.CONTROL + "a")  # Select all text
            elem.send_keys(Keys.BACKSPACE)  # Delete selected text
            elem.send_keys(f"{value:02d}")  # Enter new value

        print(f"✅ Selected Time: {hour:02d}:{minute:02d}:{second:02d}")

    except Exception as e:
        print(f"❌ Failed to select time: {e}")

def wait_for_browser_to_load(driver, timeout=10):
    """Waits until the browser finishes loading the page."""
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    time.sleep(0.5)

def main():
    """Loop through each SS site and log in."""
    driver, download_dir = initialize_driver()  # ✅ Unpack the tuple properly
    credentials = load_credentials()

    # Filter URLs where BO = SS (superswan)
    ss_urls = {url: data for url, data in credentials.items() if data["bo"] == "SS"}

    print("Starting Superswan job.")

    global moved_files
    moved_files = []
    
    if driver is None:
        print("❌ Failed to initialize WebDriver. Exiting.")
        return

    for url, creds in ss_urls.items():
        if not url or url.isspace():
            print("⚠️ Skipping an invalid URL (empty or None)")
            continue  # Skip this iteration

        # Ensure URL is fully qualified
        if not url.startswith("http"):
            url = "https://" + url  # Ensure it has a valid prefix
        
        login(driver, url, creds)

    deposit(driver, url, creds, download_dir)

    close_first_tab(driver)

    withdrawal(driver, url, creds, download_dir)  
    
    driver.quit()
    print("✅ Superswan job completed.")

    # Write the moved_files list to a temporary file for further processing if needed.
    moved_files_filepath = os.path.join(tempfile.gettempdir(), "ss_moved_files.txt")
    with open(moved_files_filepath, "w") as f:
        for path in moved_files:
            f.write(path + "\n")
    print(f"MOVED_FILES_FILE:{moved_files_filepath}")

    # Return MaterializeResult with sorted moved_files for Dagster metadata
    return MaterializeResult(
        metadata={
            "moved_files": [MetadataValue.path(path) for path in sorted(moved_files)]
        }
    )

# # Initialize Colorama
init(autoreset=True, strip=False)

if __name__ == "__main__":
    main()