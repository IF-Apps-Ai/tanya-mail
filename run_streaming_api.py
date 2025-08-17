#!/usr/bin/env python3
"""
Tanya Ma'il API Server with Streaming Support
Run this script to start the API server with real-time streaming capabilities
"""

import uvicorn
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Starting Tanya Ma'il API with Streaming Support")
    print("=" * 50)
    print("📍 API URL: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🔄 Swagger UI: http://localhost:8000/redoc")
    print("⚡ Streaming enabled for /ask endpoint")
    print("=" * 50)
    print("💡 Usage:")
    print("  - Set stream=true in request for streaming")
    print("  - Set stream=false for traditional response")
    print("=" * 50)
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        uvicorn.run(
            "api:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped!")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("📋 Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
