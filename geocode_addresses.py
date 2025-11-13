import csv
import requests
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set the maximum number of parallel worker threads.
MAX_WORKERS = 30

def fetch_geocode(session, api_key, row):
    """
    Fetches the geocode for a single address row.
    
    Args:
        session: A requests.Session object for making HTTP requests.
        api_key: The HERE API key.
        row: A dictionary representing a row from the input CSV.
        
    Returns:
        A tuple containing the original row data and the fetched lat/lon.
    """
    # Form the full address string for the API query
    address = f"{row.get('Address', '')}, {row.get('Suburb / Town', '')}"
    if not address or address.strip() == ",":
        # Silently skip rows with no address to keep logs clean in Actions
        return (row, ("", ""))

    params = {
        'q': address,
        'apiKey': api_key
    }
    
    try:
        # Make the request to the HERE API
        response = session.get("https://geocode.search.hereapi.com/v1/geocode", params=params, timeout=10)
        response.raise_for_status()  # Raises an exception for 4xx/5xx status codes
        
        data = response.json()
        
        # Check if the response contains any items
        if data.get('items'):
            position = data['items'][0].get('position', {})
            lat = position.get('lat', "")
            lon = position.get('lng', "")
            print(f"Geocoded: {address} -> ({lat}, {lon})")
            return (row, (lat, lon))
        else:
            print(f"Warning: Could not find coordinates for address: {address}")
            return (row, ("", ""))
            
    except requests.exceptions.RequestException as e:
        print(f"Error calling HERE API for address '{address}': {e}")
        # Return the row with empty geocode on API failure
        return (row, ("", ""))

def geocode_addresses_parallel():
    """
    Reads addresses from apcc_list.csv, geocodes them in parallel using the 
    HERE API, and saves the results to apcc_list_geocoded.csv.
    """
    api_key = os.environ.get("HERE_API_KEY")
    if not api_key:
        print("Error: HERE_API_KEY environment variable not set.")
        sys.exit(1)

    input_filename = 'apcc_list.csv'
    output_filename = 'apcc_list_geocoded.csv'
    
    try:
        with open(input_filename, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            # Read all rows into memory to process them
            rows_to_process = list(reader)
            if not rows_to_process:
                print("Input file is empty. Exiting.")
                return
            original_headers = reader.fieldnames
            
    except FileNotFoundError:
        print(f"Error: The input file '{input_filename}' was not found.")
        sys.exit(1)

    # Define the headers for the new CSV file, adding latitude and longitude
    output_headers = original_headers + ["Latitude", "Longitude"]
    
    # List to store the results
    results = []

    # Use a session object for connection pooling, which is more efficient
    with requests.Session() as session:
        # Use ThreadPoolExecutor to run tasks in parallel
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Create a future for each row to be processed
            future_to_row = {executor.submit(fetch_geocode, session, api_key, row): row for row in rows_to_process}
            
            print(f"Submitting {len(rows_to_process)} addresses for geocoding with {MAX_WORKERS} workers...")

            # Process futures as they complete
            for future in as_completed(future_to_row):
                original_row, (lat, lon) = future.result()
                
                # Create a new dictionary with the geocoded data
                new_row = original_row.copy()
                new_row['Latitude'] = lat
                new_row['Longitude'] = lon
                results.append(new_row)

    # Sort results first by 'APA number', then by 'ACC number' to maintain a consistent output order
    # The keys are cast to int for correct numerical sorting.
    results.sort(key=lambda x: (int(x.get('APA number', 0)), int(x.get('ACC number', 0))))

    # Write the collected results to the output CSV
    try:
        with open(output_filename, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=output_headers)
            writer.writeheader()
            writer.writerows(results)
    except IOError as e:
        print(f"Error writing to output file '{output_filename}': {e}")
        sys.exit(1)
        
    print(f"\nGeocoding complete. Output saved to '{output_filename}'.")

if __name__ == "__main__":
    geocode_addresses_parallel()
