from langchain_core.documents import Document
from doc_extractor.feature_extractor import generate_document_features

class ParserException(Exception):
    """Exception raised when parsing document content fails."""
    pass

class DocumentException(Exception):
    """Exception raised when document extraction fails."""
    pass

from .parser import parser


class DocExtractor:
    def __init__(self):
        self.parser = parser
        
    def split_docs_by_separator(self, parsed_results, separator="\n---\n"):
        """Split docs into sub-documents based on a separator."""
        sub_docs = []
        doc_chunks = parsed_results.split(separator)
        for doc_chunk in doc_chunks:
            sub_doc = Document(
                page_content=doc_chunk,
                metadata={}
            )
            sub_docs.append(sub_doc)

        return sub_docs


    async def extract_text(self, file):
            parsed_data = await self.parser.load_data(file)
            if "parsed_content" not in parsed_data:
                raise ParserException(f"Parsing failed {parsed_data['details']}")
            
            parsed_text = parsed_data["parsed_content"]
            return parsed_text
      

    async def extract(self, file):
        try:
            parsed_text = await self.extract_text(file)
            docs = self.split_docs_by_separator(parsed_text)
            features = generate_document_features(docs)
            return features , parsed_text
        except ParserException:
            raise
        except Exception as e:
            raise DocumentException(f"Failed to extract text: {str(e)}")
