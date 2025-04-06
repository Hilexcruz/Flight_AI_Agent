import requests
import json
import os
import http.client
from datetime import datetime, timedelta

# File to store cached flight data
CACHE_FILE = "flight_cache.json"
# Cache expiry time: 1 hour (to avoid calling the API too frequently)
CACHE_EXPIRY = timedelta(hours=1)

def load_cache():
    """
    Load cached flight data from a file.
    If the cache file exists, read and return its contents.
    If not, return an empty dictionary.
    """
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as file:
            return json.load(file)
    return {}

def save_cache(cache):
    """
    Save the updated cache data to a file.
    This ensures that the cache persists between program runs.
    """
    with open(CACHE_FILE, "w") as file:
        json.dump(cache, file)

def fetch_flights(origin, destination, date):
    """
    Fetch flight data from Skyscanner and Kiwi.com APIs with caching.

    Args:
        origin (str): Origin airport code.
        destination (str): Destination airport code.
        date (str): Flight departure date.

    Returns:
        dict: Flight data or None if both APIs fail.
    """
    # Load the existing cache
    cache = load_cache()
    cache_key = f"{origin}_{destination}_{date}"

    # Check if data is in the cache and still valid
    if cache_key in cache:
        cached_data = cache[cache_key]
        cached_time = datetime.fromisoformat(cached_data["timestamp"])
        if datetime.now() - cached_time < CACHE_EXPIRY:
            print("Using cached data")
            return cached_data["data"]

    # Skyscanner API request
    skyscanner_conn = http.client.HTTPSConnection("skyscanner89.p.rapidapi.com")
    skyscanner_headers = {
        "x-rapidapi-host": "skyscanner89.p.rapidapi.com",
        "x-rapidapi-key": "YOUR_SKYSCANNER_API_KEY"  # Replace with your actual API key
    }
    try:
        skyscanner_conn.request("GET", f"/flights/roundtrip/list?origin={origin}&destination={destination}&date={date}", headers=skyscanner_headers)
        response = skyscanner_conn.getresponse()
        if response.status == 200:
            print("Skyscanner API success")
            data = json.loads(response.read().decode("utf-8"))
            cache[cache_key] = {"timestamp": datetime.now().isoformat(), "data": data}
            save_cache(cache)
            return {"source": "Skyscanner", "data": data}
        else:
            print(f"Skyscanner API failed with status: {response.status}")
    except Exception as e:
        print(f"Error fetching data from Skyscanner: {e}")
    finally:
        skyscanner_conn.close()

    # Kiwi.com API request
    kiwi_conn = http.client.HTTPSConnection("kiwi-com-cheap-flights.p.rapidapi.com")
    kiwi_headers = {
        "x-rapidapi-host": "kiwi-com-cheap-flights.p.rapidapi.com",
        "x-rapidapi-key": "YOUR_KIWI_API_KEY"  # Replace with your actual API key
    }
    try:
        kiwi_conn.request(
            "GET",
            f"/round-trip?fly_from={origin}&fly_to={destination}&date_from={date}&date_to={date}&adults=1&currency=USD&limit=10",
            headers=kiwi_headers
        )
        response = kiwi_conn.getresponse()
        if response.status == 200:
            print("Kiwi.com API success")
            data = json.loads(response.read().decode("utf-8"))
            cache[cache_key] = {"timestamp": datetime.now().isoformat(), "data": data}
            save_cache(cache)
            return {"source": "Kiwi.com", "data": data}
        else:
            print(f"Kiwi.com API failed with status: {response.status}")
    except Exception as e:
        print(f"Error fetching data from Kiwi.com: {e}")
    finally:
        kiwi_conn.close()

    return None

    
def search_flights(origin, destination, date):
    """
    Handle user input and fetch flight data from Skyscanner or Kiwi.
    """
    if not origin or not destination or not date:
        return "Please provide origin, destination, and date."

    # Fetch flights using the unified fetch_flights function
    flights = fetch_flights(origin, destination, date)
    if flights:
        return flights

    return "No flights found or API limit reached."

if __name__ == "__main__":
    """
    Simple command-line interface for testing the flight search functionality.
    """
    # Get user input
    origin = input("Enter origin (e.g., NYC-sky): ")
    destination = input("Enter destination (e.g., LON-sky): ")
    date = input("Enter date (YYYY-MM-DD): ")

    # Call the search function and display the results
    result = search_flights(origin, destination, date)
    print(result)