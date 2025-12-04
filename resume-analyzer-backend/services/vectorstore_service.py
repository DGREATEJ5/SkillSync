# services/vectorstore_service.py

import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")

HF_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY

# Embedding model
embed_model = HuggingFaceEmbeddings(model_name=HF_MODEL)

# Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)
existing_indexes = pc.list_indexes().names()

# Create index if missing
if PINECONE_INDEX not in existing_indexes:
    print(f"Creating index '{PINECONE_INDEX}'...")
    pc.create_index(
        name=PINECONE_INDEX,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=PINECONE_ENV)
    )
else:
    print(f"Index '{PINECONE_INDEX}' exists.")

# Connect to index
index = pc.Index(PINECONE_INDEX)

# Vectorstore connection
vectorstore = PineconeVectorStore.from_existing_index(
    index_name=PINECONE_INDEX,
    embedding=embed_model
)

# Improved chunker 
chunker = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=30
)


class VectorStoreService:
    """Improved search with hybrid scoring and normalization."""

    def __init__(self):
        self.vectorstore = vectorstore
        self.chunker = chunker
        self.index = index
        self.embed_model = embed_model

    def build_index(self, docs: list):
        stats = self.index.describe_index_stats()
        count = stats.get("total_vector_count", 0)

        if count > 0:
            print("Index already has data. Skipping embedding.")
            return

        print("Inserting job documents into Pinecone...")

        documents = []
        for d in docs:
            chunks = self.chunker.split_text(d["content"])

            # For very short job descriptions, don't chunk
            if len(chunks) == 1:
                documents.append(Document(page_content=chunks[0], metadata=d))
            else:
                for c in chunks:
                    documents.append(Document(page_content=c, metadata=d))

        self.vectorstore.add_documents(documents)
        print("Indexing complete.")

    def _keyword_score(self, query, job):
        """Reward exact keyword / skill overlap."""
        q = query.lower()
        score = 0

        # Count keyword hits from skills
        for skill in job.get("skills", []):
            if skill.lower() in q:
                score += 1

        return score

    def _normalize(self, score):
        """Convert Pinecone scores to 0–1 range for readability."""
        return max(0, min(1, (score + 1) / 2))

    def query(self, query_text: str, k: int = 3):
        """Hybrid search: semantic + keyword + skill scoring."""

        query_embedding = self.embed_model.embed_query(query_text)

        # Get top 10 first, rerank later
        search_response = self.index.query(
            vector=query_embedding,
            top_k=10,
            include_metadata=True
        )

        ranked = []
        for match in search_response.matches:
            metadata = match.metadata

            semantic = self._normalize(match.score)
            keyword = self._keyword_score(query_text, metadata)

            # Final score (tweakable)
            final_score = (semantic * 0.7) + (keyword * 0.3)

            ranked.append({
                "id": metadata.get("id"),
                "title": metadata.get("title"),
                "description": metadata.get("description"),
                "skills": metadata.get("skills", []),
                "semantic_score": semantic,
                "keyword_score": keyword,
                "final_score": final_score
            })

        # Sort by final score
        ranked = sorted(ranked, key=lambda x: x["final_score"], reverse=True)

        return ranked[:k]
