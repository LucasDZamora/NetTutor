from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os

class RAGService:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3"),
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        self.vectorstore = Chroma(
            persist_directory=os.getenv("CHROMA_DB_DIR"),
            embedding_function=self.embeddings
        )

    def get_knowledge(self, query: str, topic: str = None):
        """
        Recupera fragmentos técnicos. Si el Agente detectó un tópico, 
        podemos filtrar por metadata.
        """
        search_kwargs = {"k": 4}
        if topic and topic != "unknown":
            search_kwargs["filter"] = {"topic": topic}

        # Usamos MMR para diversidad de información técnica
        docs = self.vectorstore.max_marginal_relevance_search(
            query, 
            **search_kwargs
        )
        
        return "\n\n".join([d.page_content for d in docs])