# selectors.py
"""
Centralized CSS selectors for Amazon scraping
Consolidates all selector lists to reduce redundancy and improve maintainability
"""

class AmazonSelectors:
    """CSS selectors for Amazon product and review extraction"""

    # Product page selectors
    PRODUCT_TITLE_SELECTORS = [
        '#productTitle',
        'span#productTitle',
        'h1#title',
        'h1.a-size-large',
        '.product-title-word-break',
        'h1[data-automation-id="product-title"]',
        '.a-size-large.product-title-word-break',
        'h1[data-feature-name="productTitle"]'
    ]

    PRODUCT_PRICE_SELECTORS = [
        'span.a-price:not(.a-text-price) span.a-offscreen',
        'span.a-price span.a-offscreen',
        '.a-price .a-offscreen',
        '#price_inside_buybox',
        '#priceblock_ourprice',
        '#priceblock_dealprice',
        '#priceblock_saleprice',
        '.a-price .a-price-whole',
        'span.a-color-price',
        'span[data-price-type="listPrice"] .a-offscreen',
        'span[data-price-type="price"] .a-offscreen'
    ]

    PRODUCT_RATING_SELECTORS = [
        'span[data-hook="rating-out-of-text"]',
        'i.a-icon-star span.a-icon-alt',
        '#acrPopover',
        '.a-icon-alt',
        'a[aria-label*="out of 5 stars"]',
        'span[aria-label*="out of 5 stars"]',
        'span[data-hook="rating-out-of-text"]'
    ]

    PRODUCT_REVIEW_COUNT_SELECTORS = [
        '#acrCustomerReviewText',
        'span[data-hook="total-review-count"]',
        '#customerReviews',
        'a[href*="product-reviews"]',
        'span[data-hook="rating-out-of-text"]',
        'span[aria-label*="ratings"]',
        'a[aria-label*="ratings"]'
    ]

    # Search results selectors
    SEARCH_PRICE_SELECTORS = [
        'span.a-price:not(.a-text-price) span.a-offscreen',
        'span.a-price span.a-offscreen',
        '.a-price .a-offscreen'
    ]

    SEARCH_RATING_SELECTORS = [
        'span.a-size-small.a-color-base',  # direct rating number
        'span.a-icon-alt',  # star icon alt text
        'a[aria-label*="out of 5 stars"]',  # link aria-label
        'i span.a-icon-alt',  # nested in i tag
        '.a-icon-star-mini span.a-icon-alt'  # mini star icon
    ]

    SEARCH_REVIEW_COUNT_SELECTORS = [
        'a[aria-label*="ratings"]',  # aria-label with full number
        'span.a-size-mini.puis-normal-weight-text.s-underline-text',  # formatted text
        'span.a-size-base.s-underline-text',  # backup selector
        'span[aria-label*="ratings"]'  # backup aria-label selector
    ]

    # Review page selectors
    REVIEW_RATING_SELECTORS = [
        'i[data-hook="cmps-review-star-rating"] span.a-icon-alt',
        'i[data-hook="review-star-rating"] span.a-icon-alt',
        'span.a-icon-alt',
        'i.a-icon-star span.a-icon-alt'
    ]

    REVIEW_TITLE_SELECTORS = [
        'a[data-hook="review-title"]',
        'span[data-hook="review-title"]',
        'a.review-title'
    ]

    REVIEW_BODY_SELECTORS = [
        'span[data-hook="review-body"]',
        'div[data-hook="review-body"]',
        'div.a-expander-content.reviewText',
        'div.review-text-content'
    ]

    REVIEW_AUTHOR_SELECTORS = [
        'span.a-profile-name'
    ]

    REVIEW_DATE_SELECTORS = [
        'span[data-hook="review-date"]'
    ]

    # Login page selectors
    EMAIL_SELECTORS = [
        'input[name="email"]',
        'input[name="username"]',
        'input[type="email"]',
        'input[placeholder*="email"]',
        'input[placeholder*="Email"]',
        '#ap_email'
    ]

    PASSWORD_SELECTORS = [
        'input[name="password"]',
        'input[type="password"]',
        '#ap_password'
    ]

    LOGIN_BUTTON_SELECTORS = [
        'input[type="submit"]',
        'button[type="submit"]',
        '#continue',
        '#signInSubmit',
        'span[id="continue"]',
        'span[id="signInSubmit"]',
        'input[aria-labelledby="continue"]',
        'button[aria-labelledby="signInSubmit"]'
    ]

    # Navigation selectors
    CONTINUE_SHOPPING_BUTTON = 'button[alt="Continue shopping"]'
    SEARCH_BOX_SELECTORS = ['input[name="field-keywords"], #twotabsearchtextbox']
    NEXT_PAGE_BUTTON_SELECTORS = [
        'li.a-last a',
        'a[data-hook="next-page"]',
        '.a-pagination .a-last a',
        'li.a-last > a',
        'a[aria-label="Next page"]',
        'a:contains("Next")'
    ]

    # Review filter selectors
    REVIEW_SEARCH_INPUT_SELECTORS = [
        'input[id="filterByKeywordTextBox"]',
        'input[placeholder*="Search customer reviews"]',
        'input[placeholder*="search customer reviews"]',
        'input[type="search"][maxlength="300"]'
    ]

    REVIEW_FILTER_SUBMIT_SELECTORS = [
        'input.a-button-input[aria-labelledby="a-autoid-1-announce"]',
        'input[type="submit"][class*="a-button-input"]',
        'input[type="submit"]'
    ]

    # Page elements
    PAGE_NUMBER_SELECTORS = ['li.a-selected span']
    REVIEW_ELEMENTS = [
        'div[data-hook="review"]',
        'div[data-hook="cr-review"]',
        'section[data-hook="review"]',
        'div:has(> div > span[data-hook="review-body"])',
        'div:has(span[data-hook="review-body"])'
    ]

    # 2FA selectors
    TWO_FA_CODE_SELECTORS = [
        'input[placeholder*="code"]',
        'input[placeholder*="OTP"]',
        'input[name*="code"]',
        'input[name*="otp"]',
        'input[id*="code"]',
        'input[id*="otp"]'
    ]