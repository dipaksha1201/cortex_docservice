from pydantic import BaseModel, Field
from typing import List
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from doc_extractor._utils import gemini_flash

class DocumentFeatures(BaseModel):
    summary: str = Field(description="A comprehensive summary of the document in 10-15 lines covering its core content and important sections.")
    highlights: List[str] = Field(description="Five key highlights from the document.")
    document_type: str = Field(description="A one-word descriptor indicating the type of document.")
    domain: str = Field(description="Construct a 2-3 lines of domain text from the document. This will be used to understand the domain of the document.")
    queries: List[str] = Field(description="A list of 5-10 example queries that are relevant to the document.")
    entity_types: List[str] = Field(description="A list of entity types that are relevant to the document.")

prompt_template = PromptTemplate(
    template="""You are an expert summarizer. Using the document below,
please produce a structured output with the requested information.

Document:
{combined_text}
""",
    input_variables=["combined_text"]
)

def generate_document_features(documents: List[Document], llm: any = gemini_flash) -> DocumentFeatures:
    """
    Combines a list of documents, sends them to the LLM with structured output instructions,
    and returns a DocumentFeatures object containing all the features defined in DocumentFeatures.
    
    Parameters:
        documents (List[Document]): List of documents to analyze.
        llm (any): An instantiated LLM (or any compatible model) from LangChain.
    
    Returns:
        DocumentFeatures: A structured output object with all the document features.
    """
    combined_text = "\n\n".join([doc.page_content for doc in documents])
    
    model = llm.with_structured_output(DocumentFeatures)
    formatted_prompt = prompt_template.format(combined_text=combined_text)
    response = model.invoke(formatted_prompt)
    return response