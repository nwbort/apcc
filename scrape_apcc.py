import requests
from bs4 import BeautifulSoup
import csv
import sys

def scrape_apcc_data():
    """
    Scrapes the APCC data from the Medicare Australia website by first fetching
    a valid ViewState and then submitting the search form with the correct field names
    and parsing the correct results table ID.
    """
    search_url = "https://www2.medicareaustralia.gov.au/pdsPortal/pub/approvedCollectionCentreSearch.faces"
    
    session = requests.Session()
    
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
        initial_response.raise_for_status()

        soup = BeautifulSoup(initial_response.text, 'html.parser')
        
        # Find the ViewState element by its 'name' attribute, which is more stable than the ID
        view_state_element = soup.find('input', {'name': 'javax.faces.ViewState'})
        
        if not view_state_element or 'value' not in view_state_element.attrs:
            print("Error: Could not find the 'javax.faces.ViewState' token.")
            # Save the page for debugging if it fails
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(initial_response.text)
            sys.exit(1)
            
        view_state = view_state_element['value']
        print("Successfully retrieved ViewState.")

        # --- Step 2: POST request to submit the form with the correct field names ---
        # These names were discovered by inspecting the initial HTML form
        form_data = {
            'j_id_m': 'j_id_m',
            'j_id_m:gui_suburb': '*',
            'j_id_m:gui_search': 'Search',
            'j_id_m_SUBMIT': '1',
            'javax.faces.ViewState': view_state,
        }

        print("Submitting search form...")
        search_response = session.post(search_url, data=form_data)
        search_response.raise_for_status()

        # --- Step 3: Parse the results table from the response ---
        results_soup = BeautifulSoup(search_response.text, 'html.parser')
        
        # --- FINAL FIX: Use the correct table ID found in the debug_results_page.html file ---
        table = results_soup.find('table', {'id': 'gui_accTable'})

        if not table:
            print("Error: Could not find the results table ('gui_accTable') after form submission.")
            # Save the results page for debugging if it fails
            with open('debug_results_page.html', 'w', encoding='utf-8') as f:
                f.write(search_response.text)
            sys.exit(1)

        print("Found results table. Writing to CSV...")
        with open('apcc_list.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            header = [th.text.strip() for th in table.find_all('th')]
            writer.writerow(header)
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
