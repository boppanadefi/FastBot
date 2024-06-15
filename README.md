download ngrok-v3-stable-windows-amd64 from ngrok website  and run  ngrok http 5000

copy forwarding url to postman POST, make sure add /webhook ex: https://b9aa-154-47-24-95.ngrok-free.app/webhook

you can check serverside messages on ngrok web interface here http://127.0.0.1:4040/inspect/http 


payload for sell / buy 
{
    "token_address": "4G86CMxGsMdLETrYnavMFKPhQzKTvDBYGMRAdVtr72nu",  
    "slippageBps": 50,
    "tradeMode": "sell",
    "amount": 100
}

amount in sol for buy and % for sell 
