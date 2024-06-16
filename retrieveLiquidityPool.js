const solanaWeb3 = require('@solana/web3.js');
const BufferLayout = require('buffer-layout');

const liquidityPoolAccount = new solanaWeb3.PublicKey('FQed3Ay883zUcGcLaubkV56JJbweiYjxPSTC84yUxqNd');

// Connect to the Solana cluster
const connection = new solanaWeb3.Connection(solanaWeb3.clusterApiUrl('mainnet-beta'));

async function getAccountData(account) {
    const accountInfo = await connection.getAccountInfo(account);
    if (accountInfo === null) {
        throw new Error('Failed to find account');
    }
    return accountInfo.data;
}

async function getLiquidityPoolTokenPair() {
    const accountData = await getAccountData(liquidityPoolAccount);

    // Define the structure of the liquidity pool account data
    const layout = BufferLayout.struct([
        BufferLayout.blob(32, 'tokenMintA'), // Token A mint address
        BufferLayout.blob(32, 'tokenMintB'), // Token B mint address
    ]);

    const decodedData = layout.decode(accountData);

    const tokenMintA = new solanaWeb3.PublicKey(decodedData.tokenMintA);
    const tokenMintB = new solanaWeb3.PublicKey(decodedData.tokenMintB);

    return {
        tokenA: tokenMintA.toBase58(),
        tokenB: tokenMintB.toBase58()
    };
}

getLiquidityPoolTokenPair()
    .then(tokenPair => {
        console.log(JSON.stringify(tokenPair));
    })
    .catch(console.error);
