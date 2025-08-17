"""
Tanya Ma'il API Client with Streaming Support
Simple Python client for testing the Tanya Ma'il API with real-time streaming
"""

import requests
import json
import time
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Generator


class TanyaMailClient:
    """Client for interacting with Tanya Ma'il API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize client with API base URL"""
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def health_check(self) -> Dict[str, Any]:
        """Check API health status"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def upload_pdf(self, file_path: str) -> Dict[str, Any]:
        """Upload a PDF file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = self.session.post(
                f"{self.base_url}/upload", files=files)

        response.raise_for_status()
        return response.json()

    def list_files(self) -> List[Dict[str, Any]]:
        """List all processed PDF files"""
        response = self.session.get(f"{self.base_url}/files")
        response.raise_for_status()
        return response.json()

    def delete_file(self, filename: str) -> Dict[str, Any]:
        """Delete a file and all its chunks"""
        response = self.session.delete(f"{self.base_url}/files/{filename}")
        response.raise_for_status()
        return response.json()

    def build_vectorstore(self) -> Dict[str, Any]:
        """Build the vector store from processed documents"""
        response = self.session.post(f"{self.base_url}/build-vectorstore")
        response.raise_for_status()
        return response.json()

    def ask_question_stream(
        self,
        question: str,
        top_k: int = 3,
        filename_filter: Optional[str] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """Ask a question with streaming response"""
        data = {
            "question": question,
            "top_k": top_k,
            "stream": True
        }
        if filename_filter:
            data["filename_filter"] = filename_filter

        response = self.session.post(
            f"{self.base_url}/ask",
            json=data,
            stream=True,
            headers={'Accept': 'text/event-stream'}
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    try:
                        event_data = json.loads(line[6:])
                        yield event_data
                    except json.JSONDecodeError:
                        continue

    def ask_question(
        self,
        question: str,
        top_k: int = 3,
        filename_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Ask a question about the documents (non-streaming)"""
        data = {
            "question": question,
            "top_k": top_k,
            "stream": False
        }
        if filename_filter:
            data["filename_filter"] = filename_filter

        response = self.session.post(f"{self.base_url}/ask", json=data)
        response.raise_for_status()
        return response.json()

    def search_documents(
        self,
        query: str,
        top_k: int = 5,
        filename_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        params = {
            "query": query,
            "top_k": top_k
        }
        if filename_filter:
            params["filename_filter"] = filename_filter

        response = self.session.get(f"{self.base_url}/search", params=params)
        response.raise_for_status()
        return response.json()

    def get_conversation_history(self) -> Dict[str, Any]:
        """Get conversation history"""
        try:
            response = self.session.get(
                f"{self.base_url}/conversation/history")
            response.raise_for_status()
            return response.json()
        except:
            # Fallback if endpoint doesn't exist
            return {"history": [], "total_exchanges": 0, "session_id": "unknown"}

    def clear_conversation_history(self) -> Dict[str, Any]:
        """Clear conversation history"""
        try:
            response = self.session.delete(
                f"{self.base_url}/conversation/history")
            response.raise_for_status()
            return response.json()
        except:
            return {"message": "History cleared (if available)"}


def interactive_demo():
    """Interactive demo of the API client with streaming support"""
    print("🤖 Tanya Ma'il API Client Demo - Streaming Edition")
    print("=" * 50)

    client = TanyaMailClient()

    # Health check
    try:
        health = client.health_check()
        print(f"✅ API Status: {health.get('status', 'unknown')}")
        print(f"📊 Total documents: {health.get('total_documents', 0)}")
        print(f"📁 Total files: {health.get('total_files', 0)}")
    except Exception as e:
        print(f"❌ API not available: {e}")
        return

    while True:
        print("\n" + "=" * 50)
        print("Choose an option:")
        print("1. 📤 Upload PDF file")
        print("2. 📁 List files")
        print("3. 🔨 Build vector store")
        print("4. ⚡ Ask question (streaming)")
        print("5. 📝 Ask question (non-streaming)")
        print("6. 🔍 Search documents")
        print("7. 💬 View conversation history")
        print("8. 🗑️  Clear conversation history")
        print("9. 🗣️  Multi-turn conversation (streaming)")
        print("10. 📊 Compare streaming vs non-streaming")
        print("0. 🚪 Exit")

        choice = input("\nEnter choice (0-10): ").strip()

        try:
            if choice == "1":
                file_path = input("Enter PDF file path: ").strip()
                if file_path and os.path.exists(file_path):
                    print("⏳ Uploading and processing...")
                    result = client.upload_pdf(file_path)
                    print(f"✅ {result.get('message', 'Upload successful')}")
                else:
                    print("❌ File not found")

            elif choice == "2":
                files = client.list_files()
                if files:
                    print(f"📁 Found {len(files)} files:")
                    for file in files:
                        print(
                            f"   - {file.get('filename', 'unknown')}: {file.get('chunks', 0)} chunks")
                else:
                    print("📭 No files found")

            elif choice == "3":
                print("⏳ Building vector store...")
                result = client.build_vectorstore()
                print(f"✅ {result.get('message', 'Vector store built')}")

            elif choice == "4":
                # Streaming question
                question = input("Enter your question: ").strip()
                if question:
                    print(f"\n🤖 Assistant: ", end="", flush=True)
                    full_answer = ""
                    sources = []

                    try:
                        for event_data in client.ask_question_stream(question):
                            if event_data.get('type') == 'content':
                                token = event_data.get('token', '')
                                print(token, end="", flush=True)
                                full_answer += token
                            elif event_data.get('type') == 'source':
                                sources = event_data.get('sources', [])
                            elif event_data.get('type') == 'done':
                                print()  # New line after streaming
                                if sources:
                                    print(f"📚 Sources: {', '.join(sources)}")
                                break
                            elif event_data.get('type') == 'error':
                                print(f"\n❌ Error: {event_data.get('error')}")
                                break
                    except Exception as e:
                        print(f"\n❌ Streaming error: {e}")

            elif choice == "5":
                # Non-streaming question
                question = input("Enter your question: ").strip()
                if question:
                    print("⏳ Generating answer...")
                    try:
                        result = client.ask_question(question)
                        print(
                            f"\n🤖 Answer: {result.get('answer', 'No answer')}")
                        if result.get('sources'):
                            print(f"📚 Sources: {', '.join(result['sources'])}")
                    except Exception as e:
                        print(f"❌ Error: {e}")

            elif choice == "6":
                query = input("Enter search query: ").strip()
                if query:
                    try:
                        results = client.search_documents(query)
                        print(f"🔍 Found {len(results)} documents:")
                        for i, doc in enumerate(results, 1):
                            print(
                                f"\n{i}. File: {doc.get('filename', 'Unknown')}")
                            print(
                                f"   Content: {doc.get('content', '')[:200]}...")
                    except Exception as e:
                        print(f"❌ Search error: {e}")

            elif choice == "7":
                try:
                    history = client.get_conversation_history()
                    print(f"💬 Session: {history.get('session_id', 'Unknown')}")
                    print(
                        f"📊 Total exchanges: {history.get('total_exchanges', 0)}")
                    for i, exchange in enumerate(history.get('history', []), 1):
                        print(f"\n{i}. Q: {exchange.get('question', '')}")
                        print(f"   A: {exchange.get('answer', '')[:100]}...")
                except Exception as e:
                    print(f"❌ Error getting history: {e}")

            elif choice == "8":
                try:
                    result = client.clear_conversation_history()
                    print(f"✅ {result.get('message', 'History cleared')}")
                except Exception as e:
                    print(f"❌ Error clearing history: {e}")

            elif choice == "9":
                # Multi-turn streaming conversation
                print("🗣️ Multi-turn conversation mode (streaming)")
                print("Type 'exit' to return to main menu")
                print("-" * 40)

                while True:
                    question = input("\n💬 You: ").strip()
                    if question.lower() == 'exit':
                        break

                    if question:
                        print("🤖 Assistant: ", end="", flush=True)

                        try:
                            for event_data in client.ask_question_stream(question):
                                if event_data.get('type') == 'content':
                                    token = event_data.get('token', '')
                                    print(token, end="", flush=True)
                                elif event_data.get('type') == 'source':
                                    sources = event_data.get('sources', [])
                                elif event_data.get('type') == 'done':
                                    print()  # New line after streaming
                                    if sources:
                                        print(
                                            f"📚 Sources: {', '.join(sources)}")
                                    break
                                elif event_data.get('type') == 'error':
                                    print(
                                        f"\n❌ Error: {event_data.get('error')}")
                                    break
                        except Exception as e:
                            print(f"\n❌ Error: {e}")

            elif choice == "10":
                # Compare streaming vs non-streaming
                question = input("Enter question to compare: ").strip()
                if question:
                    print("\n📊 Comparing streaming vs non-streaming...")

                    # Non-streaming
                    print("\n⏳ Non-streaming response:")
                    start_time = time.time()
                    try:
                        result = client.ask_question(question)
                        non_streaming_time = time.time() - start_time
                        print(f"🤖 {result.get('answer', 'No answer')}")
                        print(f"⏱️ Total time: {non_streaming_time:.2f}s")
                    except Exception as e:
                        print(f"❌ Non-streaming failed: {e}")
                        non_streaming_time = 999

                    # Streaming
                    print(f"\n⚡ Streaming response:")
                    start_time = time.time()
                    first_token_time = None

                    print("🤖 ", end="", flush=True)
                    try:
                        for event_data in client.ask_question_stream(question):
                            if event_data.get('type') == 'content':
                                if first_token_time is None:
                                    first_token_time = time.time() - start_time
                                token = event_data.get('token', '')
                                print(token, end="", flush=True)
                            elif event_data.get('type') == 'done':
                                total_time = time.time() - start_time
                                print()
                                if first_token_time:
                                    print(
                                        f"⏱️ First token: {first_token_time:.2f}s")
                                    print(f"⏱️ Total time: {total_time:.2f}s")
                                    if non_streaming_time < 999:
                                        advantage = non_streaming_time - first_token_time
                                        print(
                                            f"🚀 Streaming advantage: {advantage:.2f}s faster to first token!")
                                break
                    except Exception as e:
                        print(f"\n❌ Streaming failed: {e}")

            elif choice == "0":
                print("👋 Goodbye!")
                break

            else:
                print("❌ Invalid choice")

        except Exception as e:
            print(f"❌ Error: {e}")


def test_api_flow():
    """Test the complete API flow with streaming support"""
    print("🧪 Testing Tanya Ma'il API Flow")
    print("=" * 40)

    client = TanyaMailClient()

    # Health check
    try:
        health = client.health_check()
        print(f"✅ Health check passed: {health.get('status', 'unknown')}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return

    # List files
    try:
        files = client.list_files()
        print(f"📁 Current files: {len(files)}")
        for file in files:
            print(
                f"   - {file.get('filename', 'unknown')}: {file.get('chunks', 0)} chunks")
    except Exception as e:
        print(f"❌ List files failed: {e}")

    # Try to build vector store
    try:
        result = client.build_vectorstore()
        print(f"🔍 Vector store: {result.get('message', 'Built successfully')}")
    except Exception as e:
        print(f"⚠️ Vector store build: {e}")

    # Test search (might be empty)
    try:
        results = client.search_documents("test query", top_k=3)
        print(f"🔍 Search results: {len(results)} documents found")
    except Exception as e:
        print(f"⚠️ Search failed: {e}")

    # Test streaming question
    try:
        print("❓ Testing streaming question...")
        print("🤖 ", end="", flush=True)

        for event_data in client.ask_question_stream("What is this document about?"):
            if event_data.get('type') == 'content':
                print(event_data.get('token', ''), end="", flush=True)
            elif event_data.get('type') == 'done':
                print()
                break

        print("✅ Streaming test completed")
    except Exception as e:
        print(f"⚠️ Streaming question failed: {e}")

    # Test non-streaming question
    try:
        result = client.ask_question("What is this document about?")
        print(
            f"❓ Non-streaming test: {result.get('answer', 'No answer')[:100]}...")
    except Exception as e:
        print(f"⚠️ Non-streaming question failed: {e}")

    # Test conversation features
    try:
        history = client.get_conversation_history()
        print(
            f"💬 Conversation history: {history.get('total_exchanges', 0)} exchanges")
    except Exception as e:
        print(f"❌ Conversation history failed: {e}")

    print("✅ API flow test completed")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_api_flow()
    else:
        interactive_demo()
