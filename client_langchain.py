#!/usr/bin/env python3
"""
Client untuk API LangChain - Tanya Ma'il
Comprehensive client untuk berinteraksi dengan api_langchain.py

Features:
- Question answering dengan session support
- Streaming responses untuk real-time chat
- File management (upload, delete, list)
- Session management (create, clear, export)
- Conversation history tracking
- LangChain-specific endpoints
- Vector store management
"""

import requests
import json
import uuid
from typing import Dict, List, Optional, Any, Generator
from pathlib import Path
try:
    import sseclient  # pip install sseclient-py
    STREAMING_AVAILABLE = True
except ImportError:
    STREAMING_AVAILABLE = False
    print("⚠️ sseclient-py not installed. Streaming features disabled.")
    print("💡 Install with: pip install sseclient-py")
from datetime import datetime
import argparse


class TanyaMailLangChainClient:
    """Comprehensive client untuk Tanya Ma'il LangChain API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", session_id: Optional[str] = None):
        """
        Initialize client
        
        Args:
            base_url: Base URL API server
            session_id: Session ID untuk conversation continuity
        """
        self.base_url = base_url.rstrip('/')
        self.session_id = session_id or str(uuid.uuid4())
        self.session = requests.Session()
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Test connection
        try:
            self.get_health()
            print(f"✅ Connected to {self.base_url}")
            print(f"🆔 Session ID: {self.session_id}")
        except Exception as e:
            print(f"⚠️ Warning: Cannot connect to API server: {e}")
    
    # === Core API Methods ===
    
    def get_health(self) -> Dict[str, Any]:
        """Get system health status"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_info(self) -> Dict[str, Any]:
        """Get API information"""
        response = self.session.get(f"{self.base_url}/")
        response.raise_for_status()
        return response.json()
    
    # === Question Answering ===
    
    def ask_question(
        self, 
        question: str, 
        top_k: int = 3, 
        filename_filter: Optional[str] = None,
        use_langchain: bool = True,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ask question dengan session support
        
        Args:
            question: Pertanyaan yang ingin ditanyakan
            top_k: Jumlah dokumen relevan yang diambil (1-10)
            filename_filter: Filter berdasarkan nama file tertentu
            use_langchain: Gunakan sistem LangChain (True) atau legacy (False)
            session_id: Session ID khusus (default: client session)
        
        Returns:
            Dict dengan answer, sources, session_id, timestamp
        """
        payload = {
            "question": question,
            "top_k": top_k,
            "filename_filter": filename_filter,
            "stream": False,
            "session_id": session_id or self.session_id,
            "use_langchain": use_langchain
        }
        
        response = self.session.post(f"{self.base_url}/ask", json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Add to local history
        self.conversation_history.append({
            "question": question,
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "timestamp": datetime.now().isoformat(),
            "session_id": result.get("session_id", self.session_id)
        })
        
        return result
    
    def ask_question_streaming(
        self, 
        question: str, 
        top_k: int = 3,
        filename_filter: Optional[str] = None,
        use_langchain: bool = True,
        session_id: Optional[str] = None
    ) -> Generator[str, None, Dict[str, Any]]:
        """
        Ask question dengan streaming response
        
        Args:
            question: Pertanyaan yang ingin ditanyakan
            top_k: Jumlah dokumen relevan yang diambil
            filename_filter: Filter berdasarkan nama file
            use_langchain: Gunakan sistem LangChain
            session_id: Session ID khusus
        
        Yields:
            Token-token response secara real-time
            
        Returns:
            Dict dengan informasi lengkap setelah streaming selesai
        """
        if not STREAMING_AVAILABLE:
            # Fallback to non-streaming
            result = self.ask_question(question, top_k, filename_filter, use_langchain, session_id)
            yield result["answer"]
            return result
            
        payload = {
            "question": question,
            "top_k": top_k,
            "filename_filter": filename_filter,
            "stream": True,
            "session_id": session_id or self.session_id,
            "use_langchain": use_langchain
        }
        
        response = self.session.post(
            f"{self.base_url}/ask", 
            json=payload, 
            stream=True,
            headers={"Accept": "text/event-stream"}
        )
        response.raise_for_status()
        
        full_answer = ""
        sources = []
        final_session_id = session_id or self.session_id
        
        client = sseclient.SSEClient(response)
        for event in client.events():
            if event.event == "token":
                token = event.data
                full_answer += token
                yield token
            elif event.event == "sources":
                sources = json.loads(event.data)
            elif event.event == "session_id":
                final_session_id = event.data
            elif event.event == "end":
                break
        
        # Add to local history
        result = {
            "question": question,
            "answer": full_answer,
            "sources": sources,
            "session_id": final_session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        self.conversation_history.append(result)
        return result
    
    # === LangChain Specific Endpoints ===
    
    def ask_langchain(
        self, 
        question: str, 
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Direct LangChain endpoint"""
        payload = {
            "question": question,
            "session_id": session_id or self.session_id
        }
        
        response = self.session.post(f"{self.base_url}/langchain/ask", json=payload)
        response.raise_for_status()
        return response.json()
    
    def ask_agent(
        self, 
        question: str, 
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Use LangChain agent for complex questions"""
        payload = {
            "question": question,
            "session_id": session_id or self.session_id
        }
        
        response = self.session.post(f"{self.base_url}/langchain/agent", json=payload)
        response.raise_for_status()
        return response.json()
    
    # === File Management ===
    
    def upload_file(self, file_path: str, kategori: str = "document") -> Dict[str, Any]:
        """
        Upload PDF file
        
        Args:
            file_path: Path ke file PDF
            kategori: Kategori dokumen
        
        Returns:
            Dict dengan status upload
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path_obj.suffix.lower() == '.pdf':
            raise ValueError("Only PDF files are supported")
        
        with open(file_path_obj, 'rb') as f:
            files = {"file": (file_path_obj.name, f, "application/pdf")}
            data = {"kategori": kategori}
            
            response = self.session.post(
                f"{self.base_url}/upload", 
                files=files, 
                data=data
            )
        
        response.raise_for_status()
        return response.json()
    
    def list_files(self) -> List[Dict[str, Any]]:
        """List semua file yang telah diproses"""
        response = self.session.get(f"{self.base_url}/files")
        response.raise_for_status()
        return response.json()
    
    def delete_file(self, filename: str) -> Dict[str, Any]:
        """Delete file dan semua chunks-nya"""
        response = self.session.delete(f"{self.base_url}/files/{filename}")
        response.raise_for_status()
        return response.json()
    
    def build_vectorstore(self) -> Dict[str, Any]:
        """Build/rebuild vector database"""
        response = self.session.post(f"{self.base_url}/build-vectorstore")
        response.raise_for_status()
        return response.json()
    
    # === Session Management ===
    
    def get_sessions(self) -> Dict[str, Any]:
        """Get daftar semua sesi aktif"""
        response = self.session.get(f"{self.base_url}/sessions")
        response.raise_for_status()
        return response.json()
    
    def get_conversation_history(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get conversation history untuk session"""
        sid = session_id or self.session_id
        response = self.session.get(f"{self.base_url}/conversation/history/{sid}")
        response.raise_for_status()
        return response.json()
    
    def clear_conversation_history(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Clear conversation history"""
        sid = session_id or self.session_id
        response = self.session.delete(f"{self.base_url}/conversation/history/{sid}")
        response.raise_for_status()
        return response.json()
    
    def export_conversation(self, session_id: Optional[str] = None, save_path: Optional[str] = None) -> str:
        """
        Export conversation history sebagai JSON file
        
        Args:
            session_id: Session ID (default: client session)
            save_path: Path untuk menyimpan file (default: auto-generate)
        
        Returns:
            Path ke file yang disimpan
        """
        sid = session_id or self.session_id
        response = self.session.get(f"{self.base_url}/conversation/export/{sid}")
        response.raise_for_status()
        
        if not save_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"conversation_{sid[:8]}_{timestamp}.json"
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        return save_path
    
    def configure_conversation(
        self, 
        context_window: int = 3, 
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Configure conversation context window"""
        sid = session_id or self.session_id
        payload = {"context_window": context_window}
        
        response = self.session.post(
            f"{self.base_url}/conversation/config/{sid}", 
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    # === Search ===
    
    def search_documents(
        self, 
        query: str, 
        top_k: int = 5,
        filename_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search dokumen berdasarkan query
        
        Args:
            query: Query pencarian
            top_k: Jumlah hasil maksimal
            filename_filter: Filter berdasarkan nama file
        
        Returns:
            List hasil pencarian dengan similarity scores
        """
        params = {
            "query": query,
            "top_k": top_k
        }
        if filename_filter:
            params["filename_filter"] = filename_filter
            
        response = self.session.get(f"{self.base_url}/search", params=params)
        response.raise_for_status()
        return response.json()
    
    # === Utility Methods ===
    
    def print_status(self):
        """Print status sistem dan koneksi"""
        try:
            health = self.get_health()
            
            print("\n" + "="*50)
            print("🤖 TANYA MA'IL LANGCHAIN CLIENT STATUS")
            print("="*50)
            print(f"🌐 Server URL: {self.base_url}")
            print(f"🆔 Session ID: {self.session_id}")
            print(f"📊 System Status: {health.get('status', 'Unknown')}")
            print(f"🗄️ MongoDB: {'✅' if health.get('mongodb_connected') else '❌'}")
            print(f"🔍 ChromaDB: {'✅' if health.get('chroma_available') else '❌'}")
            print(f"🤖 OpenAI: {'✅' if health.get('openai_configured') else '❌'}")
            print(f"🦜 LangChain: {'✅' if health.get('langchain_available') else '❌'}")
            print(f"📁 Total Files: {health.get('total_files', 0)}")
            print(f"📄 Total Documents: {health.get('total_documents', 0)}")
            print(f"💬 Local History: {len(self.conversation_history)} exchanges")
            print("="*50)
            
        except Exception as e:
            print(f"❌ Status check failed: {e}")
    
    def start_interactive_chat(self, use_streaming: bool = True, use_langchain: bool = True):
        """
        Start interactive chat session
        
        Args:
            use_streaming: Gunakan streaming responses
            use_langchain: Gunakan sistem LangChain
        """
        print("\n🤖 Tanya Ma'il LangChain - Interactive Chat")
        print(f"💡 Mode: {'Streaming' if use_streaming else 'Normal'} | {'LangChain' if use_langchain else 'Legacy'}")
        print("💬 Ketik 'exit', 'quit', atau 'bye' untuk keluar")
        print("📋 Ketik '/help' untuk perintah khusus")
        print("-" * 50)
        
        while True:
            try:
                question = input("\n🔥 Pertanyaan: ").strip()
                
                if not question:
                    continue
                
                # Special commands
                if question.lower() in ['exit', 'quit', 'bye']:
                    print("👋 Goodbye!")
                    break
                elif question == '/help':
                    self._show_chat_help()
                    continue
                elif question == '/status':
                    self.print_status()
                    continue
                elif question == '/history':
                    self._show_local_history()
                    continue
                elif question == '/clear':
                    self.conversation_history.clear()
                    print("🧹 Local history cleared!")
                    continue
                elif question == '/files':
                    self._show_files()
                    continue
                elif question.startswith('/export'):
                    self._export_current_session()
                    continue
                
                print("\n🤖 Jawaban:", end=" ")
                
                if use_streaming:
                    # Streaming response
                    answer_tokens = []
                    try:
                        for token in self.ask_question_streaming(
                            question, 
                            use_langchain=use_langchain
                        ):
                            if isinstance(token, str):  # It's a token
                                print(token, end="", flush=True)
                                answer_tokens.append(token)
                    except Exception as e:
                        print(f"\n❌ Streaming error: {e}")
                        # Fallback to non-streaming
                        result = self.ask_question(question, use_langchain=use_langchain)
                        print(result["answer"])
                else:
                    # Non-streaming response
                    result = self.ask_question(question, use_langchain=use_langchain)
                    print(result["answer"])
                
                print()  # New line after answer
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    def _show_chat_help(self):
        """Show chat help commands"""
        help_text = """
📋 INTERACTIVE CHAT COMMANDS:
/help     - Show this help
/status   - Show system status  
/history  - Show local conversation history
/clear    - Clear local history
/files    - Show uploaded files
/export   - Export current session
exit/quit/bye - Exit chat
"""
        print(help_text)
    
    def _show_local_history(self):
        """Show local conversation history"""
        if not self.conversation_history:
            print("📝 No local conversation history")
            return
        
        print(f"\n📝 LOCAL CONVERSATION HISTORY ({len(self.conversation_history)} exchanges):")
        print("-" * 50)
        
        for i, exchange in enumerate(self.conversation_history[-5:], 1):  # Last 5
            print(f"\n{i}. Q: {exchange['question'][:100]}...")
            print(f"   A: {exchange['answer'][:150]}...")
            if exchange.get('sources'):
                print(f"   📚 Sources: {', '.join(exchange['sources'])}")
    
    def _show_files(self):
        """Show uploaded files"""
        try:
            files = self.list_files()
            if not files:
                print("📁 No files uploaded yet")
                return
            
            print(f"\n📁 UPLOADED FILES ({len(files)} files):")
            print("-" * 50)
            for file_info in files:
                print(f"📄 {file_info['filename']} ({file_info['chunks']} chunks)")
                if file_info.get('upload_date'):
                    print(f"   📅 Uploaded: {file_info['upload_date']}")
        except Exception as e:
            print(f"❌ Error listing files: {e}")
    
    def _export_current_session(self):
        """Export current session"""
        try:
            file_path = self.export_conversation()
            print(f"📁 Conversation exported to: {file_path}")
        except Exception as e:
            print(f"❌ Export failed: {e}")


def main():
    """Main function untuk command line usage"""
    parser = argparse.ArgumentParser(description="Tanya Ma'il LangChain Client")
    parser.add_argument(
        "--url", 
        default="http://localhost:8000",
        help="Base URL API server (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--session-id",
        help="Session ID untuk conversation continuity"
    )
    parser.add_argument(
        "--question", "-q",
        help="Single question to ask"
    )
    parser.add_argument(
        "--chat", "-c",
        action="store_true",
        help="Start interactive chat mode"
    )
    parser.add_argument(
        "--streaming", "-s",
        action="store_true",
        help="Use streaming responses (for chat mode)"
    )
    parser.add_argument(
        "--legacy",
        action="store_true", 
        help="Use legacy system instead of LangChain"
    )
    parser.add_argument(
        "--upload", "-u",
        help="Upload PDF file"
    )
    parser.add_argument(
        "--list-files", "-l",
        action="store_true",
        help="List uploaded files"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show system status"
    )
    
    args = parser.parse_args()
    
    # Initialize client
    client = TanyaMailLangChainClient(
        base_url=args.url,
        session_id=args.session_id
    )
    
    # Execute commands
    if args.status:
        client.print_status()
    elif args.upload:
        try:
            result = client.upload_file(args.upload)
            print(f"✅ Upload successful: {result}")
        except Exception as e:
            print(f"❌ Upload failed: {e}")
    elif args.list_files:
        try:
            files = client.list_files()
            print("\n📁 UPLOADED FILES:")
            for file_info in files:
                print(f"📄 {file_info['filename']} ({file_info['chunks']} chunks)")
        except Exception as e:
            print(f"❌ Failed to list files: {e}")
    elif args.question:
        try:
            result = client.ask_question(
                args.question,
                use_langchain=not args.legacy
            )
            print(f"\n🤖 Answer: {result['answer']}")
            if result.get('sources'):
                print(f"📚 Sources: {', '.join(result['sources'])}")
        except Exception as e:
            print(f"❌ Question failed: {e}")
    elif args.chat:
        client.start_interactive_chat(
            use_streaming=args.streaming,
            use_langchain=not args.legacy
        )
    else:
        # Default: show status
        client.print_status()


if __name__ == "__main__":
    main()
