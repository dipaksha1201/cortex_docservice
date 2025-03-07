from pinecone import Pinecone, ServerlessSpec
from doc_extractor._utils import gemini_embeddings
from langchain_pinecone import PineconeVectorStore
import os

def get_pinecone_index(index_name: str):
    pinecone_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    return pinecone_client.Index(index_name)

def index_documents(user_id: str, document_id: str, documents: list):
    # Initialize the embedding model
    embeddings = gemini_embeddings
    
    # Add 'source' metadata to each document
    for doc in documents:
        if 'metadata' not in doc:
            doc.metadata = {}
        doc.metadata['source'] = document_id

    # Connect to the existing Pinecone index
    index = get_pinecone_index('cortex-pinecone-index')

    # Create a PineconeVectorStore instance
    vectorstore = PineconeVectorStore(index=index, embedding=embeddings, namespace=user_id)

    # Add documents to the vector store
    vectorstore.add_documents(documents)
    
def delete_document(user_id: str, document_ids: list):
    print("Deleting document from Pinecone")
    print(document_ids)
    print(user_id)
    index = get_pinecone_index('cortex-pinecone-index')
    index.delete(ids=document_ids , namespace=user_id)
    print("Document deleted successfully")
    return True
    
def retrieve_documents(user_id: str, query: str, top_k: int = 5):
    # Initialize the embedding model
    embeddings = gemini_embeddings
    # Connect to the existing Pinecone index
    index = get_pinecone_index('cortex-pinecone-index')
    # Create a Pinecone vector store instance
    vector_store = PineconeVectorStore(index=index, embedding=embeddings, namespace=user_id)

    # Perform a similarity search within the specified namespace
    results = vector_store.similarity_search_with_relevance_scores(query, k=top_k, namespace=user_id)

    return results  