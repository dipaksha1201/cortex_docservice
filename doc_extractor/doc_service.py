import logging
from typing import List, Literal
from api.mongodb import MongoDBConfig
from doc_extractor.models import Document
from bson.objectid import ObjectId

# Configure a logger for this module.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self):
        # In-memory store for conversations; replace with a persistent store in production.
        db_config = MongoDBConfig()
        self.db = db_config.connect()
        logger.info("DocumentService initialized and database connected.")

    def insert_document(self, document: Document) -> Document:
        # Insert into MongoDB 'documents' collection
        result = self.db["documents"].insert_one(document.model_dump())
        # Assign the generated _id to the document dict
        document.id = str(result.inserted_id)
        # Return a new Document instance with the inserted data
        return document

    def update_status(self, document_id: str, status: Literal["extracting", "understanding", "completed"]) -> Document:
        result = self.db["documents"].find_one_and_update(
            {"_id": ObjectId(document_id)},
            {"$set": {"status": status}},
            return_document=True
        )
        if not result:
            raise ValueError(f"Document with id {document_id} not found")
        return Document(**result)

    def get_user_documents(self, user_id: str) -> List[Document]:
        """Retrieve all conversations for a specific user."""
        logger.info("Retrieving conversations for user_id: %s", user_id)
        # Query the database for conversations that match the given user_id.
        documents = self.db["documents"].find({"user_id": user_id})
        conversations = [Document(**doc) for doc in documents]
        logger.info("Found %d conversations for user '%s'", len(conversations), user_id)
        return conversations