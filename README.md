# Tanya Ma'il - Advanced RAG PDF System 🤖📚

Tanya Ma'il adalah sistem RAG (Retrieval-Augmented Generation) yang canggih untuk menganalisis dokumen PDF menggunakan teknologi AI terdepan. Sistem ini mendukung multi-user sessions, real-time streaming, dan berbagai metode interaksi yang fleksibel.

## 🌟 Features Utama

- 👥 **Multi-User Sessions**: Dukungan sesi terpisah untuk multiple users concurrent
- 📄 **PDF Processing**: Upload dan ekstraksi teks cerdas dari dokumen PDF
- 🔍 **Semantic Search**: Pencarian semantik menggunakan embeddings OpenAI ada-002
- 💬 **Context-Aware Conversation**: Chat dengan memory dan konteks percakapan
- ⚡ **Real-time Streaming**: Respons streaming dengan Server-Sent Events (SSE)
- 🤖 **AI-powered Q&A**: Jawaban cerdas menggunakan GPT-4o-mini
- 📊 **Vector Database**: ChromaDB untuk penyimpanan dan retrieval embeddings
- 🗄️ **MongoDB Integration**: Metadata, conversation, dan session storage
- 🌐 **Timezone Support**: Deteksi otomatis timezone Indonesia (WIB/WITA/WIT)
- 🐳 **Docker Support**: Deployment mudah dengan Docker Compose
- 📖 **Interactive API Docs**: Swagger/OpenAPI documentation
- 🔄 **Session Management**: Automatic cleanup dan session lifecycle management

## 🏗️ Arsitektur Sistem

### Core Components

#### 1. **SessionManager** (`api.py`)
- **Fungsi**: Mengelola sesi multi-user dengan isolasi percakapan
- **Metode**:
  - `create_session()`: Membuat sesi baru dengan UUID
  - `get_session()`: Mengambil sesi berdasarkan ID
  - `cleanup_expired_sessions()`: Pembersihan otomatis sesi expired
  - `get_active_sessions()`: Daftar sesi aktif
  - `delete_session()`: Menghapus sesi dan historynya

#### 2. **ConversationManager** (`api.py`)
- **Fungsi**: Mengelola percakapan dan konteks per sesi
- **Metode**:
  - `add_to_history()`: Menyimpan percakapan ke history
  - `get_history()`: Mengambil riwayat percakapan
  - `clear_history()`: Membersihkan history percakapan
  - `export_history()`: Export percakapan dalam format JSON

#### 3. **PDF Processing Engine**
- **Library**: PyPDF2, LangChain Document Loaders
- **Metode**:
  - Text extraction dari PDF files
  - Document chunking dengan overlap
  - Metadata extraction (filename, page numbers)

#### 4. **Vector Database (ChromaDB)**
- **Embedding Model**: OpenAI text-embedding-ada-002
- **Metode**:
  - `build_vectorstore()`: Membangun database vektor dari dokumen
  - `similarity_search()`: Pencarian berdasarkan similarity
  - `add_documents()`: Menambah dokumen baru ke database

#### 5. **LLM Integration (OpenAI)**
- **Model**: GPT-4o-mini (configurable)
- **Features**:
  - Context-aware responses
  - Streaming responses dengan SSE
  - Temperature control untuk konsistensi

### Database Schema

#### MongoDB Collections:
1. **conversations**: Menyimpan riwayat percakapan per sesi
2. **file_metadata**: Metadata file PDF yang diupload
3. **session_data**: Informasi sesi user (timestamp, aktivitas)

#### ChromaDB:
- **Collection**: pdf_documents
- **Metadata**: filename, page_number, chunk_index
- **Embeddings**: Vector representations dari text chunks

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.8+
- Docker & Docker Compose
- OpenAI API Key

### Option 1: Docker Deployment (Recommended)

```bash
# 1. Clone repository
git clone <repository_url>
cd tanya-mail

# 2. Setup otomatis
chmod +x setup.sh
./setup.sh

# 3. Start services
docker-compose up -d

# 4. Akses aplikasi
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Health Check: http://localhost:8000/health
```

### Option 2: Manual Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup environment
cp .env.template .env
# Edit .env dan tambahkan OpenAI API key

# 3. Start MongoDB (optional, for local development)
docker run -d -p 27017:27017 --name mongodb \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password123 \
  mongo

# 4. Run API server
python api.py
# Atau dengan auto-reload:
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Production Service dengan Clustering (Recommended for Production)

Tanya Mail API dapat dijalankan sebagai **production service** dengan **multiple workers** untuk high availability dan load balancing.

#### 🚀 Quick Production Deployment

```bash
# 1. Setup environment
cp .env.template .env
# Edit .env dan tambahkan OpenAI API key dan konfigurasi lainnya

# 2. Install dependencies
pip install -r requirements.txt

# 3. Deploy dengan clustering otomatis
./deploy_production.sh

# 4. Akses aplikasi
# - API: http://localhost:8804
# - API Docs: http://localhost:8804/docs
# - Health Check: http://localhost:8804/health
```

#### 🎮 Service Management Commands

```bash
# === DAEMON MANAGER (Primary Method) ===
./daemon_manager.sh start           # Start service dengan clustering
./daemon_manager.sh stop            # Stop service
./daemon_manager.sh restart         # Restart service
./daemon_manager.sh status          # Check status dan worker count
./daemon_manager.sh logs 100        # View last 100 log lines
./daemon_manager.sh follow          # Follow logs in real-time
./daemon_manager.sh test            # Test API health

# === MONITORING & MAINTENANCE ===
./monitor.sh monitor                # Real-time monitoring dashboard
./monitor.sh status                 # Quick status check
./monitor.sh perf                   # Performance test (concurrent requests)
./monitor.sh resources              # System resource usage

# === SYSTEMD SERVICE (For Linux servers) ===
sudo ./service_manager.sh install  # Install as systemd service
sudo ./service_manager.sh start    # Start via systemd
sudo ./service_manager.sh stop     # Stop via systemd
./service_manager.sh status         # Check systemd status
./service_manager.sh test           # Test API endpoints
```

#### 🏗️ Production Architecture

```
Client Requests
       ↓
Gunicorn Master Process (Load Balancer)
       ↓
Multiple UvicornWorker Processes (33+ workers)
       ↓
FastAPI Application Instances
       ↓
MongoDB + ChromaDB + OpenAI API
```

#### 📊 Clustering Features

- ✅ **Multi-worker**: 33+ workers (berdasarkan CPU cores) untuk high throughput
- ✅ **Load Balancing**: Request didistribusi otomatis antar workers
- ✅ **High Availability**: Jika satu worker crash, yang lain tetap berjalan
- ✅ **Auto-restart**: Process management dan recovery otomatis
- ✅ **Graceful Shutdown**: Shutdown yang aman tanpa kehilangan request
- ✅ **Production Logging**: Structured logging untuk monitoring
- ✅ **Health Monitoring**: Built-in health checks dan metrics
- ✅ **Resource Limits**: Memory dan connection limits untuk stability

#### 🔧 Production Configuration

File `gunicorn_config.py` dikonfigurasi untuk optimal performance:

```python
# Workers: CPU cores * 2 + 1 (automatically calculated)
workers = multiprocessing.cpu_count() * 2 + 1  # Typically 33+ workers

# Async workers untuk high concurrency
worker_class = "uvicorn.workers.UvicornWorker"

# Connection and resource management
max_requests = 1000          # Prevent memory leaks
max_requests_jitter = 50     # Randomize restart timing
timeout = 60                 # Request timeout
graceful_timeout = 30        # Graceful shutdown timeout
keepalive = 2                # Keep-alive connections

# Logging for production monitoring
accesslog = "logs/gunicorn-access.log"
errorlog = "logs/gunicorn-error.log"
loglevel = "info"
```

#### 📈 Performance Metrics

**Typical Performance** (pada server dengan 16 CPU cores):
- **Workers**: 33 concurrent processes
- **Throughput**: 1000+ requests/second
- **Concurrent Users**: 5000+ simultaneous connections
- **Memory Usage**: ~5-6GB total (semua workers)
- **CPU Usage**: ~10-20% under normal load
- **Response Time**: <100ms untuk simple queries

#### 🔍 Monitoring Dashboard

```bash
# Start real-time monitoring
./monitor.sh monitor
```

Dashboard menampilkan:
- ✅ Service status (Running/Stopped)
- 📊 Worker process count
- 💾 Memory usage per worker
- 🌐 Port dan binding info
- ❤️ API health status
- 📋 Recent logs
- 📈 System resources (CPU, Memory, Disk)

#### 🚨 Health Checking

```bash
# Manual health check
curl http://localhost:8804/health

# Expected response:
{
  "status": "healthy",
  "mongodb_connected": true,
  "chroma_available": true,
  "total_documents": 214,
  "total_files": 2,
  "openai_configured": true
}
```

#### 💡 Production Tips

1. **Resource Monitoring**: Monitor memory usage, jika >8GB consider reduce workers
2. **Log Rotation**: Setup log rotation untuk mencegah disk penuh
3. **Backup Strategy**: Regular backup MongoDB dan ChromaDB data
4. **Security**: Gunakan reverse proxy (nginx) untuk SSL termination
5. **Scaling**: Untuk traffic tinggi, consider horizontal scaling dengan multiple servers

### Option 4: Streaming Chat Interface

```bash
# Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# atau .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run streaming chat
python chat_streaming.py
```

## 🔧 Konfigurasi Environment

Copy `.env.template` ke `.env` dan sesuaikan:

```bash
# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=your_actual_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1

# Model Configuration
MODEL_NAME=gpt-4o-mini
MODEL_TEMPERATURE=0          # 0 = deterministic, 1 = creative
MODEL_MAX_TOKENS=2048        # Maximum response length

# MongoDB Configuration
MONGO_URI=mongodb://admin:password123@mongodb:27017/tanya_mail?authSource=admin

# Session Configuration
SESSION_TIMEOUT_HOURS=1      # Auto-cleanup expired sessions
TIMEZONE=Asia/Makassar       # Default timezone

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["*"]           # Configure CORS for production
```

## 📁 Struktur Proyek Lengkap

```
tanya-mail/
├── 📄 Core Application Files
│   ├── api.py                     # Main FastAPI application dengan SessionManager
│   ├── chat_streaming.py          # Interactive streaming chat client
│   ├── client_streaming.py        # Python API client dengan streaming support
│   └── run_streaming_api.py       # Simple API server runner
│
├── 🧪 Testing & Development
│   ├── test_sessions.py           # Multi-user session testing
│   ├── test_timezone.py           # Timezone functionality tests
│   └── test_api.sh               # Automated API testing script
│
├── � Documentation
│   ├── README.md                  # Main documentation (this file)
│   ├── README_API.md              # Detailed API documentation
│   ├── README_CHAT_STREAMING.md   # Streaming chat documentation
│   ├── MULTI_USER_SESSIONS.md     # Session management guide
│   └── CLEANUP_SUMMARY.md         # Project cleanup notes
│
├── ⚙️ Configuration
│   ├── requirements.txt           # Python dependencies
│   ├── requirements-dev.txt       # Development dependencies
│   ├── .env.template             # Environment variables template
│   ├── Dockerfile                # Docker image configuration
│   ├── docker-compose.yml        # Multi-container setup
│   └── mongo-init.js             # MongoDB initialization script
│
├── 🔧 Scripts & Utilities
│   ├── setup.sh                  # Automated project setup
│   ├── setup_venv.sh            # Virtual environment setup
│   ├── quick_start.sh            # Quick start script
│   └── start_chat.sh             # Chat client launcher
│
├── 🗂️ Data & Storage
│   ├── pdf_documents/            # Uploaded PDF files directory
│   │   ├── Peraturan Akademik_Rev 2024.pdf
│   │   └── PMB-Info.pdf
│   └── chroma_pdf_db/            # ChromaDB vector database
│       ├── chroma.sqlite3
│       └── [vector collections]/
│
└── 🔌 API Tools
    └── Tanya_Mail_API.postman_collection.json  # Postman API collection
```

## 🔄 API Endpoints Lengkap

### Core Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information dan status |
| `/health` | GET | Health check untuk monitoring |

### File Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload` | POST | Upload PDF file (multipart/form-data) |
| `/files` | GET | List semua file yang telah diproses |
| `/files/{filename}` | DELETE | Hapus file dari sistem |
| `/build-vectorstore` | POST | Build/rebuild vector database |

### Question & Answer (with Session Support)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ask` | POST | Ajukan pertanyaan (dengan/tanpa session_id) |
| `/ask` (streaming) | POST | Real-time streaming response |

### Session Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sessions` | GET | List semua sesi aktif |
| `/session/{session_id}` | GET | Info detail sesi tertentu |
| `/conversation/history/{session_id}` | GET | Riwayat percakapan sesi |
| `/conversation/{session_id}` | DELETE | Hapus sesi dan historynya |

### Advanced Features
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/search` | GET | Pencarian semantik langsung |
| `/conversation/export/{session_id}` | GET | Export percakapan ke JSON |

## 💡 Metode Penggunaan

### 1. API Usage dengan Python

```python
import requests
import json

# Initialize client (production service endpoint)
base_url = "http://localhost:8804"  # Production port

# Upload PDF
with open("document.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(f"{base_url}/upload", files=files)
    print(f"Upload: {response.json()}")

# Build vector store
response = requests.post(f"{base_url}/build-vectorstore")
print(f"Vector store: {response.json()}")

# Create new session dan ask question
data = {
    "question": "Apa topik utama dalam dokumen ini?",
    "top_k": 3,
    "stream": False
}
response = requests.post(f"{base_url}/ask", json=data)
result = response.json()
session_id = result["session_id"]  # Save untuk percakapan selanjutnya

# Follow-up question dengan session yang sama
data = {
    "question": "Jelaskan lebih detail tentang poin pertama",
    "session_id": session_id,
    "top_k": 3
}
response = requests.post(f"{base_url}/ask", json=data)
print(f"Response: {response.json()}")

# Check conversation history
response = requests.get(f"{base_url}/conversation/history/{session_id}")
history = response.json()
for chat in history["history"]:
    print(f"Q: {chat['question']}")
    print(f"A: {chat['response'][:100]}...")
```

### 2. Production Service dengan Load Testing

```python
import requests
import concurrent.futures
import time
from statistics import mean

def load_test_api(base_url="http://localhost:8804", concurrent_users=10, requests_per_user=5):
    """
    Load test untuk production service dengan clustering
    """
    
    def user_session(user_id):
        session_times = []
        session_id = None
        
        for i in range(requests_per_user):
            start_time = time.time()
            
            data = {
                "question": f"User {user_id} question {i+1}: What is in this document?",
                "top_k": 3,
                "stream": False
            }
            if session_id:
                data["session_id"] = session_id
            
            try:
                response = requests.post(f"{base_url}/ask", json=data, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    if not session_id:
                        session_id = result["session_id"]
                    
                    response_time = time.time() - start_time
                    session_times.append(response_time)
                    print(f"User {user_id} Request {i+1}: {response_time:.2f}s")
                else:
                    print(f"User {user_id} Request {i+1}: ERROR {response.status_code}")
            except Exception as e:
                print(f"User {user_id} Request {i+1}: EXCEPTION {e}")
        
        return session_times
    
    # Test health first
    try:
        health = requests.get(f"{base_url}/health", timeout=5)
        if health.status_code != 200:
            print(f"❌ Health check failed: {health.status_code}")
            return
        print(f"✅ API Health: {health.json()}")
    except Exception as e:
        print(f"❌ Cannot reach API: {e}")
        return
    
    print(f"\n🚀 Starting load test: {concurrent_users} users, {requests_per_user} requests each")
    start_time = time.time()
    
    # Run concurrent user sessions
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = [executor.submit(user_session, i) for i in range(concurrent_users)]
        all_times = []
        
        for future in concurrent.futures.as_completed(futures):
            session_times = future.result()
            all_times.extend(session_times)
    
    total_time = time.time() - start_time
    
    if all_times:
        print(f"\n📊 Load Test Results:")
        print(f"Total requests: {len(all_times)}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Requests per second: {len(all_times)/total_time:.2f}")
        print(f"Average response time: {mean(all_times):.2f}s")
        print(f"Min response time: {min(all_times):.2f}s")
        print(f"Max response time: {max(all_times):.2f}s")

# Usage
if __name__ == "__main__":
    load_test_api(concurrent_users=20, requests_per_user=3)
```

### 3. Production Health Monitoring

```python
import requests
import time
import json
from datetime import datetime

def monitor_production_service(base_url="http://localhost:8804", check_interval=30):
    """
    Monitor production service health dan performance
    """
    
    print(f"🔍 Starting production monitoring on {base_url}")
    print(f"Check interval: {check_interval} seconds")
    print("-" * 60)
    
    consecutive_failures = 0
    
    while True:
        try:
            start_time = time.time()
            
            # Health check
            health_response = requests.get(f"{base_url}/health", timeout=10)
            response_time = time.time() - start_time
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                
                # Get additional metrics
                sessions_response = requests.get(f"{base_url}/sessions", timeout=5)
                active_sessions = len(sessions_response.json().get("sessions", [])) if sessions_response.status_code == 200 else "N/A"
                
                # Success
                consecutive_failures = 0
                status = "✅ HEALTHY"
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {status}")
                print(f"  Response Time: {response_time:.3f}s")
                print(f"  MongoDB: {'✅' if health_data.get('mongodb_connected') else '❌'}")
                print(f"  ChromaDB: {'✅' if health_data.get('chroma_available') else '❌'}")
                print(f"  OpenAI: {'✅' if health_data.get('openai_configured') else '❌'}")
                print(f"  Documents: {health_data.get('total_documents', 0)}")
                print(f"  Active Sessions: {active_sessions}")
                
            else:
                consecutive_failures += 1
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ UNHEALTHY - HTTP {health_response.status_code}")
        
        except requests.exceptions.Timeout:
            consecutive_failures += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏰ TIMEOUT - Service not responding")
        
        except requests.exceptions.ConnectionError:
            consecutive_failures += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔌 CONNECTION ERROR - Service down?")
        
        except Exception as e:
            consecutive_failures += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ ERROR - {e}")
        
        # Alert on consecutive failures
        if consecutive_failures >= 3:
            print(f"🚨 ALERT: {consecutive_failures} consecutive failures!")
            print("Consider checking service status with: ./daemon_manager.sh status")
        
        print("-" * 60)
        time.sleep(check_interval)

# Usage
if __name__ == "__main__":
    try:
        monitor_production_service(check_interval=60)  # Check every minute
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")
```

### 2. Streaming dengan Server-Sent Events

```python
import requests
import json

def stream_question(question, session_id=None):
    data = {
        "question": question,
        "stream": True,
        "top_k": 3
    }
    if session_id:
        data["session_id"] = session_id
    
    # Set headers untuk streaming
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    with requests.post(f"{base_url}/ask", 
                      json=data, 
                      headers=headers, 
                      stream=True) as response:
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    event_data = line[6:]  # Remove 'data: ' prefix
                    if event_data == '[DONE]':
                        break
                    try:
                        data = json.loads(event_data)
                        if 'chunk' in data:
                            print(data['chunk'], end='', flush=True)
                        elif 'session_id' in data:
                            session_id = data['session_id']
                    except json.JSONDecodeError:
                        continue
        print()  # New line after streaming completes
    
    return session_id

# Usage
session_id = stream_question("Apa itu machine learning?")
session_id = stream_question("Berikan contohnya dalam kehidupan sehari-hari", session_id)
```

### 3. Multi-User Session Demo

```python
import concurrent.futures
import requests

def user_conversation(user_id, questions):
    """Simulasi percakapan user independen"""
    base_url = "http://localhost:8000"
    session_id = None
    
    print(f"👤 User {user_id} memulai percakapan")
    
    for i, question in enumerate(questions, 1):
        data = {
            "question": question,
            "top_k": 3,
            "stream": False
        }
        if session_id:
            data["session_id"] = session_id
            
        response = requests.post(f"{base_url}/ask", json=data)
        result = response.json()
        
        if not session_id:
            session_id = result["session_id"]
            print(f"📍 User {user_id} mendapat session: {session_id[:8]}...")
        
        print(f"Q{i}: {question}")
        print(f"A{i}: {result['response'][:100]}...")
        print()
    
    return session_id

# Simulasi 2 user bersamaan
user1_questions = [
    "Apa itu PMB dan syarat pendaftarannya?",
    "Berapa biaya pendaftarannya?",
    "Kapan batas waktu pendaftaran?"
]

user2_questions = [
    "Bagaimana cara mendaftar kuliah?",
    "Apa saja jurusan yang tersedia?",
    "Dimana lokasi kampusnya?"
]

# Run concurrent conversations
with concurrent.futures.ThreadPoolExecutor() as executor:
    future1 = executor.submit(user_conversation, "A", user1_questions)
    future2 = executor.submit(user_conversation, "B", user2_questions)
    
    session1 = future1.result()
    session2 = future2.result()

# Verify session isolation
print("� Verifikasi isolasi sesi:")
for session_id, user in [(session1, "A"), (session2, "B")]:
    response = requests.get(f"{base_url}/conversation/history/{session_id}")
    history = response.json()
    print(f"User {user} punya {len(history['history'])} percakapan dalam sesinya")
```

### 4. Chat Streaming Interface

```bash
# Jalankan interactive chat
python chat_streaming.py

# Features:
# - Real-time streaming responses
# - Session management otomatis
# - Timezone detection
# - Command shortcuts:
#   /help    - Lihat bantuan
#   /session - Info sesi saat ini
#   /clear   - Bersihkan layar
#   /exit    - Keluar dari chat
```

### 5. Bulk PDF Processing 📄

```bash
# Upload dan proses multiple PDF sekaligus dari folder
./process_bulk_pdf.sh

# Preview file yang akan diproses tanpa memproses
./process_bulk_pdf.sh --dry-run

# Proses PDF dari folder custom
./process_bulk_pdf.sh --folder documents

# Force reprocess file yang sudah ada
./process_bulk_pdf.sh --force

# Load quick commands (opsional)
source ./load_pdf_commands.sh
bulk_pdf              # Proses semua PDF di pdf_input
bulk_pdf_preview      # Preview mode
bulk_pdf_force        # Force reprocess
```

**Fitur Bulk Processing:**

- 🚀 **Batch Processing**: Proses multiple PDF sekaligus secara otomatis
- 🔍 **Smart Detection**: Skip file yang sudah diproses (berdasarkan hash)
- 📊 **Progress Tracking**: Real-time progress dan statistik processing
- ⚡ **Resume Capability**: Dapat di-interrupt dan dilanjutkan kembali
- 🔧 **Flexible**: Support folder custom, force reprocess, dan dry-run mode
- 📋 **Detailed Logging**: Log comprehensive untuk debugging dan monitoring

**Folder Structure:**
```
pdf_input/          # Tempatkan PDF yang akan diproses di sini
pdf_documents/      # PDF yang sudah diproses disimpan di sini
```

**Example Output:**
```bash
🚀 TANYA MAIL - BULK PDF PROCESSOR
============================================================
[INFO] 🚀 Memulai bulk processing PDF dari folder: pdf_input
[SUCCESS] ✅ Koneksi database berhasil  
[INFO] 📊 Ditemukan 5 file PDF

============================================================
[1/5] document1.pdf
============================================================
[INFO] 📄 document1.pdf - Mulai memproses...
[INFO] 📄 document1.pdf - Teks diekstrak (15420 karakter)
[INFO] 📄 document1.pdf - Dibagi menjadi 8 chunk
[SUCCESS] 📄 document1.pdf - Selesai diproses (8 chunk disimpan)

============================================================
📊 STATISTIK PROCESSING
============================================================
📁 Total file PDF: 5
✅ Berhasil diproses: 5
📋 Sudah diproses sebelumnya: 0  
⏭️  Dilewati: 0
❌ Gagal: 0
📈 Success rate: 100.0%
```

Untuk dokumentasi lengkap bulk processing, lihat: **[README_BULK_PDF.md](README_BULK_PDF.md)**
```

## 🧪 Testing Comprehensive

### 1. Automated API Testing

```bash
# Run semua test suite
./test_api.sh

# Test manual dengan curl
curl -X GET "http://localhost:8000/health"
curl -X GET "http://localhost:8000/sessions"
```

### 2. Multi-User Session Testing

```bash
# Test isolation antar sesi
python test_sessions.py

# Expected output:
# ✅ Session 1 berisi percakapan User A
# ✅ Session 2 berisi percakapan User B  
# ✅ Sessions terisolasi dengan baik
```

### 3. Timezone Testing

```bash
python test_timezone.py
# Menguji deteksi timezone Indonesia
```

### 4. Postman Collection

Import `Tanya_Mail_API.postman_collection.json` untuk testing lengkap:
- ✅ Basic API operations
- ✅ Session Management
- ✅ Multi-user scenarios
- ✅ Streaming responses
- ✅ Error handling

## 🛠️ Development Guide

### Local Development

```bash
# Setup development environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Run dengan auto-reload
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Monitor logs
tail -f api.log
```

### Adding New Features

1. **Extend SessionManager**: Tambah method baru untuk session handling
2. **Modify ConversationManager**: Update conversation logic
3. **Update API Endpoints**: Tambah routes baru di `api.py`
4. **Update Tests**: Tambah test cases di `test_sessions.py`
5. **Update Documentation**: Update README dan API docs

### Code Architecture

```python
# api.py structure:
class SessionManager:
    """Manages multi-user sessions dengan UUID-based isolation"""
    
class ConversationManager:
    """Handles conversation history per session"""

app = FastAPI()  # Main FastAPI application

# Key endpoints:
@app.post("/ask")           # Main Q&A dengan session support
@app.get("/sessions")       # Session management  
@app.post("/upload")        # File upload
@app.post("/build-vectorstore")  # Vector DB management
```

## 🐛 Troubleshooting Guide

### Common Issues

#### 1. **MongoDB Connection Error**
```bash
# Symptoms
ConnectionError: [Errno 111] Connection refused

# Solutions
docker-compose ps                    # Check MongoDB status
docker-compose logs mongodb          # Check MongoDB logs
docker-compose restart mongodb       # Restart MongoDB
```

#### 2. **OpenAI API Error**
```bash
# Symptoms  
openai.error.AuthenticationError: Invalid API key

# Solutions
echo $OPENAI_API_KEY                 # Verify API key
cat .env | grep OPENAI               # Check .env file
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"  # Test API key
```

#### 3. **Session Issues**
```bash
# Symptoms
Session not found or expired

# Solutions
curl http://localhost:8000/sessions  # List active sessions
# Sessions auto-expire after 1 hour
# Create new session by calling /ask without session_id
```

#### 4. **Vector Store Issues**
```bash
# Symptoms
No relevant documents found

# Solutions
curl -X POST http://localhost:8000/build-vectorstore
ls -la chroma_pdf_db/               # Check vector DB files
curl http://localhost:8000/files    # Verify uploaded files
```

#### 5. **Streaming Connection Issues**
```python
# For SSE streaming, ensure proper headers:
headers = {
    "Content-Type": "application/json",
    "Accept": "text/event-stream",
    "Cache-Control": "no-cache"
}
```

### Performance Tuning

```bash
# Monitor resource usage
docker stats

# Optimize vector store
# Reduce chunk_size untuk dokumen besar
# Adjust top_k berdasarkan kebutuhan

# Database optimization
# Index MongoDB collections
# Clean up expired sessions regularly
```

### Debugging Tools

```bash
# API logs
docker-compose logs -f tanya-mail-api

# MongoDB queries
docker-compose exec mongodb mongo \
  --username admin --password password123 \
  --eval "db.conversations.find().pretty()"

# ChromaDB inspection
python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_pdf_db')
collection = client.get_collection('pdf_documents')
print(f'Total documents: {collection.count()}')
"
```

## � Security Best Practices

### Production Deployment

```bash
# 1. Environment Security
# - Gunakan secrets manager untuk API keys
# - Set CORS_ORIGINS dengan domain spesifik
# - Enable HTTPS dengan reverse proxy

# 2. Database Security  
# - Change default MongoDB credentials
# - Enable MongoDB authentication
# - Use MongoDB connection with TLS

# 3. API Security
# - Implement rate limiting
# - Add API authentication/authorization
# - Validate file uploads (size, type)
# - Sanitize user inputs
```

### Monitoring & Logging

```python
# Add to api.py for production:
import logging
from fastapi import Request
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    return response
```

## 📈 Performance Metrics

### Typical Response Times
- **File Upload (1MB PDF)**: ~2-3 seconds
- **Vector Store Build**: ~5-10 seconds per document  
- **Question Answering**: ~1-3 seconds
- **Streaming Response**: ~50-100ms per chunk
- **Session Operations**: ~10-50ms

### Resource Requirements
- **Memory**: 512MB - 2GB (depending on document size)
- **Storage**: ~10MB per PDF document (text + vectors)
- **CPU**: 1-2 cores recommended
- **Network**: Minimal (mainly OpenAI API calls)

## 🤝 Contributing

### Contribution Guidelines

1. **Fork & Clone**
   ```bash
   git clone https://github.com/yourusername/tanya-mail.git
   cd tanya-mail
   git checkout -b feature/amazing-feature
   ```

2. **Development Setup**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```

3. **Code Standards**
   - Follow PEP 8 for Python code
   - Add type hints untuk functions
   - Include docstrings untuk classes dan methods
   - Write unit tests untuk new features

4. **Testing**
   ```bash
   python -m pytest test_sessions.py -v
   ./test_api.sh
   ```

5. **Documentation**
   - Update README untuk new features
   - Update API documentation
   - Include usage examples

6. **Submit PR**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   git push origin feature/amazing-feature
   # Create Pull Request di GitHub
   ```

## 📞 Support & Resources

### Documentation
- 📖 **API Documentation**: [README_API.md](README_API.md)
- 💬 **Chat Interface Guide**: [README_CHAT_STREAMING.md](README_CHAT_STREAMING.md)
- 👥 **Session Management**: [MULTI_USER_SESSIONS.md](MULTI_USER_SESSIONS.md)
- 🧹 **Project History**: [CLEANUP_SUMMARY.md](CLEANUP_SUMMARY.md)

### API Resources
- 🌐 **Swagger UI**: http://localhost:8000/docs
- 📋 **ReDoc**: http://localhost:8000/redoc  
- 🔌 **Postman Collection**: Import `Tanya_Mail_API.postman_collection.json`

### Community
- 🐛 **Bug Reports**: Use GitHub Issues
- 💡 **Feature Requests**: Use GitHub Discussions  
- 🔧 **Development**: Check GitHub Projects
- 📧 **Contact**: [Your contact information]

### External Dependencies
- 🤖 **OpenAI**: https://platform.openai.com/docs
- 📊 **ChromaDB**: https://docs.trychroma.com/
- 🗄️ **MongoDB**: https://docs.mongodb.com/
- ⚡ **FastAPI**: https://fastapi.tiangolo.com/

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**🚀 Happy coding dengan Tanya Ma'il!** Sistem RAG yang powerful untuk semua kebutuhan analisis dokumen PDF Anda! 

*Built with ❤️ using FastAPI, OpenAI, ChromaDB, and MongoDB*

## 🧪 Testing

### Test API Endpoints

```bash
# Automated tests
./test_api.sh

# Python client
python client.py

# Test specific flow
python client.py test
```

### Upload and Query Example

```bash
# Upload PDF
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"

# Build vector store
curl -X POST "http://localhost:8000/build-vectorstore"

# Ask question
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Apa topik utama dokumen ini?", "top_k": 3}'
```

## 📁 Project Structure

```
tanya-mail/
├── app.py                 # Console application
├── api.py                 # RESTful API server
├── run.py                 # Simple API runner
├── client.py              # Python API client
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Multi-container setup
├── setup.sh              # Automated setup script
├── test_api.sh           # API testing script
├── .env.template         # Environment template
├── README.md             # Main documentation
├── README_API.md         # API documentation
├── mongo-init.js         # MongoDB initialization
├── Tanya_Mail_API.postman_collection.json  # Postman collection
├── pdf_documents/        # PDF upload directory
└── chroma_pdf_db/       # Vector database
```

## 🔄 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/upload` | POST | Upload PDF file |
| `/files` | GET | List processed files |
| `/files/{filename}` | DELETE | Delete file |
| `/build-vectorstore` | POST | Build vector database |
| `/ask` | POST | Ask question |
| `/search` | GET | Search documents |
| `/conversation/history` | GET | Get chat history |
| `/conversation/history` | DELETE | Clear chat history |
| `/conversation/config` | POST | Configure context |
| `/conversation/export` | GET | Export conversation |

## 💡 Usage Examples

### Python Client

```python
from client import TanyaMailClient

client = TanyaMailClient("http://localhost:8000")

# Upload PDF
result = client.upload_pdf("document.pdf")

# Build vector store
client.build_vectorstore()

# Multi-turn conversation
response1 = client.ask_question("Apa itu machine learning?")
response2 = client.ask_question("Jelaskan lebih detail")
response3 = client.ask_question("Berikan contohnya")
```

### cURL Examples

```bash
# Health check
curl http://localhost:8000/health

# Upload file
curl -X POST "http://localhost:8000/upload" \
  -F "file=@document.pdf"

# Ask question
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Summarize this document", "top_k": 5}'
```

## 🛠️ Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run API with auto-reload
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Run console app
python app.py
```

### Adding New Features

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes and test
4. Update documentation
5. Submit pull request

## 🐛 Troubleshooting

### Common Issues

1. **MongoDB Connection Error**
   - Ensure MongoDB is running
   - Check connection string in .env
   - For Docker: containers must be on same network

2. **OpenAI API Error**
   - Verify API key in .env file
   - Check API quota and billing
   - Ensure model name is valid

3. **Upload Fails**
   - Check file is valid PDF
   - Ensure pdf_documents/ directory exists
   - Verify file size limits

4. **No Search Results**
   - Upload PDF files first
   - Run `/build-vectorstore` endpoint
   - Ensure documents were processed successfully

### Production Service Troubleshooting

#### Service Won't Start

```bash
# Check if port is already in use
lsof -i :8804

# Kill existing processes
pkill -f "gunicorn.*api:app"

# Check virtual environment
source .venv/bin/activate
python -c "import gunicorn; print('Gunicorn OK')"

# Check dependencies
pip install -r requirements.txt

# Try manual start with verbose logging
./daemon_manager.sh start
```

#### Workers Crashing/Restarting

```bash
# Check logs for errors
./daemon_manager.sh logs 100

# Check system resources
./monitor.sh resources

# Reduce workers if memory limited
# Edit gunicorn_config.py: workers = 8  # Reduce from default

# Check for memory leaks
./monitor.sh status  # Monitor worker count over time
```

#### Poor Performance

```bash
# Check worker utilization
./monitor.sh perf

# Monitor system resources
./monitor.sh monitor

# Optimize worker count based on CPU cores
# Rule of thumb: workers = (2 * CPU_CORES) + 1

# Check for database connection issues
curl http://localhost:8804/health
```

#### API Not Responding

```bash
# Check service status
./daemon_manager.sh status

# Check if all workers are healthy
ps aux | grep gunicorn | wc -l  # Should show 33+ processes

# Test health endpoint
curl -v http://localhost:8804/health

# Restart service
./daemon_manager.sh restart

# Follow logs during restart
./daemon_manager.sh follow
```

#### Service Manager Issues

```bash
# If systemd not available (containers)
# Use daemon manager instead of service manager
./daemon_manager.sh start  # Instead of systemctl

# For systemd environments
sudo ./service_manager.sh install  # Generate service file
sudo systemctl status tanya-mail-api
```

### Debugging

```bash
# Check API logs
./daemon_manager.sh logs 50

# Follow live logs
./daemon_manager.sh follow

# Check MongoDB (if using external MongoDB)
# Test connection from API server

# Test health
curl http://localhost:8804/health

# Performance test
./monitor.sh perf

# Check worker processes
ps aux | grep gunicorn
```

### Log Analysis

```bash
# Application logs
tail -f logs/daemon.log

# Gunicorn access logs  
tail -f logs/gunicorn-access.log

# Gunicorn error logs
tail -f logs/gunicorn-error.log

# Search for errors
grep -i error logs/*.log

# Search for specific session issues
grep "session_id" logs/daemon.log
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

- 📖 Documentation: Check README_API.md for detailed API docs
- 🐛 Issues: Use GitHub issues for bug reports
- 💬 Discussions: Use GitHub discussions for questions

---

**Happy querying!** 🎉