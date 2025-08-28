#!/usr/bin/env python3
"""
Example usage script for TanyaMailLangChainClient
Contoh penggunaan client untuk api_langchain.py
"""

from client_langchain import TanyaMailLangChainClient
import time


def example_basic_usage():
    """Basic usage example"""
    print("🚀 BASIC USAGE EXAMPLE")
    print("=" * 50)
    
    # Initialize client
    client = TanyaMailLangChainClient("http://localhost:8000")
    
    # Show system status
    client.print_status()
    
    # Ask a simple question (non-streaming)
    print("\n📝 Testing non-streaming question...")
    try:
        result = client.ask_question(
            "Apa itu akreditasi program studi?",
            top_k=3,
            use_langchain=True
        )
        print(f"🤖 Answer: {result['answer'][:200]}...")
        if result.get('sources'):
            print(f"📚 Sources: {', '.join(result['sources'])}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Show conversation history
    print(f"\n💬 Local conversation history: {len(client.conversation_history)} exchanges")


def example_streaming_chat():
    """Streaming chat example"""
    print("\n🔄 STREAMING EXAMPLE")
    print("=" * 50)
    
    client = TanyaMailLangChainClient("http://localhost:8000")
    
    questions = [
        "Apa persyaratan akreditasi?",
        "Bagaimana proses evaluasi?",
        "Siapa yang bisa mengajukan akreditasi?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{i}. 🔥 Question: {question}")
        print("🤖 Streaming Answer: ", end="", flush=True)
        
        try:
            # Stream the response token by token
            for token in client.ask_question_streaming(question, use_langchain=True):
                if isinstance(token, str):  # It's a token
                    print(token, end="", flush=True)
                    time.sleep(0.01)  # Small delay to see streaming effect
            print("\n" + "-" * 30)
        except Exception as e:
            print(f"\n❌ Streaming error: {e}")
            # Fallback to non-streaming
            try:
                result = client.ask_question(question, use_langchain=True)
                print(f"🤖 Fallback Answer: {result['answer']}")
            except Exception as e2:
                print(f"❌ Fallback also failed: {e2}")


def example_file_management():
    """File management example"""
    print("\n📁 FILE MANAGEMENT EXAMPLE")
    print("=" * 50)
    
    client = TanyaMailLangChainClient("http://localhost:8000")
    
    # List current files
    try:
        files = client.list_files()
        print(f"📄 Current files: {len(files)}")
        for file_info in files[:3]:  # Show first 3 files
            print(f"  📄 {file_info['filename']} ({file_info['chunks']} chunks)")
    except Exception as e:
        print(f"❌ Failed to list files: {e}")
    
    # Example upload (uncomment if you have a PDF file)
    # try:
    #     result = client.upload_file("example.pdf", "test document")
    #     print(f"✅ Upload result: {result}")
    # except Exception as e:
    #     print(f"❌ Upload failed: {e}")


def example_langchain_endpoints():
    """LangChain specific endpoints example"""
    print("\n🦜 LANGCHAIN ENDPOINTS EXAMPLE")
    print("=" * 50)
    
    client = TanyaMailLangChainClient("http://localhost:8000")
    
    # Direct LangChain endpoint
    try:
        print("📝 Testing direct LangChain endpoint...")
        result = client.ask_langchain("Bagaimana cara mendapatkan akreditasi internasional?")
        print(f"🤖 LangChain Answer: {result['answer'][:200]}...")
    except Exception as e:
        print(f"❌ LangChain endpoint error: {e}")
    
    # Agent endpoint
    try:
        print("\n🤖 Testing LangChain agent endpoint...")
        result = client.ask_agent("Berapa lama proses akreditasi?")
        print(f"🤖 Agent Answer: {result['answer'][:200]}...")
    except Exception as e:
        print(f"❌ Agent endpoint error: {e}")


def example_session_management():
    """Session management example"""
    print("\n👥 SESSION MANAGEMENT EXAMPLE")
    print("=" * 50)
    
    client = TanyaMailLangChainClient("http://localhost:8000")
    
    # Show active sessions
    try:
        sessions = client.get_sessions()
        print(f"📊 Active sessions: {sessions}")
    except Exception as e:
        print(f"❌ Failed to get sessions: {e}")
    
    # Show conversation history
    try:
        history = client.get_conversation_history()
        print(f"💬 Conversation history: {history.get('total_exchanges', 0)} exchanges")
    except Exception as e:
        print(f"❌ Failed to get history: {e}")
    
    # Export conversation
    try:
        if client.conversation_history:  # Only if we have local history
            file_path = client.export_conversation()
            print(f"📁 Exported conversation to: {file_path}")
    except Exception as e:
        print(f"❌ Failed to export: {e}")


def example_search():
    """Document search example"""
    print("\n🔍 SEARCH EXAMPLE")
    print("=" * 50)
    
    client = TanyaMailLangChainClient("http://localhost:8000")
    
    search_queries = [
        "akreditasi program studi",
        "standar kualitas pendidikan",
        "evaluasi eksternal"
    ]
    
    for query in search_queries:
        try:
            print(f"\n🔍 Searching for: '{query}'")
            results = client.search_documents(query, top_k=2)
            print(f"📄 Found {len(results)} results:")
            for i, result in enumerate(results[:2], 1):
                print(f"  {i}. {result.get('filename', 'Unknown')} - {result.get('content', '')[:100]}...")
        except Exception as e:
            print(f"❌ Search failed for '{query}': {e}")


def main():
    """Main example runner"""
    print("🤖 TANYA MA'IL LANGCHAIN CLIENT - EXAMPLES")
    print("=" * 60)
    
    examples = [
        ("Basic Usage", example_basic_usage),
        ("Streaming Chat", example_streaming_chat),
        ("File Management", example_file_management),
        ("LangChain Endpoints", example_langchain_endpoints),
        ("Session Management", example_session_management),
        ("Document Search", example_search),
    ]
    
    for name, func in examples:
        try:
            print(f"\n\n🎯 Running: {name}")
            print("=" * 60)
            func()
            time.sleep(1)  # Brief pause between examples
        except KeyboardInterrupt:
            print("\n\n👋 Examples interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Example '{name}' failed: {e}")
            continue
    
    print("\n\n✅ All examples completed!")
    print("💡 To start interactive chat, run: python client_langchain.py --chat")


if __name__ == "__main__":
    main()
