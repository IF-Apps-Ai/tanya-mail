"""
LangChain RAG Implementation for Tanya Ma'il API
Complete implementation using LangChain chains, memory, and agents
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio

from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import Tool, create_react_agent, AgentExecutor
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever

from dotenv import load_dotenv
import json

load_dotenv()


class StreamingLangChainHandler(AsyncCallbackHandler):
    """Custom async streaming callback handler for LangChain"""
    
    def __init__(self):
        self.tokens = asyncio.Queue()
        self.is_streaming = False
        
    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """Called when LLM starts generating"""
        self.is_streaming = True
        
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Called when LLM generates a new token"""
        if self.is_streaming:
            await self.tokens.put(token)
    
    async def on_llm_end(self, response, **kwargs) -> None:
        """Called when LLM finishes generating"""
        self.is_streaming = False
        await self.tokens.put(None)  # Signal end of stream
        
    async def on_llm_error(self, error: Exception, **kwargs) -> None:
        """Called when LLM encounters an error"""
        self.is_streaming = False
        await self.tokens.put(f"Error: {str(error)}")
        await self.tokens.put(None)


class MongoDocumentRetriever(BaseRetriever):
    """Custom retriever that combines ChromaDB with MongoDB metadata"""
    
    def __init__(self, chroma_retriever: BaseRetriever, mongo_collection, top_k: int = 5):
        super().__init__()
        self._chroma_retriever = chroma_retriever
        self._mongo_collection = mongo_collection
        self._top_k = top_k
        
    def _get_relevant_documents(self, query: str, *, run_manager=None) -> List[Document]:
        """Retrieve relevant documents with enhanced metadata from MongoDB"""
        # Get documents from ChromaDB
        chroma_docs = self._chroma_retriever._get_relevant_documents(query)
        
        # Enhance with MongoDB metadata
        enhanced_docs = []
        for doc in chroma_docs:
            doc_id = doc.metadata.get("doc_id")
            if doc_id:
                # Get full document info from MongoDB
                mongo_doc = self._mongo_collection.find_one({"doc_id": doc_id})
                if mongo_doc:
                    enhanced_metadata = {
                        **doc.metadata,
                        "upload_date": mongo_doc.get("upload_date"),
                        "file_hash": mongo_doc.get("file_hash"),
                        "chunk_id": mongo_doc.get("chunk_id"),
                        "kategori": mongo_doc.get("kategori"),
                        "chunk_size": mongo_doc.get("chunk_size")
                    }
                    enhanced_doc = Document(
                        page_content=doc.page_content,
                        metadata=enhanced_metadata
                    )
                    enhanced_docs.append(enhanced_doc)
                    
        return enhanced_docs[:self._top_k]

    async def aget_relevant_documents(self, query: str, *, run_manager=None) -> List[Document]:
        """Async version of get_relevant_documents"""
        return self._get_relevant_documents(query, run_manager=run_manager)


class LangChainRAGSystem:
    """Complete LangChain-based RAG system for Tanya Ma'il"""
    
    def __init__(self, mongo_collection, chroma_persist_dir: str = "chroma_pdf_db"):
        self.mongo_collection = mongo_collection
        self.chroma_persist_dir = chroma_persist_dir
        
        # Initialize LangChain components
        self.llm = self._initialize_llm()
        self.embeddings = self._initialize_embeddings()
        self.text_splitter = self._initialize_text_splitter()
        self.vectorstore = self._initialize_vectorstore()
        self.retriever = self._initialize_retriever()
        
        # Initialize chains
        self.qa_chain = None
        self.conversational_chain = None
        self.agent = None
        
        # Memory management
        self.memories: Dict[str, ConversationBufferWindowMemory] = {}
        
        self._build_chains()
        
    def _initialize_llm(self) -> ChatOpenAI:
        """Initialize ChatOpenAI LLM"""
        return ChatOpenAI(
            model_name=os.getenv("MODEL_NAME", "gpt-4o-mini"),
            temperature=float(os.getenv("MODEL_TEMPERATURE", "0")),
            max_tokens=int(os.getenv("MODEL_MAX_TOKENS", "2048")),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_API_BASE"),
            streaming=True
        )
    
    def _initialize_embeddings(self) -> OpenAIEmbeddings:
        """Initialize OpenAI embeddings"""
        return OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    
    def _initialize_text_splitter(self) -> RecursiveCharacterTextSplitter:
        """Initialize text splitter"""
        return RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
    
    def _initialize_vectorstore(self) -> Optional[Chroma]:
        """Initialize ChromaDB vectorstore"""
        if os.path.exists(self.chroma_persist_dir):
            return Chroma(
                persist_directory=self.chroma_persist_dir,
                embedding_function=self.embeddings
            )
        return None
    
    def _initialize_retriever(self) -> Optional[MongoDocumentRetriever]:
        """Initialize custom retriever"""
        if self.vectorstore:
            chroma_retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )
            return MongoDocumentRetriever(
                chroma_retriever=chroma_retriever,
                mongo_collection=self.mongo_collection,
                top_k=5
            )
        return None
    
    def _build_chains(self):
        """Build LangChain chains"""
        if not self.retriever:
            return
            
        # Create prompts
        system_prompt = """Anda adalah asisten AI yang membantu menjawab pertanyaan berdasarkan dokumen PDF yang diberikan.
        Gunakan konteks berikut untuk menjawab pertanyaan dengan akurat dan informatif.
        Jika informasi tidak tersedia dalam konteks, katakan bahwa Anda tidak tahu.
        Berikan jawaban dalam bahasa Indonesia yang jelas dan mudah dipahami.
        
        Konteks:
        {context}
        
        Riwayat Percakapan:
        {chat_history}
        
        Pertanyaan: {input}
        """
        
        qa_prompt = ChatPromptTemplate.from_template(system_prompt)
        
        # History-aware retriever prompt
        contextualize_q_system_prompt = """Berdasarkan riwayat percakapan dan pertanyaan terbaru dari pengguna yang mungkin merujuk pada konteks dalam riwayat percakapan, formulasikan pertanyaan mandiri yang dapat dipahami tanpa riwayat percakapan. JANGAN menjawab pertanyaan, hanya reformulasikan jika diperlukan dan jika tidak maka kembalikan apa adanya."""
        
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        # Create history-aware retriever
        history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, contextualize_q_prompt
        )
        
        # Create document chain
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        
        # Create RAG chain
        self.qa_chain = create_retrieval_chain(
            history_aware_retriever, 
            question_answer_chain
        )
        
        # Create conversational chain with memory
        self.conversational_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.retriever,
            return_source_documents=True,
            verbose=True,
            combine_docs_chain_kwargs={
                "prompt": ChatPromptTemplate.from_template(
                    """Anda adalah asisten AI untuk sistem RAG Tanya Ma'il. 
                    Gunakan konteks dokumen berikut untuk menjawab pertanyaan dengan akurat.
                    
                    Konteks: {context}
                    
                    Pertanyaan: {question}
                    
                    Jawaban:"""
                )
            }
        )
        
        # Create tools for agent
        self._create_agent()
    
    def _create_agent(self):
        """Create LangChain agent with tools"""
        tools = [
            Tool(
                name="document_qa",
                description="Menjawab pertanyaan berdasarkan dokumen PDF yang telah diproses",
                func=lambda q: self._simple_qa(q)
            ),
            Tool(
                name="search_documents", 
                description="Mencari dokumen yang relevan berdasarkan query",
                func=lambda q: self._search_documents(q)
            ),
            Tool(
                name="list_files",
                description="Menampilkan daftar file PDF yang telah diproses",
                func=lambda _: self._list_processed_files()
            )
        ]
        
        try:
            # Create a simple agent prompt with required variables
            agent_prompt = ChatPromptTemplate.from_messages([
                ("system", "Anda adalah asisten AI untuk sistem RAG Tanya Ma'il. Anda memiliki akses ke tools berikut: {tools}\n\nTool names: {tool_names}\n\nGunakan tools yang tersedia untuk menjawab pertanyaan pengguna."),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad")
            ])
            
            # Create agent
            agent = create_react_agent(self.llm, tools, agent_prompt)
            self.agent = AgentExecutor(agent=agent, tools=tools, verbose=True)
        except Exception as e:
            print(f"Agent creation failed: {e}")
            self.agent = None
    
    def get_memory(self, session_id: str) -> ConversationBufferWindowMemory:
        """Get or create conversation memory for session"""
        if session_id not in self.memories:
            self.memories[session_id] = ConversationBufferWindowMemory(
                k=5,  # Keep last 5 exchanges
                memory_key="chat_history",
                output_key="answer",
                return_messages=True
            )
        return self.memories[session_id]
    
    async def ask_question_streaming(
        self, 
        question: str, 
        session_id: str,
        callback_handler: StreamingLangChainHandler
    ) -> Dict[str, Any]:
        """Ask question with streaming response using LangChain"""
        try:
            memory = self.get_memory(session_id)
            
            # Get chat history for the new format
            chat_history = []
            if hasattr(memory, 'chat_memory') and memory.chat_memory.messages:
                for msg in memory.chat_memory.messages[-10:]:  # Last 10 messages
                    if isinstance(msg, HumanMessage):
                        chat_history.append(("human", msg.content))
                    elif isinstance(msg, AIMessage):
                        chat_history.append(("ai", msg.content))
            
            # Use the new RAG chain
            response = await self.qa_chain.ainvoke(
                {
                    "input": question,
                    "chat_history": chat_history
                },
                config={"callbacks": [callback_handler]}
            )
            
            answer = response.get("answer", "")
            source_docs = response.get("context", [])
            
            # Extract source files
            sources = list(set([
                doc.metadata.get("filename", "Unknown") 
                for doc in source_docs
            ]))
            
            # Save to memory
            memory.save_context(
                {"input": question},
                {"answer": answer}
            )
            
            return {
                "answer": answer,
                "sources": sources,
                "source_documents": source_docs,
                "session_id": session_id
            }
            
        except Exception as e:
            await callback_handler.tokens.put(f"Error: {str(e)}")
            await callback_handler.tokens.put(None)
            raise e
    
    async def ask_question(self, question: str, session_id: str) -> Dict[str, Any]:
        """Ask question without streaming using LangChain"""
        try:
            memory = self.get_memory(session_id)
            
            # Get chat history
            chat_history = []
            if hasattr(memory, 'chat_memory') and memory.chat_memory.messages:
                for msg in memory.chat_memory.messages[-10:]:
                    if isinstance(msg, HumanMessage):
                        chat_history.append(("human", msg.content))
                    elif isinstance(msg, AIMessage):
                        chat_history.append(("ai", msg.content))
            
            # Use the RAG chain
            response = await self.qa_chain.ainvoke({
                "input": question,
                "chat_history": chat_history
            })
            
            answer = response.get("answer", "")
            source_docs = response.get("context", [])
            
            # Extract source files
            sources = list(set([
                doc.metadata.get("filename", "Unknown") 
                for doc in source_docs
            ]))
            
            # Save to memory
            memory.save_context(
                {"input": question},
                {"answer": answer}
            )
            
            return {
                "answer": answer,
                "sources": sources,
                "source_documents": source_docs,
                "session_id": session_id
            }
            
        except Exception as e:
            raise e
    
    def ask_agent(self, question: str, session_id: str) -> str:
        """Use agent to answer complex questions"""
        if not self.agent:
            return "Agent tidak tersedia. Pastikan sistem telah diinisialisasi dengan benar."
        
        try:
            response = self.agent.run(question)
            return response
        except Exception as e:
            return f"Error dalam agent: {str(e)}"
    
    def _simple_qa(self, question: str) -> str:
        """Simple QA function for agent tool"""
        try:
            if not self.retriever:
                return "Retriever tidak tersedia"
            
            # Use basic retriever search
            docs = self.retriever._get_relevant_documents(question)
            context = "\n\n".join([doc.page_content for doc in docs[:3]])
            
            prompt = f"""Berdasarkan konteks berikut, jawab pertanyaan:
            
            Konteks: {context}
            
            Pertanyaan: {question}
            
            Jawaban:"""
            
            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _search_documents(self, query: str) -> str:
        """Search documents function for agent tool"""
        try:
            if not self.retriever:
                return "Retriever tidak tersedia"
            
            docs = self.retriever._get_relevant_documents(query)
            results = []
            for i, doc in enumerate(docs[:5], 1):
                filename = doc.metadata.get("filename", "Unknown")
                content_preview = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                results.append(f"{i}. File: {filename}\nContent: {content_preview}\n")
            
            return "\n".join(results)
        except Exception as e:
            return f"Error searching documents: {str(e)}"
    
    def _list_processed_files(self) -> str:
        """List processed files function for agent tool"""
        try:
            pipeline = [
                {"$group": {
                    "_id": "$filename",
                    "chunks": {"$sum": 1},
                    "upload_date": {"$first": "$upload_date"}
                }},
                {"$sort": {"_id": 1}}
            ]
            
            files = list(self.mongo_collection.aggregate(pipeline))
            if not files:
                return "Tidak ada file yang diproses."
            
            result = "File yang telah diproses:\n"
            for file_info in files:
                filename = file_info["_id"]
                chunks = file_info["chunks"]
                upload_date = file_info.get("upload_date", "Unknown")
                result += f"- {filename} ({chunks} chunks, uploaded: {upload_date})\n"
            
            return result
        except Exception as e:
            return f"Error listing files: {str(e)}"
    
    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]]) -> None:
        """Add documents to vectorstore"""
        if not self.vectorstore:
            # Create new vectorstore
            self.vectorstore = Chroma.from_texts(
                texts,
                self.embeddings,
                metadatas=metadatas,
                persist_directory=self.chroma_persist_dir
            )
        else:
            # Add to existing vectorstore
            self.vectorstore.add_texts(texts, metadatas=metadatas)
        
        # Update retriever
        self.retriever = self._initialize_retriever()
        # Rebuild chains with new retriever
        self._build_chains()
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get formatted conversation history"""
        memory = self.get_memory(session_id)
        history = []
        
        if hasattr(memory, 'chat_memory') and memory.chat_memory.messages:
            messages = memory.chat_memory.messages
            for i in range(0, len(messages), 2):
                if i + 1 < len(messages):
                    human_msg = messages[i]
                    ai_msg = messages[i + 1]
                    if isinstance(human_msg, HumanMessage) and isinstance(ai_msg, AIMessage):
                        history.append({
                            "question": human_msg.content,
                            "answer": ai_msg.content,
                            "timestamp": datetime.now().isoformat()  # Simplified timestamp
                        })
        
        return history
    
    def clear_conversation_history(self, session_id: str) -> bool:
        """Clear conversation history for session"""
        if session_id in self.memories:
            self.memories[session_id].clear()
            return True
        return False
    
    def export_conversation(self, session_id: str) -> Dict[str, Any]:
        """Export conversation history"""
        history = self.get_conversation_history(session_id)
        return {
            "session_id": session_id,
            "history": history,
            "exported_at": datetime.now().isoformat(),
            "total_exchanges": len(history)
        }
