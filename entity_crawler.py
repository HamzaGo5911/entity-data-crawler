import time
import random
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
from urllib.parse import urlparse


class EntityDataCrawler:
    def __init__(self, urls, max_depth=2):
        self.urls = urls
        self.visited_urls = set()  # Track visited URLs
        self.data = []
        self.max_depth = max_depth  # Limit recursion depth

    @staticmethod
    def is_valid_url(url):
        """Check if the provided URL is valid."""
        parsed = urlparse(url)
        return all([parsed.scheme, parsed.netloc])

    def fetch_html_dynamic(self, driver, url):
        """Fetch HTML from a dynamic site using Selenium."""
        driver.get(url)
        try:
            # Wait for the main content to load (Adjust as per site structure)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)  # Give time for additional content to load if needed
            return driver.page_source
        except TimeoutException:
            print(f"Timeout occurred while loading {url}")
            return None

    def extract_links_from_page(self, soup):
        """Extract all relevant internal links from the current page."""
        links = []
        for a_tag in soup.find_all('a', href=True):
            link = a_tag['href']
            # Print the extracted links for debugging
            print(f"Extracted link: {link}")
            # Filter out irrelevant or external links and convert relative links to absolute
            if link.startswith('/members/profile'):
                full_link = f"https://www.pap.gov.pk{link}"  # Assuming relative links need base URL
                if full_link not in self.visited_urls:
                    links.append(full_link)
        return links

    def extract_data_from_current_page(self, soup):
        """Extract entity-specific data from the current page using BeautifulSoup."""
        # Initialize a list to store entity data for the current page
        entity_data_list = []

        # Define the mapping of entity types to their corresponding HTML tags and conditions
        entity_mappings = {
            'Name': [
                ('a', {'href': lambda href: href and '/profile/' in href}),  # Primary tag for names in links
                ('h2', {}),  # Fallback tag for names in headers
                ('span', {'class': 'name'}),  # Another possible container for names
                ('div', {'class': 'name-container'})  # Additional fallback
            ],
            'Contact Information': [('br', {'previous_sibling': True})],  # Special case for contact info from <br> tag
            'Occupation': [('a', {'href': lambda href: href and '/occupation/' in href})],
            'Family Details': [('div', {'class': 'posts_text'})],
            'Political Party Affiliation': [('a', {'href': lambda href: href and '/listing/' in href})],
            'Images': [('img', {})],  # Extract images from <img> tags
        }

        # Extract data for each entity type based on the defined mappings
        extracted_data = {key: [] for key in entity_mappings.keys()}

        for entity, conditions in entity_mappings.items():
            found_data = False  # Flag to check if any data was found for the entity

            for tag, attrs in conditions:
                if tag == 'br' and attrs.get('previous_sibling'):
                    # Special case for extracting contact information from <br>
                    for br_tag in soup.find_all(tag):
                        prev_sibling = br_tag.previous_sibling
                        if prev_sibling and isinstance(prev_sibling, str):
                            extracted_data[entity].append(prev_sibling.strip())
                            found_data = True
                else:
                    # Ensure that attrs is a dictionary before passing to find_all
                    elements = soup.find_all(tag, **attrs)

                    if tag == 'img':  # Special case for extracting image URLs from <img>
                        extracted_data[entity].extend(
                            [element.get('src') for element in elements if element.get('src')])
                    else:
                        extracted_data[entity].extend([element.text.strip() for element in elements])

                    if elements:  # If any elements are found, set the flag
                        found_data = True

                if found_data:  # Break the loop if data was found for this entity
                    break

        # Find the maximum number of entries across all categories to ensure proper alignment
        max_length = max(len(data) for data in extracted_data.values())

        # Fill entity data into structured rows
        for i in range(max_length):
            entity_data = {
                'Name': extracted_data['Name'][i] if i < len(extracted_data['Name']) else '',
                'Contact Information': extracted_data['Contact Information'][i] if i < len(
                    extracted_data['Contact Information']) else '',
                'Occupation': extracted_data['Occupation'][i] if i < len(extracted_data['Occupation']) else '',
                'Family Details': extracted_data['Family Details'][i] if i < len(
                    extracted_data['Family Details']) else '',
                'Political Party Affiliation': extracted_data['Political Party Affiliation'][i] if i < len(
                    extracted_data['Political Party Affiliation']) else '',
                'Images': extracted_data['Images'][i] if i < len(extracted_data['Images']) else ''
            }
            entity_data_list.append(entity_data)

        # Debugging output for extracted entities
        for entity_data in entity_data_list:
            print(f"Extracted Entity Data: {entity_data}")

        # Append the extracted entity data to the main data list
        self.data.extend(entity_data_list)

    def crawl_nested_links(self, driver, soup, depth):
        """Recursively crawl nested links within a page, respecting max depth."""
        if depth > self.max_depth:
            print("Reached maximum crawl depth.")
            return

        links = self.extract_links_from_page(soup)
        for link in links:
            if link not in self.visited_urls:
                self.visited_urls.add(link)
                print(f"Crawling nested link: {link}")
                html = self.fetch_html_dynamic(driver, link)
                if html:
                    new_soup = BeautifulSoup(html, 'html.parser')
                    self.extract_data_from_current_page(new_soup)
                    self.crawl_nested_links(driver, new_soup, depth + 1)  # Recur for deeper nested links

    def handle_pagination(self, driver, url):
        """Handle pagination by identifying 'Next' buttons or page numbers."""
        while True:
            print(f"Processing URL: {url}")  # Debug: Print the URL being processed
            html = self.fetch_html_dynamic(driver, url)
            if not html:
                break  # Stop if no content is returned

            soup = BeautifulSoup(html, 'html.parser')
            self.extract_data_from_current_page(soup)
            self.crawl_nested_links(driver, soup, depth=1)  # Start crawling nested links

            # Check if there's a 'Next' page button
            try:
                next_button = driver.find_element(By.LINK_TEXT, 'Next')
                if next_button:
                    next_button.click()  # Go to the next page
                    time.sleep(random.uniform(2, 5))  # Sleep to mimic human interaction
                else:
                    break  # Stop if no 'Next' button is found
            except NoSuchElementException:
                print("No 'Next' button found. Ending pagination.")
                break

    def start_crawling(self):
        """Start the crawling process."""
        # Setup Selenium WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Headless mode
        options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(service=ChromeService(), options=options)

        for url in self.urls:
            if self.is_valid_url(url):
                print(f"Crawling: {url}")
                self.handle_pagination(driver, url)
            else:
                print(f"Invalid URL skipped: {url}")

        driver.quit()
        print("Crawling complete. Saving data...")  # Indicate saving process
        self.save_data_to_csv('extracted_data.csv')

    def save_data_to_csv(self, filename):
        """Save extracted data to a CSV file."""
        # Convert list of dictionaries to DataFrame, handling lists appropriately
        df = pd.DataFrame(self.data)

        # Flatten the DataFrame if there are lists in any of the columns
        for column in df.columns:
            if df[column].apply(lambda x: isinstance(x, list)).any():
                # Explode the lists into separate rows
                df = df.explode(column)

        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
