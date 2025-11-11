import requests
from bs4 import BeautifulSoup
import csv
import sys

def scrape_apcc_data():
    """
    Scrapes the APCC data from the Medicare Australia website by first fetching
    a valid ViewState and then submitting the search form.
    """
    search_url = "https://www2.medicareaustralia.gov.au/pdsPortal/pub/approvedCollectionCentreSearch.faces"
    
    # Use a session object to persist cookies and headers across requests
    session = requests.Session()
    
    # Set a User-Agent to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    session.headers.update(headers)

    try:
        # --- Step 1: GET request to fetch the initial page and ViewState ---
        print("Fetching initial page to get ViewState token...")
        initial_response = session.get(search_url)
        initial_response.raise_for_status()

        soup = BeautifulSoup(initial_response.text, 'html.parser')
        
        # Find the ViewState token in the form
        view_state_element = soup.find('input', {'id': 'javax.faces.ViewState'})
        
        if not view_state_element or 'value' not in view_state_element.attrs:
            print("Could not find the javax.faces.ViewState token. The website structure may have changed.")
            sys.exit(1) # Exit with an error code
            
        view_state = view_state_element['value']
        print("Successfully retrieved ViewState.")

        # --- Step 2: POST request to submit the form with the dynamic ViewState ---
        form_data = {
            'approvedCollectionCentreSearchForm': 'approvedCollectionCentreSearchForm',
            'approvedCollectionCentreSearchForm:suburb': '*',
            'approvedCollectionCentreSearchForm:search': 'Search',
            'javax.faces.ViewState': view_state,
        }

        print("Submitting search form...")
        search_response = session.post(search_url, data=form_data)
        search_response.raise_for_status()

        # --- Step 3: Parse the results table from the response ---
        results_soup = BeautifulSoup(search_response.text, 'html.parser')
        table = results_soup.find('table', {'id': 'approvedCollectionCentreSearchForm:accp_search_result_table'})

        if not table:
            print("Could not find the results table after form submission.")
            # Add some debugging output to see what the page looks like
            print("Page Title:", results_soup.title.string if results_soup.title else "No Title")
            sys.exit(1) # Exit with an error code

        print("Found results table. Writing to CSV...")
        with open('apcc_list.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # Write header
            header = [th.text.strip() for th in table.find_all('th')]
            writer.writerow(header)

            # Write rows
            for row in table.find_all('tr'):
                # Ensure it's a data row by checking for 'td' elements
                if row.find_all('td'):
                    cols = [td.text.strip() for td in row.find_all('td')]
                    writer.writerow(cols)

        print("Successfully scraped and saved apcc_list.csv")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the request: {e}")
        sys.exit(1)

if __name__ == "__main__":
    scrape_apcc_data()
