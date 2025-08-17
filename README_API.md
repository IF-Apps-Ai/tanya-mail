# Tanya Ma'il RESTful API Documentation

## Overview

Tanya Ma'il adalah sistem RAG (Retrieval-Augmented Generation) yang memungkinkan Anda untuk mengupload dokumen PDF dan bertanya tentang isinya menggunakan AI. API ini dibangun dengan FastAPI dan menyediakan dokumentasi Swagger interaktif.

## Features

- 📄 Upload dan proses dokumen PDF
- 🔍 Pencarian semantik dalam dokumen
- 💬 Conversation dengan context history
- 🤖 AI-powered Q&A menggunakan OpenAI
- 📊 Vector database dengan ChromaDB
- 🗄️ MongoDB untuk penyimpanan metadata
- 🐳 Docker support
- 📖 Interactive Swagger documentation

## Quick Start

### 1. Using Docker Compose (Recommended)

```bash
# Clone repository
git clone <repository_url>
cd tanya-mail

# Copy environment template
cp .env.template .env

# Edit .env file and add your OpenAI API key
nano .env

# Start services
docker-compose up -d

# Check if services are running
docker-compose ps
```

### 2. Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.template .env
# Edit .env file with your configurations

# Start MongoDB (if not using Docker)
# Option 1: Local MongoDB
sudo systemctl start mongod

# Option 2: MongoDB with Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Run the API
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### 3. Access the API

- **API Base URL**: http://localhost:8000
- **Swagger Documentation**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

## API Endpoints

### 1. System Endpoints

#### Health Check
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "mongodb_connected": true,
  "chroma_available": true,
  "total_documents": 150,
  "total_files": 3,
  "openai_configured": true
}
```

#### System Info
```http
GET /
```

### 2. File Management

#### Upload PDF File
```http
POST /upload
Content-Type: multipart/form-data

file: <pdf_file>
```

Response:
```json
{
  "status": "success",
  "message": "File document.pdf uploaded successfully and is being processed",
  "data": {
    "filename": "document.pdf",
    "size": 1024000
  }
}
```

#### List Processed Files
```http
GET /files
```

Response:
```json
[
  {
    "filename": "document1.pdf",
    "chunks": 25,
    "file_hash": "a1b2c3d4e5f6",
    "upload_date": "2024-01-15T10:30:00"
  },
  {
    "filename": "document2.pdf", 
    "chunks": 18,
    "file_hash": "f6e5d4c3b2a1",
    "upload_date": "2024-01-16T14:20:00"
  }
]
```

#### Delete File
```http
DELETE /files/{filename}
```

Response:
```json
{
  "status": "success",
  "message": "File document.pdf deleted successfully",
  "data": {
    "deleted_chunks": 25
  }
}
```

### 3. Vector Store Management

#### Build Vector Store
```http
POST /build-vectorstore
```

Response:
```json
{
  "status": "success",
  "message": "Vector store built successfully with 150 documents",
  "data": {
    "total_documents": 150,
    "total_files": 3
  }
}
```

### 4. Question & Answer

#### Ask Question
```http
POST /ask
Content-Type: application/json

{
  "question": "Apa itu machine learning?",
  "top_k": 3,
  "filename_filter": "ml-guide.pdf"
}
```

Response:
```json
{
  "question": "Apa itu machine learning?",
  "answer": "Machine learning adalah cabang dari artificial intelligence (AI) yang memungkinkan komputer untuk belajar dan membuat keputusan dari data tanpa diprogram secara eksplisit. Berdasarkan dokumen yang Anda berikan, machine learning menggunakan algoritma untuk mengidentifikasi pola dalam data dan membuat prediksi atau keputusan berdasarkan pola tersebut.",
  "sources": ["ml-guide.pdf", "ai-basics.pdf"],
  "timestamp": "2024-01-15T15:30:45",
  "session_id": "session_20240115_153045"
}
```

#### Search Documents
```http
GET /search?query=machine learning&top_k=5&filename_filter=ml-guide.pdf
```

Response:
```json
[
  {
    "doc_id": "ml-guide.pdf_chunk_5",
    "filename": "ml-guide.pdf", 
    "content": "Machine learning is a subset of artificial intelligence that focuses on algorithms which can learn from and make predictions on data. The main types include supervised learning, unsupervised learning, and reinforcement learning...",
    "similarity_score": 0.95
  }
]
```

### 5. Conversation Management

#### Get Conversation History
```http
GET /conversation/history
```

Response:
```json
{
  "session_id": "session_20240115_153045",
  "total_exchanges": 3,
  "history": [
    {
      "question": "Apa itu machine learning?",
      "answer": "Machine learning adalah...",
      "sources": ["ml-guide.pdf"],
      "timestamp": "2024-01-15T15:30:45"
    }
  ]
}
```

#### Clear Conversation History
```http
DELETE /conversation/history
```

#### Configure Conversation Context
```http
POST /conversation/config
Content-Type: application/json

{
  "context_window": 5
}
```

#### Export Conversation History
```http
GET /conversation/export
```

Returns a downloadable JSON file with conversation history.

## Python Client Examples

### Basic Usage

```python
import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

# 1. Upload PDF file
def upload_pdf(file_path):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/upload", files=files)
    return response.json()

# 2. Build vector store
def build_vectorstore():
    response = requests.post(f"{BASE_URL}/build-vectorstore")
    return response.json()

# 3. Ask question
def ask_question(question, top_k=3):
    data = {
        "question": question,
        "top_k": top_k
    }
    response = requests.post(f"{BASE_URL}/ask", json=data)
    return response.json()

# Example usage
if __name__ == "__main__":
    # Upload PDF
    result = upload_pdf("document.pdf")
    print("Upload result:", result)
    
    # Wait a moment for processing, then build vector store
    import time
    time.sleep(5)
    
    vectorstore_result = build_vectorstore()
    print("Vector store result:", vectorstore_result)
    
    # Ask question
    answer = ask_question("Apa topik utama dalam dokumen ini?")
    print("Answer:", answer)
```

### Advanced Usage with Conversation Context

```python
class TanyaMailClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def ask_question(self, question, top_k=3, filename_filter=None):
        data = {
            "question": question,
            "top_k": top_k
        }
        if filename_filter:
            data["filename_filter"] = filename_filter
            
        response = self.session.post(f"{self.base_url}/ask", json=data)
        return response.json()
    
    def get_conversation_history(self):
        response = self.session.get(f"{self.base_url}/conversation/history")
        return response.json()
    
    def clear_conversation(self):
        response = self.session.delete(f"{self.base_url}/conversation/history")
        return response.json()

# Multi-turn conversation example
client = TanyaMailClient()

# First question
response1 = client.ask_question("Apa itu machine learning?")
print("Q1:", response1["answer"])

# Follow-up question (will use conversation context)
response2 = client.ask_question("Jelaskan lebih detail tentang supervised learning")
print("Q2:", response2["answer"])

# Another follow-up
response3 = client.ask_question("Berikan contoh algoritma supervised learning")
print("Q3:", response3["answer"])

# Check conversation history
history = client.get_conversation_history()
print(f"Total conversations: {history['total_exchanges']}")
```

## cURL Examples

### Upload File
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

### Ask Question
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Apa itu artificial intelligence?",
    "top_k": 3
  }'
```

### Search Documents
```bash
curl -X GET "http://localhost:8000/search?query=machine%20learning&top_k=5"
```

### Health Check
```bash
curl -X GET "http://localhost:8000/health"
```

## Error Handling

The API returns standard HTTP status codes:

- **200**: Success
- **400**: Bad Request (invalid input)
- **404**: Not Found
- **500**: Internal Server Error

Error response format:
```json
{
  "detail": "Error message description"
}
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | - | ✅ |
| `OPENAI_API_BASE` | OpenAI API base URL | https://api.openai.com/v1 | ❌ |
| `MONGO_URI` | MongoDB connection string | - | ✅ |
| `MODEL_NAME` | OpenAI model name | gpt-4o-mini | ❌ |
| `MODEL_TEMPERATURE` | Model temperature | 0 | ❌ |
| `MODEL_MAX_TOKENS` | Max tokens for response | 2048 | ❌ |

### Docker Environment

When using Docker Compose, MongoDB is automatically configured with:
- Username: `admin`
- Password: `password123`
- Database: `tanya_mail`

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Ensure MongoDB is running
   - Check connection string in .env file
   - For Docker: ensure containers are on the same network

2. **OpenAI API Error**
   - Verify API key is correct
   - Check API quota and billing
   - Ensure model name is valid

3. **Upload Fails**
   - Ensure file is a valid PDF
   - Check file size limits
   - Verify pdf_documents directory exists

4. **Vector Store Not Found**
   - Run `/build-vectorstore` endpoint after uploading files
   - Ensure documents are processed successfully

### Logs

Check application logs:
```bash
# Docker Compose
docker-compose logs tanya-mail-api

# Direct run
# Logs will appear in terminal
```

## Development

### Running in Development Mode

```bash
# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Testing

The API includes built-in health checks and validation. You can test endpoints using:

1. **Swagger UI**: http://localhost:8000/docs
2. **Postman Collection**: Import the OpenAPI spec
3. **Python tests**: Create test scripts using the examples above

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
