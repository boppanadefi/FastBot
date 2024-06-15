import json
import os

# Define the path to the config file
config_path = os.path.join(os.path.dirname(__file__), "config.json")

# Load the config file
with open(config_path, "r") as config_file:
    config = json.load(config_file)

# Set the configuration variables
SOLANA_RPC_URL = config["SOLANA_RPC_URL"]
PRIVATE_KEY = config["PRIVATE_KEY"]
PUBLIC_KEY = config["PUBLIC_KEY"]
SOL_MINT = config["SOL_MINT"]
JUPITER_API_URL = config["JUPITER_API_URL"]
PORT = config["PORT"]
