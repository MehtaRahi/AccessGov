# Shifting to an API-Based Chat architecture

Migrating a local or monolithic chat application to an API-based architecture (like FastAPI + React/Next.js) is a huge step for scalability. Based on what we implemented in this Architectural Assistant project, here is a step-by-step checklist to help you transition your other RAG project.

## 1. Define Strict Data Models (Backend)
When moving to an API, you must clearly define what data is coming **in** and what data is going **out**. Use `pydantic` in Python.

```python
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Incoming Request
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    query: str
    history: List[ChatMessage] = []
    # Include any extra context your RAG needs (e.g., current document being viewed)
    context_data: Optional[Dict[str, Any]] = None 

# Outgoing Response
class ChatResponse(BaseModel):
    response_text: str
    sources_retrieved: List[str] = []
    # Add any structured data the frontend needs to render (like our layout JSON)
    structured_data: Optional[Dict] = None
```

## 2. Set Up the API Endpoint with CORS
If your frontend runs on a different port (e.g., `localhost:3000`) than your backend (e.g., `localhost:8000`), you **must** configure CORS, otherwise the browser will block the requests.

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Or "*" for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # 1. Parse history
    # 2. Run your RAG / Agent logic using request.query and request.context_data
    # 3. Return the ChatResponse
    return ChatResponse(
        response_text="Here is your answer...",
        sources_retrieved=["doc1.pdf"]
    )
```

## 3. Frontend: Fetching & State Management
Move all LLM logic out of the frontend. The frontend should only handle UI state and network requests.

```typescript
const [history, setHistory] = useState([]);
const [isLoading, setIsLoading] = useState(false);

const sendMessage = async (userQuery, currentContext) => {
    setIsLoading(true);
    
    // Optimistically add user message to UI
    setHistory(prev => [...prev, { role: 'user', content: userQuery }]);

    try {
        const res = await fetch('http://localhost:8000/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                query: userQuery, 
                history: history, 
                context_data: currentContext // <-- Crucial for iterative RAG!
            })
        });

        const data = await res.json();
        
        // Add AI response to UI
        setHistory(prev => [...prev, { 
            role: 'assistant', 
            content: data.response_text,
            sources: data.sources_retrieved 
        }]);
    } catch (error) {
        console.error("API Error:", error);
    } finally {
        setIsLoading(false);
    }
}
```

## 4. Context Saving (The Iterative Loop)
As we discovered with the floor plan designs, RAG models often lose context of what the user is currently looking at. 

**The Fix:** 
Always pass the *current state* of the frontend back to the backend on every request.
* **If it's a code editor:** Pass the current file contents.
* **If it's a document viewer:** Pass the ID or text of the highlighted paragraph.
* **If it's a design tool:** Pass the JSON of the active layout.

In the backend, write explicit prompt routing:
```python
if request.context_data:
    prompt = f"Modify this existing context based on the user request:\n{request.context_data}"
else:
    prompt = f"Generate a brand new response for: {request.query}"
```

## 5. Graceful Failure (Lazy Loading & Error Handling)
APIs will fail (network timeouts, LLM crashes, missing API keys). 
* Wrap your backend graph/LLM execution in a `try/except` block and return an `HTTPException(status_code=500)`.
* In the frontend `catch` block, push an assistant message to the chat history that says: `"Connection error: Please try again."` instead of just crashing the white screen.
