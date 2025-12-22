# gui_app.py
"""
Amazon Review Scraper GUI Application
Main Tkinter GUI for the Amazon scraper
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import queue
import os
import sys

from amazon_scraper_gui import AmazonScraperGUI
from config import AmazonConfig

class AmazonScraperApp:
    """Main GUI application for Amazon scraper"""

    def __init__(self, root):
        self.root = root
        self.root.title("Amazon Review Scraper - GUI")
        self.root.geometry("630x650+0+0")
        self.root.resizable(True, True)

        # Initialize variables
        self.scraper = None
        self.search_results = []
        self.selected_product = None
        self.scraping_thread = None
        self.message_queue = queue.Queue()
        self.headless_var = tk.BooleanVar(value=True)
        self.review_keyword_var = tk.StringVar()
        self.last_saved_file = None
        self.stop_event = threading.Event()  # Thread stopping mechanism

        
        # Country to domain mapping
        self.country_domains = {
            "US": "amazon.com",
            "Germany": "amazon.de",
            "Canada": "amazon.ca",
            "Japan": "amazon.co.jp",
            "Australia": "amazon.com.au",
            "Brazil": "amazon.com.br",
            "Mexico": "amazon.com.mx",
            "Netherlands": "amazon.nl"
        }

        # Setup GUI
        self.setup_gui()

        # Setup auto login
        self.setup_credentials()

        # Create initial scraper
        self.create_scraper()

        # Start message processing
        self.process_messages()

    def setup_credentials(self):
        """Setup Amazon credentials"""
        try:
            email, password = AmazonConfig.check_and_setup()
            if email and password:
                self.update_status("Credentials loaded successfully")
            else:
                self.update_status("No credentials available - manual login may be required")
        except Exception as e:
            self.update_status(f"Error setting up credentials: {e}")

    def create_scraper(self):
        """Create scraper with current headless setting and selected country"""
        headless = self.headless_var.get()
        country = self.country_var.get()
        domain = self.country_domains.get(country, "amazon.com")
        self.scraper = AmazonScraperGUI(self.gui_callback, headless=headless, domain=domain)
        self.update_status(f"Scraper created (headless: {headless}, country: {country})")

    def on_headless_change(self, *args):
        """Handle headless mode change"""
        if self.scraper:
            # Close existing driver if any
            if hasattr(self.scraper, 'driver') and self.scraper.driver:
                self.scraper.close_driver()
            # Recreate scraper with new headless setting
            self.create_scraper()
        else:
            # If no scraper yet, just update status
            headless = self.headless_var.get()
            self.update_status(f"Headless mode set to: {headless}")

    def on_country_change(self, *args):
        """Handle country change"""
        if self.scraper:
            # Close existing driver if any
            if hasattr(self.scraper, 'driver') and self.scraper.driver:
                self.scraper.close_driver()
            # Recreate scraper with new country setting
            self.create_scraper()
        else:
            # If no scraper yet, just update status
            country = self.country_var.get()
            self.update_status(f"Country set to: {country}")

    def setup_gui(self):
        """Setup the GUI components"""
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="Amazon Review Scraper",
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Search Input", padding="5")
        input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="Search Type:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.search_type = tk.StringVar(value="keyword")
        search_type_combo = ttk.Combobox(input_frame, textvariable=self.search_type,
                                        values=["keyword", "asin", "url"], state="readonly", width=10)
        search_type_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))

        ttk.Label(input_frame, text="Country:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.country_var = tk.StringVar(value="US")
        self.country_combo = ttk.Combobox(input_frame, textvariable=self.country_var,
                                          values=["US", "Germany", "Canada", "Japan", "Australia", "Brazil", "Mexico", "Netherlands"],
                                          state="readonly", width=10)
        self.country_combo.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(0, 10))

        ttk.Label(input_frame, text="Search Term:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=5)
        self.search_entry = ttk.Entry(input_frame)
        self.search_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)

        self.search_button = ttk.Button(input_frame, text="Search", command=self.start_search)
        self.search_button.grid(row=1, column=2, pady=5)

        # Headless mode checkbox
        ttk.Label(input_frame, text="Headless Mode:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 5))
        self.headless_checkbox = ttk.Checkbutton(input_frame, text="Run browser in background", variable=self.headless_var)
        self.headless_checkbox.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=(10, 5))
        # Add trace to recreate scraper when headless changes
        self.headless_var.trace_add("write", self.on_headless_change)
        # Add trace to recreate scraper when country changes
        self.country_var.trace_add("write", self.on_country_change)

        # Results section
        results_frame = ttk.LabelFrame(main_frame, text="Search Results", padding="5")
        results_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        # Results treeview
        columns = ("#", "ASIN", "Price", "Rating", "Reviews", "Title")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=8)

        for col in columns:
            self.results_tree.heading(col, text=col)
            if col == "Title":
                self.results_tree.column(col, width=300)
            else:
                self.results_tree.column(col, width=80)

        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)

        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        self.results_tree.bind('<<TreeviewSelect>>', self.on_product_select)

        # Scrape section
        scrape_frame = ttk.LabelFrame(main_frame, text="Review Scraping", padding="5")
        scrape_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(scrape_frame, text="Pages to scrape:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.pages_var = tk.IntVar(value=5)
        pages_spin = tk.Spinbox(scrape_frame, from_=1, to=20, textvariable=self.pages_var, width=5)
        pages_spin.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))

        ttk.Label(scrape_frame, text="Review keyword filter:").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        self.review_keyword_entry = ttk.Entry(scrape_frame, textvariable=self.review_keyword_var, width=15)
        self.review_keyword_entry.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Label(scrape_frame, text="(optional)", font=("Arial", 8)).grid(row=0, column=4, sticky=tk.W)

        self.scrape_button = ttk.Button(scrape_frame, text="Scrape Reviews", command=self.start_scraping, state=tk.DISABLED)
        self.scrape_button.grid(row=1, column=0, padx=(0, 10), pady=(10, 0))

        self.stop_button = ttk.Button(scrape_frame, text="Stop", command=self.stop_scraping, state=tk.DISABLED)
        self.stop_button.grid(row=1, column=1, pady=(10, 0))

        self.open_csv_button = ttk.Button(scrape_frame, text="Open CSV File", command=self.open_csv_file, state=tk.DISABLED)
        self.open_csv_button.grid(row=1, column=2, padx=(10, 0), pady=(10, 0))

        # Status section
        ttk.Label(main_frame, text="Status", font=("Arial", 10, "bold")).grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(0, 2))
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)

        self.status_text = scrolledtext.ScrolledText(status_frame, height=10, wrap=tk.WORD)
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Initial status
        self.update_status("Application started. Ready to search.")

    def gui_callback(self, message_type, data):
        """Callback function for scraper to update GUI"""
        self.message_queue.put((message_type, data))

    def process_messages(self):
        """Process messages from the message queue"""
        try:
            while True:
                message_type, data = self.message_queue.get_nowait()
                self.handle_message(message_type, data)
        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(100, self.process_messages)

    def handle_message(self, message_type, data):
        """Handle different types of messages"""
        if message_type == 'status':
            self.update_status(data)
        elif message_type == 'error':
            self.update_status(f"ERROR: {data}")
            messagebox.showerror("Error", data)
        elif message_type == 'progress':
            # For progress updates
            self.update_status(data)
        elif message_type == 'results':
            self.display_search_results(data)
        elif message_type == 'file_saved':
            self.last_saved_file = data
            self.open_csv_button.config(state=tk.NORMAL)

    def update_status(self, message):
        """Update status text area"""
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)

    def start_search(self):
        """Start the search in a separate thread"""
        search_term = self.search_entry.get().strip()
        if not search_term:
            messagebox.showwarning("Input Required", "Please enter a search term")
            return

        # Input validation
        if len(search_term) < 2:
            messagebox.showwarning("Input Too Short", "Search term must be at least 2 characters long")
            return

        if len(search_term) > 200:
            messagebox.showwarning("Input Too Long", "Search term must be less than 200 characters")
            return

        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.search_results = []
        self.selected_product = None
        self.scrape_button.config(state=tk.DISABLED)

        # Update UI
        self.search_button.config(state=tk.DISABLED)
        self.update_status(f"Starting search for: {search_term}")

        # Start search thread
        search_thread = threading.Thread(target=self.perform_search, args=(search_term,))
        search_thread.daemon = True
        search_thread.start()

    def perform_search(self, search_term):
        """Perform the search operation"""
        try:
            if not self.scraper:
                self.gui_callback('error', 'Scraper not initialized')
                return

            self.scraper.setup_stealth_driver()
            products = self.scraper.search_amazon_products(search_term, max_results=10)

            if products:
                self.gui_callback('results', products)
                self.gui_callback('status', f"Found {len(products)} products")
            else:
                self.gui_callback('status', "No products found")

        except Exception as e:
            self.gui_callback('error', f'Search failed: {str(e)}')
        finally:
            self.root.after(0, lambda: self.search_button.config(state=tk.NORMAL))

    def display_search_results(self, products):
        """Display search results in the treeview"""
        self.search_results = products

        for product in products:
            values = (
                product.get('index', ''),
                product.get('asin', ''),
                product.get('price', ''),
                product.get('rating', ''),
                product.get('reviews_count', ''),
                product.get('title', '')[:50] + "..." if len(product.get('title', '')) > 50 else product.get('title', '')
            )
            self.results_tree.insert('', tk.END, values=values)

        if products:
            self.scrape_button.config(state=tk.NORMAL)

    def on_product_select(self, event):
        """Handle product selection"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            index = int(item['values'][0]) - 1  # Convert to 0-based index
            if 0 <= index < len(self.search_results):
                self.selected_product = self.search_results[index]
                self.update_status(f"Selected: {self.selected_product['title'][:50]}...")

    def start_scraping(self):
        """Start scraping reviews"""
        if not self.selected_product:
            messagebox.showwarning("Selection Required", "Please select a product first")
            return

        max_pages = self.pages_var.get()

        # Input validation
        if max_pages < 1 or max_pages > 20:
            messagebox.showwarning("Invalid Pages", "Number of pages must be between 1 and 20")
            return

        review_keyword = self.review_keyword_var.get().strip()
        if len(review_keyword) > 50:
            messagebox.showwarning("Keyword Too Long", "Review keyword filter must be less than 50 characters")
            return

        # Reset stop event
        self.stop_event.clear()

        # Update UI
        self.scrape_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.open_csv_button.config(state=tk.DISABLED)

        # Start scraping thread
        self.scraping_thread = threading.Thread(target=self.perform_scraping, args=(max_pages,))
        self.scraping_thread.daemon = True
        self.scraping_thread.start()

    def perform_scraping(self, max_pages):
        """Perform the scraping operation"""
        try:
            # Check if stop was requested before starting
            if self.stop_event.is_set():
                self.gui_callback('status', 'Scraping cancelled before starting')
                return

            asin = self.selected_product['asin']
            review_keyword = self.review_keyword_var.get().strip()
            reviews = self.scraper.scrape_reviews_for_product(asin, max_pages, review_keyword)

            # Check if stop was requested during scraping
            if self.stop_event.is_set():
                self.gui_callback('status', 'Scraping was cancelled')
                return

            if reviews:
                # Save to CSV
                review_keyword = self.review_keyword_var.get().strip()
                filename = self.scraper.save_reviews_to_csv(reviews, asin, review_keyword)

                # Show success message
                self.root.after(0, lambda: messagebox.showinfo("Success",
                    f"Scraped {len(reviews)} reviews\nSaved to: {filename}"))
            else:
                self.root.after(0, lambda: messagebox.showwarning("No Reviews",
                    "No reviews were found for this product"))

        except Exception as e:
            if self.stop_event.is_set():
                self.gui_callback('status', 'Scraping was cancelled')
            else:
                self.gui_callback('error', f'Scraping failed: {str(e)}')
        finally:
            self.root.after(0, lambda: self.scrape_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))

    def stop_scraping(self):
        """Stop the scraping operation"""
        if self.scraping_thread and self.scraping_thread.is_alive():
            self.update_status("Stopping scraping...")
            # Signal the thread to stop
            self.stop_event.set()
            # Close driver to interrupt operations
            if self.scraper:
                self.scraper.close_driver()
            # Wait for thread to finish (with timeout)
            self.scraping_thread.join(timeout=5.0)
            if self.scraping_thread.is_alive():
                self.update_status("Warning: Scraping thread did not stop gracefully")
            self.stop_button.config(state=tk.DISABLED)
            self.scrape_button.config(state=tk.NORMAL)
        else:
            self.update_status("No active scraping to stop")
            self.stop_button.config(state=tk.DISABLED)
            self.scrape_button.config(state=tk.NORMAL)


    def open_csv_file(self):
        """Open the saved CSV file"""
        if not self.last_saved_file:
            messagebox.showwarning("No File", "No CSV file has been saved yet.")
            return

        try:
            import subprocess
            import platform

            # Full path to the CSV file on Desktop
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", self.last_saved_file)

            if not os.path.exists(desktop_path):
                messagebox.showerror("File Not Found", f"CSV file not found: {desktop_path}")
                return

            system = platform.system()
            if system == "Windows":
                # Windows - open with default application
                subprocess.run(["start", desktop_path], shell=True)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", desktop_path])
            elif system == "Linux":
                # Linux - try different applications
                apps = ["xdg-open", "libreoffice", "soffice", "ooffice", "excel"]
                opened = False
                for app in apps:
                    try:
                        subprocess.run([app, desktop_path], check=True)
                        opened = True
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue

                if not opened:
                    self.update_status("Could not open CSV file. File is saved on Desktop.")
                    return

            self.update_status(f"Opened CSV file: {self.last_saved_file}")

        except Exception as e:
            self.update_status(f"Error opening CSV file: {str(e)}")
            messagebox.showerror("Error", f"Could not open CSV file:\n{str(e)}")

    def on_closing(self):
        """Handle application closing"""
        try:
            # Signal any running threads to stop
            if hasattr(self, 'stop_event'):
                self.stop_event.set()

            # Wait for threads to finish
            if self.scraping_thread and self.scraping_thread.is_alive():
                self.scraping_thread.join(timeout=2.0)

            # Close scraper resources
            if self.scraper:
                self.scraper.close_driver()

        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            self.root.destroy()

def main():
    """Main function"""
    root = tk.Tk()
    app = AmazonScraperApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()