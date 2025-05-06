import tempfile
import json
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.expected_conditions import any_of
from selenium.webdriver.common.action_chains import ActionChains
from dagster import MaterializeResult, MetadataValue
from selenium.webdriver.common.keys import Keys
from urllib.parse import urlparse
from pathlib import Path
import sys
import threading
import itertools
import time
import math
import os
import shutil
import colorsys
from colorama import Fore, Back, Style, init

current_dir = os.getcwd()
utils_dir = os.path.join(current_dir, "scripts", "utils")  # Assuming "scripts" is the folder

if utils_dir not in sys.path:
    sys.path.append(utils_dir)

import daterange

timezones_dir = os.path.join(utils_dir, "timezone-ibs.json")

creds_dir = os.path.join(current_dir, ".key", "credentials.json")

### **Step 1: Load Data from JSON Files**
def load_credentials():
    """Load credentials from JSON file."""
    with open(creds_dir, "r") as file:
        return json.load(file)

def load_timezones():
    """Load timezone mappings from JSON file."""
    with open(timezones_dir, "r") as file:
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
    download_dir = os.path.join(current_directory, "downloads", "smls")
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

    driver = webdriver.Chrome(options=options)
    return driver, download_dir  # ✅ Now returning both driver and download_dir

def login(driver, url, creds):
    """Logs in to the IBS website using credentials and waits for the dashboard to load."""
    print(f"Attempting to log in: {url}")
    
    driver.get(url)
    time.sleep(0.5)
    
    attempts = 0  # Track login attempts
    max_attempts = 30  # Maximum retries if captcha is blank

    while attempts < max_attempts:
        try:
            # **Step 2: Fill in the merchant code if available**
            try:
                merchant_field = driver.find_element(By.CSS_SELECTOR, "#mer_code")
                merchant_field.clear()
                merchant_field.send_keys(creds["merchant_code"])
            except NoSuchElementException:
                print(f"Merchant code field not found for {url}, skipping this step.")

            # **Step 3: Fill in the username**
            username_field = driver.find_element(By.CSS_SELECTOR, "#username")
            username_field.clear()
            username_field.send_keys(creds["username"])

            # **Step 4: Fill in the password**
            password_field = driver.find_element(By.CSS_SELECTOR, "#password")
            password_field.clear()
            password_field.send_keys(creds["password"])

            # **Step 5: Extract and enter the captcha**
            try:
                captcha_container = driver.find_element(By.CSS_SELECTOR, ".captchaNum")
                captcha_text = "".join(span.text.strip() for span in captcha_container.find_elements(By.TAG_NAME, "span"))

                # **If captcha is blank, retry the login process**
                if not captcha_text.strip():
                    attempts += 1
                    print(f"⚠️ Captcha was blank! Retrying login attempt {attempts}/{max_attempts}...")
                    time.sleep(1.5)  # Short delay before retrying
                    continue  # Restart the login attempt
                
                print(f"Extracted Captcha: {captcha_text}")

                captcha_field = driver.find_element(By.CSS_SELECTOR, "#captcha")
                captcha_field.clear()
                captcha_field.send_keys(captcha_text)
            except NoSuchElementException:
                print(f"Captcha not found for {url}, skipping captcha step.")

            # **Step 6: Submit login form**
            login_button = driver.find_element(By.CSS_SELECTOR, "#btnLogin")
            login_button.click()

            # **Step 7: Wait for the page redirect to complete**
            try:
                WebDriverWait(driver, 60).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "body > div.wrapper > aside > section > ul > li.treeview.a-1"))  # Ensure we have been redirected
                )
                print(f"✅ Successfully logged in and redirected to dashboard.\n")
                return True  # Login success

            except TimeoutException:
                print(f"❌ Error: Login successful but redirection to dashboard took too long (> 60 seconds).\n")
                return False  # Return False if redirection fails

        except Exception as e:
            print(f"❌ Error logging into {url}: {str(e)}")
            return False  # Return False if login fails

    print(f"❌ Failed to log in after {max_attempts} attempts. Skipping this site.\n")
    return False  # Return False after max retries

### **Step 4: Navigate to Deposit Page**
def deposit(driver, url, creds, timezone_mapping, download_dir):
    """Navigates to the deposit page, handles currency selection per brand, selects the correct timezone, and prepares for export."""
    
    deposit_url = f"{url}/deposit"
    print(f"🌍 Navigating to deposit page: {deposit_url}")
    
    driver.get(deposit_url)
    deposit_withdrawal_nav(driver, creds, timezone_mapping, download_dir)

def withdrawal(driver, url, creds, timezone_mapping, download_dir):
    """Navigates to the deposit page, handles currency selection per brand, selects the correct timezone, and prepares for export."""
    
    withdrawal_url = f"{url}/withdraw"
    print(f"🌍 Navigating to withdrawal page: {withdrawal_url}")
    
    driver.get(withdrawal_url)
    deposit_withdrawal_nav(driver, creds, timezone_mapping, download_dir)

def qr_deposit(driver, url, creds, timezone_mapping, download_dir):
    """Navigates to the QR deposit page, checks for redirects, and proceeds accordingly."""
    
    qr_deposit_url = f"{url}/qr-deposit"

    print(f"🌍 Navigating to QR deposit page: {qr_deposit_url}")
    driver.get(qr_deposit_url)

    # ✅ Step 1: Wait until the browser finishes loading
    wait_for_browser_to_load(driver)
    time.sleep(1)

    # ✅ Step 2: Check if the QR deposit page exists
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".title-holder .breadcrumb span"))
        )
        
        # ✅ Extract breadcrumb span text
        breadcrumb_span = driver.find_element(By.CSS_SELECTOR, ".title-holder .breadcrumb span")
        breadcrumb_text = breadcrumb_span.text.strip()

        # ✅ Check if it contains "QR Deposit"
        if "QR Deposit" not in breadcrumb_text:
            print(f"⏭️ QR deposit page not available. Skipping QR deposits.")
            return  # ✅ Exit function gracefully

        print(f"✅ QR deposit page loaded successfully: {breadcrumb_text}")

    except Exception:
        print("⚠️ Warning: QR deposit page did not load as expected. Proceeding with caution...")

    # ✅ Continue execution if "QR Deposit" was found
    deposit_withdrawal_nav(driver, creds, timezone_mapping, download_dir)

def deposit_withdrawal_nav(driver, creds, timezone_mapping, download_dir):

    # Create an ActionChains object
    actions = ActionChains(driver)

    try:
        # **Step 1: Wait for the deposit page to load**
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".input-group"))
        )
        print("\n✅ Page loaded successfully.")

        # **Step 3: Iterate Over Each Brand**
        for brand in creds.get("brand", []):
            if brand not in creds:
                print(f"⚠️ No currency mapping found for brand {brand}, skipping...")
                continue

            currency = creds[brand]
            timezone_value = timezone_mapping.get(currency, "GMT+00:00")  # Default GMT

            print(f"🌍 Setting timezone for {brand} ({currency}): {timezone_value}")
            driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": timezone_value})

            print(f"✅ WebDriver timezone updated: {timezone_value}")

            wait_for_browser_to_load(driver)
            # time.sleep(1)

            # ✅ Wait for page reload
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".input-group"))  # Adjust this selector to match your page
            )
            time.sleep(2)
            # **Wait for the page to load**
            try:
                loading_overlay_selector = ".ajaxLoader"
                time.sleep(1)
                WebDriverWait(driver, 300).until(
                    EC.text_to_be_present_in_element_attribute((By.CSS_SELECTOR, loading_overlay_selector), "style", "display: none")
                )
            except TimeoutException:
                print("⚠️ Loading overlay took too long! Retrying full sequence...")
                retry_count += 1
                time.sleep(1)
                continue  

            print("✅ Page reloaded successfully.")
            # ✅ Continue with currency selection, search, and export...     

            # **Step 2: Handle "Approved" status selection with JavaScript click for stale elements**
            try:
                status_dropdown = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#status"))
                )
                safe_click(driver, status_dropdown)
                print("✅ Opened status dropdown.")

                all_option = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//select[@id="status"]/option[text()="All"]'))
                )
            
                try:
                    # ✅ First attempt normal click
                    # safe_click(driver, all_option)
                    all_option.click()
                    print("✅ Selected 'All' status.")
                    
                except StaleElementReferenceException:
                    print("⚠️ Stale element detected! Using JavaScript click instead.")
                    driver.execute_script("arguments[0].click();", all_option)  # ✅ JavaScript click
                    print("✅ Selected 'All' status using JavaScript.")
            
            except TimeoutException:
                print("❌ Error: Could not find or select 'All' status.")     

            # **Step 4: Handle currency selection, timezone, and export with full retry**
            max_retries = 3  # ✅ Retry entire block 3 times if there's a stale element
            retry_count = 0

            while retry_count < max_retries:
                try:
                    # **Open the currency dropdown**
                    currency_dropdown = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".select2-selection"))
                    )
                    safe_click(driver, currency_dropdown)
                    print(f"✅ Opened currency dropdown for {brand} ({currency}).")

                    # **Deselect all selected currencies first**
                    deselect_attempts = 0
                    max_deselect_attempts = 5  

                    while deselect_attempts < max_deselect_attempts:
                        try:
                            # ✅ Find all remove buttons inside the selection container
                            remove_buttons = driver.find_elements(By.CSS_SELECTOR, ".select2-selection__choice__remove")

                            if not remove_buttons:
                                print("✅ All currencies are now deselected.")
                                break  # Exit loop if no selected options remain
                            
                            for _ in range(len(remove_buttons)):  # Process all remove buttons
                                remove_buttons = driver.find_elements(By.CSS_SELECTOR, ".select2-selection__choice__remove")
                                if not remove_buttons:
                                    print("✅ All currencies are now deselected.")
                                    break  # Stop if list is empty
                                
                                button = remove_buttons[0]  # Always click the first remove button
                                option_text = button.get_attribute("textContent").strip()
                                print(f"Attempting to deselect: {option_text}...")

                                # ✅ Click remove button
                                safe_click(driver, button)
                                time.sleep(0.5)  # Allow UI to update

                                # ✅ Ensure UI updates before proceeding
                                WebDriverWait(driver, 5).until_not(
                                    EC.presence_of_element_located((By.XPATH, f"//li[@class='select2-selection__choice' and @title='{option_text}']"))
                                )
                                print(f"✅ Deselected: {option_text}")

                            deselect_attempts += 1  # Increase attempt count

                        except StaleElementReferenceException:
                            print(f"⚠️ Stale element detected! Retrying... Attempt {deselect_attempts + 1}/{max_deselect_attempts}")
                            deselect_attempts += 1
                            time.sleep(0.5)  # Wait before retrying

                    # **Step 5: Select the corresponding currency**
                    max_attempts = 5  
                    attempts = 0

                    while attempts < max_attempts:
                        try:
                            # ✅ Find the correct currency option in the dropdown
                            currency_option = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, f"//li[contains(@class, 'select2-results__option') and text()='{currency}']"))
                            )

                            safe_click(driver, currency_option)
                            print(f"✅ Selected currency: {currency}")
                            break  
                        
                        except StaleElementReferenceException:
                            print(f"⚠️ Stale element detected! Retrying currency selection... Attempt {attempts + 1}/{max_attempts}")
                            attempts += 1
                            time.sleep(0.5)

                    # ✅ If currency selection failed after max attempts, retry full process
                    if attempts == max_attempts:
                        print(f"❌ Failed to select currency {currency} after {max_attempts} attempts. Retrying full sequence...")
                        retry_count += 1
                        time.sleep(1)
                        continue  

                    start_date = daterange.start_date
                    end_date = daterange.end_date

                    # ✅ Convert `start_date` and `end_date` to `YYYY-MM-DD` format if needed
                    if isinstance(start_date, tuple):
                        start_date = f"{start_date[0]}-{start_date[1]:02d}-{start_date[2]:02d}"
                    if isinstance(end_date, tuple):
                        end_date = f"{end_date[0]}-{end_date[1]:02d}-{end_date[2]:02d}"

                    #from_date
                    # Enter start date
                    try:
                        start_date_input = driver.find_element(By.CSS_SELECTOR, "#from_date")
                        actions.move_to_element(start_date_input)\
                       .click()\
                       .key_down(Keys.CONTROL)\
                       .send_keys("a")\
                       .key_up(Keys.CONTROL)\
                       .send_keys(start_date)\
                       .perform()
                        print(f"✅ Entered start date: {start_date}")
                    except TimeoutException:
                        print("⚠️ 'Failed to enter start date! Retrying full sequence...")
                        retry_count += 1
                        time.sleep(1)
                        continue   

                    blank_space = driver.find_element(By.CSS_SELECTOR, ".content")
                    safe_click(driver, blank_space)

                    # Enter end date
                    try:
                        end_date_input = driver.find_element(By.CSS_SELECTOR, "#to_date")
                        actions.move_to_element(end_date_input)\
                       .click()\
                       .key_down(Keys.CONTROL)\
                       .send_keys("a")\
                       .key_up(Keys.CONTROL)\
                       .send_keys(end_date)\
                       .perform()
                        print(f"✅ Entered end date: {end_date}")
                    except TimeoutException:
                        print("⚠️ 'Failed to enter end date! Retrying full sequence...")
                        retry_count += 1
                        time.sleep(1)
                        continue   
                    
                    # driver.save_screenshot("pre-search.png")

                    # Lambdas for always grabbing fresh elements
                    get_search_button = lambda: WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "#btnSearch"))
                    )

                    # **Step 8: Click "Search" button**
                    try:
                        search_button = get_search_button()
                        actions.move_to_element(search_button)\
                       .click()\
                       .perform()
                        print(f"✅ Loading data from {start_date} to {end_date} for {brand}.")
                    except TimeoutException:
                        print("⚠️ 'Search' button not found! Retrying full sequence...")
                        retry_count += 1
                        time.sleep(1)
                        continue  

                    # **Step 10: Wait for the page to load**
                    try:
                        loading_overlay_selector = ".ajaxLoader"
                        time.sleep(1)
                        WebDriverWait(driver, 300).until(
                            EC.text_to_be_present_in_element_attribute((By.CSS_SELECTOR, loading_overlay_selector), "style", "display: none")
                        )
                    except TimeoutException:
                        print("⚠️ Loading overlay took too long! Retrying full sequence...")
                        retry_count += 1
                        time.sleep(1)
                        continue  

                    # **Step 11: Check if "No Record" is displayed**
                    if driver.find_elements(By.XPATH, "//div[contains(@class, 'box box-info tableData hide')]"):
                        print(f"⚠️ No data available for {brand}. Moving to next brand!\n")
                        break  
                    
                    time.sleep(1)
                    # driver.save_screenshot("pre-export.png")

                    # Lambdas for always grabbing fresh elements
                    get_export_button = lambda: WebDriverWait(driver, 60).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "#btnExport"))
                    )

                    # **Step 12: Click Export button**
                    try:
                        export_button = get_export_button()
                        actions.move_to_element(export_button)\
                       .click()\
                       .perform()
                        export_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"✅ Export for {brand} initiated at: {export_time} UTC +8")

                        time.sleep(3)  
                        export_report(driver, export_time, download_dir, brand)  

                    except TimeoutException:
                        print(f"⚠️ No data available for {brand}. Moving to next brand!\n")
                        break  # ✅ Instead of `continue`, we break to move to the next brand
                    
                    print(f"➡️ Completed export for brand {brand}. Moving to next brand...\n")
                    time.sleep(0.5)  
                    break  
                
                except StaleElementReferenceException:
                    print(f"⚠️ Retrying entire process for {brand} ({currency}) due to stale elements... Attempt {retry_count + 1}/{max_retries}")
                    retry_count += 1
                    time.sleep(1)
                    continue  
                
            # **Final check: If we exhausted retries, log a failure**
            if retry_count == max_retries:
                print(f"❌ Critical: Failed to process {brand} ({currency}) after {max_retries} full attempts!")
            
    except TimeoutException as e:
        print(f"❌ Error during page navigation: {str(e)}")

def get_webdriver_with_timezone(timezone_value):
    """Launch WebDriver with a specific timezone using DevTools Protocol."""
    
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)  # Keep browser open for debugging

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {
        "timezoneId": timezone_value  
    })

    print(f"🌍 WebDriver timezone set to: {timezone_value}")
    return driver

def qr_nav(driver, creds, timezone_mapping, download_dir):

    # Create an ActionChains object
    actions = ActionChains(driver)

    try:
        # **Step 1: Wait for the deposit page to load**
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".input-group"))
        )
        print("\n✅ Page loaded successfully.")

        # **Step 3: Iterate Over Each Brand**
        for brand in creds.get("brand", []):
            if brand not in creds:
                print(f"⚠️ No currency mapping found for brand {brand}, skipping...")
                continue

            currency = creds[brand]
            timezone_value = timezone_mapping.get(currency, "GMT+00:00")  # Default GMT

            print(f"🌍 Setting timezone for {brand} ({currency}): {timezone_value}")
            driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": timezone_value})

            print(f"✅ WebDriver timezone updated: {timezone_value}")

            # ✅ Refresh the page after setting the timezone
            print("🔄 Refreshing the page to apply timezone changes...")
            driver.refresh()

            # ✅ Wait for page reload
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".input-group"))  # Adjust this selector to match your page
            )
            print("✅ Page reloaded successfully.")
            # ✅ Continue with currency selection, search, and export...     

            # **Step 2: Handle "Approved" status selection**
            try:
                status_dropdown = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#status"))
                )
                safe_click(driver, status_dropdown)
                print("✅ Opened status dropdown.")

                all_option = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//select[@id='status']/option[text()='All']"))
                )
                safe_click(driver, all_option)
                print("✅ Selected 'All' status.")

            except TimeoutException:
                print("❌ Error: Could not find or select 'All' status.")      

            # **Step 4: Handle currency selection, timezone, and export with full retry**
            max_retries = 3  # ✅ Retry entire block 3 times if there's a stale element
            retry_count = 0

            while retry_count < max_retries:
                try:
                    # **Open the currency dropdown**
                    currency_dropdown = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".select2-selection"))
                    )
                    safe_click(driver, currency_dropdown)
                    print(f"✅ Opened currency dropdown for {brand} ({currency}).")

                    # **Deselect all selected currencies first**
                    deselect_attempts = 0
                    max_deselect_attempts = 5  

                    while deselect_attempts < max_deselect_attempts:
                        try:
                            # ✅ Find all remove buttons inside the selection container
                            remove_buttons = driver.find_elements(By.CSS_SELECTOR, ".select2-selection__choice__remove")

                            if not remove_buttons:
                                print("✅ All currencies are now deselected.")
                                break  # Exit loop if no selected options remain
                            
                            for _ in range(len(remove_buttons)):  # Process all remove buttons
                                remove_buttons = driver.find_elements(By.CSS_SELECTOR, ".select2-selection__choice__remove")
                                if not remove_buttons:
                                    print("✅ All currencies are now deselected.")
                                    break  # Stop if list is empty
                                
                                button = remove_buttons[0]  # Always click the first remove button
                                option_text = button.get_attribute("textContent").strip()
                                print(f"Attempting to deselect: {option_text}...")

                                # ✅ Click remove button
                                safe_click(driver, button)
                                time.sleep(0.5)  # Allow UI to update

                                # ✅ Ensure UI updates before proceeding
                                WebDriverWait(driver, 5).until_not(
                                    EC.presence_of_element_located((By.XPATH, f"//li[@class='select2-selection__choice' and @title='{option_text}']"))
                                )
                                print(f"✅ Deselected: {option_text}")

                            deselect_attempts += 1  # Increase attempt count

                        except StaleElementReferenceException:
                            print(f"⚠️ Stale element detected! Retrying... Attempt {deselect_attempts + 1}/{max_deselect_attempts}")
                            deselect_attempts += 1
                            time.sleep(0.5)  # Wait before retrying

                    # **Step 5: Select the corresponding currency**
                    max_attempts = 5  
                    attempts = 0

                    while attempts < max_attempts:
                        try:
                            # ✅ Find the correct currency option in the dropdown
                            currency_option = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, f"//li[contains(@class, 'select2-results__option') and text()='{currency}']"))
                            )

                            safe_click(driver, currency_option)
                            print(f"✅ Selected currency: {currency}")
                            break  
                        
                        except StaleElementReferenceException:
                            print(f"⚠️ Stale element detected! Retrying currency selection... Attempt {attempts + 1}/{max_attempts}")
                            attempts += 1
                            time.sleep(0.5)

                    # ✅ If currency selection failed after max attempts, retry full process
                    if attempts == max_attempts:
                        print(f"❌ Failed to select currency {currency} after {max_attempts} attempts. Retrying full sequence...")
                        retry_count += 1
                        time.sleep(1)
                        continue  
                    
                    # **Step 8: Click "Yesterday" button**
                    try:
                        yesterday_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//div[@data-type='yesterday' and contains(@class, 'range-item')]"))
                        )
                        safe_click(driver, yesterday_button)
                        print("✅ Loading previous day's data.")
                    except TimeoutException:
                        print("⚠️ 'Yesterday' button not found! Retrying full sequence...")
                        retry_count += 1
                        time.sleep(1)
                        continue  

                    # **Step 10: Wait for the page to load**
                    try:
                        loading_overlay_selector = ".ajaxLoader"
                        time.sleep(0.2)
                        WebDriverWait(driver, 300).until(
                            EC.text_to_be_present_in_element_attribute((By.CSS_SELECTOR, loading_overlay_selector), "style", "display: none")
                        )
                    except TimeoutException:
                        print("⚠️ Loading overlay took too long! Retrying full sequence...")
                        retry_count += 1
                        time.sleep(1)
                        continue  

                    # **Step 11: Check if "No Record" is displayed**
                    if driver.find_elements(By.XPATH, "//div[contains(@class, 'no-record-holder')]"):
                        print(f"⚠️ No data available for {brand}. Moving to next brand!\n")
                        break  
                    
                    # Lambdas for always grabbing fresh elements
                    get_export_button = lambda: WebDriverWait(driver, 60).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "#btnExport"))
                    )

                    # **Step 12: Click Export button**
                    try:
                        export_button = get_export_button()
                        actions.move_to_element(export_button)\
                       .click()\
                       .perform()
                        export_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"✅ Export for {brand} initiated at: {export_time} UTC +8")

                        time.sleep(3)  
                        export_report(driver, export_time, download_dir, brand)  

                    except TimeoutException:
                        print(f"⚠️ No data available for {brand}. Moving to next brand!\n")
                        break  # ✅ Instead of `continue`, we break to move to the next brand
                    
                    print(f"➡️ Completed export for brand {brand}. Moving to next brand...\n")
                    time.sleep(0.5)  
                    break  
                
                except StaleElementReferenceException:
                    print(f"⚠️ Retrying entire process for {brand} ({currency}) due to stale elements... Attempt {retry_count + 1}/{max_retries}")
                    retry_count += 1
                    time.sleep(1)
                    continue  
                
            # **Final check: If we exhausted retries, log a failure**
            if retry_count == max_retries:
                print(f"❌ Critical: Failed to process {brand} ({currency}) after {max_retries} full attempts!")
            
    except TimeoutException as e:
        print(f"❌ Error during page navigation: {str(e)}")

def get_most_recent_file(directory):
    """Returns the most recently modified file in the directory."""
    files = list(Path(directory).glob('*'))
    return max(files, key=os.path.getmtime) if files else None

    return None

### **Step 5: Export Report**
def export_report(driver, export_time, download_dir, brand):
    """Selects and downloads the latest completed export report, ensuring it appears in download_dir with a correct modified time."""
    
    try:
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
                    if recent_file.suffix.lower() in [".csv"]:
                        download_complete = True
                        print(f"✅ Download completed for {brand}! File saved as: {recent_file.name}")
    
                        rename_and_move_file(driver, download_dir, brand)
                        break
                    else:
                        print(f"⚠️ Found file '{recent_file.name}', but it is not a valid .csv file. Retrying...")
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

        # ✅ Extract the current URL to determine folder placement
        current_url = driver.current_url
        parsed_url = urlparse(current_url)
        path_segments = parsed_url.path.strip("/").split("/")
        last_segment = path_segments[-1] if path_segments else ""

        # ✅ Ensure 'ibs' directory exists
        smls_folder = os.path.join(download_dir)
        os.makedirs(smls_folder, exist_ok=True)

        # ✅ Determine the folder based on the last segment in the URL
        folder_mapping = {
            "deposit": "deposit",
            "withdraw": "withdrawal",
            "qr-deposit": "qr-deposit"
        }
        target_folder = os.path.join(smls_folder, folder_mapping.get(last_segment, ""))

        if not target_folder:
            print(f"⚠️ Unknown URL segment '{last_segment}', keeping file in default Downloads folder.")
            return  # ✅ Exit without moving if URL is unknown

        # ✅ Ensure the target folder exists before moving
        os.makedirs(target_folder, exist_ok=True)

        start_date = daterange.start_date
        end_date = daterange.end_date

        # ✅ Convert `start_date` and `end_date` to `YYYY-MM-DD` format if needed
        if isinstance(start_date, tuple):
            start_date = f"{start_date[0]}-{start_date[1]:02d}-{start_date[2]:02d}"
        if isinstance(end_date, tuple):
            end_date = f"{end_date[0]}-{end_date[1]:02d}-{end_date[2]:02d}"

        # ✅ Construct new file name using `{brand} {start_date} {end_date}`
        new_filename = f"{brand} {start_date} {end_date}{recent_file.suffix}"
        new_filepath = os.path.join(target_folder, new_filename)

        # ✅ If a file with the same name exists, delete it before moving
        if os.path.exists(new_filepath):
            os.remove(new_filepath)
            print(f"⚠️ Existing file '{new_filename}' found. Overwriting...")

        # ✅ Move and rename the file
        shutil.move(str(recent_file), new_filepath)
        print(Fore.GREEN + f"✅ File renamed and moved to: {new_filepath}")

        moved_files.append(new_filepath)

    except Exception as e:
        print(f"❌ Error renaming/moving file for {brand}: {e}")

def wait_for_browser_to_load(driver, timeout=10):
    """Waits until the browser finishes loading the page."""
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    time.sleep(0.5)

def safe_click(driver, locator, locator_type=By.CSS_SELECTOR, retries=100, wait_time=1):
    """
    Safely clicks on an element with retries if it becomes stale or is intercepted.
    """

    for attempt in range(retries):
        try:
            # ✅ If `locator` is a WebElement, don't search for it again
            if isinstance(locator, webdriver.remote.webelement.WebElement):
                element = locator
            else:
                element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((locator_type, locator))
                )

            element.click()
            return True  # ✅ Click succeeded
        
        except StaleElementReferenceException:
            print(f"⚠️ Stale element detected! Retrying {attempt + 1}/{retries}...")
        
        except ElementClickInterceptedException:
            print(f"⚠️ Click intercepted! Retrying {attempt + 1}/{retries}...")
        
        except TimeoutException:
            print("❌ Timeout waiting for element to be clickable.")
            return False
        
        time.sleep(wait_time)  # Wait before retrying

    print("❌ Click failed after multiple retries.")
    return False  # ❌ Click ultimately failed

def wait_for_loader_to_disappear(driver, timeout=20):
    try:
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element((By.CLASS_NAME, "modal-body"))
        )
        print("✅ Loader disappeared. Proceeding with the next step.")
    except Exception as e:
        print(f"❌ Loader did not disappear within {timeout} seconds: {e}")

def loading_animation(stop_event):
    """Displays a spinner animation in the terminal while loading is in progress."""
    spinner = itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
    while not stop_event.is_set():
        sys.stdout.write(f"\r⏳ Loading... {next(spinner)} ")
        sys.stdout.flush()
        time.sleep(0.001)
    sys.stdout.write("\r✅ Page finished loading.          \n")

# Initialize Colorama
init(autoreset=True, strip=False)

### **Main Execution**
def main():
    driver, download_dir = initialize_driver()  # ✅ Unpack the tuple properly
    credentials = load_credentials()
    timezones = load_timezones()

    smls_urls = {url: data for url, data in credentials.items() if data["bo"] == "IBS (seamless)"}
    
    print("Starting Seamless job.")

    global moved_files
    moved_files = []

    for url, creds in smls_urls.items():
        if not url or url.isspace():
            print("⚠️ Skipping an invalid URL (empty or None)")
            continue  # Skip this iteration

        if not url.startswith("http"):
            url = "https://" + url  # Ensure valid prefix

        print(f"\n🚀 Starting process for: {url}")

        login_success = login(driver, url, creds)
        if not login_success:
            print(f"⏩ Skipping {url} due to failed login.")
            continue  

        deposit(driver, url, creds, timezones, download_dir)
        withdrawal(driver, url, creds, timezones, download_dir)
        qr_deposit(driver, url, creds, timezones, download_dir)

    driver.quit()
    print("\n✅ Seamless job completed!")

    # Write the moved_files list to a temporary file for further processing if needed.
    moved_files_filepath = os.path.join(tempfile.gettempdir(), "smls_moved_files.txt")
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

if __name__ == "__main__":
    main()  # ✅ No need to pass parameters, as they are set inside `main()`