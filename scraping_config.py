# scraping_config.py
"""
Configuration settings for Amazon scraping delays and behavior
Allows customization of timing to balance speed vs anti-detection
"""

import random

class ScrapingConfig:
    """Configuration class for scraping delays and settings"""

    # Page load delays (seconds)
    PAGE_LOAD_DELAY_MIN = 3
    PAGE_LOAD_DELAY_MAX = 6

    # Interaction delays (seconds)
    INTERACTION_DELAY_MIN = 1
    INTERACTION_DELAY_MAX = 2

    # Page transition delays (seconds)
    PAGE_TRANSITION_DELAY_MIN = 3
    PAGE_TRANSITION_DELAY_MAX = 7

    # Login delays (seconds)
    LOGIN_DELAY_MIN = 2
    LOGIN_DELAY_MAX = 4
    LOGIN_COMPLETE_DELAY_MIN = 3
    LOGIN_COMPLETE_DELAY_MAX = 6

    # 2FA delays (seconds)
    TWO_FA_DELAY_MIN = 8
    TWO_FA_DELAY_MAX = 15

    # Retry delays (seconds)
    RETRY_DELAY_MIN = 5
    RETRY_DELAY_MAX = 10

    # Human typing simulation delays (seconds per character)
    TYPING_DELAY_MIN = 0.05
    TYPING_DELAY_MAX = 0.15

    @classmethod
    def get_page_load_delay(cls):
        """Get random page load delay"""
        return random.uniform(cls.PAGE_LOAD_DELAY_MIN, cls.PAGE_LOAD_DELAY_MAX)

    @classmethod
    def get_interaction_delay(cls):
        """Get random interaction delay"""
        return random.uniform(cls.INTERACTION_DELAY_MIN, cls.INTERACTION_DELAY_MAX)

    @classmethod
    def get_page_transition_delay(cls):
        """Get random page transition delay"""
        return random.uniform(cls.PAGE_TRANSITION_DELAY_MIN, cls.PAGE_TRANSITION_DELAY_MAX)

    @classmethod
    def get_login_delay(cls):
        """Get random login delay"""
        return random.uniform(cls.LOGIN_DELAY_MIN, cls.LOGIN_DELAY_MAX)

    @classmethod
    def get_login_complete_delay(cls):
        """Get random login completion delay"""
        return random.uniform(cls.LOGIN_COMPLETE_DELAY_MIN, cls.LOGIN_COMPLETE_DELAY_MAX)

    @classmethod
    def get_two_fa_delay(cls):
        """Get random 2FA delay"""
        return random.uniform(cls.TWO_FA_DELAY_MIN, cls.TWO_FA_DELAY_MAX)

    @classmethod
    def get_retry_delay(cls):
        """Get random retry delay"""
        return random.uniform(cls.RETRY_DELAY_MIN, cls.RETRY_DELAY_MAX)

    @classmethod
    def get_typing_delay(cls):
        """Get random typing delay per character"""
        return random.uniform(cls.TYPING_DELAY_MIN, cls.TYPING_DELAY_MAX)