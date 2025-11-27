from src.vector_db.qdrant_client import LocalVectorDB
import uuid
import random

db = LocalVectorDB(dim=384)

# 1) create fake embeddings
ids = [str(uuid.uuid4()) for _ in range(3)]
embeddings = [[random.random() for _ in range(384)] for _ in range(3)]
metas = [{"text": f"doc {i}"} for i in range(3)]

print("Inserting...")
db.upsert_documents(ids, embeddings, metas)

print("Searching...")
query = embeddings[0]   # best match should be itself
results = db.search_vector(query, top_k=3)

print("\nResults:")
for r in results:
    print(r)
