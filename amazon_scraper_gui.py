# amazon_scraper_gui.py
"""
Amazon Product Search & Review Scraper - GUI Version
Enhanced scraper with GUI integration and threading support
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
import time
import os
import sys
import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import pandas as pd
import random
import re
import json
import urllib.parse

from config import AmazonConfig
from amazon_auto_login import AmazonAutoLogin
from amazon_selectors import AmazonSelectors
from scraping_config import ScrapingConfig

class AmazonScraperGUI:
    """Enhanced Amazon scraper with GUI integration"""

    def __init__(self, gui_callback=None, headless=False, domain="amazon.com", email=None, password=None):
        """
        Initialize scraper with GUI callback

        Args:
            gui_callback: Function to call for GUI updates (progress, status, etc.)
            headless: Whether to run browser in headless mode
            domain: Amazon domain to use (e.g., 'amazon.com', 'amazon.co.uk')
            email: Amazon account email (optional)
            password: Amazon account password (optional)
        """
        self.gui_callback = gui_callback
        self.headless = headless
        self.domain = domain
        self.driver = None
        self.auto_login = None

        # Setup auto login
        if email and password:
            self.auto_login = AmazonAutoLogin(email, password)
            self.update_gui('status', 'Auto login configured with provided credentials')
        else:
            # Fallback to config
            try:
                email, password = AmazonConfig.check_and_setup()
                if email and password:
                    self.auto_login = AmazonAutoLogin(email, password)
                    self.update_gui('status', 'Auto login configured from .env')
                else:
                    self.update_gui('status', 'No credentials available - manual login may be required')
            except Exception as e:
                self.update_gui('error', f'Error setting up credentials: {e}')

    def update_gui(self, message_type, data):
        """Update GUI through callback"""
        if self.gui_callback:
            self.gui_callback(message_type, data)

    def setup_stealth_driver(self):
        """Configure a stealthy Chrome browser driver"""
        self.update_gui('status', 'Setting up Chrome driver...')

        chrome_options = Options()

        # Anti-detection settings
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Regular browser-like settings
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        # Headless mode
        if self.headless:
            chrome_options.add_argument('--headless')
        else:
            chrome_options.add_argument('--start-maximized')

        # Random user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        ]
        chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')

        # Setup driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        # Hide automation
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            '''
        })

        self.update_gui('status', 'Chrome driver ready')

        return self.driver

    def extract_asin_from_url(self, url):
        """Extract ASIN from Amazon URL"""
        patterns = [
            r'/dp/([A-Z0-9]{10})',
            r'/gp/product/([A-Z0-9]{10})',
            r'/product/([A-Z0-9]{10})',
            r'/([A-Z0-9]{10})(?:[/?]|$)',
            r'/ASIN/([A-Z0-9]{10})'
        ]

        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1).upper()

        return None

    def _initialize_product_info(self):
        """Initialize product info dictionary with default values"""
        return {
            'index': 1,
            'asin': "UNKNOWN",
            'title': "Title not found",
            'price': "Price not available",
            'rating': "No rating",
            'reviews_count': "0",
            'extraction_errors': []  # Track which fields failed to extract
        }

    def _handle_page_navigation(self, url):
        """Navigate to URL and handle continue shopping button"""
        self.driver.get(url)
        time.sleep(ScrapingConfig.get_page_load_delay())

        # Handle "Continue shopping" button if present (sometimes Amazon shows this before login)
        try:
            continue_button = self.driver.find_element(By.CSS_SELECTOR, AmazonSelectors.CONTINUE_SHOPPING_BUTTON)
            continue_button.click()
            time.sleep(ScrapingConfig.get_interaction_delay())
            self.update_gui('status', 'Clicked "Continue shopping" button')
        except NoSuchElementException:
            pass  # Button not present, continue normally

    def _check_for_blocking_pages(self, product_info):
        """Check if page is blocked by login or CAPTCHA"""
        current_url = self.driver.current_url.lower()
        page_title = self.driver.title.lower()

        if '/ap/signin' in current_url or 'sign in' in page_title:
            product_info['extraction_errors'].append("Login required")
            self.update_gui('status', 'Login page detected')
            return True

        if 'captcha' in page_title or 'robot' in page_title:
            product_info['extraction_errors'].append("CAPTCHA/robot detection")
            self.update_gui('status', 'CAPTCHA detected')
            return True

        return False

    def _extract_product_asin(self, url, product_info):
        """Extract ASIN from various sources"""
        try:
            # Method 1: Extract from URL
            asin = self.extract_asin_from_url(url)
            if asin:
                product_info['asin'] = asin
                self.update_gui('status', f'ASIN extracted from URL: {asin}')
                return

            # Method 2: Extract from page source
            try:
                asin_elem = self.driver.find_element(By.CSS_SELECTOR, 'input[name="ASIN"]')
                asin = asin_elem.get_attribute('value')
                if asin and len(asin) == 10:
                    product_info['asin'] = asin
                    self.update_gui('status', f'ASIN extracted from form: {asin}')
                    return
            except:
                pass

            # Method 3: Extract from meta tags or script tags
            try:
                page_source = self.driver.page_source
                # Look for ASIN in various formats
                asin_patterns = [
                    r'"ASIN"\s*:\s*"([A-Z0-9]{10})"',
                    r'ASIN["\']?\s*:\s*["\']?([A-Z0-9]{10})',
                    r'var asin = "([A-Z0-9]{10})"',
                    r'data-asin="([A-Z0-9]{10})"',
                    r'input.*name="ASIN".*value="([A-Z0-9]{10})"'
                ]

                for pattern in asin_patterns:
                    match = re.search(pattern, page_source, re.IGNORECASE)
                    if match:
                        asin = match.group(1)
                        if len(asin) == 10:
                            product_info['asin'] = asin
                            self.update_gui('status', f'ASIN extracted from page source: {asin}')
                            return
            except:
                pass

            # Method 4: Try to extract from page title as last resort
            try:
                title_elem = self.driver.find_element(By.TAG_NAME, 'title')
                title_text = title_elem.text
                asin_match = re.search(r'([A-Z0-9]{10})', title_text)
                if asin_match and len(asin_match.group(1)) == 10:
                    product_info['asin'] = asin_match.group(1).upper()
                    self.update_gui('status', f'ASIN extracted from title: {product_info["asin"]}')
            except:
                pass

        except Exception as e:
            product_info['extraction_errors'].append(f"ASIN extraction failed: {str(e)[:50]}")
            self.update_gui('status', f'ASIN extraction error: {e}')

    def _extract_product_title(self, product_info):
        """Extract product title"""
        try:
            title_found = False
            for selector in AmazonSelectors.PRODUCT_TITLE_SELECTORS:
                try:
                    title_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    title_text = title_elem.text.strip()
                    if title_text and len(title_text) > 3:
                        product_info['title'] = title_text[:150]
                        self.update_gui('status', f'Title extracted: {title_text[:50]}...')
                        title_found = True
                        break
                except:
                    continue

            if not title_found:
                product_info['extraction_errors'].append("Title not found with any selector")
                self.update_gui('status', 'Title not found with any selector')

        except Exception as e:
            product_info['extraction_errors'].append(f"Title extraction failed: {str(e)[:50]}")
            self.update_gui('status', f'Title extraction error: {e}')

    def _extract_product_price(self, product_info):
        """Extract product price"""
        try:
            price_found = False
            for selector in AmazonSelectors.PRODUCT_PRICE_SELECTORS:
                try:
                    price_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_elem.get_attribute('textContent') or price_elem.text
                    price_text = html.unescape(price_text).strip()

                    # Validate price format
                    if price_text and ('$' in price_text or '€' in price_text or '£' in price_text):
                        # Clean up price text
                        price_text = re.sub(r'[^\d.,$€£\s]', '', price_text)
                        price_text = re.sub(r'\s+', ' ', price_text).strip()

                        if price_text:
                            product_info['price'] = price_text
                            self.update_gui('status', f'Price extracted: {price_text}')
                            price_found = True
                            break
                except:
                    continue

            if not price_found:
                # Try to find price in text content
                try:
                    body_text = self.driver.find_element(By.TAG_NAME, 'body').text
                    price_matches = re.findall(r'[$€£]\s*\d+[.,]?\d*', body_text)
                    if price_matches:
                        product_info['price'] = price_matches[0]
                        self.update_gui('status', f'Price extracted from body text: {price_matches[0]}')
                        price_found = True
                except:
                    pass

            if not price_found:
                product_info['extraction_errors'].append("Price not found with any method")
                self.update_gui('status', 'Price not found with any method')

        except Exception as e:
            product_info['extraction_errors'].append(f"Price extraction failed: {str(e)[:50]}")
            self.update_gui('status', f'Price extraction error: {e}')

    def _extract_product_rating(self, product_info):
        """Extract product rating"""
        try:
            rating_found = False
            for selector in AmazonSelectors.PRODUCT_RATING_SELECTORS:
                try:
                    rating_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    rating_text = rating_elem.get_attribute('aria-label') or rating_elem.text or rating_elem.get_attribute('innerHTML')

                    if rating_text:
                        # Extract numeric rating
                        match = re.search(r'(\d+\.?\d*)', rating_text)
                        if match:
                            rating_value = float(match.group(1))
                            # Validate rating is in reasonable range
                            if 1 <= rating_value <= 5:
                                product_info['rating'] = str(rating_value)
                                self.update_gui('status', f'Rating extracted: {rating_value}')
                                rating_found = True
                                break
                except:
                    continue

            if not rating_found:
                product_info['extraction_errors'].append("Rating not found with any selector")
                self.update_gui('status', 'Rating not found with any selector')

        except Exception as e:
            product_info['extraction_errors'].append(f"Rating extraction failed: {str(e)[:50]}")
            self.update_gui('status', f'Rating extraction error: {e}')

    def _extract_product_reviews_count(self, product_info):
        """Extract product reviews count"""
        try:
            reviews_found = False
            for selector in AmazonSelectors.PRODUCT_REVIEW_COUNT_SELECTORS:
                try:
                    review_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    review_text = review_elem.get_attribute('aria-label') or review_elem.text

                    if review_text:
                        # Extract numbers and handle different formats
                        review_text = review_text.replace(',', '').replace(' ', '')

                        # Handle K format (thousands)
                        if 'K' in review_text.upper():
                            match = re.search(r'(\d+\.?\d*)', review_text)
                            if match:
                                num = float(match.group(1))
                                reviews_count = str(int(num * 1000))
                                product_info['reviews_count'] = reviews_count
                                self.update_gui('status', f'Reviews extracted (K format): {reviews_count}')
                                reviews_found = True
                                break

                        # Handle M format (millions)
                        elif 'M' in review_text.upper():
                            match = re.search(r'(\d+\.?\d*)', review_text)
                            if match:
                                num = float(match.group(1))
                                reviews_count = str(int(num * 1000000))
                                product_info['reviews_count'] = reviews_count
                                self.update_gui('status', f'Reviews extracted (M format): {reviews_count}')
                                reviews_found = True
                                break

                        # Handle regular number format
                        else:
                            match = re.search(r'(\d+)', review_text)
                            if match:
                                reviews_count = match.group(1)
                                if int(reviews_count) > 0:  # Valid review count
                                    product_info['reviews_count'] = reviews_count
                                    self.update_gui('status', f'Reviews extracted: {reviews_count}')
                                    reviews_found = True
                                    break
                except:
                    continue

            if not reviews_found:
                product_info['extraction_errors'].append("Review count not found with any method")
                self.update_gui('status', 'Review count not found with any method')

        except Exception as e:
            product_info['extraction_errors'].append(f"Review count extraction failed: {str(e)[:50]}")
            self.update_gui('status', f'Review count extraction error: {e}')

    def _validate_product_info(self, product_info):
        """Validate and finalize product info"""
        # Ensure all required fields have values
        required_fields = ['asin', 'title', 'price', 'rating', 'reviews_count']
        for field in required_fields:
            if field not in product_info or not product_info[field] or product_info[field] == "":
                product_info[field] = "N/A"
                self.update_gui('status', f'WARNING: {field} missing, set to N/A')

        # Log extraction summary
        self.update_gui('status', f'EXTRACTION SUMMARY: ASIN: {product_info["asin"]}, Title: {product_info["title"][:50]}..., Price: {product_info["price"]}, Rating: {product_info["rating"]}, Reviews: {product_info["reviews_count"]}')

        if product_info['extraction_errors']:
            self.update_gui('status', f'Extraction issues: {len(product_info["extraction_errors"])}')

    def get_product_info_from_url(self, url):
        """Extract product information from Amazon product URL - REFACTORED VERSION"""
        self.update_gui('status', f'Extracting product info from URL: {url}')

        # Initialize product info
        product_info = self._initialize_product_info()

        try:
            # Navigate to page
            self._handle_page_navigation(url)

            # Check for blocking pages
            if self._check_for_blocking_pages(product_info):
                return [product_info]

            # Extract product information
            self._extract_product_asin(url, product_info)
            self._extract_product_title(product_info)
            self._extract_product_price(product_info)
            self._extract_product_rating(product_info)
            self._extract_product_reviews_count(product_info)

            # Validate and finalize
            self._validate_product_info(product_info)

            return [product_info]

        except Exception as e:
            error_msg = f"Critical error extracting product info: {str(e)}"
            self.update_gui('error', error_msg)
            product_info['extraction_errors'].append(f"Critical error: {error_msg[:50]}")
            return [product_info]

    def search_amazon_products(self, keyword, max_results=10):
        """
        Search Amazon for products and return list of results - FIXED VERSION
        """
        self.update_gui('status', f'Searching Amazon for: "{keyword}"')

        # Check if input is an ASIN (10-character alphanumeric)
        if len(keyword) == 10 and keyword.isalnum() and keyword.upper() == keyword:
            self.update_gui('status', f'Detected ASIN: {keyword}')
            url = f'https://www.{self.domain}/dp/{keyword}'
            return self.get_product_info_from_url(url)

        # Check if input is a URL
        elif keyword.startswith(('http://', 'https://', f'www.{self.domain}')):
            return self.get_product_info_from_url(keyword)

        # Otherwise treat as keyword search
        else:
            self.update_gui('status', 'Navigating to Amazon home page...')
            self.driver.get(f'https://www.{self.domain}')
            time.sleep(ScrapingConfig.get_page_load_delay())

            # Handle "Continue shopping" button if present on home page
            try:
                continue_button = self.driver.find_element(By.CSS_SELECTOR, AmazonSelectors.CONTINUE_SHOPPING_BUTTON)
                continue_button.click()
                time.sleep(ScrapingConfig.get_interaction_delay())
                self.update_gui('status', 'Clicked "Continue shopping" button on home page')
            except NoSuchElementException:
                pass  # Button not present, continue normally

            # Find and use the search box
            try:
                search_box = self.driver.find_element(By.CSS_SELECTOR, AmazonSelectors.SEARCH_BOX_SELECTORS[0])
                search_box.clear()
                search_box.send_keys(keyword)
                time.sleep(ScrapingConfig.get_interaction_delay())

                # Press Enter to search instead of clicking button
                search_box.send_keys(Keys.RETURN)
                self.update_gui('status', f'Performed search for: "{keyword}"')

            except (NoSuchElementException, TimeoutException) as e:
                self.update_gui('error', f'Error using search box: {e}')
                # Fallback to direct URL
                search_term = keyword.replace(' ', '+')
                url = f'https://www.{self.domain}/s?k={search_term}'
                self.driver.get(url)
                self.update_gui('status', f'Fallback to direct URL: {url}')
            except Exception as e:
                self.update_gui('error', f'Unexpected error during search: {e}')
                raise

            # Wait for search results
            time.sleep(ScrapingConfig.get_page_load_delay())

            products = []

            try:
                # Wait for search results
                wait = WebDriverWait(self.driver, 15)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-component-type="s-search-result"]')))

                result_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-component-type="s-search-result"]')
                self.update_gui('status', f'Found {len(result_elements)} search results')

                # Extract product information
                for idx, element in enumerate(result_elements[:max_results], 1):
                    try:
                        product_info = {}

                        # Extract ASIN
                        asin = element.get_attribute('data-asin')
                        if not asin or len(asin) != 10:
                            continue

                        product_info['index'] = idx
                        product_info['asin'] = asin

                        # ====== 修复1: 提取标题 ======
                        try:
                            # 方法1: 直接获取h2里的span
                            title_elem = element.find_element(By.CSS_SELECTOR, 'h2 span')
                            if title_elem and title_elem.text.strip():
                                title = title_elem.text.strip()
                                product_info['title'] = title[:120]  # 适当截断
                            else:
                                # 方法2: 获取h2的aria-label
                                h2_elem = element.find_element(By.CSS_SELECTOR, 'h2')
                                aria_label = h2_elem.get_attribute('aria-label')
                                if aria_label:
                                    product_info['title'] = aria_label[:120]
                                else:
                                    # 方法3: 获取h2文本
                                    product_info['title'] = h2_elem.text.strip()[:120]
                        except:
                            product_info['title'] = "Title not found"

                        # ====== 修复2: 提取价格 ======
                        try:
                            price_found = False
                            for selector in AmazonSelectors.SEARCH_PRICE_SELECTORS:
                                try:
                                    price_elem = element.find_element(By.CSS_SELECTOR, selector)
                                    if price_elem:
                                        price_text = price_elem.get_attribute('textContent') or price_elem.text
                                        # 清理文本
                                        price_text = html.unescape(price_text).strip()
                                        product_info['price'] = price_text
                                        price_found = True
                                        break
                                except:
                                    continue

                            if not price_found:
                                product_info['price'] = "Price not available"

                        except:
                            product_info['price'] = "Price not available"

                        # ====== 提取评分 ======
                        try:
                            # 新的选择器策略，基于实际HTML结构
                            rating_found = False
                            for selector in AmazonSelectors.SEARCH_RATING_SELECTORS:
                                try:
                                    rating_elem = element.find_element(By.CSS_SELECTOR, selector)
                                    rating_text = rating_elem.get_attribute('aria-label') or rating_elem.text or rating_elem.get_attribute('innerHTML')

                                    if rating_text and ('out of' in rating_text or rating_text.replace('.', '').isdigit()):
                                        # 提取数字部分，如 "4.5 out of 5 stars" 或直接的 "4.4"
                                        match = re.search(r'(\d+\.?\d*)', rating_text)
                                        if match:
                                            rating_value = match.group(1)
                                            # 验证评分在合理范围内 (1-5)
                                            if 1 <= float(rating_value) <= 5:
                                                product_info['rating'] = rating_value
                                                rating_found = True
                                                break
                                except:
                                    continue

                            if not rating_found:
                                product_info['rating'] = "No rating"

                        except:
                            product_info['rating'] = "No rating"

                        # ====== 提取评价数量 ======
                        try:
                            # 新的选择器策略，基于实际HTML结构
                            reviews_found = False
                            for selector in AmazonSelectors.SEARCH_REVIEW_COUNT_SELECTORS:
                                try:
                                    reviews_elem = element.find_element(By.CSS_SELECTOR, selector)

                                    # 优先使用aria-label（包含完整数字）
                                    aria_label = reviews_elem.get_attribute('aria-label')
                                    if aria_label and 'ratings' in aria_label:
                                        # 提取数字部分，如 "3,943 ratings"
                                        match = re.search(r'([\d,]+)', aria_label)
                                        if match:
                                            reviews_count = match.group(1).replace(',', '')
                                            if reviews_count.isdigit():
                                                product_info['reviews_count'] = reviews_count
                                                reviews_found = True
                                                break

                                    # 如果aria-label不可用，使用文本内容
                                    reviews_text = reviews_elem.text.strip()
                                    if reviews_text:
                                        # 处理括号内的文本，如 "(3.9K)"
                                        if reviews_text.startswith('(') and reviews_text.endswith(')'):
                                            reviews_text = reviews_text[1:-1]

                                        # 处理K/M格式，如 "3.9K" -> "3900"
                                        if 'K' in reviews_text:
                                            try:
                                                num = float(re.search(r'(\d+\.?\d*)', reviews_text).group(1))
                                                reviews_count = str(int(num * 1000))
                                                product_info['reviews_count'] = reviews_count
                                                reviews_found = True
                                                break
                                            except:
                                                pass
                                        elif 'M' in reviews_text:
                                            try:
                                                num = float(re.search(r'(\d+\.?\d*)', reviews_text).group(1))
                                                reviews_count = str(int(num * 1000000))
                                                product_info['reviews_count'] = reviews_count
                                                reviews_found = True
                                                break
                                            except:
                                                pass
                                        elif reviews_text.isdigit():
                                            product_info['reviews_count'] = reviews_text
                                            reviews_found = True
                                            break

                                except:
                                    continue

                            if not reviews_found:
                                product_info['reviews_count'] = "0"

                        except:
                            product_info['reviews_count'] = "0"

                        products.append(product_info)

                        # 显示提取的信息用于调试
                        self.update_gui('status', f'Product {idx}: {product_info.get("title", "No title")[:50]}...')

                    except Exception as e:
                        self.update_gui('status', f'Error extracting product {idx}: {str(e)[:50]}')
                        continue

            except TimeoutException:
                self.update_gui('error', 'Search results not found within timeout')
            except Exception as e:
                self.update_gui('error', f'General error in search: {e}')

            return products

    def validate_review_element(self, element):
        """验证元素是否真的是评论容器"""
        try:
            # 检查是否包含必要的评论元素
            has_review_body = element.find_elements(By.CSS_SELECTOR, 'span[data-hook="review-body"]')
            has_rating = element.find_elements(By.CSS_SELECTOR, 'i[class*="star"], span.a-icon-alt')

            if has_review_body and has_rating:
                # 进一步检查评论文本是否有效
                review_text = has_review_body[0].text.strip()
                if review_text and len(review_text) > 10:
                    return True

            return False
        except:
            return False

    def find_review_elements(self, driver):
        """Find review elements on the page - PRECISE VERSION"""
        review_elements = []

        # 精确选择器：只选择包含评论内容的元素
        # 基于你提供的HTML结构
        precise_selectors = [
            'div[data-hook="review"]',
            'div[data-hook="cr-review"]',
            'section[data-hook="review"]',
            # 这个选择器最精确：包含评论文本span的父容器
            'div:has(> div > span[data-hook="review-body"])',
            'div:has(span[data-hook="review-body"])'
        ]

        for selector in precise_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    self.update_gui('status', f'Found {len(elements)} elements with: {selector}')

                    # 验证这些确实是评论（包含评论文本）
                    valid_elements = []
                    for elem in elements:
                        if self.validate_review_element(elem):
                            valid_elements.append(elem)

                    self.update_gui('status', f'Validated {len(valid_elements)} actual reviews')
                    review_elements = valid_elements
                    break
            except:
                continue

        # 如果还是没找到，使用XPath
        if not review_elements:
            self.update_gui('status', 'Trying XPath selection...')
            xpaths = [
                "//div[.//span[@data-hook='review-body'] and .//i[contains(@class, 'star')]]",
                "//*[@data-hook='review' or @data-hook='cr-review']",
                "//div[contains(@class, 'review') and .//span[@data-hook='review-body']]"
            ]

            for xpath in xpaths:
                try:
                    elements = driver.find_elements(By.XPATH, xpath)
                    if elements:
                        self.update_gui('status', f'Found {len(elements)} elements with XPath')
                        # 对XPath结果也进行验证
                        valid_elements = [elem for elem in elements if self.validate_review_element(elem)]
                        self.update_gui('status', f'Validated {len(valid_elements)} actual reviews from XPath')
                        review_elements = valid_elements
                        break
                except:
                    continue

        return review_elements

    def extract_review_data(self, element):
        """Extract data from a single review element"""
        review_data = {}

        # Extract rating
        try:
            rating_selectors = [
                'i[data-hook="cmps-review-star-rating"] span.a-icon-alt',
                'i[data-hook="review-star-rating"] span.a-icon-alt',
                'span.a-icon-alt',
                'i.a-icon-star span.a-icon-alt'
            ]

            rating = None
            for selector in rating_selectors:
                try:
                    rating_elem = element.find_element(By.CSS_SELECTOR, selector)
                    rating_text = rating_elem.text.strip()
                    if rating_text:
                        match = re.search(r'(\d+\.?\d*)', rating_text)
                        if match:
                            rating = float(match.group(1))
                            break
                except:
                    continue

            review_data['rating'] = rating
        except:
            review_data['rating'] = None

        # Extract title
        try:
            title_selectors = [
                'a[data-hook="review-title"]',
                'span[data-hook="review-title"]',
                'a.review-title'
            ]

            title = ''
            for selector in title_selectors:
                try:
                    title_elem = element.find_element(By.CSS_SELECTOR, selector)
                    title = title_elem.text.strip()
                    if title:
                        title = re.sub(r'^\d+\.?\d*\s+out of \d+ stars\s*', '', title)
                        break
                except:
                    continue

            review_data['title'] = title
        except:
            review_data['title'] = ''

        # ====== 修复：改进评论内容提取 ======
        # 提取评论内容
        text = ''
        try:
            # 尝试多个选择器获取评论内容
            body_selectors = [
                'span[data-hook="review-body"]',
                'div[data-hook="review-body"]',
                'div.a-expander-content.reviewText',
                'div.review-text-content'
            ]

            for selector in body_selectors:
                try:
                    body_elem = element.find_element(By.CSS_SELECTOR, selector)
                    # 获取完整文本（包括隐藏部分）
                    text = body_elem.text.strip()
                    if text:
                        # 清理文本：合并多余空格和换行
                        text = re.sub(r'\s+', ' ', text)
                        break
                except:
                    continue

            # 如果还是没找到，尝试获取所有文本
            if not text:
                text = element.text.strip()
                # 尝试移除评分、标题等其他部分
                lines = text.split('\n')
                # 找到最长的段落作为评论内容
                if lines:
                    text = max(lines, key=len).strip()

        except Exception as e:
            self.update_gui('status', f'Text extraction error: {e}')

        review_data['text'] = text
        # ====== 修复结束 ======

        # Extract reviewer
        try:
            reviewer_elem = element.find_element(By.CSS_SELECTOR, 'span.a-profile-name')
            review_data['reviewer'] = reviewer_elem.text.strip()
        except:
            review_data['reviewer'] = 'Amazon Customer'

        # Extract date
        try:
            date_elem = element.find_element(By.CSS_SELECTOR, 'span[data-hook="review-date"]')
            review_data['date'] = date_elem.text.strip()
        except:
            review_data['date'] = ''

        return review_data

    def get_current_page_number(self, driver):
        """获取当前页码"""
        try:
            current_url = driver.current_url
            if 'pageNumber=' in current_url:
                import re
                match = re.search(r'pageNumber=(\d+)', current_url)
                if match:
                    return int(match.group(1))

            # 查找页码指示器
            try:
                page_elem = driver.find_element(By.CSS_SELECTOR, 'li.a-selected span')
                page_text = page_elem.text.strip()
                if page_text.isdigit():
                    return int(page_text)
            except:
                pass

        except:
            pass

        return 1  # 默认为第1页

    def click_next_page_button(self, driver):
        """点击'下一页'按钮"""
        try:
            # 查找下一页按钮的各种可能选择器
            next_button_selectors = [
                'li.a-last a',
                'a[data-hook="next-page"]',
                '.a-pagination .a-last a',
                'li.a-last > a',
                'a[aria-label="Next page"]',
                'a:contains("Next")'
            ]

            for selector in next_button_selectors:
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button and next_button.is_displayed() and next_button.is_enabled():
                        self.update_gui('status', f'Found next button with selector: {selector}')

                        # 滚动到按钮
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_button)
                        time.sleep(1)

                        # 获取当前页面信息以便验证
                        current_url_before = driver.current_url

                        # 点击按钮
                        next_button.click()
                        self.update_gui('status', 'Clicked next button')

                        # 等待页面加载
                        time.sleep(ScrapingConfig.get_page_transition_delay())

                        # 验证页面是否变化
                        current_url_after = driver.current_url
                        if current_url_before != current_url_after:
                            self.update_gui('status', f'URL changed: {current_url_after}')
                            return True
                        else:
                            self.update_gui('status', 'WARNING: URL did not change after clicking next')
                            return False

                except Exception as e:
                    continue

            self.update_gui('status', 'No next button found')
            return False

        except Exception as e:
            self.update_gui('status', f'Error clicking next button: {e}')
            return False

    def extract_reviews_from_current_page(self, driver, page_num, collected_review_ids):
        """从当前页面提取评论"""
        reviews = []

        try:
            # 查找评论元素
            review_elements = self.find_review_elements(driver)

            if not review_elements:
                self.update_gui('status', f'No reviews found on page {page_num}')
                return reviews

            self.update_gui('status', f'Found {len(review_elements)} review elements to process')

            for idx, element in enumerate(review_elements, 1):
                try:
                    # 提取评论数据
                    review_data = self.extract_review_data(element)

                    # 获取评论文本
                    review_text = review_data.get('text', '').strip()

                    if not review_text or len(review_text) < 20:
                        continue

                    # 生成评论ID
                    review_id = None
                    try:
                        review_id_elem = element.find_element(By.CSS_SELECTOR, '[data-review-id], [id*="review"]')
                        review_id = review_id_elem.get_attribute('data-review-id') or review_id_elem.get_attribute('id')
                    except:
                        import hashlib
                        title_part = review_data.get('title', '')[:20]
                        rating_part = str(review_data.get('rating', ''))
                        text_part = review_text[:100]
                        combined = f"{title_part}|{rating_part}|{text_part}"
                        review_id = hashlib.md5(combined.encode()).hexdigest()[:16]

                    # 检查重复
                    if review_id and review_id in collected_review_ids:
                        continue

                    if review_id:
                        collected_review_ids.add(review_id)

                    review_data['page'] = page_num
                    reviews.append(review_data)

                except Exception as e:
                    continue

        except Exception as e:
            self.update_gui('error', f'Error extracting reviews from page {page_num}: {e}')

        return reviews

    def _simulate_human_typing(self, element, text, min_delay=None, max_delay=None):
        """Simulate human-like typing with random delays"""
        if min_delay is None:
            min_delay = ScrapingConfig.TYPING_DELAY_MIN
        if max_delay is None:
            max_delay = ScrapingConfig.TYPING_DELAY_MAX
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(min_delay, max_delay))

    def apply_review_keyword_filter(self, driver, keyword):
        """Apply keyword filter to reviews on the current page"""
        if not keyword:
            return True  # No filter to apply

        try:
            self.update_gui('status', f'Applying review keyword filter: "{keyword}"')

            # Wait for the page to load completely
            time.sleep(ScrapingConfig.get_page_load_delay())

            # Find the review search input
            search_selectors = [
                'input[id="filterByKeywordTextBox"]',
                'input[placeholder*="Search customer reviews"]',
                'input[placeholder*="search customer reviews"]',
                'input[type="search"][maxlength="300"]'
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    search_input = driver.find_element(By.CSS_SELECTOR, selector)
                    if search_input and search_input.is_displayed():
                        self.update_gui('status', f'Found search input with selector: {selector}')
                        break
                except:
                    continue

            if not search_input:
                self.update_gui('status', 'Review search input not found - proceeding without filter')
                return False

            # Clear and enter the keyword
            search_input.clear()
            self._simulate_human_typing(search_input, keyword)
            time.sleep(ScrapingConfig.get_interaction_delay())

            # Find and click the submit button
            submit_selectors = [
                'input.a-button-input[aria-labelledby="a-autoid-1-announce"]',
                'input[type="submit"][class*="a-button-input"]',
                'input[type="submit"]'
            ]

            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                    if submit_button and submit_button.is_displayed() and submit_button.is_enabled():
                        self.update_gui('status', f'Found submit button with selector: {selector}')
                        break
                except:
                    continue

            if submit_button:
                submit_button.click()
                self.update_gui('status', 'Clicked submit button for keyword filter')
            else:
                # Fallback to Enter key
                search_input.send_keys(Keys.RETURN)
                self.update_gui('status', 'Submitted keyword filter with Enter key (fallback)')

            # Wait for filtered results to load
            time.sleep(ScrapingConfig.get_page_transition_delay())

            # Verify the filter was applied by checking if keyword appears in URL or page content
            current_url = driver.current_url
            if 'filterByKeyword' in current_url or keyword.lower() in driver.page_source.lower():
                self.update_gui('status', 'Review keyword filter applied successfully')
                return True
            else:
                self.update_gui('status', 'WARNING: Keyword filter may not have been applied')
                return False

        except Exception as e:
            self.update_gui('status', f'Error applying keyword filter: {e}')
            return False

    def _initialize_scraping_session(self, product_asin):
        """Initialize scraping session variables"""
        self.update_gui('status', f'Starting to scrape reviews for product: {product_asin}')
        return [], set()

    def _handle_login_for_reviews(self, url):
        """Handle login for reviews page"""
        # 处理登录 - 使用自动登录如果可用，否则使用手动
        if self.auto_login:
            login_success = self.auto_login.handle_login_automatically(self.driver, url)
            if not login_success:
                self.update_gui('error', 'Auto login failed, cannot proceed with scraping.')
                return False
        else:
            # Fallback to manual login
            time.sleep(ScrapingConfig.get_page_load_delay())
            current_url = self.driver.current_url.lower()
            if '/ap/signin' in current_url or 'sign in' in self.driver.title.lower():
                self.update_gui('status', 'Login required - please login manually in browser')
                # For GUI, we might need to pause or handle differently
                return False
        return True

    def _apply_review_filters(self, review_keyword):
        """Apply review keyword filter if provided"""
        if review_keyword:
            filter_applied = self.apply_review_keyword_filter(self.driver, review_keyword)
            if not filter_applied:
                self.update_gui('status', 'Continuing without keyword filter')

    def _scrape_reviews_from_pages(self, max_pages, collected_review_ids, all_reviews):
        """Scrape reviews from multiple pages using pagination"""
        # 第2页及以后：使用分页按钮
        for page in range(2, max_pages + 1):
            self.update_gui('progress', f'Scraping page {page}/{max_pages}')
            self.update_gui('status', f'Attempting to navigate to page {page}...')

            # 方法1：尝试点击"下一页"按钮
            navigation_success = self.click_next_page_button(self.driver)

            if not navigation_success:
                self.update_gui('status', 'No next button found - stopping pagination')
                break

            self.update_gui('status', f'Processing page {page}...')

            # 验证当前页面
            current_page = self.get_current_page_number(self.driver)
            if current_page != page:
                self.update_gui('status', f'WARNING: Expected page {page}, but actually on page {current_page}')
                if current_page == 1:
                    self.update_gui('status', 'Pagination failed, stopping')
                    break

            # 提取评论
            page_reviews = self.extract_reviews_from_current_page(self.driver, page, collected_review_ids)
            all_reviews.extend(page_reviews)
            self.update_gui('status', f'Added {len(page_reviews)} reviews from page {page}')

            if len(page_reviews) == 0:
                self.update_gui('status', f'No new reviews on page {page}')
                # 可以继续尝试下一页或break

            # 延迟
            if page < max_pages:
                delay = ScrapingConfig.get_page_transition_delay()
                self.update_gui('status', f'Waiting {delay:.1f} seconds before next page...')
                time.sleep(delay)

    def scrape_reviews_for_product(self, product_asin, max_pages=5, review_keyword=""):
        """Scrape reviews for a specific product ASIN - REFACTORED VERSION"""
        # Initialize scraping session
        all_reviews, collected_review_ids = self._initialize_scraping_session(product_asin)

        try:
            # 第1页：直接访问
            self.update_gui('status', 'Processing page 1...')
            url = f'https://www.{self.domain}/product-reviews/{product_asin}/'

            # Handle login
            if not self._handle_login_for_reviews(url):
                return all_reviews

            # Apply review keyword filter
            self._apply_review_filters(review_keyword)

            # 提取第1页评论
            page1_reviews = self.extract_reviews_from_current_page(self.driver, 1, collected_review_ids)
            all_reviews.extend(page1_reviews)
            self.update_gui('status', f'Added {len(page1_reviews)} reviews from page 1')

            # Scrape additional pages
            self._scrape_reviews_from_pages(max_pages, collected_review_ids, all_reviews)

            self.update_gui('status', f'Finished scraping. Total unique reviews collected: {len(all_reviews)}')
            return all_reviews

        except Exception as e:
            self.update_gui('error', f'Error during scraping: {e}')
            return all_reviews

    def save_reviews_to_csv(self, reviews, product_asin, keyword=""):
        """Save reviews to CSV file"""
        if not reviews:
            self.update_gui('error', 'No reviews to save.')
            return None

        df = pd.DataFrame(reviews)

        # Ensure column order
        column_order = ['asin', 'rating', 'title', 'text', 'reviewer', 'date', 'page']
        existing_columns = [col for col in column_order if col in df.columns]
        df = df[existing_columns]

        # Create filename
        if keyword:
            safe_keyword = re.sub(r'[^\w\s]', '', keyword).replace(' ', '_')[:20]
            filename = f'amazon_reviews_{safe_keyword}_{product_asin}.csv'
        else:
            filename = f'amazon_reviews_{product_asin}.csv'

        # Save to Desktop
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        full_path = os.path.join(desktop_path, filename)
        df.to_csv(full_path, index=False, encoding='utf-8-sig')

        self.update_gui('status', f'CSV file saved at Desktop: {filename}')
        self.update_gui('file_saved', filename)
        self.update_gui('status', f'Total reviews: {len(df)}')

        # Show statistics
        if 'rating' in df.columns and df['rating'].notna().any():
            avg_rating = df['rating'].dropna().mean()
            self.update_gui('status', f'Average rating: {avg_rating:.2f}')

            self.update_gui('status', 'Rating distribution:')
            rating_dist = df['rating'].value_counts().sort_index()
            for rating, count in rating_dist.items():
                self.update_gui('status', f'  {rating} stars: {count} reviews')

        return filename

    def close_driver(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.update_gui('status', 'Browser closed')