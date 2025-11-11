import requests
from bs4 import BeautifulSoup
import csv
import sys

def scrape_apcc_data():
    """
    Scrapes the APCC data from the Medicare Australia website by first fetching
    a valid ViewState and then submitting the search form. Includes enhanced debugging.
    """
    search_url = "https://www2.medicareaustralia.gov.au/pdsPortal/pub/approvedCollectionCentreSearch.faces"
    
    session = requests.Session()
    
    # Use more comprehensive headers to better mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
    }
    session.headers.update(headers)

    try:
        # --- Step 1: GET request to fetch the initial page and ViewState ---
        print("Fetching initial page to get ViewState token...")
        initial_response = session.get(search_url)

        # --- Enhanced Debugging ---
        print(f"Initial request status code: {initial_response.status_code}")
        print("Response Headers:")
        for key, value in initial_response.headers.items():
            print(f"  {key}: {value}")
        
        # Save the content to a file for artifact inspection
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(initial_response.text)
        print("Full page content saved to debug_page.html")
        # --- End Debugging ---

        initial_response.raise_for_status()

        soup = BeautifulSoup(initial_response.text, 'html.parser')
        
        view_state_element = soup.find('input', {'id': 'javax.faces.ViewState'})
        
        if not view_state_element:
            print("\nError: Could not find the 'javax.faces.ViewState' token in the HTML.")
            print("The website structure may have changed, or we may not have received the correct page.")
            print(f"Page Title: {soup.title.string if soup.title else 'No Title Found'}")
            sys.exit(1)
            
        view_state = view_state_element.get('value')
        if view_state is None:
            print("\nError: Found the ViewState element, but it has no 'value' attribute.")
            sys.exit(1)
            
        print("Successfully retrieved ViewState.")

        # ... (rest of the script remains the same)

        form_data = {
            'approvedCollectionCentreSearchForm': 'approvedCollectionCentreSearchForm',
            'approvedCollectionCentreSearchForm:suburb': '*',
            'approvedCollectionCentreSearchForm:search': 'Search',
            'javax.faces.ViewState': view_state,
        }

        print("Submitting search form...")
        search_response = session.post(search_url, data=form_data)
        search_response.raise_for_status()

        results_soup = BeautifulSoup(search_response.text, 'html.parser')
        table = results_soup.find('table', {'id': 'approvedCollectionCentreSearchForm:accp_search_result_table'})

        if not table:
            print("Could not find the results table after form submission.")
            with open('debug_results_page.html', 'w', encoding='utf-8') as f:
                f.write(search_response.text)
            print("Full results page content saved to debug_results_page.html")
            sys.exit(1)

        print("Found results table. Writing to CSV...")
        with open('apcc_list.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            header = [th.text.strip() for th in table.find_all('th')]
            writer.writerow(header)
            for row in table.find_all('tr'):
                if row.find_all('td'):
                    cols = [td.text.strip() for td in row.find_all('td')]
                    writer.writerow(cols)

        print("Successfully scraped and saved apcc_list.csv")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the request: {e}")
        sys.exit(1)

if __name__ == "__main__":
    scrape_apcc_data()
