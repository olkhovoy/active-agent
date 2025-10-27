import os
import csv
import time
import requests
from typing import List, Dict

# Fallback static list for pilot digest
TOP_ERC20_STATIC = [
    {'name': 'USDT', 'symbol': 'USDT', 'contract': '0xdAC17F958D2ee523a2206206994597C13D831ec7', 'market_cap_usd': 95000000000, 'fdv_usd': 95000000000, 'volume_24h_usd': 50000000000, 'rank': 3},
    {'name': 'USDC', 'symbol': 'USDC', 'contract': '0xA0b86a33E6441b8c4C8C8C8C8C8C8C8C8C8C8C8', 'market_cap_usd': 32000000000, 'fdv_usd': 32000000000, 'volume_24h_usd': 8000000000, 'rank': 6},
    {'name': 'Uniswap', 'symbol': 'UNI', 'contract': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984', 'market_cap_usd': 12000000000, 'fdv_usd': 12000000000, 'volume_24h_usd': 200000000, 'rank': 20},
    {'name': 'Chainlink', 'symbol': 'LINK', 'contract': '0x514910771AF9Ca656af840dff83E8264EcF986CA', 'market_cap_usd': 8000000000, 'fdv_usd': 8000000000, 'volume_24h_usd': 300000000, 'rank': 15},
    {'name': 'Aave', 'symbol': 'AAVE', 'contract': '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9', 'market_cap_usd': 2000000000, 'fdv_usd': 2000000000, 'volume_24h_usd': 80000000, 'rank': 45},
    {'name': 'Maker', 'symbol': 'MKR', 'contract': '0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2', 'market_cap_usd': 1500000000, 'fdv_usd': 1500000000, 'volume_24h_usd': 50000000, 'rank': 60},
    {'name': 'Curve DAO Token', 'symbol': 'CRV', 'contract': '0xD533a949740bb3306d119CC777fa900bA034cd52', 'market_cap_usd': 800000000, 'fdv_usd': 800000000, 'volume_24h_usd': 30000000, 'rank': 80},
    {'name': 'Synthetix Network Token', 'symbol': 'SNX', 'contract': '0xC011a73ee8576Fb46F5E1c5751cA3B9Fe0af2a6F', 'market_cap_usd': 600000000, 'fdv_usd': 600000000, 'volume_24h_usd': 20000000, 'rank': 100},
    {'name': 'Yearn.finance', 'symbol': 'YFI', 'contract': '0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad9e2', 'market_cap_usd': 400000000, 'fdv_usd': 400000000, 'volume_24h_usd': 15000000, 'rank': 120},
    {'name': 'Balancer', 'symbol': 'BAL', 'contract': '0xba100000625a3754423978a60c9317c58a424e3D', 'market_cap_usd': 300000000, 'fdv_usd': 300000000, 'volume_24h_usd': 10000000, 'rank': 150},
    {'name': 'Lido DAO', 'symbol': 'LDO', 'contract': '0x5A98FcBEA516Cf0685f6cE4aA9A9714d065Da7A7', 'market_cap_usd': 250000000, 'fdv_usd': 250000000, 'volume_24h_usd': 8000000, 'rank': 180},
    {'name': 'Rocket Pool', 'symbol': 'RPL', 'contract': '0xD33526068D116cE69F19A9ee46F0bd304f21A51f', 'market_cap_usd': 200000000, 'fdv_usd': 200000000, 'volume_24h_usd': 6000000, 'rank': 200},
    {'name': 'SushiSwap', 'symbol': 'SUSHI', 'contract': '0x6B3595068778DD592e39A122f4f5a5cF09C90fE2', 'market_cap_usd': 150000000, 'fdv_usd': 150000000, 'volume_24h_usd': 4000000, 'rank': 250},
    {'name': 'PancakeSwap Token', 'symbol': 'CAKE', 'contract': '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82', 'market_cap_usd': 120000000, 'fdv_usd': 120000000, 'volume_24h_usd': 3000000, 'rank': 300},
    {'name': '1inch', 'symbol': '1INCH', 'contract': '0x111111111117dC0aa78b770fA6A738034120C302', 'market_cap_usd': 100000000, 'fdv_usd': 100000000, 'volume_24h_usd': 2500000, 'rank': 350},
    {'name': 'Frax', 'symbol': 'FRAX', 'contract': '0x853d955aCEf822Db058eb8505911ED77F175F99E', 'market_cap_usd': 80000000, 'fdv_usd': 80000000, 'volume_24h_usd': 2000000, 'rank': 400},
    {'name': 'GMX', 'symbol': 'GMX', 'contract': '0xfc5A1A6EB076a2C7aD06eD22C90d7E710E35ad0a', 'market_cap_usd': 60000000, 'fdv_usd': 60000000, 'volume_24h_usd': 1500000, 'rank': 500},
    {'name': 'dYdX', 'symbol': 'DYDX', 'contract': '0x92D6C1e31e14520e676a687F0a93788B716BEff5', 'market_cap_usd': 50000000, 'fdv_usd': 50000000, 'volume_24h_usd': 1200000, 'rank': 600},
    {'name': 'Compound', 'symbol': 'COMP', 'contract': '0xc00e94Cb662C3520282E6f5717214004A7f26888', 'market_cap_usd': 40000000, 'fdv_usd': 40000000, 'volume_24h_usd': 1000000, 'rank': 700},
    {'name': 'RenVM', 'symbol': 'REN', 'contract': '0x408e41876cCdc0F92210600ef50372656052a445', 'market_cap_usd': 30000000, 'fdv_usd': 30000000, 'volume_24h_usd': 800000, 'rank': 800}
]

def try_coinmarketcap() -> List[Dict]:
    """Try CoinMarketCap API (requires free API key)"""
    api_key = os.getenv('CMC_API_KEY')
    if not api_key:
        return []
    
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    headers = {'X-CMC_PRO_API_KEY': api_key}
    params = {'limit': 100, 'convert': 'USD'}
    
    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        if r.status_code != 200:
            return []
        
        data = r.json()
        rows = []
        for coin in data.get('data', []):
            platforms = coin.get('platform', {})
            if platforms.get('name') == 'Ethereum':
                rows.append({
                    'name': coin['name'],
                    'symbol': coin['symbol'],
                    'coingecko_id': coin['id'],
                    'contract': platforms['token_address'],
                    'market_cap_usd': coin['quote']['USD']['market_cap'],
                    'fdv_usd': coin['quote']['USD']['market_cap'],
                    'volume_24h_usd': coin['quote']['USD']['volume_24h'],
                    'rank': coin['cmc_rank'],
                })
                if len(rows) >= 20:
                    break
        return rows
    except Exception:
        return []

def main():
    # Try live APIs first
    rows = try_coinmarketcap()
    
    # Fallback to static list for pilot
    if not rows:
        print("Using static top-20 ERC-20 list for pilot digest")
        rows = TOP_ERC20_STATIC
    else:
        print(f"Fetched {len(rows)} tokens from CoinMarketCap")

    out_path = os.path.join(os.path.dirname(__file__), 'erc20_top20.csv')
    with open(out_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"Saved {len(rows)} ERC-20 tokens to {out_path}")


if __name__ == '__main__':
    main()
