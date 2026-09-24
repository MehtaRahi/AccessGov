from langchain_community.llms import Ollama
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from app.services.vector_store import VectorStoreManager

class RAGPipeline:
    def __init__(self):
        from app.services.llm_provider import get_llm
        self.llm = get_llm()
        
        # Setup Retriever
        self.vector_store = VectorStoreManager().vector_store
        if self.vector_store is not None:
            self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        else:
            self.retriever = None
        
    def query(self, user_query: str, mode: str = "normal", chat_history: list = None, detail: str = "auto") -> str:
        if not self.retriever:
            return "Error: Database is offline. Cannot retrieve context."

        if chat_history is None:
            chat_history = []
            
        history_str = ""
        for msg in chat_history:
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get('content', '')
            content = content.replace("<div class='tts-button'>▶ Play Audio (Text-to-Speech)</div>", "").strip()
            history_str += f"{role}: {content}\n"

        # 1. Fallback for Greetings / Typos
        is_greeting = False
        lower_query = user_query.lower().strip()
        greetings = ["hi", "hello", "hey", "thanks", "thank you", "hwy"]
        if len(lower_query.split()) <= 3 and any(g in lower_query for g in greetings):
            is_greeting = True

        # 2. Detail Heuristic
        if detail == "auto":
            detail_keywords = ["list", "steps", "explain", "detail", "many", "options", "how to"]
            if any(k in lower_query for k in detail_keywords) or len(user_query.split()) > 12:
                detail = "detailed"
            else:
                detail = "brief"

        # 3. System Prompt Construction
        if is_greeting:
            system_prompt = (
                "You are AccessGov, a friendly AI assistant for government services. "
                "The user is just greeting you or saying something brief. Respond conversationally and warmly. "
                "Do NOT provide random legal facts. Keep it short."
            )
        else:
            system_prompt = (
                "You are AccessGov, an AI assistant for government services. "
                "Answer the user's question accurately using ONLY the provided context. "
                "Do NOT use generic prefixes like 'Based on the context, I can answer your question.' Start your answer directly. "
                "CRITICAL: If the retrieved context contains conflicting information or multiple versions of a policy, you MUST act as a conflict-resolution judge. Analyze dates, timestamps, or version numbers within the context to prioritize the most recent information. Explicitly inform the user if an older policy was superseded by a newer one. "
                "If the answer is not in the context, say you don't know and do not guess.\n\n"
            )
            
            if detail == "detailed":
                system_prompt += (
                    "The user has asked a detailed question. Provide a comprehensive, structured response. "
                    "You MUST use proper markdown formatting. Ensure that every single bullet point or numbered step is placed on a completely NEW LINE (e.g., '1. Step one\\n2. Step two'). Do not scrunch steps together in a single paragraph.\n\n"
                )
            else:
                system_prompt += (
                    "Provide a brief, concise answer (1-3 sentences). Do not list out all options unless explicitly requested.\n\n"
                )
            
            system_prompt += "Context:\n{context}\n\n"
            
            if history_str:
                system_prompt += f"Recent Conversation History:\n{history_str}\n\n"
        
        if mode == "eli5":
            system_prompt += "Explain your answer in very simple terms, like explaining to a 5-year-old. Completely avoid jargon.\n"
        elif mode == "wizard":
            system_prompt += "Act like an interactive wizard guiding the user through a process. End your response by asking the next logical step.\n"
            
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        
        if is_greeting:
            # Bypass retrieval for greetings
            chain = prompt | self.llm
            response = chain.invoke({"input": user_query})
            if hasattr(response, "content"):
                return response.content
            return str(response)
        else:
            # Full RAG chain
            question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
            chain = create_retrieval_chain(self.retriever, question_answer_chain)
            response = chain.invoke({"input": user_query})
            return response.get("answer", "No answer generated.")
