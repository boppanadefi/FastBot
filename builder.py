from solana.publickey import PublicKey
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction, TransactionInstruction, AccountMeta
from solana.keypair import Keypair
from solana.rpc.core import RPCException
import logging
import httpx
from config import SOLANA_RPC_URL, PRIVATE_KEY, PUBLIC_KEY, SOL_MINT, JUPITER_API_URL
from base64 import b64decode

# Initialize Solana client
client = AsyncClient(SOLANA_RPC_URL)

def get_transaction_url(txid: str) -> str:
    return f"https://explorer.solana.com/tx/{txid}?cluster=mainnet-beta"

async def get_native_balance(account_address: PublicKey) -> int:
    try:
        balance_response = await client.get_balance(account_address)
        return balance_response['result']['value']
    except Exception as e:
        logging.error(f"Error fetching native balance: {e}")
        return 0

async def get_token_balance(account_address: PublicKey, token_mint: PublicKey) -> int:
    try:
        balance_response = await client.get_token_accounts_by_owner(account_address, {"mint": token_mint})
        balance = 0
        if balance_response['result']['value']:
            for token_account in balance_response['result']['value']:
                account_info = await client.get_token_account_balance(token_account['pubkey'])
                balance += int(account_info['result']['value']['amount'])
        return balance
    except Exception as e:
        logging.error(f"Error fetching token balance: {e}")
        return 0

def validate_wallet():
    try:
        # Check if the provided keys can derive a valid Solana account
        keypair = Keypair.from_secret_key(bytes.fromhex(PRIVATE_KEY))
        if keypair.public_key != PublicKey(PUBLIC_KEY):
            raise ValueError("Public key does not match the private key")
        logging.info("Wallet validated successfully")
    except Exception as e:
        logging.error(f"Invalid wallet: {e}")
        raise

def sol_to_lamports(sol: float) -> int:
    return int(sol * 1_000_000_000)

def calculate_slippage(amount: int, slippage_bps: int) -> int:
    return amount + int(amount * slippage_bps / 10_000)

# Disable SSL verification (for testing purposes only)
async def get_best_route(input_mint: str, output_mint: str, amount: int, slippage_bps: int):
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:  # Disable SSL verification
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount,
            "slippageBps": slippage_bps,
            "userPublicKey": str(PUBLIC_KEY),
            "swapMode": "ExactIn"  # This ensures that the amount specified is the amount input into the swap
        }
        logging.info(f"Fetching best route with params: {params}")
        print(f"Params for get_best_route: {params}")  # Print the params for debugging
        try:
            response = await client.get(f"{JUPITER_API_URL}/quote", params=params)
            logging.info(f"Received response for best route with status code: {response.status_code}")
            if response.status_code != 200:
                logging.error(f"Non-200 response: {response.text}")
                return {"error": f"Non-200 response: {response.text}"}
            response_data = response.json()
            logging.info(f"Received response data for best route: {response_data}")
            if 'data' not in response_data or not response_data['data']:
                logging.error(f"Invalid response data: {response_data}")
                return {"error": "Invalid response data from Jupiter API"}
            return response_data['data'][0]  # Get the best route
        except httpx.ReadTimeout:
            logging.error("Request to Jupiter API timed out")
            return {"error": "Request to Jupiter API timed out"}
        except httpx.HTTPStatusError as exc:
            logging.error(f"HTTP error occurred: {exc.response.text}")
            return {"error": f"HTTP error occurred: {exc.response.text}"}
        except Exception as exc:
            logging.error(f"An error occurred while fetching the route: {exc}")
            return {"error": f"An error occurred while fetching the route: {exc}"}

async def build_and_send_transaction(trading_signal: dict):
    try:
        validate_wallet()
        logging.info("Starting transaction build and send process")

        slippage_bps = trading_signal['slippageBps']
        input_mint = trading_signal['inputMint']
        output_mint = trading_signal['outputMint']
        amount = trading_signal['amount']
        trade_mode = trading_signal['tradeMode']

        # Calculate the amount in lamports if buying, or as percentage if selling
        if trade_mode == 'buy':
            amount_in_lamports = sol_to_lamports(amount)  # Amount is in SOL
            logging.info(f"Trade mode is buy, amount in SOL: {amount}, amount in Lamports: {amount_in_lamports}")
        elif trade_mode == 'sell':
            balance = await get_token_balance(PUBLIC_KEY, PublicKey(input_mint))
            amount_in_lamports = int(balance * amount / 100)  # Amount is % of tokens to sell
            logging.info(f"Trade mode is sell, percentage to sell: {amount}%, amount in tokens: {amount_in_lamports}")
        else:
            raise ValueError("Invalid trade mode")

        logging.info(f"Calculated amount in Lamports: {amount_in_lamports}")

        # Calculate amount considering slippage
        amount_with_slippage = calculate_slippage(amount_in_lamports, slippage_bps)
        logging.info(f"Amount with slippage: {amount_with_slippage}")

        # Check balance
        if trade_mode == 'buy':
            balance = await get_native_balance(PUBLIC_KEY)
        else:
            balance = await get_token_balance(PUBLIC_KEY, PublicKey(input_mint))
        
        logging.info(f"Balance for {input_mint}: {balance}")

        if balance < amount_with_slippage:
            logging.error("Insufficient balance for the trade")
            return {"error": "Insufficient balance for the trade"}

        # Get the best route from Jupiter API
        quote_response = await get_best_route(input_mint, output_mint, amount_with_slippage, slippage_bps)
        if 'error' in quote_response:
            return quote_response

        logging.info(f"Best route: {quote_response}")

        # Send the transaction via Jupiter API
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:  # Disable SSL verification
            swap_data = {
                "userPublicKey": str(PUBLIC_KEY),
                "quoteResponse": quote_response,
                "wrapAndUnwrapSol": True,
                "useSharedAccounts": True,
                # Add other optional parameters if needed
            }
            logging.info(f"Sending swap transaction with data: {swap_data}")
            try:
                response = await client.post(f"{JUPITER_API_URL}/swap", json=swap_data)
                logging.info(f"Received response for swap transaction with status code: {response.status_code}")
                if response.status_code != 200:
                    logging.error(f"Non-200 response: {response.text}")
                    return {"error": f"Non-200 response: {response.text}"}
                response_data = response.json()
                logging.info(f"Received response data for swap transaction: {response_data}")
                if 'txid' not in response_data:
                    logging.error(f"Invalid response data: {response_data}")
                    return {"error": "Invalid response data from Jupiter API"}
                txid = response_data['txid']
                transaction_url = get_transaction_url(txid)
                logging.info(f"Transaction URL: {transaction_url}")
                return {"txid": txid, "transaction_url": transaction_url}
            except httpx.ReadTimeout:
                logging.error("Request to Jupiter API timed out during swap transaction")
                return {"error": "Request to Jupiter API timed out"}
            except httpx.HTTPStatusError as exc:
                logging.error(f"HTTP error occurred during swap transaction: {exc.response.text}")
                return {"error": f"HTTP error occurred during swap transaction: {exc.response.text}"}
            except Exception as exc:
                logging.error(f"An error occurred during swap transaction: {exc}")
                return {"error": f"An error occurred during swap transaction: {exc}"}

    except Exception as e:
        logging.error(f"Error in build_and_send_transaction: {e}", exc_info=True)
        return {"error": str(e)}
