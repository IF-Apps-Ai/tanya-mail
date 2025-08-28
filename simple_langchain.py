"""
Simplified LangChain Integration for Tanya Ma'il
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import HumanMessage, AIMessage

from dotenv import load_dotenv
import asyncio

load_dotenv()


class SimpleLangChainRAG:
    """Simplified LangChain RAG system"""
    
    def __init__(self, mongo_collection, chroma_persist_dir: str = "chroma_pdf_db"):
        self.mongo_collection = mongo_collection
        self.chroma_persist_dir = chroma_persist_dir
        
        # Initialize core components
        self.llm = ChatOpenAI(
            model_name=os.getenv("MODEL_NAME", "gpt-4o-mini"),
            temperature=float(os.getenv("MODEL_TEMPERATURE", "0")),
            max_tokens=int(os.getenv("MODEL_MAX_TOKENS", "2048")),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            streaming=True
        )
        
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        # Initialize vectorstore if exists
        self.vectorstore = None
        if os.path.exists(self.chroma_persist_dir):
            try:
                self.vectorstore = Chroma(
                    persist_directory=self.chroma_persist_dir,
                    embedding_function=self.embeddings
                )
            except Exception as e:
                print(f"Failed to load vectorstore: {e}")
                
        # Memory for conversations
        self.memories: Dict[str, ConversationBufferWindowMemory] = {}
        
        # System prompt
        self.system_prompt = ChatPromptTemplate.from_messages([
            ("system", """Anda adalah asisten AI untuk sistem RAG Tanya Ma'il. 
            Gunakan konteks dokumen yang diberikan untuk menjawab pertanyaan dengan akurat.
            Jika informasi tidak tersedia dalam konteks, katakan bahwa Anda tidak tahu.
            Berikan jawaban dalam bahasa Indonesia yang jelas dan mudah dipahami.
            
            Konteks dokumen:
            {context}
            
            Riwayat percakapan:
            {chat_history}"""),
            ("human", "{question}")
        ])
    
    def get_memory(self, session_id: str) -> ConversationBufferWindowMemory:
        """Get or create memory for session"""
        if session_id not in self.memories:
            self.memories[session_id] = ConversationBufferWindowMemory(
                k=5,
                memory_key="chat_history",
                return_messages=True
            )
        return self.memories[session_id]
    
    def search_documents(self, query: str, k: int = 5) -> List[Document]:
        """Search for relevant documents"""
        if not self.vectorstore:
            return []
        
        try:
            results = self.vectorstore.similarity_search(query, k=k)
            return results
        except Exception as e:
            print(f"Search failed: {e}")
            return []
    
    def get_enhanced_documents(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Get documents with enhanced metadata from MongoDB"""
        chroma_docs = self.search_documents(query, k)
        enhanced_docs = []
        
        for doc in chroma_docs:
            doc_id = doc.metadata.get("doc_id")
            if doc_id:
                mongo_doc = self.mongo_collection.find_one({"doc_id": doc_id})
                if mongo_doc:
                    enhanced_doc = {
                        "content": doc.page_content,
                        "metadata": {
                            **doc.metadata,
                            "upload_date": mongo_doc.get("upload_date"),
                            "file_hash": mongo_doc.get("file_hash"),
                            "chunk_id": mongo_doc.get("chunk_id"),
                            "kategori": mongo_doc.get("kategori"),
                            "chunk_size": mongo_doc.get("chunk_size")
                        }
                    }
                    enhanced_docs.append(enhanced_doc)
        
        return enhanced_docs
    
    async def ask_question(self, question: str, session_id: str) -> Dict[str, Any]:
        """Ask question with memory"""
        try:
            # Get relevant documents
            docs = self.get_enhanced_documents(question, k=5)
            if not docs:
                return {
                    "answer": "Tidak ada dokumen relevan ditemukan untuk pertanyaan Anda.",
                    "sources": [],
                    "session_id": session_id
                }
            
            # Prepare context
            context_parts = []
            sources = set()
            
            for doc in docs:
                filename = doc["metadata"].get("filename", "Unknown")
                content = doc["content"]
                context_parts.append(f"[File: {filename}]\n{content}")
                sources.add(filename)
            
            context = "\n\n---\n\n".join(context_parts)
            
            # Get memory and format chat history
            memory = self.get_memory(session_id)
            chat_history = ""
            
            if hasattr(memory, 'chat_memory') and memory.chat_memory.messages:
                history_parts = []
                messages = memory.chat_memory.messages[-6:]  # Last 3 exchanges
                
                for i in range(0, len(messages), 2):
                    if i + 1 < len(messages):
                        human_msg = messages[i]
                        ai_msg = messages[i + 1]
                        if isinstance(human_msg, HumanMessage) and isinstance(ai_msg, AIMessage):
                            history_parts.append(f"Q: {human_msg.content}")
                            history_parts.append(f"A: {ai_msg.content}")
                
                chat_history = "\n".join(history_parts)
            
            # Create prompt and get response
            prompt = self.system_prompt.format(
                context=context,
                chat_history=chat_history,
                question=question
            )
            
            response = await self.llm.ainvoke(prompt)
            answer = response.content
            
            # Save to memory
            memory.save_context(
                {"input": question},
                {"output": answer}
            )
            
            return {
                "answer": answer,
                "sources": list(sources),
                "session_id": session_id,
                "documents": docs
            }
            
        except Exception as e:
            raise Exception(f"Question processing failed: {e}")
    
    async def ask_question_streaming(self, question: str, session_id: str, callback_handler) -> Dict[str, Any]:
        """Ask question with streaming response"""
        try:
            # Get relevant documents
            docs = self.get_enhanced_documents(question, k=5)
            if not docs:
                await callback_handler.on_llm_new_token("Tidak ada dokumen relevan ditemukan untuk pertanyaan Anda.")
                await callback_handler.on_llm_end(None)
                return {
                    "answer": "Tidak ada dokumen relevan ditemukan untuk pertanyaan Anda.",
                    "sources": [],
                    "session_id": session_id
                }
            
            # Prepare context
            context_parts = []
            sources = set()
            
            for doc in docs:
                filename = doc["metadata"].get("filename", "Unknown")
                content = doc["content"]
                context_parts.append(f"[File: {filename}]\n{content}")
                sources.add(filename)
            
            context = "\n\n---\n\n".join(context_parts)
            
            # Get memory and format chat history
            memory = self.get_memory(session_id)
            chat_history = ""
            
            if hasattr(memory, 'chat_memory') and memory.chat_memory.messages:
                history_parts = []
                messages = memory.chat_memory.messages[-6:]
                
                for i in range(0, len(messages), 2):
                    if i + 1 < len(messages):
                        human_msg = messages[i]
                        ai_msg = messages[i + 1]
                        if isinstance(human_msg, HumanMessage) and isinstance(ai_msg, AIMessage):
                            history_parts.append(f"Q: {human_msg.content}")
                            history_parts.append(f"A: {ai_msg.content}")
                
                chat_history = "\n".join(history_parts)
            
            # Create prompt and get streaming response
            prompt = self.system_prompt.format(
                context=context,
                chat_history=chat_history,
                question=question
            )
            
            # Stream response
            full_answer = ""
            async for chunk in self.llm.astream(prompt):
                if chunk.content:
                    await callback_handler.on_llm_new_token(chunk.content)
                    full_answer += chunk.content
            
            await callback_handler.on_llm_end(None)
            
            # Save to memory
            memory.save_context(
                {"input": question},
                {"output": full_answer}
            )
            
            return {
                "answer": full_answer,
                "sources": list(sources),
                "session_id": session_id,
                "documents": docs
            }
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            await callback_handler.on_llm_new_token(error_msg)
            await callback_handler.on_llm_end(None)
            raise e
    
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
                            "timestamp": datetime.now().isoformat()
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
    
    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]]) -> None:
        """Add documents to vectorstore"""
        try:
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
            print(f"Added {len(texts)} documents to vectorstore")
        except Exception as e:
            print(f"Failed to add documents: {e}")
    
    def search_files(self) -> str:
        """Search for processed files"""
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


class SimpleStreamingHandler(AsyncCallbackHandler):
    """Simplified streaming callback handler"""
    
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
