# Copilot Coding Agent Instructions for Tanya Ma'il

This guide provides essential knowledge for AI coding agents working in the Tanya Ma'il codebase. Follow these conventions and workflows to be immediately productive and maintain project consistency.

## 🏗️ Big Picture Architecture
- **Main API**: FastAPI app in `api.py` with multi-user session management, PDF processing, semantic search, and OpenAI integration.
- **Clustering/Production**: Use Gunicorn (`gunicorn_config.py`) with UvicornWorker for high concurrency. Managed via `daemon_manager.sh` and optionally systemd (`service_manager.sh`).
- **Vector DB**: ChromaDB for storing PDF text embeddings. MongoDB for metadata, sessions, and conversation history.
- **Streaming**: Real-time chat and Q&A via SSE endpoints and `chat_streaming.py`.
- **Data Flow**: PDF → Text Extraction → Chunking → Embedding → ChromaDB → Semantic Search → LLM Response.

## ⚙️ Developer Workflows
- **Setup**: Use `setup.sh` for initial install, or `setup_venv.sh` for Python venv. Copy `.env.template` to `.env` and configure secrets.
- **Run Locally**: `uvicorn api:app --reload --host 0.0.0.0 --port 8000` or `python api.py` for dev. Use `daemon_manager.sh start` for production clustering.
- **Testing**: Run `test_api.sh` for API tests, `test_sessions.py` for session isolation, and `test_timezone.py` for timezone logic.
- **Monitoring**: Use `monitor.sh monitor` for dashboard, `monitor.sh perf` for load testing.
- **Bulk PDF Processing**: Use `bulk_pdf_processor.py` and `process_bulk_pdf.sh` to process all PDFs in `pdf_input/`.

## 📦 Project-Specific Conventions
- **Config**: All runtime config via `.env` (see `.env.template`).
- **APP_NAME**: Read from `.env` and used for all service banners and logs.
- **PDF Storage**: Raw PDFs in `pdf_documents/`, processed via chunking and embedding.
- **SessionManager/ConversationManager**: Custom classes in `api.py` for multi-user isolation and chat history.
- **No LangChain**: Direct OpenAI/ChromaDB integration, not via LangChain abstractions.
- **Logging**: Logs written to `logs/daemon.log`, `logs/gunicorn-access.log`, and `logs/gunicorn-error.log`.
- **Service Naming**: Service name for PID/log files is derived from `APP_NAME` in `.env` (lowercase, dash-separated, suffixed with `-api`).

## 🔗 Integration Points
- **OpenAI**: API key and base URL from `.env`. Used for embeddings and LLM responses.
- **ChromaDB**: Local vector DB in `chroma_pdf_db/`.
- **MongoDB**: Connection string from `.env`. Used for all metadata and session storage.
- **Postman**: API collection in `Tanya_Mail_API.postman_collection.json` for endpoint testing.
- **Docker**: Use `docker-compose.yml` for multi-container setup. `Dockerfile` for image builds.

## 🧩 Key Files & Directories
- `api.py`: Main FastAPI app, session/chat logic, PDF processing.
- `gunicorn_config.py`: Gunicorn clustering config.
- `daemon_manager.sh`: Service lifecycle management.
- `bulk_pdf_processor.py`, `process_bulk_pdf.sh`: Bulk PDF ingestion.
- `logs/`: All service logs.
- `pdf_documents/`, `pdf_input/`: PDF storage and ingestion.
- `.env`, `.env.template`: Environment config.
- `monitor.sh`, `service_manager.sh`: Monitoring and systemd integration.

## 📝 Example Patterns
- **SessionManager**: `session_id = create_session()` → `add_to_history(session_id, ...)` → `get_history(session_id)`
- **Bulk PDF**: Place files in `pdf_input/` → run `process_bulk_pdf.sh` → processed files in `pdf_documents/`
- **Production**: `daemon_manager.sh start` → Gunicorn cluster → API on port from `.env`

---

If any conventions or workflows are unclear, please ask for clarification or request examples from the codebase.
