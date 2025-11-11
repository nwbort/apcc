import requests
from bs4 import BeautifulSoup
import csv

def scrape_apcc_data():
    """
    Scrapes the APCC data from the Medicare Australia website and saves it to a CSV file.
    """
    url = "https://www2.medicareaustralia.gov.au/pdsPortal/pub/approvedCollectionCentreSearch.faces"
    data = {
        "approvedCollectionCentreSearchForm:suburb": "*",
        "approvedCollectionCentreSearchForm:search": "Search",
        "javax.faces.ViewState": "rO0ABXVyABNbTGphdmEubGFuZy5PYmplY3Q7kM5YnxBzKWwCAAB4cAAAAAN0AAExcHQAG2FwcHJvdmVkQ29sbGVjdGlvbkNlbnRyZVNlYXJjaA=="
    }

    try:
        response = requests.post(url, data=data)
        response.raise_for_status()  # Raise an exception for bad status codes

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'id': 'approvedCollectionCentreSearchForm:accp_search_result_table'})

        if not table:
            print("Could not find the results table.")
            return

        with open('apcc_list.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # Write header
            header = [th.text.strip() for th in table.find_all('th')]
            writer.writerow(header)

            # Write rows
            for row in table.find_all('tr'):
                cols = [td.text.strip() for td in row.find_all('td')]
                if cols:
                    writer.writerow(cols)
        print("Successfully scraped and saved apcc_list.csv")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    scrape_apcc_data()
