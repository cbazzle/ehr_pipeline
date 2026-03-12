import json

import requests

BASE_URL = "http://127.0.0.1:8000"


def print_response(title: str, response: requests.Response):
    print(f"\n--- {title} ---")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def test_basic_get():
    """Test retrieving a small batch of patients."""
    response = requests.get(f"{BASE_URL}/patients?skip=0&limit=2")
    print_response("Basic GET: /patients (Limit 2)", response)


def test_query_parameters():
    """Test filtering encounters by a start date for incremental loading."""
    params = {"start_date": "2023-01-01", "limit": 3}
    response = requests.get(f"{BASE_URL}/encounters", params=params)
    print_response("Query Params: /encounters since 2023-01-01", response)


def test_pagination_loop():
    """Test fetching all observations for a specific encounter using pagination."""
    print("\n--- Pagination Loop: /observations for Encounter ID 1 ---")

    encounter_id = 1
    skip = 0
    limit = 5
    all_observations = []

    while True:
        params = {"encounter_id": encounter_id, "skip": skip, "limit": limit}

        response = requests.get(f"{BASE_URL}/observations", params=params)

        if response.status_code != 200:
            print(f"Failed to fetch data: {response.status_code}")
            break

        data = response.json()
        records = data.get("data", [])

        if not records:
            # Break the loop when no more records are returned
            break

        all_observations.extend(records)
        print(f"Fetched {len(records)} records. Total so far: {len(all_observations)}")

        # Increment skip for the next page
        skip += limit

    print(f"Finished pagination. Total observations retrieved: {len(all_observations)}")


if __name__ == "__main__":
    # Ensure the FastAPI server is running before executing this script
    test_basic_get()
    test_query_parameters()
    test_pagination_loop()
