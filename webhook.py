from fastapi import FastAPI
from pydantic import BaseModel
import logging
from builder import build_and_send_transaction
from config import PORT, SOL_MINT

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)

class WebhookData(BaseModel):
    token_address: str
    amount: float  # Amount in SOL if buy, percentage if sell
    slippageBps: int = 50
    tradeMode: str

@app.post("/webhook")
async def webhook_listener(data: WebhookData):
    try:
        logging.info(f"Received webhook data: {data}")

        # Parse trading signal from webhook data
        trading_signal = data.dict()
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
