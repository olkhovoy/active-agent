import argparse
import json
import os
import yaml
from typing import List, Dict

from tenacity import retry, stop_after_attempt, wait_exponential
from openai import OpenAI

from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer


def load_config(path: str) -> dict:
    with open(path, 'r') as f:
        return yaml.safe_load(f)

class LLMClient:
    def __init__(self):
        base = os.getenv('OPENAI_API_BASE', 'http://127.0.0.1:8000/v1')
        key = os.getenv('OPENAI_API_KEY', 'local-any')
        self.model = os.getenv('OPENAI_MODEL', 'Qwen/Qwen2.5-7B-Instruct')
        self.client = OpenAI(base_url=base, api_key=key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def complete_json(self, system: str, user: str) -> dict:
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.2,
            )
            txt = resp.choices[0].message.content.strip()
            if '```' in txt:
                txt = txt.split('```')[1]
                if txt.lower().startswith('json'):
                    txt = txt.split('\n', 1)[1]
            return json.loads(txt)
        except Exception:
            return {}

class QdrantRAG:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.encoder = SentenceTransformer(cfg.get('embedding_model', 'BAAI/bge-m3'), device='cpu')
        url = cfg['qdrant']['url']
        self.collection = cfg['qdrant']['collection']
        try:
            self.client = QdrantClient(url=url)
            _ = self.client.get_collections()
            self.available = True
        except Exception:
            self.client = None
            self.available = False

    def search(self, query: str, top_k: int) -> List[Dict]:
        if not self.available:
            return []
        vec = self.encoder.encode(query, convert_to_numpy=True, normalize_embeddings=True)
        res = self.client.search(collection_name=self.collection, query_vector=vec.tolist(), limit=top_k)
        snippets = []
        for hit in res:
            payload = hit.payload or {}
            text = payload.get('text', '')
            path = payload.get('path', '')
            if text:
                snippets.append({"text": text[:2000], "path": path, "score": hit.score})
        return snippets

class DataIngestionAgent:
    def __init__(self, sources_dir: str):
        self.sources_dir = sources_dir
    def run(self, project: str) -> Dict[str, List[str]]:
        docs = []
        if os.path.isdir(self.sources_dir):
            for root, _, files in os.walk(self.sources_dir):
                for fn in files:
                    if fn.endswith(('.txt','.md')):
                        with open(os.path.join(root, fn), 'r', errors='ignore') as f:
                            docs.append(f.read()[:5000])
        return {"project": project, "docs": docs}

class ClaimExtractionAgent:
    def __init__(self, prompt_path: str, llm: LLMClient):
        self.prompt = open(prompt_path, 'r').read()
        self.llm = llm
    def run(self, docs: List[str]) -> List[Dict]:
        joined = '\n\n'.join(docs)[:12000]
        result = {}
        try:
            result = self.llm.complete_json(system=self.prompt, user=joined)
        except Exception:
            result = {}
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and 'claims' in result:
            return result['claims']
        claims = []
        for i, d in enumerate(docs):
            if len(d) > 40:
                claims.append({"claim_id": f"c{i}", "statement": d.split('\n')[0][:140], "timeframe": "TBD", "evidence_type": "repo|onchain|news"})
        return claims[:10]

class EvidenceRetrievalAgent:
    def __init__(self, rag: QdrantRAG, top_k: int = 8):
        self.rag = rag
        self.top_k = top_k
    def run(self, claims: List[Dict], local_corpus: List[str]) -> List[Dict]:
        items = []
        for c in claims:
            q = c.get('statement','')
            snippets = self.rag.search(q, self.top_k) if q else []
            if not snippets:
                snippets = [{"text": d[:2000], "path": "local"} for d in local_corpus[:self.top_k]]
            items.append({"claim": c, "evidence": snippets})
        return items

class VerificationAgent:
    def __init__(self, prompt_path: str, llm: LLMClient):
        self.prompt = open(prompt_path, 'r').read()
        self.llm = llm
    def run(self, items: List[Dict]) -> List[Dict]:
        results = []
        for it in items:
            claim = it['claim']
            ev_text = '\n\n'.join([e['text'] for e in it['evidence']])[:12000]
            payload = {"claim": claim, "evidence": ev_text}
            res = {}
            try:
                res = self.llm.complete_json(system=self.prompt, user=json.dumps(payload, ensure_ascii=False))
            except Exception:
                res = {}
            if not res:
                res = {"label": "neutral", "score": 0.5, "rationale": "short", "evidence_used": []}
            results.append({"claim": claim, **res})
        return results

class ScoringAgent:
    def __init__(self, prompt_path: str, llm: LLMClient):
        self.prompt = open(prompt_path, 'r').read()
        self.llm = llm
    def _to_int_score(self, value, default: int = 50) -> int:
        try:
            if isinstance(value, (int, float)):
                v = int(round(float(value)))
            elif isinstance(value, str) and value.strip():
                v = int(round(float(value.strip())))
            else:
                v = default
        except Exception:
            v = default
        return max(0, min(100, v))
    def _to_float_conf(self, value, default: float = 0.6) -> float:
        try:
            if isinstance(value, (int, float)):
                v = float(value)
            elif isinstance(value, str) and value.strip():
                v = float(value.strip())
            else:
                v = default
        except Exception:
            v = default
        return max(0.0, min(1.0, v))
    def run(self, verif: List[Dict], aux: Dict = None) -> Dict:
        aux = aux or {}
        payload = {"verifications": verif, **aux}
        res = {}
        try:
            res = self.llm.complete_json(system=self.prompt, user=json.dumps(payload, ensure_ascii=False))
        except Exception:
            res = {}
        coh = self._to_int_score(res.get('coherence'), 50)
        sti = self._to_int_score(res.get('stimulation'), 55)
        conf = self._to_float_conf(res.get('confidence'), 0.6)
        explanations = res.get('explanations') or {"coherence": "short", "stimulation": "short"}
        return {"coherence": coh, "stimulation": sti, "confidence": conf, "explanations": explanations}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default='config.yaml')
    ap.add_argument('--project', required=True)
    ap.add_argument('--sources', default='./demo_samples')
    args = ap.parse_args()

    cfg = load_config(args.config)

    llm = LLMClient()
    rag = QdrantRAG(cfg)

    ingestion = DataIngestionAgent(args.sources)
    extraction = ClaimExtractionAgent('prompts/claim_extraction.md', llm)
    retrieval = EvidenceRetrievalAgent(rag, top_k=cfg.get('retrieval',{}).get('top_k',8))
    verify = VerificationAgent('prompts/verification.md', llm)
    scoring = ScoringAgent('prompts/scoring.md', llm)

    bundle = ingestion.run(args.project)
    claims = extraction.run(bundle['docs'])
    items = retrieval.run(claims, bundle['docs'])
    verif = verify.run(items)
    scores = scoring.run(verif)

    print(json.dumps({"project": args.project, "num_docs": len(bundle['docs']), "num_claims": len(claims), "scores": scores}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
