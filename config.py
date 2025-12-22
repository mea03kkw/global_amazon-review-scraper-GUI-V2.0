# config.py
import os
from dotenv import load_dotenv
from getpass import getpass

# 加载环境变量
load_dotenv()

class AmazonConfig:
    @staticmethod
    def get_credentials():
        """从环境变量获取Amazon凭据"""
        email = os.getenv('AMAZON_EMAIL')
        password = os.getenv('AMAZON_PASSWORD')

        return email, password

    @staticmethod
    def setup_credentials():
        """交互式设置环境变量"""
        print("\n" + "="*60)
        print("Amazon Credentials Setup")
        print("="*60)
        print("Your credentials will NOT be saved to any file.")
        print("They will only be used for this session.")
        print("="*60)

        email = input("Enter your Amazon email: ").strip()
        password = getpass("Enter your Amazon password: ").strip()

        if not email or not password:
            print("Both email and password are required!")
            return None, None

        # 设置环境变量（仅当前会话）
        os.environ['AMAZON_EMAIL'] = email
        os.environ['AMAZON_PASSWORD'] = password

        print("\n✓ Credentials set for this session.")
        print("  (To make permanent, add to .env file)")
        print("="*60)

        return email, password

    @staticmethod
    def check_and_setup():
        """检查并设置凭据"""
        email, password = AmazonConfig.get_credentials()

        if not email or not password:
            print("Amazon credentials not found in environment.")
            choice = input("Set up credentials now? (y/n): ").lower().strip()
            if choice == 'y':
                return AmazonConfig.setup_credentials()
            else:
                return None, None

        return email, password

    @staticmethod
    def create_env_template():
        """创建.env模板文件"""
        template = """# Amazon Credentials
# Copy this file to .env and fill in your credentials
AMAZON_EMAIL=your_email@example.com
AMAZON_PASSWORD=your_password_here

# Optional Settings
# HEADLESS=false  # Set to true for headless browsing
# TIMEOUT=30
# MAX_RETRIES=3
"""

        if not os.path.exists('.env.template'):
            with open('.env.template', 'w') as f:
                f.write(template)
            print("Created .env.template file. Copy to .env and edit.")
            return True
        return False