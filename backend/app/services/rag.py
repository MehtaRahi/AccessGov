from langchain_community.llms import Ollama
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from app.services.vector_store import VectorStoreManager

class RAGPipeline:
    def __init__(self):
        # We will use Ollama with the llama3 model for generation
        self.llm = Ollama(model="llama3")
        
        # Setup Retriever
        self.vector_store = VectorStoreManager().vector_store
        if self.vector_store:
            self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        else:
            self.retriever = None
        
    def query(self, user_query: str, mode: str = "normal") -> str:
        if not self.retriever:
            return "Error: Database is offline. Cannot retrieve context."

        system_prompt = (
            "You are AccessGov, an AI assistant for government services. "
            "Use the following context to answer the question. If the answer is not in the context, say you don't know.\n\n"
            "Context:\n{context}\n\n"
        )
        
        if mode == "eli5":
            system_prompt += "Explain your answer in very simple terms, like explaining to a 5-year-old. Completely avoid jargon.\n"
        elif mode == "wizard":
            system_prompt += "Act like an interactive wizard guiding the user through a process. End your response by asking the next logical step.\n"
            
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        
        question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
        chain = create_retrieval_chain(self.retriever, question_answer_chain)
        
        response = chain.invoke({"input": user_query})
        return response.get("answer", "No answer generated.")
