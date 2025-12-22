# amazon_auto_login.py
"""
Amazon Auto Login Module
Handles automatic login to Amazon with human-like behavior and 2FA support
"""

import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys

from scraping_config import ScrapingConfig


class AmazonAutoLogin:
    """Handles automatic login to Amazon with anti-detection measures"""

    def __init__(self, email, password, max_retries=2):
        """
        Initialize auto login handler

        Args:
            email (str): Amazon account email
            password (str): Amazon account password
            max_retries (int): Maximum login attempts before falling back to manual
        """
        self.email = email
        self.password = password
        self.max_retries = max_retries

    def _simulate_human_typing(self, element, text, min_delay=None, max_delay=None):
        """Simulate human-like typing with random delays"""
        if min_delay is None:
            min_delay = ScrapingConfig.TYPING_DELAY_MIN
        if max_delay is None:
            max_delay = ScrapingConfig.TYPING_DELAY_MAX
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(min_delay, max_delay))

    def _is_login_page(self, driver):
        """Check if current page is a login page"""
        try:
            current_url = driver.current_url.lower()
            page_title = driver.title.lower()
            page_source = driver.page_source.lower()

            # First check if we're on a product/reviews page (if so, not login page)
            try:
                review_elements = driver.find_elements(By.CSS_SELECTOR, 'div[data-hook="review"], div[data-hook="cr-review"]')
                if review_elements:
                    return False  # Has reviews, so not login page
            except:
                pass

            # Multiple indicators for login page
            login_indicators = [
                '/ap/signin' in current_url,
                'sign in' in page_title,
                'signin' in page_source,
                'amazon sign-in' in page_title,
                'login' in page_title and 'amazon' in page_title
            ]

            return any(login_indicators)
        except:
            return False

    def _wait_for_element(self, driver, selector, timeout=10):
        """Wait for element to be present and return it"""
        try:
            return WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
        except TimeoutException:
            return None

    def _fill_email_field(self, driver):
        """Fill in the email field"""
        email_selectors = [
            'input[name="email"]',
            'input[name="username"]',
            'input[type="email"]',
            'input[placeholder*="email"]',
            'input[placeholder*="Email"]',
            '#ap_email'
        ]

        for selector in email_selectors:
            try:
                email_field = self._wait_for_element(driver, selector, timeout=5)
                if email_field and email_field.is_displayed():
                    print("  Found email field, typing email...")
                    self._simulate_human_typing(email_field, self.email)
                    time.sleep(ScrapingConfig.get_interaction_delay())
                    return True
            except:
                continue

        return False

    def _fill_password_field(self, driver):
        """Fill in the password field"""
        password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
            '#ap_password'
        ]

        for selector in password_selectors:
            try:
                password_field = self._wait_for_element(driver, selector, timeout=5)
                if password_field and password_field.is_displayed():
                    print("  Found password field, typing password...")
                    self._simulate_human_typing(password_field, self.password)
                    time.sleep(ScrapingConfig.get_interaction_delay())
                    return True
            except:
                continue

        return False

    def _click_continue_or_signin(self, driver):
        """Click continue or sign in button"""
        button_selectors = [
            'input[type="submit"]',
            'button[type="submit"]',
            '#continue',
            '#signInSubmit',
            'span[id="continue"]',
            'span[id="signInSubmit"]',
            'input[aria-labelledby="continue"]',
            'button[aria-labelledby="signInSubmit"]'
        ]

        for selector in button_selectors:
            try:
                button = self._wait_for_element(driver, selector, timeout=3)
                if button and button.is_displayed() and button.is_enabled():
                    print(f"  Clicking button: {selector}")
                    button.click()
                    time.sleep(ScrapingConfig.get_login_delay())
                    return True
            except:
                continue

        return False

    def _handle_two_factor_auth(self, driver):
        """Handle two-factor authentication"""
        print("\n" + "="*60)
        print("TWO-FACTOR AUTHENTICATION DETECTED!")
        print("="*60)
        print("Please complete 2FA in the browser window:")
        print("1. Check your email/SMS for the verification code")
        print("2. Enter the code in the browser")
        print("3. Click 'Continue' or 'Verify'")
        print("4. Wait for the login to complete")
        print("5. THEN press Enter here to continue...")
        print("="*60)

        input("Press Enter after completing 2FA: ")

        # Wait longer for the page to load after 2FA (Amazon may take time to redirect)
        time.sleep(ScrapingConfig.get_two_fa_delay())

        # Check if we're still on a login-related page
        if self._is_login_page(driver):
            print("  Still on login page after 2FA. Login may have failed.")
            return False

        print("  2FA completed successfully.")
        return True

    def _verify_login_success(self, driver, original_url):
        """Verify that login was successful"""
        try:
            current_url = driver.current_url.lower()
            page_title = driver.title.lower()

            # Check if we're back to the original page or a product page
            success_indicators = [
                'product-reviews' in current_url,
                'dp/' in current_url,
                'product' in current_url and 'amazon' in page_title,
                'customer reviews' in page_title,
                not self._is_login_page(driver)
            ]

            if any(success_indicators):
                print("  Login verification successful.")
                return True
            else:
                print("  Login verification failed - still on unexpected page.")
                return False

        except Exception as e:
            print(f"  Error during login verification: {e}")
            return False

    def _attempt_automatic_login(self, driver):
        """Attempt automatic login"""
        try:
            print("  Attempting automatic login...")

            # Step 1: Fill email
            if not self._fill_email_field(driver):
                print("  Could not find email field.")
                return False

            # Step 2: Click continue (if separate step)
            self._click_continue_or_signin(driver)

            # Step 3: Fill password (may be on same or next page)
            if not self._fill_password_field(driver):
                print("  Could not find password field.")
                return False

            # Step 4: Click sign in
            if not self._click_continue_or_signin(driver):
                print("  Could not find sign in button.")
                return False

            # Step 5: Check for 2FA
            time.sleep(ScrapingConfig.get_login_delay())
            if self._check_for_2fa(driver):
                if not self._handle_two_factor_auth(driver):
                    return False

            # Step 6: Wait for login to complete
            time.sleep(ScrapingConfig.get_login_complete_delay())

            return True

        except Exception as e:
            print(f"  Error during automatic login attempt: {e}")
            return False

    def _check_for_2fa(self, driver):
        """Check if 2FA challenge is present"""
        try:
            page_source = driver.page_source.lower()
            title = driver.title.lower()

            # Check for specific 2FA form elements first
            twofa_selectors = [
                'input[placeholder*="code"]',
                'input[placeholder*="OTP"]',
                'input[name*="code"]',
                'input[name*="otp"]',
                'input[id*="code"]',
                'input[id*="otp"]'
            ]

            for selector in twofa_selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        return True
                except NoSuchElementException:
                    continue

            # Fallback to text indicators (more specific)
            twofa_indicators = [
                'two-step verification' in page_source and 'amazon' in page_source,
                '2-step verification' in page_source and 'amazon' in page_source,
                'verification code' in page_source and 'amazon' in page_source,
                'enter the code' in page_source and 'amazon' in page_source,
                'otp' in page_source and 'verification' in page_source,
                'authentication code' in title
            ]

            return any(twofa_indicators)
        except:
            return False

    def _manual_login_fallback(self, driver, original_url):
        """Fallback to manual login"""
        print("\n" + "="*60)
        print("AUTOMATIC LOGIN FAILED - MANUAL LOGIN REQUIRED")
        print("="*60)
        print("Please manually login in the browser window.")
        print("\nInstructions:")
        print("1. Enter your Amazon username/password")
        print("2. Complete 2FA if required")
        print("3. WAIT until you see the product reviews page")
        print("4. THEN press Enter here to continue")
        print("="*60)

        input("Press Enter ONLY AFTER you have completed login and see reviews: ")

        # Reload the original URL after manual login
        print("\nReloading reviews page...")
        driver.get(original_url)
        time.sleep(ScrapingConfig.get_page_load_delay())

        # Verify we're not back on login page
        if self._is_login_page(driver):
            print("Still on login page after manual login attempt.")
            return False

        return True

    def handle_login_automatically(self, driver, url):
        """
        Main method to handle login automatically with manual fallback

        Args:
            driver: Selenium WebDriver instance
            url (str): Target URL to navigate to

        Returns:
            bool: True if login successful, False otherwise
        """
        print(f"\nNavigating to: {url}")
        driver.get(url)

        # Wait for page to load
        time.sleep(ScrapingConfig.get_page_load_delay())

        # Check if login is required
        current_url = driver.current_url.lower()
        if not self._is_login_page(driver) or 'dp/' in current_url:
            print("No login required - proceeding with scraping.")
            return True

        print("Login page detected - attempting automatic login...")

        # Try automatic login up to max_retries times
        for attempt in range(1, self.max_retries + 1):
            print(f"\nLogin attempt {attempt}/{self.max_retries}")

            if self._attempt_automatic_login(driver):
                # Verify login success
                if self._verify_login_success(driver, url):
                    print("✓ Automatic login successful!")
                    return True
                else:
                    print("Login attempt failed verification.")
            else:
                print("Automatic login attempt failed.")

            # If not the last attempt, wait before retry
            if attempt < self.max_retries:
                wait_time = ScrapingConfig.get_retry_delay()
                print(f"Waiting {wait_time:.1f} seconds before retry...")
                time.sleep(wait_time)

                # Refresh page for next attempt
                driver.refresh()
                time.sleep(ScrapingConfig.get_interaction_delay())

        # All automatic attempts failed - fallback to manual
        print("All automatic login attempts failed.")
        return self._manual_login_fallback(driver, url)