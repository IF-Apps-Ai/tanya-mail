"""
Updated API with LangChain Integration
"""

import os
import hashlib
import json
import asyncio
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, AsyncGenerator
from datetime import datetime
import uvicorn

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

# Import existing modules
from pymongo import MongoClient
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from openai import OpenAI
import PyPDF2
import fitz  # PyMuPDF

# Import our simplified LangChain RAG system
from simple_langchain import SimpleLangChainRAG, SimpleStreamingHandler

# Load environment variables
load_dotenv()

# === API Models (Pydantic) ===


class QuestionRequest(BaseModel):
    """Model for question requests"""
    question: str = Field(
        ..., description="The question to ask about the PDF documents", min_length=1)
    top_k: int = Field(
        3, description="Number of top similar documents to retrieve", ge=1, le=10)
    filename_filter: Optional[str] = Field(
        None, description="Optional filename filter to search only specific file")
    stream: bool = Field(False, description="Enable streaming response")
    session_id: Optional[str] = Field(
        None, description="Session ID for conversation continuity")
    use_langchain: bool = Field(
        True, description="Use LangChain-based RAG system")


class ConversationContextRequest(BaseModel):
    """Model for conversation context configuration"""
    context_window: int = Field(
        3, description="Number of recent conversations to use as context", ge=1, le=10)


class QuestionResponse(BaseModel):
    """Model for question responses"""
    question: str
    answer: str
    sources: List[str]
    timestamp: str
    session_id: str


class FileInfo(BaseModel):
    """Model for file information"""
    filename: str
    chunks: int
    file_hash: str
    upload_date: Optional[str] = None


class ConversationHistory(BaseModel):
    """Model for conversation history"""
    session_id: str
    history: List[Dict[str, Any]]
    total_exchanges: int


class SearchResult(BaseModel):
    """Model for search results"""
    doc_id: str
    filename: str
    content: str
    similarity_score: Optional[float] = None


class APIResponse(BaseModel):
    """Generic API response model"""
    status: str
    message: str
    data: Optional[Any] = None


class SystemStatus(BaseModel):
    """Model for system status"""
    status: str
    mongodb_connected: bool
    chroma_available: bool
    total_documents: int
    total_files: int
    openai_configured: bool
    langchain_available: bool


# === Configuration ===
APP_NAME = os.getenv("APP_NAME", "Tanya Ma'il")

client_openai = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE")
)

MONGO_URI = os.getenv("MONGO_URI")
MONGO_URI_LOCAL = "mongodb://localhost:27017"
DB_NAME = os.getenv("DB_NAME", "RAG_DB")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "pdf_docs")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0"))
MODEL_MAX_TOKENS = int(os.getenv("MODEL_MAX_TOKENS", "2048"))

# PDF Configuration
PDF_FOLDER = "pdf_documents"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Conversation Configuration
MAX_CONVERSATION_HISTORY = 10
CONVERSATION_CONTEXT_WINDOW = 3

# === MongoDB Connection ===


def connect_mongodb():
    """Connect to MongoDB with fallback to local"""
    if MONGO_URI:
        try:
            mongo_client = MongoClient(
                MONGO_URI, serverSelectionTimeoutMS=5000)
            mongo_client.admin.command('ping')
            return mongo_client
        except Exception as e:
            print(f"Remote MongoDB failed: {e}")

    try:
        mongo_client = MongoClient(
            MONGO_URI_LOCAL, serverSelectionTimeoutMS=3000)
        mongo_client.admin.command('ping')
        return mongo_client
    except Exception as e:
        print(f"Local MongoDB failed: {e}")
        return None


# Initialize MongoDB
mongo_client = connect_mongodb()
if mongo_client is None:
    raise Exception("Cannot connect to MongoDB")

db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]

# === Initialize LangChain RAG System ===
try:
    langchain_rag = SimpleLangChainRAG(mongo_collection=collection)
    LANGCHAIN_AVAILABLE = True
    print(f"✅ LangChain RAG System initialized")
except Exception as e:
    langchain_rag = None
    LANGCHAIN_AVAILABLE = False
    print(f"⚠️ LangChain RAG System failed to initialize: {e}")

# === Session Manager (Legacy for non-LangChain) ===


class SessionManager:
    """Manages multiple user sessions (legacy system)"""

    def __init__(self):
        self.sessions: Dict[str, 'ConversationManager'] = {}
        self.session_timeout = 3600  # 1 hour in seconds
        self.last_activity: Dict[str, datetime] = {}

    def get_or_create_session(self, session_id: Optional[str] = None) -> tuple[str, 'ConversationManager']:
        """Get existing session or create new one"""
        # Clean up old sessions
        self._cleanup_old_sessions()

        # If no session_id provided or session doesn't exist, create new
        if not session_id or session_id not in self.sessions:
            session_id = str(uuid.uuid4())
            self.sessions[session_id] = ConversationManager()
            self.last_activity[session_id] = datetime.now()
        else:
            # Update last activity
            self.last_activity[session_id] = datetime.now()

        return session_id, self.sessions[session_id]

    def get_session(self, session_id: str) -> Optional['ConversationManager']:
        """Get existing session"""
        if session_id in self.sessions:
            self.last_activity[session_id] = datetime.now()
            return self.sessions[session_id]
        return None

    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            if session_id in self.last_activity:
                del self.last_activity[session_id]
            return True
        return False

    def _cleanup_old_sessions(self):
        """Remove sessions that have been inactive"""
        current_time = datetime.now()
        sessions_to_remove = []

        for session_id, last_time in self.last_activity.items():
            if (current_time - last_time).total_seconds() > self.session_timeout:
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            self.delete_session(session_id)

# === Conversation Manager (Legacy) ===


class ConversationManager:
    """Manages conversation history for multi-turn chat (legacy system)"""

    def __init__(self, max_history: int = MAX_CONVERSATION_HISTORY):
        self.conversation_history = []
        self.max_history = max_history
        self.context_window = CONVERSATION_CONTEXT_WINDOW
        self.current_session_id = self._generate_session_id()

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def add_exchange(self, question: str, answer: str, sources: List[str] = None):
        """Add Q&A exchange to history"""
        exchange = {
            "question": question,
            "answer": answer,
            "sources": sources or [],
            "timestamp": datetime.now().isoformat()
        }

        self.conversation_history.append(exchange)

        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

    def get_conversation_context(self, num_recent: int = None) -> str:
        """Get context from previous conversations"""
        if not self.conversation_history:
            return ""

        if num_recent is None:
            num_recent = self.context_window

        recent_exchanges = self.conversation_history[-num_recent:]
        context_parts = []

        for i, exchange in enumerate(recent_exchanges, 1):
            context_parts.append(f"Q{i}: {exchange['question']}")
            context_parts.append(f"A{i}: {exchange['answer']}")

        return "\n".join(context_parts)

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.current_session_id = self._generate_session_id()


# Global session manager (for legacy system)
session_manager = SessionManager()

# === Utility Functions ===


def extract_text_from_pdf(pdf_path: str, method: str = "pymupdf") -> str:
    """Extract text from PDF file"""
    try:
        if method == "pymupdf":
            doc = fitz.open(pdf_path)
            text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text() + "\n"
            doc.close()
            return text
        elif method == "pypdf2":
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {e}")


def get_file_hash(file_path: str) -> str:
    """Generate hash for file"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def split_text_into_chunks(text: str, filename: str) -> List[Dict[str, Any]]:
    """Split text into chunks"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )

    chunks = text_splitter.split_text(text)

    documents = []
    for i, chunk in enumerate(chunks):
        doc = {
            "text": chunk,
            "filename": filename,
            "chunk_id": i,
            "source": "pdf",
            "chunk_size": len(chunk)
        }
        documents.append(doc)

    return documents


def get_embedding(text: str) -> List[float]:
    """Create embedding for text"""
    try:
        result = client_openai.embeddings.create(
            input=[text],
            model="text-embedding-3-small"
        )
        return result.data[0].embedding
    except Exception as e:
        raise Exception(f"Error creating embedding: {e}")


def search_similar_documents(query: str, top_k: int = 3, filename_filter: str = None):
    """Search for similar documents (legacy method)"""
    try:
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        if not os.path.exists("chroma_pdf_db"):
            raise Exception(
                "ChromaDB not built. Please build vector store first.")

        chroma = Chroma(persist_directory="chroma_pdf_db",
                        embedding_function=embeddings)

        filter_dict = {
            "filename": filename_filter} if filename_filter else None
        results = chroma.similarity_search(query, k=top_k, filter=filter_dict)

        return results
    except Exception as e:
        raise Exception(f"Error searching documents: {e}")


# === FastAPI App ===
app = FastAPI(
    title=f"{APP_NAME} API with LangChain",
    description=f"Enhanced RAG (Retrieval-Augmented Generation) system with LangChain integration - {APP_NAME}",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === API Endpoints ===


@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint - API information"""
    return APIResponse(
        status="success",
        message=f"{APP_NAME} API with LangChain is running",
        data={
            "version": "2.0.0",
            "description": "Enhanced RAG system with LangChain integration",
            "app_name": APP_NAME,
            "langchain_available": LANGCHAIN_AVAILABLE,
            "endpoints": {
                "docs": "/docs",
                "health": "/health",
                "upload": "/upload",
                "question": "/ask",
                "langchain_ask": "/langchain/ask"
            }
        }
    )


@app.get("/health", response_model=SystemStatus)
async def health_check():
    """Health check endpoint"""
    try:
        # Check MongoDB connection
        mongo_connected = True
        try:
            mongo_client.admin.command('ping')
        except:
            mongo_connected = False

        # Check ChromaDB
        chroma_available = os.path.exists("chroma_pdf_db")

        # Count documents
        total_docs = collection.count_documents({})

        # Count unique files
        pipeline = [{"$group": {"_id": "$filename"}}]
        unique_files = len(list(collection.aggregate(pipeline)))

        # Check OpenAI configuration
        openai_configured = bool(os.getenv("OPENAI_API_KEY"))

        status = "healthy" if all([
            mongo_connected, openai_configured, LANGCHAIN_AVAILABLE
        ]) else "partial" if any([mongo_connected, openai_configured]) else "unhealthy"

        return SystemStatus(
            status=status,
            mongodb_connected=mongo_connected,
            chroma_available=chroma_available,
            total_documents=total_docs,
            total_files=unique_files,
            openai_configured=openai_configured,
            langchain_available=LANGCHAIN_AVAILABLE
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Health check failed: {e}")


@app.post("/upload", response_model=APIResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF file to upload")
):
    """Upload and process PDF file"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400, detail="Only PDF files are allowed")

    try:
        # Create PDF folder if not exists
        os.makedirs(PDF_FOLDER, exist_ok=True)

        # Save uploaded file
        file_path = os.path.join(PDF_FOLDER, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Process file in background
        background_tasks.add_task(process_pdf_file, file_path)

        return APIResponse(
            status="success",
            message=f"File {file.filename} uploaded successfully and is being processed",
            data={"filename": file.filename, "size": len(content)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


def process_pdf_file(file_path: str):
    """Background task to process PDF file"""
    try:
        filename = os.path.basename(file_path)
        file_hash = get_file_hash(file_path)

        # Check if already processed
        existing_doc = collection.find_one(
            {"filename": filename, "file_hash": file_hash})
        if existing_doc:
            return

        # Extract text
        text = extract_text_from_pdf(file_path)
        if not text.strip():
            return

        # Split into chunks
        documents = split_text_into_chunks(text, filename)

        # Process each chunk for MongoDB
        texts_for_langchain = []
        metadatas_for_langchain = []

        for doc in documents:
            embedding = get_embedding(doc["text"])
            if not embedding:
                continue

            mongo_doc = {
                "doc_id": f"{filename}_chunk_{doc['chunk_id']}",
                "filename": filename,
                "file_hash": file_hash,
                "text": doc["text"],
                "chunk_id": doc["chunk_id"],
                "source": doc["source"],
                "chunk_size": doc["chunk_size"],
                "embedding": embedding,
                "kategori": "pdf_document",
                "upload_date": datetime.now().isoformat()
            }

            collection.insert_one(mongo_doc)

            # Prepare for LangChain
            texts_for_langchain.append(doc["text"])
            metadatas_for_langchain.append({
                "doc_id": mongo_doc["doc_id"],
                "filename": filename,
                "kategori": "pdf_document"
            })

        # Add to LangChain if available
        if langchain_rag and texts_for_langchain:
            try:
                langchain_rag.add_documents(
                    texts_for_langchain, metadatas_for_langchain)
                print(
                    f"✅ Added {len(texts_for_langchain)} documents to LangChain system")
            except Exception as e:
                print(f"⚠️ Failed to add documents to LangChain: {e}")

    except Exception as e:
        print(f"Error processing PDF: {e}")


@app.post("/build-vectorstore", response_model=APIResponse)
async def build_vectorstore():
    """Build ChromaDB vector store from processed documents"""
    try:
        docs = list(collection.find(
            {}, {"doc_id": 1, "text": 1, "filename": 1, "kategori": 1}))
        if not docs:
            raise HTTPException(
                status_code=404, detail="No documents found in database")

        texts = [doc["text"] for doc in docs]
        metadatas = [
            {
                "doc_id": doc["doc_id"],
                "filename": doc["filename"],
                "kategori": doc["kategori"]
            } for doc in docs
        ]

        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        Chroma.from_texts(
            texts,
            embeddings,
            metadatas=metadatas,
            persist_directory="chroma_pdf_db"
        )

        # Rebuild LangChain system
        if langchain_rag:
            try:
                langchain_rag.add_documents(texts, metadatas)
                print("✅ LangChain system updated with vector store")
            except Exception as e:
                print(f"⚠️ Failed to update LangChain system: {e}")

        return APIResponse(
            status="success",
            message=f"Vector store built successfully with {len(docs)} documents",
            data={"total_documents": len(docs), "total_files": len(
                set(doc["filename"] for doc in docs))}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to build vector store: {e}")


@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """Ask a question - can use either LangChain or legacy system"""
    try:
        query = request.question
        stream = request.stream
        use_langchain = request.use_langchain and LANGCHAIN_AVAILABLE

        # Use LangChain system if available and requested
        if use_langchain and langchain_rag:
            session_id = request.session_id or str(uuid.uuid4())

            if stream:
                # LangChain streaming response
                async def generate():
                    try:
                        # Send session_id first
                        yield f"data: {json.dumps({'session_id': session_id, 'type': 'session'})}\n\n"

                        # Create streaming handler
                        handler = SimpleStreamingHandler()

                        # Start async task for LangChain
                        response_task = asyncio.create_task(
                            langchain_rag.ask_question_streaming(
                                query, session_id, handler)
                        )

                        # Stream tokens
                        while True:
                            try:
                                token = await asyncio.wait_for(handler.tokens.get(), timeout=1.0)
                                if token is None:  # End of stream
                                    break
                                if token.startswith("Error:"):
                                    yield f"data: {json.dumps({'error': token, 'type': 'error'})}\n\n"
                                    break
                                else:
                                    yield f"data: {json.dumps({'token': token, 'type': 'content'})}\n\n"
                            except asyncio.TimeoutError:
                                continue

                        # Get final result
                        try:
                            result = await response_task
                            if result.get("sources"):
                                yield f"data: {json.dumps({'sources': result['sources'], 'type': 'source'})}\n\n"
                        except Exception as e:
                            yield f"data: {json.dumps({'error': str(e), 'type': 'error'})}\n\n"

                        yield f"data: {json.dumps({'type': 'done'})}\n\n"

                    except Exception as e:
                        yield f"data: {json.dumps({'error': str(e), 'type': 'error'})}\n\n"

                return EventSourceResponse(generate())
            else:
                # LangChain non-streaming response
                session_id = request.session_id or str(uuid.uuid4())
                result = await langchain_rag.ask_question(query, session_id)

                return QuestionResponse(
                    question=query,
                    answer=result["answer"],
                    sources=result["sources"],
                    timestamp=datetime.now().isoformat(),
                    session_id=session_id
                )

        else:
            # Use legacy system
            return await ask_question_legacy(request)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process question: {e}")


async def ask_question_legacy(request: QuestionRequest):
    """Legacy question processing (original implementation)"""
    try:
        query = request.question
        top_k = request.top_k
        filename_filter = request.filename_filter
        stream = request.stream

        # Get or create session
        session_id, conversation_manager = session_manager.get_or_create_session(
            request.session_id)

        # Get conversation context
        conversation_context = conversation_manager.get_conversation_context()

        # Enhanced query with conversation context
        enhanced_query = query
        if conversation_context:
            follow_up_indicators = [
                "lanjut", "selanjutnya", "lebih detail", "contoh", "bagaimana",
                "jelaskan lebih", "detail", "itu", "tersebut", "tadi", "sebelumnya"
            ]

            is_follow_up = any(indicator in query.lower()
                               for indicator in follow_up_indicators)

            if is_follow_up:
                last_question = conversation_manager.conversation_history[-1][
                    "question"] if conversation_manager.conversation_history else ""
                enhanced_query = f"Berdasarkan pertanyaan sebelumnya '{last_question}', {query}"

        # Search similar documents
        results = search_similar_documents(
            enhanced_query, top_k, filename_filter)

        if not results:
            answer = "Tidak ada dokumen relevan ditemukan untuk pertanyaan Anda."
            conversation_manager.add_exchange(query, answer, [])

            if stream:
                def generate():
                    yield f"data: {json.dumps({'session_id': session_id, 'type': 'session'})}\n\n"
                    yield f"data: {json.dumps({'token': answer, 'type': 'content'})}\n\n"
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return EventSourceResponse(generate())
            else:
                return QuestionResponse(
                    question=query,
                    answer=answer,
                    sources=[],
                    timestamp=datetime.now().isoformat(),
                    session_id=session_id
                )

        # Get full documents from MongoDB
        doc_ids = [res.metadata["doc_id"] for res in results]
        full_docs = list(collection.find({"doc_id": {"$in": doc_ids}}))

        # Prepare context
        context_parts = []
        source_files = set()

        for doc in full_docs:
            filename = doc.get("filename", "Unknown")
            text = doc.get("text", "")
            context_parts.append(f"[File: {filename}]\n{text}")
            source_files.add(filename)

        document_context = "\n\n---\n\n".join(context_parts)

        # Build comprehensive prompt
        prompt_parts = []

        if conversation_context:
            prompt_parts.append("CONVERSATION HISTORY:")
            prompt_parts.append(conversation_context)
            prompt_parts.append("\n" + "="*50 + "\n")

        prompt_parts.append("DOKUMEN REFERENSI:")
        prompt_parts.append(document_context)
        prompt_parts.append("\n" + "="*50 + "\n")

        if conversation_context:
            prompt_parts.append(f"PERTANYAAN SAAT INI: {query}")
            prompt_parts.append("\nInstruksi: Jawab pertanyaan saat ini dengan mempertimbangkan konteks percakapan sebelumnya. Jika pertanyaan ini adalah lanjutan dari pertanyaan sebelumnya, berikan jawaban yang konsisten dan terhubung. Gunakan informasi dari dokumen referensi untuk memberikan jawaban yang akurat dan lengkap.")
        else:
            prompt_parts.append(f"PERTANYAAN: {query}")
            prompt_parts.append(
                "\nInstruksi: Berdasarkan dokumen referensi di atas, jawab pertanyaan dengan akurat dan lengkap.")

        prompt_parts.append("\nJAWABAN:")
        full_prompt = "\n".join(prompt_parts)

        if stream:
            # Streaming response
            def generate():
                try:
                    # Send session_id first
                    yield f"data: {json.dumps({'session_id': session_id, 'type': 'session'})}\n\n"

                    response_stream = client_openai.chat.completions.create(
                        model=MODEL_NAME,
                        messages=[{"role": "user", "content": full_prompt}],
                        temperature=MODEL_TEMPERATURE,
                        max_tokens=MODEL_MAX_TOKENS,
                        stream=True
                    )

                    full_answer = ""
                    for chunk in response_stream:
                        if chunk.choices[0].delta.content:
                            token = chunk.choices[0].delta.content
                            full_answer += token
                            yield f"data: {json.dumps({'token': token, 'type': 'content'})}\n\n"

                    # Send sources
                    sources = list(source_files)
                    if sources:
                        yield f"data: {json.dumps({'sources': sources, 'type': 'source'})}\n\n"

                    # Store in conversation history
                    conversation_manager.add_exchange(
                        query, full_answer, sources)

                    yield f"data: {json.dumps({'type': 'done'})}\n\n"

                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e), 'type': 'error'})}\n\n"

            return EventSourceResponse(generate())
        else:
            # Non-streaming response
            response = client_openai.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": full_prompt}],
                temperature=MODEL_TEMPERATURE,
                max_tokens=MODEL_MAX_TOKENS
            )

            answer = response.choices[0].message.content
            sources = list(source_files)

            # Store in conversation history
            conversation_manager.add_exchange(query, answer, sources)

            return QuestionResponse(
                question=query,
                answer=answer,
                sources=sources,
                timestamp=datetime.now().isoformat(),
                session_id=session_id
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process question: {e}")


@app.post("/langchain/ask")
async def ask_langchain_question(request: QuestionRequest):
    """Direct LangChain endpoint"""
    if not LANGCHAIN_AVAILABLE or not langchain_rag:
        raise HTTPException(
            status_code=503,
            detail="LangChain system not available"
        )

    try:
        session_id = request.session_id or str(uuid.uuid4())
        result = await langchain_rag.ask_question(request.question, session_id)

        return QuestionResponse(
            question=request.question,
            answer=result["answer"],
            sources=result["sources"],
            timestamp=datetime.now().isoformat(),
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LangChain query failed: {e}"
        )


@app.post("/langchain/agent")
async def ask_agent_question(request: QuestionRequest):
    """Use simplified LangChain for complex questions"""
    if not LANGCHAIN_AVAILABLE or not langchain_rag:
        raise HTTPException(
            status_code=503,
            detail="LangChain system not available"
        )

    try:
        session_id = request.session_id or str(uuid.uuid4())

        # Use the same ask_question method since we simplified the system
        result = await langchain_rag.ask_question(request.question, session_id)

        # Add file search information
        files_info = langchain_rag.search_files()
        enhanced_answer = f"{result['answer']}\n\n--- Files Information ---\n{files_info}"

        return QuestionResponse(
            question=request.question,
            answer=enhanced_answer,
            sources=result["sources"],
            timestamp=datetime.now().isoformat(),
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent query failed: {e}"
        )


@app.get("/files", response_model=List[FileInfo])
async def list_files():
    """List all processed PDF files"""
    try:
        pipeline = [
            {"$group": {
                "_id": "$filename",
                "chunks": {"$sum": 1},
                "file_hash": {"$first": "$file_hash"},
                "upload_date": {"$first": "$upload_date"}
            }},
            {"$sort": {"_id": 1}}
        ]

        files = list(collection.aggregate(pipeline))

        return [
            FileInfo(
                filename=file_info["_id"],
                chunks=file_info["chunks"],
                file_hash=file_info["file_hash"],
                upload_date=file_info.get("upload_date")
            )
            for file_info in files
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list files: {e}")


@app.delete("/files/{filename}", response_model=APIResponse)
async def delete_file(filename: str):
    """Delete a specific file and all its chunks"""
    try:
        result = collection.delete_many({"filename": filename})
        if result.deleted_count > 0:
            return APIResponse(
                status="success",
                message=f"File {filename} deleted successfully",
                data={"deleted_chunks": result.deleted_count}
            )
        else:
            raise HTTPException(
                status_code=404, detail=f"File {filename} not found")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete file: {e}")


@app.get("/search", response_model=List[SearchResult])
async def search_documents(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(
        5, description="Number of results to return", ge=1, le=20),
    filename_filter: Optional[str] = Query(
        None, description="Optional filename filter")
):
    """Search for similar documents"""
    try:
        results = search_similar_documents(query, top_k, filename_filter)

        return [
            SearchResult(
                doc_id=result.metadata.get("doc_id", "Unknown"),
                filename=result.metadata.get("filename", "Unknown"),
                content=result.page_content[:500] + "..." if len(
                    result.page_content) > 500 else result.page_content
            )
            for result in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")


@app.get("/conversation/history/{session_id}", response_model=ConversationHistory)
async def get_conversation_history(session_id: str):
    """Get conversation history for a specific session"""

    # Try LangChain first
    if LANGCHAIN_AVAILABLE and langchain_rag:
        try:
            history = langchain_rag.get_conversation_history(session_id)
            return ConversationHistory(
                session_id=session_id,
                history=history,
                total_exchanges=len(history)
            )
        except Exception as e:
            print(f"LangChain history retrieval failed: {e}")

    # Fallback to legacy system
    conversation_manager = session_manager.get_session(session_id)
    if not conversation_manager:
        raise HTTPException(status_code=404, detail="Session not found")

    return ConversationHistory(
        session_id=session_id,
        history=conversation_manager.conversation_history,
        total_exchanges=len(conversation_manager.conversation_history)
    )


@app.delete("/conversation/history/{session_id}", response_model=APIResponse)
async def clear_conversation_history(session_id: str):
    """Clear conversation history for a specific session"""

    # Try LangChain first
    if LANGCHAIN_AVAILABLE and langchain_rag:
        success = langchain_rag.clear_conversation_history(session_id)
        if success:
            return APIResponse(
                status="success",
                message="LangChain session cleared successfully",
                data={"session_id": session_id, "system": "langchain"}
            )

    # Fallback to legacy system
    if session_manager.delete_session(session_id):
        return APIResponse(
            status="success",
            message="Legacy session cleared successfully",
            data={"session_id": session_id, "system": "legacy"}
        )
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.post("/conversation/config/{session_id}", response_model=APIResponse)
async def configure_conversation(session_id: str, request: ConversationContextRequest):
    """Configure conversation context window for a specific session"""
    try:
        # For legacy system
        conversation_manager = session_manager.get_session(session_id)
        if conversation_manager:
            conversation_manager.context_window = request.context_window
            return APIResponse(
                status="success",
                message=f"Legacy conversation context window set to {request.context_window}",
                data={"context_window": request.context_window,
                      "session_id": session_id, "system": "legacy"}
            )

        # LangChain system uses fixed context window
        return APIResponse(
            status="success",
            message=f"LangChain uses fixed context window (last 5 exchanges)",
            data={"context_window": 5,
                  "session_id": session_id, "system": "langchain"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Configuration failed: {e}")


@app.get("/conversation/export/{session_id}", response_class=FileResponse)
async def export_conversation(session_id: str):
    """Export conversation history as JSON file for a specific session"""
    try:
        # Try LangChain first
        if LANGCHAIN_AVAILABLE and langchain_rag:
            try:
                conversation_data = langchain_rag.export_conversation(
                    session_id)
                if conversation_data["history"]:  # Has history
                    filename = f"langchain_conversation_{session_id}.json"
                    filepath = f"/tmp/{filename}"

                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(conversation_data, f,
                                  indent=2, ensure_ascii=False)

                    return FileResponse(
                        filepath,
                        media_type='application/json',
                        filename=filename
                    )
            except Exception as e:
                print(f"LangChain export failed: {e}")

        # Fallback to legacy system
        conversation_manager = session_manager.get_session(session_id)
        if not conversation_manager:
            raise HTTPException(status_code=404, detail="Session not found")

        filename = f"legacy_conversation_{session_id}.json"
        filepath = f"/tmp/{filename}"

        conversation_data = {
            "session_id": session_id,
            "history": conversation_manager.conversation_history,
            "exported_at": datetime.now().isoformat(),
            "system": "legacy"
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, indent=2, ensure_ascii=False)

        return FileResponse(
            filepath,
            media_type='application/json',
            filename=filename
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")


@app.get("/sessions", response_model=APIResponse)
async def list_sessions():
    """List all active sessions"""
    sessions_info = []

    # Legacy sessions
    for session_id, last_activity in session_manager.last_activity.items():
        conv_manager = session_manager.sessions[session_id]
        sessions_info.append({
            "session_id": session_id,
            "last_activity": last_activity.isoformat(),
            "total_exchanges": len(conv_manager.conversation_history),
            "system": "legacy"
        })

    # LangChain sessions
    if LANGCHAIN_AVAILABLE and langchain_rag:
        for session_id in langchain_rag.memories.keys():
            history = langchain_rag.get_conversation_history(session_id)
            sessions_info.append({
                "session_id": session_id,
                "last_activity": datetime.now().isoformat(),  # Simplified
                "total_exchanges": len(history),
                "system": "langchain"
            })

    return APIResponse(
        status="success",
        message=f"Found {len(sessions_info)} active sessions",
        data=sessions_info
    )


# === Startup Event ===

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    print(f"🚀 {APP_NAME} API with LangChain starting up...")

    # Create PDF folder
    os.makedirs(PDF_FOLDER, exist_ok=True)
    print(f"📁 PDF folder ready: {PDF_FOLDER}")

    # Test MongoDB connection
    try:
        mongo_client.admin.command('ping')
        print("✅ MongoDB connection successful")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")

    # Check OpenAI configuration
    if os.getenv("OPENAI_API_KEY"):
        print("✅ OpenAI API key configured")
    else:
        print("⚠️ OpenAI API key not found")

    # Check LangChain system
    if LANGCHAIN_AVAILABLE:
        print("✅ LangChain RAG system ready")
    else:
        print("⚠️ LangChain RAG system not available - using legacy system")

    print(f"🎉 {APP_NAME} API ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print(f"🛑 {APP_NAME} API shutting down...")
    if mongo_client:
        mongo_client.close()
        print("🔌 MongoDB connection closed")

# === Main ===
if __name__ == "__main__":
    uvicorn.run(
        "api_langchain:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
