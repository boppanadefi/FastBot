import requests
from fastapi import FastAPI
from pydantic import BaseModel
import logging
from builder import build_and_send_transaction
from config import PORT, SOL_MINT

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.ERROR)

class WebhookData(BaseModel):
    pair_id: str
    amount: float  # Amount in SOL if buy, percentage if sell
    slippageBps: int = 50
    tradeMode: str

@app.post("/webhook")
async def webhook_listener(data: WebhookData):
    try:
        logging.info(f"Received webhook data: {data}")

        # Parse trading signal from webhook data
        trading_signal = data.dict()
        trading_signal = update_trading_signal(trading_signal)
    
        # Set inputMint and outputMint based on tradeMode
        if trading_signal['tradeMode'] == 'buy':
            trading_signal['inputMint'] = SOL_MINT
            trading_signal['outputMint'] = trading_signal['token_address']
        elif trading_signal['tradeMode'] == 'sell':
            trading_signal['inputMint'] = trading_signal['token_address']
            trading_signal['outputMint'] = SOL_MINT
        else:
            raise ValueError("Invalid trade mode")
        
        # Process transaction asynchronously
        tx_receipt = await build_and_send_transaction(trading_signal)
        
        return {"status": "success", "transaction_receipt": tx_receipt}
    except Exception as e:
        logging.error(f"Error processing webhook: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


def get_token_address_by_pairid(pair_id):
    # Replace this with the actual implementation of the function
    url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{pair_id}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    
    if data and 'pairs' in data:
        for pair in data['pairs']:
            if 'baseToken' in pair and 'address' in pair['baseToken']:
                print(f"baseToken address: {pair['baseToken']['address']}")
                return pair['baseToken']['address']
    else:
        print("No data available or unexpected response format.")
        return None
    
# Function to update trading signal with token address
def update_trading_signal(trading_signal):
    pair_id = trading_signal.get('pair_id')
    if pair_id is not None:
        token_address = get_token_address_by_pairid(pair_id)
        trading_signal['token_address'] = token_address
    return trading_signal

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
