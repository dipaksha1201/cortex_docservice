from pydantic import BaseModel, Field
from typing import List
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from doc_extractor._utils import gemini_flash
from doc_extractor.models import DocumentFeatures
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