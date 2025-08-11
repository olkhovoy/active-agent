import os
import csv
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List

# Import from orchestrator
from orchestrator import load_config, LLMClient, QdrantRAG, DataIngestionAgent, ClaimExtractionAgent, EvidenceRetrievalAgent, VerificationAgent, ScoringAgent

GITHUB_API = "https://api.github.com"
HEADERS = {
    'Accept': 'application/vnd.github+json'
}
if os.getenv('GITHUB_TOKEN'):
    HEADERS['Authorization'] = f"token {os.getenv('GITHUB_TOKEN')}"

# Expanded repo map (EVM-heavy blue chips)
REPOS = {
    'Uniswap': 'Uniswap/uniswap-v3-core',
    'Aave': 'aave/aave-v3-core',
    'Compound': 'compound-finance/compound-protocol',
    'MakerDAO': 'makerdao/dss',
    'Curve': 'curvefi/curve-contract',
    'Synthetix': 'Synthetixio/synthetix',
    'Yearn': 'yearn/yearn-vaults',
    'Balancer': 'balancer-labs/balancer-v2-monorepo',
    'Lido': 'lidofinance/lido-dao',
    'RocketPool': 'rocket-pool/rocketpool',
    'Sushi': 'sushiswap/sushiswap',
    'PancakeSwap': 'pancakeswap/pancake-smart-contracts',
    '1inch': '1inch/limit-order-protocol',
    'Frax': 'FraxFinance/frax-solidity',
    'GMX': 'GMX-io/gmx-synthetics',
    'dYdX': 'dydxprotocol/v4-chain',
}


def fetch_repo_context(full_repo: str, months_back: int = 2) -> str:
    repo_url = f"{GITHUB_API}/repos/{full_repo}"
    r = requests.get(repo_url, headers=HEADERS)
    if r.status_code != 200:
        return f"Repo {full_repo} fetch error: {r.status_code}"
    repo = r.json()
    description = repo.get('description') or ''

    cutoff = datetime.utcnow() - timedelta(days=months_back*30)
    commits_url = f"{repo_url}/commits"
    params = {'per_page': 50}
    commits = []
    try:
        rc = requests.get(commits_url, headers=HEADERS, params=params)
        if rc.status_code == 200:
            for c in rc.json():
                date = c.get('commit',{}).get('author',{}).get('date')
                msg = c.get('commit',{}).get('message','')
                if date:
                    try:
                        dt = datetime.fromisoformat(date.replace('Z','+00:00'))
                        if dt >= cutoff:
                            commits.append(msg.strip())
                    except Exception:
                        continue
    except Exception:
        pass

    lines = [f"# {full_repo}", '', f"Description: {description}", '', 'Recent commits:', '']
    for m in commits[:20]:
        lines.append(f"- {m}")
    return '\n'.join(lines)


def ensure_docs(root: str, projects: Dict[str,str]) -> Dict[str,str]:
    os.makedirs(root, exist_ok=True)
    paths = {}
    for name, repo in projects.items():
        text = fetch_repo_context(repo)
        pdir = os.path.join(root, name)
        os.makedirs(pdir, exist_ok=True)
        path = os.path.join(pdir, 'context.md')
        with open(path, 'w') as f:
            f.write(text)
        paths[name] = pdir
        time.sleep(0.2)
    return paths


def run_batch(project_dirs: Dict[str,str], cfg_path: str = 'config.yaml') -> List[Dict]:
    cfg = load_config(cfg_path)
    llm = LLMClient()
    rag = QdrantRAG(cfg)  # will fallback to local docs if Qdrant not running

    extraction = ClaimExtractionAgent('prompts/claim_extraction.md', llm)
    verify = VerificationAgent('prompts/verification.md', llm)
    scoring = ScoringAgent('prompts/scoring.md', llm)

    results = []
    for name, pdir in project_dirs.items():
        ingestion = DataIngestionAgent(pdir)
        bundle = ingestion.run(name)
        claims = extraction.run(bundle['docs'])
        retrieval = EvidenceRetrievalAgent(rag, top_k=cfg.get('retrieval',{}).get('top_k',8))
        items = retrieval.run(claims, bundle['docs'])
        verif = verify.run(items)
        scores = scoring.run(verif)
        coh = scores.get('coherence')
        sti = scores.get('stimulation')
        conf = scores.get('confidence', 0.6)
        recommend = (coh is not None and sti is not None and coh >= 65 and sti >= 60 and conf >= 0.55)
        results.append({
            'project': name,
            'num_docs': len(bundle['docs']),
            'num_claims': len(claims),
            'coherence': coh,
            'stimulation': sti,
            'confidence': conf,
            'recommend': int(recommend),
        })
    return results


def write_csv(path: str, rows: List[Dict]):
    if not rows:
        return
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main():
    root = './batch_samples'
    project_dirs = ensure_docs(root, REPOS)
    rows = run_batch(project_dirs)
    out_csv = './batch_results.csv'
    write_csv(out_csv, rows)
    print('Batch results:')
    for r in rows:
        print(r)
    print(f'CSV saved to {out_csv}')


if __name__ == '__main__':
    main()
