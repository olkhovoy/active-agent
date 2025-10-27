import os
import csv
import json
import requests
import sys
from typing import Dict, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from orchestrator import LLMClient

ETHERSCAN_API = os.getenv('ETHERSCAN_API_KEY')
ETHERSCAN_URL = 'https://api.etherscan.io/api'


def get_token_transfers(contract: str, max_pages: int = 2) -> Dict:
    if not ETHERSCAN_API:
        return {'holders_estimate': None, 'tx_sample': []}
    txs = []
    page = 1
    while page <= max_pages:
        params = {
            'module': 'account',
            'action': 'tokentx',
            'contractaddress': contract,
            'page': page,
            'offset': 100,
            'sort': 'desc',
            'apikey': ETHERSCAN_API
        }
        r = requests.get(ETHERSCAN_URL, params=params, timeout=30)
        if r.status_code != 200:
            break
        data = r.json()
        if data.get('status') != '1' or not data.get('result'):
            break
        txs.extend(data['result'])
        page += 1
    # rough holder estimate from unique addresses in sample
    addrs = set()
    for t in txs:
        addrs.add(t['from'])
        addrs.add(t['to'])
    return {'holders_estimate': len(addrs) if addrs else None, 'tx_sample': txs[:200]}


def llm_assess(llm: LLMClient, name: str, symbol: str, contract: str, market_cap: float, fdv: float, volume: float, holders_estimate: int) -> Dict:
    sys = (
        "You are a risk analyst. Classify an ERC-20 token on reliability vs. scamminess. "
        "Output JSON with numeric values: {\"label\":\"investable|neutral|avoid\", \"reliability\":0.0-1.0, \"risk\":0.0-1.0, \"rationale\":\"brief explanation\"}"
    )
    user = json.dumps({
        'token': {'name': name, 'symbol': symbol, 'contract': contract},
        'market': {'market_cap_usd': market_cap, 'fdv_usd': fdv, 'volume_24h_usd': volume},
        'onchain_sample': {'holders_estimate': holders_estimate}
    }, ensure_ascii=False)
    res = llm.complete_json(system=sys, user=user) or {}
    
    # Parse and validate output
    label = res.get('label', 'review')
    if label not in ['investable', 'neutral', 'avoid']:
        label = 'review'
    
    # Handle reliability field
    reliability_raw = res.get('reliability')
    try:
        reliability = float(reliability_raw) if reliability_raw is not None else 0.5
        reliability = max(0.0, min(1.0, reliability))  # clamp to 0-1
    except (ValueError, TypeError):
        reliability = 0.5
    
    # Handle risk field  
    risk_raw = res.get('risk')
    try:
        risk = float(risk_raw) if risk_raw is not None else 0.5
        risk = max(0.0, min(1.0, risk))  # clamp to 0-1
    except (ValueError, TypeError):
        risk = 0.5
    
    rationale = res.get('rationale', 'Assessment completed')
    
    return {
        'label': label,
        'reliability': reliability,
        'risk': risk,
        'rationale': rationale
    }


def main():
    base = os.path.dirname(__file__)
    inp = os.path.join(base, 'erc20_top20.csv')
    out = os.path.join(base, 'erc20_eval.jsonl')
    if not os.path.exists(inp):
        raise SystemExit('Run top20_fetch.py first')

    llm = LLMClient()

    rows = list(csv.DictReader(open(inp)))
    with open(out, 'w') as f:
        for r in rows:
            name = r['name']; symbol = r['symbol']; contract = r['contract']
            market_cap = float(r['market_cap_usd'] or 0)
            fdv = float(r['fdv_usd'] or 0)
            volume = float(r['volume_24h_usd'] or 0)
            onchain = get_token_transfers(contract)
            holders = onchain.get('holders_estimate')
            assessment = llm_assess(llm, name, symbol, contract, market_cap, fdv, volume, holders or 0)
            record = {
                'name': name,
                'symbol': symbol,
                'contract': contract,
                'market_cap_usd': market_cap,
                'fdv_usd': fdv,
                'volume_24h_usd': volume,
                'holders_estimate': holders,
                **assessment
            }
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(f'Saved assessments to {out}')


if __name__ == '__main__':
    main()
