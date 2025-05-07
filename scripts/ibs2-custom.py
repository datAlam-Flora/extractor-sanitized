import tempfile
import json
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains as actions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.expected_conditions import any_of
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
    download_dir = os.path.join(current_directory, "downloads", "ibs-2")
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

    
    # ✅ Set WebDriver Timezone to GMT+0
    try:
        driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "GMT"})
        print("✅ WebDriver timezone set to GMT+0")
    except Exception as e:
        print(f"⚠️ Failed to set WebDriver timezone: {str(e)}")

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
            # # **Step 1: Wait until the page is loaded**
            # WebDriverWait(driver, 30).until(
            #     EC.element_to_be_clickable((By.CSS_SELECTOR, ".font-normal"))
            # )

            # **Step 2: Fill in the merchant code if available**
            try:
                merchant_field = driver.find_element(By.CSS_SELECTOR, "._dog-form > div:nth-child(1) > input:nth-child(1)")
                merchant_field.clear()
                merchant_field.send_keys(creds["merchant_code"])
            except NoSuchElementException:
                print(f"Merchant code field not found for {url}, skipping this step.")

            # **Step 3: Fill in the username**
            username_field = driver.find_element(By.CSS_SELECTOR, "div.mt-5:nth-child(2) > input:nth-child(1)")
            username_field.clear()
            username_field.send_keys(creds["username"])

            # **Step 4: Fill in the password**
            password_field = driver.find_element(By.CSS_SELECTOR, ".undefined")
            password_field.clear()
            password_field.send_keys(creds["password"])

            # **Step 5: Extract and enter the captcha**
            try:
                captcha_container = driver.find_element(By.CSS_SELECTOR, ".font-normal")
                captcha_text = "".join(span.text.strip() for span in captcha_container.find_elements(By.TAG_NAME, "span"))

                # **If captcha is blank, retry the login process**
                if not captcha_text.strip():
                    attempts += 1
                    print(f"⚠️ Captcha was blank! Retrying login attempt {attempts}/{max_attempts}...")
                    time.sleep(1.5)  # Short delay before retrying
                    continue  # Restart the login attempt
                
                print(f"Extracted Captcha: {captcha_text}")

                captcha_field = driver.find_element(By.CSS_SELECTOR, ".\\!border-none")
                captcha_field.clear()
                captcha_field.send_keys(captcha_text)
            except NoSuchElementException:
                print(f"Captcha not found for {url}, skipping captcha step.")

            # **Step 6: Submit login form**
            login_button = driver.find_element(By.CSS_SELECTOR, ".btn")
            login_button.click()

            # **Step 7: Wait for the page redirect to complete**
            try:
                WebDriverWait(driver, 60).until(
                    EC.url_contains("/en-us/dashboard")  # Ensure we have been redirected
                )
                print(f"✅ Successfully logged in and redirected to dashboard: {driver.current_url}\n")
                return True  # Login success

            except TimeoutException:
                print(f"❌ Error: Login successful but redirection to dashboard took too long (> 60 seconds).\n")
                return False  # Return False if redirection fails

        except Exception as e:
            print(f"❌ Error logging into {url}: {str(e)}")
            return False  # Return False if login fails

    print(f"❌ Failed to log in after {max_attempts} attempts. Skipping this site.\n")
    return False  # Return False after max retries

def get_most_recent_file(directory):
    """Returns the most recently modified file in the directory."""
    files = list(Path(directory).glob('*'))
    return max(files, key=os.path.getmtime) if files else None

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

### **Step 4: Navigate to Deposit Page**
def deposit_custom(driver, url, creds, timezone_mapping, download_dir):
    """Navigates to the deposit page, handles currency selection per brand, selects the correct timezone, and prepares for export."""
    
    deposit_url = f"{url}/en-us/finance-management/deposit"
    print(f"🌍 Navigating to deposit page: {deposit_url}")
    
    driver.get(deposit_url)
    deposit_withdrawal_nav_custom(driver, creds, timezone_mapping, download_dir)

def withdrawal_custom(driver, url, creds, timezone_mapping, download_dir):
    """Navigates to the deposit page, handles currency selection per brand, selects the correct timezone, and prepares for export."""
    
    withdrawal_url = f"{url}/en-us/finance-management/withdraw"
    print(f"🌍 Navigating to withdrawal page: {withdrawal_url}")
    
    driver.get(withdrawal_url)
    deposit_withdrawal_nav_custom(driver, creds, timezone_mapping, download_dir)

def qr_deposit_custom(driver, url, creds, timezone_mapping, download_dir):
    """Navigates to the QR deposit page, checks for redirects, and proceeds accordingly."""
    
    qr_deposit_url = f"{url}/en-us/finance-management/qr-deposit"
    dashboard_url = f"{url}/en-us/dashboard"

    print(f"🌍 Navigating to QR deposit page: {qr_deposit_url}")
    driver.get(qr_deposit_url)

    # ✅ Step 1: Wait until the browser finishes loading
    wait_for_browser_to_load(driver)
    time.sleep(1)

    # ✅ Step 2: Check if the user got redirected to the dashboard
    try:
        # ✅ Simultaneously check for either:
        # - The QR deposit page successfully loading (identified by a unique element)
        # - A redirect back to the dashboard (indicating the QR deposit page doesn't exist)
        WebDriverWait(driver, 10).until(
            any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".o-input-wrapper.right.o-select-container.cursor-pointer.capitalize")),
                EC.url_to_be(dashboard_url)  # ✅ Detects redirection immediately
            )
        )

        # ✅ Check final URL after waiting
        if driver.current_url == dashboard_url:
            print(f"⏭️ QR deposit page not available. Skipping QR deposits.")
            return  # ✅ Exit function gracefully
        print(f"current url {driver.current_url}")
        print("✅ QR deposit page loaded successfully.")

    except Exception:
        print("⚠️ Warning: QR deposit page did not load as expected. Proceeding with caution...")

    # ✅ Continue execution if not redirected
    qr_nav_custom(driver, creds, timezone_mapping, download_dir)

def deposit_withdrawal_nav_custom(driver, creds, timezone_mapping, download_dir):
    try:
        # **Step 1: Wait for the deposit page to load**
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".input-group"))
        )
        print("\n✅ Page loaded successfully.")

        # **Step 2: Handle "Approved" status selection**
        try:
            status_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".input-group > div:nth-child(5) > div:nth-child(2) > div:nth-child(1)"))
            )
            safe_click(driver, status_dropdown)
            print("✅ Opened status dropdown.")

            all_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'o-select-option')]/span[text()='All']"))
            )
            safe_click(driver, all_option)
            print("✅ Selected 'All' status.")
        
        except TimeoutException:
            print("❌ Error: Could not find or select 'All' status.")

        # **Step 3: Iterate Over Each Brand**
        for brand in creds.get("brand", []):
            if brand not in creds:
                print(f"⚠️ No currency mapping found for brand {brand}, skipping...")
                continue

            currency = creds[brand]             

            # **Step 4: Handle currency selection, timezone, and export with full retry**
            max_retries = 3  # ✅ Retry entire block 3 times if there's a stale element
            retry_count = 0

            while retry_count < max_retries:
                try:
                    # **Open the currency dropdown**
                    currency_dropdown = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".input-group > div:nth-child(2) > div:nth-child(2) > div:nth-child(1)"))
                    )
                    safe_click(driver, currency_dropdown)
                    print(f"✅ Opened currency dropdown for {brand} ({currency}).")

                    # **Deselect all selected currencies first**
                    deselect_attempts = 0
                    max_deselect_attempts = 5  

                    while deselect_attempts < max_deselect_attempts:
                        try:
                            selected_options = driver.find_elements(By.CSS_SELECTOR, ".o-select-option.selected")

                            for option in selected_options:
                                if "All" not in option.text:
                                    safe_click(driver, option)  
                                    print(f"✅ Deselected: {option.text}")

                            # ✅ Verify all options are unselected
                            remaining_selected = [
                                opt.text for opt in driver.find_elements(By.CSS_SELECTOR, ".o-select-option.selected") if "All" not in opt.text
                            ]

                            if not remaining_selected:
                                print("✅ All currencies are now deselected.")
                                break  
                            
                            print(f"⚠️ Warning: Some currencies are still selected ({remaining_selected}). Retrying deselection...")
                            deselect_attempts += 1

                        except StaleElementReferenceException:
                            print(f"⚠️ Stale element detected while deselecting! Retrying... Attempt {deselect_attempts + 1}/{max_deselect_attempts}")
                            deselect_attempts += 1
                            time.sleep(0.5)

                    # **Step 5: Select the corresponding currency**
                    max_attempts = 5  
                    attempts = 0

                    while attempts < max_attempts:
                        try:
                            currency_option = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, f"//span[@data-slug='{currency}']"))
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
                    
                    # **Step 6: Open timezone dropdown**
                    timezone_selectors = [
                        (By.CSS_SELECTOR, ".\\!text-black > div:nth-child(1)"),  
                        (By.CSS_SELECTOR, ".input-group > div:nth-child(12) > div:nth-child(2) > div:nth-child(1)")  
                    ]

                    timezone_container = None
                    for selector in timezone_selectors:
                        try:
                            timezone_container = WebDriverWait(driver, 2).until(
                                EC.element_to_be_clickable(selector)
                            )
                            break
                        except TimeoutException:
                            continue  
                        
                    if timezone_container:
                        safe_click(driver, timezone_container)
                        print("✅ Opened timezone dropdown.")
                    else:
                        print("❌ Failed to locate timezone dropdown! Retrying full sequence...")
                        retry_count += 1
                        time.sleep(1)
                        continue  
                    
                    # **Step 7: Select the correct timezone**
                    timezone_value = timezone_mapping.get(currency, "GMT+00:00")
                    try:
                        timezone_option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, f"//span[text()='{timezone_value}']"))
                        )
                        safe_click(driver, timezone_option)
                        print(f"✅ Selected timezone: {timezone_value}")
                    except TimeoutException:
                        print(f"❌ Failed to select timezone: {timezone_value}. Retrying full sequence...")
                        retry_count += 1
                        time.sleep(1)
                        continue  
                    
                    select_start_date(driver)
                    select_end_date(driver)

                    # Wait for the "Search" button to be clickable
                    search_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and normalize-space(text())='Search']"))
                    )
                    search_button.click()
                    print("✅ Clicked on the 'Search' button successfully.")

                    # **Step 10: Wait for the page to load**
                    try:
                        loading_overlay_selector = "div.box:nth-child(3) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1)"
                        WebDriverWait(driver, 300).until(
                            EC.invisibility_of_element_located((By.CSS_SELECTOR, loading_overlay_selector))
                        )
                    except TimeoutException:
                        print("⚠️ Loading overlay took too long! Retrying full sequence...")
                        retry_count += 1
                        time.sleep(1)
                        continue  

                    # **Step 11: Check if "No Record" is displayed**
                    if driver.find_elements(By.XPATH, "//span[contains(text(),'No Record')]\n"):
                        print(f"⚠️ No data available for {brand}. Moving to next brand!\n")
                        break  
                    
                    # **Step 12: Click Export button**
                    try:
                        export_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")   
                        time.sleep(1)
                        export_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, ".\\!bg-white"))
                        )
                        safe_click(driver, export_button)
                        print(f"✅ Export for {brand} initiated at: {export_time} UTC +8")

                        time.sleep(3)  
                        export_report_custom(driver, export_time, download_dir, brand)  

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

def qr_nav_custom(driver, creds, timezone_mapping, download_dir):
    try:
        # **Step 1: Wait for the deposit page to load**
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".o-input-wrapper"))
        )
        print("\n✅ Page loaded successfully.")

        # **Step 3: Iterate Over Each Brand**
        for brand in creds.get("brand", []):
            if brand not in creds:
                print(f"⚠️ No currency mapping found for brand {brand}, skipping...")
                continue

            currency = creds[brand]             

            # **Step 4: Handle currency selection, timezone, and export with full retry**
            max_retries = 3  # ✅ Retry entire block 3 times if there's a stale element
            retry_count = 0

            while retry_count < max_retries:
                try:
                    # **Open the currency dropdown**
                    currency_dropdown = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".input-group-lg > div:nth-child(1) > div:nth-child(2) > div:nth-child(1)"))
                    )
                    safe_click(driver, currency_dropdown)
                    print(f"✅ Opened currency dropdown for {brand} ({currency}).")

                    # **Deselect all selected currencies first**
                    deselect_attempts = 0
                    max_deselect_attempts = 5  

                    while deselect_attempts < max_deselect_attempts:
                        try:
                            selected_options = driver.find_elements(By.CSS_SELECTOR, ".o-select-option.selected")

                            for option in selected_options:
                                if "All" not in option.text:
                                    safe_click(driver, option)  
                                    print(f"✅ Deselected: {option.text}")

                            # ✅ Verify all options are unselected
                            remaining_selected = [
                                opt.text for opt in driver.find_elements(By.CSS_SELECTOR, ".o-select-option.selected") if "All" not in opt.text
                            ]

                            if not remaining_selected:
                                print("✅ All currencies are now deselected.")
                                break  
                            
                            print(f"⚠️ Warning: Some currencies are still selected ({remaining_selected}). Retrying deselection...")
                            deselect_attempts += 1

                        except StaleElementReferenceException:
                            print(f"⚠️ Stale element detected while deselecting! Retrying... Attempt {deselect_attempts + 1}/{max_deselect_attempts}")
                            deselect_attempts += 1
                            time.sleep(0.5)

                    # **Step 5: Select the corresponding currency**
                    max_attempts = 5  
                    attempts = 0

                    while attempts < max_attempts:
                        try:
                            currency_option = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, f"//span[@data-slug='{currency}']"))
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
                    
                    # **Step 6: Open timezone dropdown**
                    timezone_selectors = [
                        (By.CSS_SELECTOR, ".input-group-lg > div:nth-child(11) > div:nth-child(2) > div:nth-child(1)")  
                    ]

                    timezone_container = None
                    for selector in timezone_selectors:
                        try:
                            timezone_container = WebDriverWait(driver, 2).until(
                                EC.element_to_be_clickable(selector)
                            )
                            break
                        except TimeoutException:
                            continue  
                        
                    if timezone_container:
                        safe_click(driver, timezone_container)
                        print("✅ Opened timezone dropdown.")
                    else:
                        print("❌ Failed to locate timezone dropdown! Retrying full sequence...")
                        retry_count += 1
                        time.sleep(1)
                        continue  
                    
                    # **Step 7: Select the correct timezone**
                    timezone_value = timezone_mapping.get(currency, "GMT+00:00")
                    try:
                        timezone_option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, f"//span[text()='{timezone_value}']"))
                        )
                        safe_click(driver, timezone_option)
                        print(f"✅ Selected timezone: {timezone_value}")
                    except TimeoutException:
                        print(f"❌ Failed to select timezone: {timezone_value}. Retrying full sequence...")
                        retry_count += 1
                        time.sleep(1)
                        continue  
                    
                    select_start_date(driver)
                    select_end_date(driver)

                    # Wait for the "Search" button to be clickable
                    search_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and normalize-space(text())='Search']"))
                    )
                    search_button.click()
                    print("✅ Clicked on the 'Search' button successfully.")

                    # **Step 10: Wait for the page to load**
                    try:
                        loading_overlay_selector = "div.box:nth-child(3) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1)"
                        WebDriverWait(driver, 300).until(
                            EC.invisibility_of_element_located((By.CSS_SELECTOR, loading_overlay_selector))
                        )
                    except TimeoutException:
                        print("⚠️ Loading overlay took too long! Retrying full sequence...")
                        retry_count += 1
                        time.sleep(1)
                        continue  
                    
                    # **Step 12: Click Export button**
                    try:
                        export_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")   
                        time.sleep(1)
                        export_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, ".\\!bg-white"))
                        )
                        safe_click(driver, export_button)
                        print(f"✅ Export for {brand} initiated at: {export_time} UTC +8")

                        time.sleep(3)  
                        export_report_custom(driver, export_time, download_dir, brand)  

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

def export_report_custom(driver, export_time, download_dir, brand):
    """Selects and downloads the latest completed export report, ensuring it appears in download_dir with a correct modified time."""
    
    try:
        max_open_retries = 3  # ✅ Max retries if dropdown mysteriously closes
        open_attempts = 0

        while open_attempts < max_open_retries:
            try:
                # **Step 1: Click the Export dropdown button using text "Downloads"**
                export_dropdown = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Downloads')]"))
                )
                if not safe_click(driver, export_dropdown):
                    print(f"❌ Failed to click Export dropdown for {brand}.")
                    return
                print(f"✅ Export dropdown opened for {brand}.")

                # **Step 2: Ensure the dropdown remains visible**
                dropdown_visible = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".relative.w-full.h-full.p-1"))
                )

                if dropdown_visible:
                    print(f"✅ Confirmed dropdown is open for {brand}.")
                    break  # ✅ Proceed if dropdown stays open

            except TimeoutException:
                print(f"⚠️ Export dropdown closed unexpectedly! Retrying for {brand}... Attempt {open_attempts + 1}/{max_open_retries}")
                open_attempts += 1
                time.sleep(1)

        if open_attempts == max_open_retries:
            print(f"❌ Critical: Export dropdown could not be kept open after multiple attempts for {brand}!")
            return

        # **Step 3: Retrying loop to wait for valid reports to appear**
        max_retries = 15  # Wait for up to 30 seconds
        retry_count = 0
        found_valid_report = False  
        report_times = []

        while retry_count < max_retries:
            # Define lambda for checking if dropdown is open
            is_dropdown_open = lambda: len(driver.find_elements(By.CSS_SELECTOR, ".relative.w-full.h-full.p-1")) > 0

            # Fix 1: Remove the comma after driver
            get_dropdown = lambda: WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".actual-dropdown-selector"))
            )

            # Fix 2: Define reopen_dropdown as a function
            reopen_dropdown = lambda: actions(driver).move_to_element(get_dropdown()).pause(0.5).click().perform()

            # Use in your code
            try:
                # Check if dropdown is open using the lambda
                if not is_dropdown_open():
                    print(f"⚠️ Dropdown closed while searching for reports for {brand}. Reopening...")
                    reopen_dropdown()
                    time.sleep(1)
                    continue 

                # **Re-locate timestamp elements inside the loop**
                get_timestamp_elements = lambda: WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.text-xs"))
                )

                timestamp_elements = get_timestamp_elements()

                for timestamp_element in timestamp_elements:
                    try:
                        report_time_str = timestamp_element.text.strip()
                        # **Convert string timestamp to datetime object**
                        try:
                            report_time = datetime.strptime(report_time_str, "%Y-%m-%d %H:%M:%S")
                            report_times.append(report_time)
                        except ValueError:
                            continue  
                        
                        # **Convert export_time (string) to datetime for comparison**
                        export_time_dt = datetime.strptime(export_time, "%Y-%m-%d %H:%M:%S")
                        # print(f"Report time: {report_time_str} for {brand}. Expected time: ({export_time_dt})")

                        # **Step 4: Check if report is later than export_time**
                        if report_time >= export_time_dt:
                            get_parent_button = lambda: timestamp_element.find_element(By.XPATH, "./ancestor::button")
                            
                            # **Step 5: Check if status is "Completed"**
                            try:
                                parent_button = get_parent_button()
                                get_status_text = lambda button: button.find_element(By.CSS_SELECTOR, "span.progress-status.text-xs").text.strip()
                                status_text = get_status_text(parent_button)

                                if status_text == "Completed":
                                    print(f"✅ Found valid report for {brand}: {report_time_str}")
                                    if not safe_click(driver, parent_button):
                                        print(f"❌ Failed to click report button for {brand}.")
                                        continue
                                    
                                    print(f"📂 Report download initiated for {brand}.")
                                    found_valid_report = True
                                    break  

                            except NoSuchElementException:
                                print(f"⚠️ Skipping {report_time_str} for {brand} (Status not found)")

                    except StaleElementReferenceException:
                        print(f"⚠️ Stale element detected for {brand}, retrying...")
                        time.sleep(1)
                        continue  

            except StaleElementReferenceException:
                print(f"⚠️ Stale elements detected, retrying search for reports for {brand}...")
                retry_count += 1
                time.sleep(1)
                continue  
            
            if found_valid_report:
                break  

            retry_count += 1
            time.sleep(2)  # ✅ Wait before retrying
            if report_times:
                latest_report_time = max(report_times)  # Get the latest time
                if latest_report_time >= export_time_dt:
                    print(f"✅ Found valid report time {latest_report_time} for {brand}, but status is still {status_text}. Retrying...")
                else:
                    print(f"⏳Latest report time {latest_report_time} is earlier than {export_time_dt} for {brand}. Retrying...")
            else:
                print(f"⏳No valid report times found for {brand}. Retrying...") 

        if not found_valid_report:
            print(f"⚠️ No valid reports found after waiting for 60 attempts for {brand}.")
            return

        # **Step 6: Wait for the downloaded file to appear in the download directory**
        print(f"⏳ Waiting for the report file for {brand} to finish downloading...")
        download_complete = False
        start_time = time.time()
        timeout = 300  # ✅ Increase timeout for slower downloads
        
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
                    if recent_file.suffix.lower() in [".csv", ".xlsx"]:
                        download_complete = True
                        print(f"✅ Download completed for {brand}! File saved as: {recent_file.name}")

                        # ✅ Rename and move the file
                        rename_and_move_file_custom(driver, download_dir, brand)
                        break
                    else:
                        print(f"⚠️ Found file '{recent_file.name}', but it is not a valid CSV or Excel file. Retrying...")
                        time.sleep(1)
                else:
                    print(f"⚠️ Found file '{recent_file.name}', but modified at {file_modified_time_str}, which is before {export_time}. Retrying...")
                    time.sleep(1)
            else:
                time.sleep(0.5)
        
        if not download_complete:
            print(f"❌ Error: File download did not complete within the expected time for {brand}.")
        

    except Exception as e:
        print(f"❌ Failed to open export dropdown: {e}")

    finally:
        try:
            blank_space = driver.find_element(By.CSS_SELECTOR, "body")
            safe_click(driver, blank_space)
            print(f"✅ Clicked on blank space to reset the page for {brand}.")
        except Exception as e:
            print(f"⚠️ Failed to click blank space for {brand}: {e}")   

def rename_and_move_file_custom(driver, download_dir, brand):
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
        ibs_folder = os.path.join(current_dir, "downloads", "ibs")
        os.makedirs(ibs_folder, exist_ok=True)

        # ✅ Determine the folder based on the last segment in the URL
        folder_mapping = {
            "deposit": "deposit",
            "withdraw": "withdrawal",
            "qr-deposit": "qr-deposit"
        }
        target_folder = os.path.join(ibs_folder, folder_mapping.get(last_segment, ""))

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

def select_start_date(driver):
    """
    Selects a specific start date from the calendar dropdown.

    Args:
        driver: The Selenium WebDriver instance.
        target_year: The desired year (e.g., 2025).
        target_month: The desired month as an integer (e.g., 2 for February).
        target_day: The desired day of the month (e.g., 10).
    """
    wait = WebDriverWait(driver, 10)

    target_year, target_month, target_day = daterange.start_date  # Extract year, month, day from daterange.py

    # **Step 1: Click the "Start Date" or "Date From" input field to open the calendar dropdown**
    date_picker = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//div[contains(@class, 'label') and (contains(text(), 'Start Date') or contains(text(), 'Date From'))]/following-sibling::div//div[contains(@class, 'o-input-wrapper')]")
    ))
    date_picker.click()

    # **Step 2: Ensure the correct year is selected**
    while True:
        year_element = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//button[contains(@class, 'op-dp-date-btn')][2]")
        ))
        displayed_year = year_element.text.strip()

        if displayed_year.isdigit():  # Ensure the year is a valid number
            displayed_year = int(displayed_year)
            if displayed_year == target_year:
                break  # ✅ Year is correct

            if displayed_year < target_year:
                next_year_btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(@class, 'op-dp-nav-btn')][2]")
                ))
                next_year_btn.click()

            else:
                prev_year_btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(@class, 'op-dp-nav-btn')][1]")
                ))
                prev_year_btn.click()
        else:
            print("⚠️ Year not loaded properly. Retrying...")

    # **Step 3: Ensure the correct month is selected**
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    next_month_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(@class, 'op-dp-nav-btn')][2]")
    ))
    next_month_btn.click()

    while True:
        month_element = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//button[contains(@class, 'op-dp-date-btn')][1]")
        ))
        displayed_month = month_element.text.strip()

        if displayed_month == month_names[target_month - 1]:
            break  # ✅ Month is correct

        prev_month_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@class, 'op-dp-nav-btn')][1]")
        ))
        prev_month_btn.click()

    # **Step 4: Select the correct day**
    day_xpath = f"//div[(@class='dpBodyCell' or @class='dpBodyCell selected') and text()='{target_day}']"
    day_element = wait.until(EC.element_to_be_clickable((By.XPATH, day_xpath)))

    try:
        day_element.click()
    except ElementClickInterceptedException:
        print(f"⚠️ Click intercepted, using JavaScript click.")
        driver.execute_script("arguments[0].click();", day_element)


    # day_element.click()

    print(f"✅ Successfully selected {target_year}-{target_month:02d}-{target_day}")

def select_end_date(driver):
    """
    Selects a specific end date from the calendar dropdown.

    Args:
        driver: The Selenium WebDriver instance.
        target_year: The desired year (e.g., 2025).
        target_month: The desired month as an integer (e.g., 2 for February).
        target_day: The desired day of the month (e.g., 10).
    """
    wait = WebDriverWait(driver, 10)

    target_year, target_month, target_day = daterange.end_date  # Extract year, month, day from daterange.py

    # **Step 1: Click the "End Date" or "Date To" input field to open the calendar dropdown**
    date_picker = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//div[contains(@class, 'label') and (contains(text(), 'End Date') or contains(text(), 'Date To'))]/following-sibling::div//div[contains(@class, 'o-input-wrapper')]")
    ))
    date_picker.click()

    # **Step 2: Ensure the correct year is selected**
    while True:
        year_element = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//button[contains(@class, 'op-dp-date-btn')][2]")
        ))
        displayed_year = year_element.text.strip()

        if displayed_year.isdigit():  # Ensure the year is a valid number
            displayed_year = int(displayed_year)
            if displayed_year == target_year:
                break  # ✅ Year is correct

            if displayed_year < target_year:
                next_year_btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(@class, 'op-dp-nav-btn')][2]")
                ))
                next_year_btn.click()
            else:
                prev_year_btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(@class, 'op-dp-nav-btn')][1]")
                ))
                prev_year_btn.click()
        else:
            print("⚠️ Year not loaded properly. Retrying...")

    # **Step 3: Ensure the correct month is selected**
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    next_month_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(@class, 'op-dp-nav-btn')][2]")
    ))
    next_month_btn.click()

    while True:
        month_element = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//button[contains(@class, 'op-dp-date-btn')][1]")
        ))
        displayed_month = month_element.text.strip()

        if displayed_month == month_names[target_month - 1]:
            break  # ✅ Month is correct

        prev_month_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@class, 'op-dp-nav-btn')][1]")
        ))
        prev_month_btn.click()

    # **Step 4: Select the correct day**
    day_xpath = f"//div[(@class='dpBodyCell' or @class='dpBodyCell selected') and text()='{target_day}']"
    day_element = wait.until(EC.element_to_be_clickable((By.XPATH, day_xpath)))
    # day_element.click()
    
    try:
        day_element.click()
    except ElementClickInterceptedException:
        print(f"⚠️ Click intercepted, using JavaScript click.")
        driver.execute_script("arguments[0].click();", day_element)

    print(f"✅ Successfully selected {target_year}-{target_month:02d}-{target_day}")

### **Main Execution**
def main():
    driver, download_dir = initialize_driver()  # ✅ Unpack the tuple properly
    credentials = load_credentials()
    timezones = load_timezones()

    ibs_urls = {url: data for url, data in credentials.items() if data["bo"] == "IBS-2"}
    
    print("Starting IBS job.")

    global moved_files
    moved_files = []

    for url, creds in ibs_urls.items():
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

        deposit_custom(driver, url, creds, timezones, download_dir)
        withdrawal_custom(driver, url, creds, timezones, download_dir)
        qr_deposit_custom(driver, url, creds, timezones, download_dir)

    driver.quit()
    print("\n✅ IBS job completed!")

    # Write the moved_files list to a temporary file for further processing if needed.
    moved_files_filepath = os.path.join(tempfile.gettempdir(), "ibs2_moved_files.txt")
    with open(moved_files_filepath, "w") as f:
        for path in moved_files:
            f.write(path + "\n")
    print(f"MOVED_FILES_FILE:{moved_files_filepath}")

if __name__ == "__main__":
    main()  # ✅ No need to pass parameters, as they are set inside `main()`