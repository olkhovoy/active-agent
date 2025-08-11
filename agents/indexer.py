import argparse
import os
import yaml
from typing import List
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer


def load_config(path: str) -> dict:
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def ensure_collection(client: QdrantClient, collection: str, dim: int):
    if collection not in [c.name for c in client.get_collections().collections]:
        client.create_collection(collection_name=collection, vectors_config=VectorParams(size=dim, distance=Distance.COSINE))


def iter_files(root: str) -> List[str]:
    docs = []
    for r, _, files in os.walk(root):
        for fn in files:
            if fn.endswith(('.txt', '.md')):
                path = os.path.join(r, fn)
                with open(path, 'r', errors='ignore') as f:
                    text = f.read()
                    if text.strip():
                        docs.append((path, text[:5000]))
    return docs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default='config.yaml')
    ap.add_argument('--collection', default=None)
    ap.add_argument('--source', required=True)
    args = ap.parse_args()

    cfg = load_config(args.config)
    collection = args.collection or cfg['qdrant']['collection']

    embed_model = cfg.get('embedding_model', 'BAAI/bge-m3')
    encoder = SentenceTransformer(embed_model)
    dim = encoder.get_sentence_embedding_dimension()

    client = QdrantClient(url=cfg['qdrant']['url'])
    ensure_collection(client, collection, dim)

    docs = iter_files(args.source)
    if not docs:
        print('No documents found')
        return

    payloads = []
    vectors = []
    points = []
    for idx, (path, text) in enumerate(docs):
        vec = encoder.encode(text)
        vectors.append(vec)
        payloads.append({"path": path, "text": text})
        points.append(PointStruct(id=idx, vector=vec, payload=payloads[-1]))

    client.upsert(collection_name=collection, points=points)
    print(f'Indexed {len(points)} docs into collection {collection}')


if __name__ == '__main__':
    main()
