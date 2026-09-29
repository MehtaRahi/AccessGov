import logging
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(self):
        self.llm = None
        self.retriever = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization - only connect to services on first query."""
        if self._initialized:
            return
        
        try:
            from app.services.llm_provider import get_llm
            self.llm = get_llm()
            logger.info("✅ LLM provider initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM: {e}")
            self.llm = None
        
        try:
            from app.services.vector_store import VectorStoreManager
            vector_store = VectorStoreManager().vector_store
            if vector_store is not None:
                self.retriever = vector_store.as_retriever(search_kwargs={"k": 3})
            logger.info("✅ Vector store connected successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to connect to vector store: {e}")
            self.retriever = None

        self._initialized = True
        
    def query(self, user_query: str, mode: str = "normal", chat_history: list = None, detail: str = "auto") -> str:
        self._ensure_initialized()

        if not self.llm:
            return "Error: The AI model is not available. Please check the server configuration."

        if chat_history is None:
            chat_history = []
            
        history_str = ""
        for msg in chat_history:
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get('content', '')
            content = content.replace("<div class='tts-button'>▶ Play Audio (Text-to-Speech)</div>", "").strip()
            history_str += f"{role}: {content}\n"

        # 1. Detect greetings FIRST (these don't need the vector store)
        is_greeting = False
        lower_query = user_query.lower().strip()
        greetings = ["hi", "hello", "hey", "thanks", "thank you", "hwy", "good morning", "good evening"]
        if len(lower_query.split()) <= 3 and any(g in lower_query for g in greetings):
            is_greeting = True

        # 2. Handle greetings immediately — no retriever needed
        if is_greeting:
            system_prompt = (
                "You are AccessGov, a friendly AI assistant for government services. "
                "The user is just greeting you or saying something brief. Respond conversationally and warmly. "
                "Do NOT provide random legal facts. Keep it short."
            )
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{input}"),
            ])
            try:
                chain = prompt | self.llm
                response = chain.invoke({"input": user_query})
                if hasattr(response, "content"):
                    return response.content
                return str(response)
            except Exception as e:
                logger.error(f"Greeting query failed: {e}")
                return "Hello! I'm AccessGov, your government services assistant. How can I help you today?"

        # 3. For knowledge queries, we NEED the retriever
        if not self.retriever:
            return "Error: The knowledge database is offline. Please try again later."

        # 4. Detail Heuristic
        if detail == "auto":
            detail_keywords = ["list", "steps", "explain", "detail", "many", "options", "how to"]
            if any(k in lower_query for k in detail_keywords) or len(user_query.split()) > 12:
                detail = "detailed"
            else:
                detail = "brief"

        # 5. System Prompt for knowledge queries (greetings already handled above)
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
            system_prompt += "Recent Conversation History:\n{chat_history}\n\n"
        
        if mode == "eli5":
            system_prompt += "Explain your answer in very simple terms, like explaining to a 5-year-old. Completely avoid jargon.\n"
        elif mode == "wizard":
            system_prompt += "Act like an interactive wizard guiding the user through a process. End your response by asking the next logical step.\n"
            
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        
        try:
            question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
            chain = create_retrieval_chain(self.retriever, question_answer_chain)
            response = chain.invoke({"input": user_query, "chat_history": history_str})
            return response.get("answer", "No answer generated.")
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return f"I encountered an error processing your request. Please try again. (Error: {str(e)[:100]})"

