import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv # type: ignore
load_dotenv()

STOREHUB_API_BASE_URL = "http://api.storehubhq.com"
STOREHUB_API_USERNAME = os.getenv("STOREHUB_API_USERNAME")
STOREHUB_API_PASSWORD = os.getenv("STOREHUB_API_PASSWORD")

def test_fetch_stores():
    try:
        # Make the GET request to fetch stores
        store_response = requests.get(
            f"{STOREHUB_API_BASE_URL}/stores",
            auth=HTTPBasicAuth(STOREHUB_API_USERNAME, STOREHUB_API_PASSWORD),
        )

        # Print the response for debugging
        print(f"Response Status Code: {store_response.status_code}")
        print(f"Response Content: {store_response.text}")

        # Check if the response is successful
        if store_response.status_code == 200:
            stores = store_response.json()
            print("Fetched stores successfully:")
            print(stores)
        else:
            print(f"Failed to fetch stores. Status code: {store_response.status_code}")
            print(f"Error Detail: {store_response.text}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Run the test
test_fetch_stores()