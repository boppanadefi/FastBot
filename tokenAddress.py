import requests

def get_dex_pairs(chain_id, pair_addresses):
    """
    Fetches data from Dexscreener API for given chain ID and pair addresses.

    Parameters:
    - chain_id (str): The chain ID to query.
    - pair_addresses (str): The pair addresses to query, comma-separated if multiple.

    Returns:
    - dict: The JSON response from the API if the request is successful.
    - None: If the request fails.
    """
    url = f"https://api.dexscreener.com/latest/dex/pairs/{chain_id}/{pair_addresses}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def print_base_token_address(data):
    """
    Prints the baseToken address from the Dexscreener API response.

    Parameters:
    - data (dict): The JSON response from the Dexscreener API.
    """
    if data and 'pairs' in data:
        for pair in data['pairs']:
            if 'baseToken' in pair and 'address' in pair['baseToken']:
                print(f"baseToken address: {pair['baseToken']['address']}")
    else:
        print("No data available or unexpected response format.")

# Example usage:
chain_id = "solana"  # Replace with the actual chain ID
pair_addresses = "FQed3Ay883zUcGcLaubkV56JJbweiYjxPSTC84yUxqNd"  # Replace with the actual pair addresses

data = get_dex_pairs(chain_id, pair_addresses)
print_base_token_address(data)
