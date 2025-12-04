# services/vectorstore_service.py

import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")

HF_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY

# Load embedding model
embed_model = HuggingFaceEmbeddings(model_name=HF_MODEL)

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)
existing_indexes = pc.list_indexes().names()

# Create index if missing
if PINECONE_INDEX not in existing_indexes:
    print(f"Creating Pinecone index '{PINECONE_INDEX}'...")
    pc.create_index(
        name=PINECONE_INDEX,
        dimension=384,  # embedding dimension for MiniLM-L6-v2
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=PINECONE_ENV)
    )
else:
    print(f"Index '{PINECONE_INDEX}' already exists. Skipping creation.")

# Connect to Pinecone index
index = pc.Index(PINECONE_INDEX)

# Check vector count
stats = index.describe_index_stats()
vector_count = stats.get("total_vector_count", 0)
print(f"Pinecone index contains {vector_count} vectors.")

# Initialize vector store for reading
vectorstore = PineconeVectorStore.from_existing_index(
    index_name=PINECONE_INDEX,
    embedding=embed_model
)

# Text chunker
chunker = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)


class VectorStoreService:
    """Vector store service using HuggingFace embeddings + Pinecone."""

    def __init__(self):
        self.vectorstore = vectorstore
        self.chunker = chunker
        self.index = index
        self.embed_model = embed_model

    def build_index(self, docs: list):
        """Insert documents only if the index is empty."""
        stats = self.index.describe_index_stats()
        count = stats.get("total_vector_count", 0)

        if count > 0:
            print("Index already has data. Skipping embedding.")
            return {"status": "skipped", "message": "Index already contains vectors."}

        print("Index is empty → inserting documents...")

        documents = []
        for d in docs:
            chunks = self.chunker.split_text(d["content"])
            for c in chunks:
                documents.append(Document(page_content=c, metadata=d))

        self.vectorstore.add_documents(documents)

        return {"status": "success", "message": "Documents indexed successfully."}

    def query(self, query_text: str, k: int = 3):
        """
        Return top-k similar documents from Pinecone with similarity scores.
        Each result is a dict:
        {
            "id": ...,
            "title": ...,
            "description": ...,
            "skills": ...,
            "similarity_score": ...
        }
        """

        # Compute embedding for query
        query_embedding = self.embed_model.embed_query(query_text)

        # Query Pinecone directly
        search_response = self.index.query(
            vector=query_embedding,
            top_k=k,
            include_metadata=True,
            include_values=False
        )

        results = []
        for match in search_response.matches:
            metadata = match.metadata
            results.append({
                "id": metadata.get("id"),
                "title": metadata.get("title"),
                "description": metadata.get("description"),
                "skills": metadata.get("skills", []),
                "similarity_score": match.score
            })

        return results
