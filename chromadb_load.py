import chromadb, os
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path='./chroma_db')
col = client.get_or_create_collection('day09_docs', metadata={"hnsw:space": "cosine"})
model = SentenceTransformer('AITeamVN/Vietnamese_Embedding')

docs_dir = './data/docs'

texts = []
metadatas = []
ids = []

for fname in os.listdir(docs_dir):
    if not fname.endswith('.txt'): continue
    with open(os.path.join(docs_dir, fname), encoding='utf-8') as f:
        content = f.read()
    
    # Simple chunking by paragraphs for demonstration
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    for i, p in enumerate(paragraphs):
        texts.append(p)
        metadatas.append({"source": fname})
        ids.append(f"{fname}_chunk{i}")

print(f"Embedding {len(texts)} chunks...")
embeddings = model.encode(texts).tolist()

print("Adding to ChromaDB...")
col.add(
    documents=texts,
    embeddings=embeddings,
    metadatas=metadatas,
    ids=ids
)
print('Index ready.')