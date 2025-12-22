# Amazon Review Scraper - GUI Version

A user-friendly graphical interface for the Amazon Review Scraper, built with Tkinter. This GUI version provides an intuitive way to search for products and scrape reviews without using the command line.

## 🚀 Features

### GUI Features
- **User-Friendly Interface** - Clean, modern Tkinter-based GUI
- **Multiple Search Types** - Search by keyword, ASIN, or product URL
- **Interactive Results Display** - View search results in a table format
- **Progress Tracking** - Real-time progress updates and status messages
- **Non-Blocking Operations** - Scraping runs in background threads
- **Automatic CSV Export** - Reviews saved automatically with timestamps
- **Output Folder Access** - One-click button to open the folder containing CSV files
- **Headless Mode Option** - Run browser in background without visible window

### Core Features (Full Implementation)
- 🛍️ **Product Search & Review Scraping** - Search products and scrape reviews in one workflow
- 📊 **Comprehensive Data Extraction** - Ratings, titles, content, dates, reviewer info with robust error handling
- 💾 **CSV Output** - Automatic CSV export with timestamped filenames and statistics
- 🔄 **Smart Pagination** - Advanced button clicking with URL validation and fallback strategies
- 🛡️ **Anti-Detection** - Full stealth browser implementation with randomized delays and User-Agent rotation
- 🔐 **Automatic Login** - Complete programmatic login system with 2FA support and manual fallback
- 🧪 **Advanced Review Extraction** - Precise element detection with multiple selector strategies and XPath fallbacks
- 🔍 **Duplicate Prevention** - Content-based deduplication using review IDs and hashing
- ⚡ **Robust Error Handling** - Comprehensive error recovery and validation mechanisms

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- Chrome browser (for Selenium scraper)
- Tkinter (usually included with Python, but install if missing)

### Step-by-Step Installation

1. **Navigate to the GUI directory**
   ```bash
   cd amazon-scraper-gui
   ```

2. **Install required packages**
   ```bash
   pip install -r requirements-gui.txt
   ```

3. **Set up Amazon credentials (Optional but recommended)**
   - Copy the `.env` file from the parent directory or create one
   - Edit with your Amazon credentials:
   ```bash
   AMAZON_EMAIL=your_email@example.com
   AMAZON_PASSWORD=your_password_here
   ```

4. **Verify Chrome browser is installed**
   - Ensure you have Google Chrome installed
   - The scraper will automatically download the correct ChromeDriver

## 🚀 Usage

### Quick Start

#### Windows
Double-click `amazon-review-scraper.bat` or run it from command prompt:
```cmd
amazon-review-scraper.bat
```

#### Mac/Linux
Make the script executable and run:
```bash
chmod +x run_gui.sh
./run_gui.sh
```

### Manual Launch
```bash
python gui_app.py
```

### GUI Workflow

1. **Launch the Application**
    - Run the appropriate launcher script for your OS
    - The GUI window will open

2. **Configure Settings**
    - **Headless Mode**: Check the box to run the browser in background (no visible window)
    - This is useful for server environments or when you don't want to see the browser

3. **Enter Search Criteria**
    - **Search Type**: Choose from:
      - `keyword` - Search by product name (e.g., "wireless headphones")
      - `asin` - Direct ASIN input (e.g., "B07XJ8C8F5")
      - `url` - Full Amazon product URL
    - **Search Term**: Enter your search query

3. **Perform Search**
   - Click "Search" button
   - Wait for search results to appear in the table
   - The application will open a Chrome browser window

4. **Select Product**
   - Review the search results in the table
   - Click on a product row to select it
   - Selected product info will be displayed in status

5. **Scrape Reviews**
   - Set the number of pages to scrape (1-20)
   - Click "Scrape Reviews" button
   - Monitor progress in the status area
   - Reviews will be automatically saved to CSV

6. **View Results**
   - CSV files are saved in the current directory
   - File names include timestamp and search term
   - Check the status area for file location and statistics
   - Click "Open Output Folder" to directly access the CSV files in your file explorer

## 🔐 Credentials Setup

The GUI version uses the same credential system as the CLI version:

### Automatic Setup
- Credentials are loaded from `.env` file in the parent directory
- If no credentials found, you'll be prompted to set them up

### Manual Setup
Create a `.env` file in the `amazon-scraper-gui` directory:
```bash
# Amazon Credentials
AMAZON_EMAIL=your_email@example.com
AMAZON_PASSWORD=your_password_here
```

## 📊 Output Format

### CSV Columns
| Column | Description | Example |
|--------|-------------|---------|
| asin | Product ASIN code | B07XJ8C8F5 |
| rating | Star rating (1-5) | 4.5 |
| title | Review title | "Great product!" |
| text | Full review content | "This product exceeded my expectations..." |
| reviewer | Customer name | "John D." |
| date | Review date | "December 15, 2023" |
| page | Page number where found | 1 |

### File Naming
Files are automatically named with timestamps:
- From keyword search: `amazon_reviews_keyword_ASIN.csv`
- From ASIN: `amazon_reviews_ASIN.csv`

## 🛠️ Troubleshooting

### Common Issues

**"Python is not installed"**
- Install Python 3.8+ from python.org
- Ensure Python is added to your system PATH

**"Chrome driver issues"**
- Update Chrome browser to latest version
- Ensure Chrome is installed
- The scraper automatically manages ChromeDriver

**"Login required"**
- Set up credentials in `.env` file
- Or manually login when prompted in the browser window

**"No reviews found"**
- Verify the product actually has reviews
- Try a different product
- Amazon may have updated their page structure

**GUI not responding**
- Scraping operations run in background threads
- Wait for operations to complete
- Use the "Stop" button if needed

### Debug Information
- Check the status text area for detailed progress
- Error messages will be displayed in popups
- Browser window shows scraping activity

## 🔧 Configuration

### Optional Settings
Add to your `.env` file:
```bash
# Optional Settings
HEADLESS=false  # Set to true for headless browsing
TIMEOUT=30
MAX_RETRIES=3
```

### GUI Customization
The GUI is built with Tkinter and can be customized by modifying `gui_app.py`:
- Window size and layout
- Colors and fonts
- Additional input fields
- Progress indicators

## 📋 Dependencies

### Core Dependencies
- `selenium` - Browser automation and anti-detection
- `webdriver-manager` - Automatic ChromeDriver management
- `pandas` - Data processing and CSV output
- `python-dotenv` - Secure credential management
- `tkinter` - GUI framework (built-in with Python)

### Installation
```bash
pip install -r requirements-gui.txt
```

## ⚖️ Legal & Ethical Use

### Important Guidelines
- **Respect Amazon's Terms of Service**
- **Use for research and analysis only**
- **Don't overload Amazon's servers** - Built-in delays prevent this
- **Consider the impact on small sellers**
- **Data should not be used for commercial resale**

### Built-in Protection
- Randomized delays between requests
- Rate limiting through page-by-page scraping
- Anti-detection features to avoid being blocked
- No parallel scraping to reduce server load

## 🆘 Support

### Getting Help
1. **Check this README** for common issues
2. **Review the status messages** in the GUI for clues
3. **Ensure all prerequisites are installed**
4. **Try the CLI version** if GUI issues persist

### System Requirements
- **OS**: Windows 10+, macOS 10.15+, Linux
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB free space
- **Network**: Stable internet connection

---

**Note**: This tool is for educational and research purposes. Always respect website terms of service and use responsibly.