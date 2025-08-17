# 🤖 Tanya Ma'il - Streaming Chat Interface

File khusus untuk **"Ask question (streaming)"** yang dioptimalkan untuk pengalaman chat real-time dengan dokumen Anda.

## 📁 File: `chat_streaming.py`

### ✨ Fitur Utama:
- **Real-time streaming responses** - Respons muncul token demi token
- **Dedicated chat interface** - Fokus pada percakapan streaming
- **Professional UI** - Interface yang bersih dan user-friendly  
- **Statistics tracking** - Mencatat jumlah pertanyaan dan waktu
- **Command system** - Perintah khusus untuk kontrol chat
- **Error handling** - Penanganan error yang robust

### 🚀 Cara Menggunakan:

#### 1. Start Chat Interface
```bash
cd /workspaces/tanya-mail
python chat_streaming.py
```

#### 2. Chat Commands
```
/help         - Tampilkan bantuan
/clear        - Bersihkan layar  
/status       - Cek status API
/stats        - Statistik percakapan
/exit         - Keluar dari chat
<pertanyaan>  - Tanyakan sesuatu tentang dokumen
```

#### 3. Custom API URL
```bash
python chat_streaming.py --url http://localhost:8080
```

#### 4. Help Information
```bash
python chat_streaming.py --help
```

### 💬 Interface Preview:
```
🤖 Tanya Ma'il - Streaming Chat Interface
==================================================
💬 Real-time conversation dengan dokumen Anda
⚡ Respons streaming untuk pengalaman yang lebih interaktif

✅ API Status: Terhubung
📊 Total dokumen: 64
📁 File tersedia: 1

💡 Tips:
   - Ketik pertanyaan Anda dan tekan Enter
   - Gunakan '/help' untuk melihat perintah khusus
   - Ketik '/exit' untuk keluar
   - Respons akan muncul secara real-time
==================================================

👤 Anda [01:51:28]: tanggal berapa pendaftaran tutup?
🤖 Assistant [01:51:28]: Pendaftaran untuk calon mahasiswa tutup pada tanggal 31 Januari 2025...
📚 Sumber: PMB-Info.pdf

👤 Anda [01:51:35]: /help
📋 Perintah Chat Streaming:
─────────────────────────────────────────
🔹 /help         - Tampilkan bantuan ini
🔹 /clear        - Bersihkan layar
🔹 /status       - Cek status API  
🔹 /stats        - Statistik percakapan
🔹 /exit         - Keluar dari chat
🔹 <pertanyaan>  - Tanyakan sesuatu tentang dokumen
```

### 🎯 Contoh Pertanyaan:
- Kapan pendaftaran ditutup?
- Apa saja syarat pendaftaran?
- Berapa biaya kuliah?
- Bagaimana cara mendaftar?
- Apa saja program studi yang tersedia?

### 🔧 Fitur Teknis:
- **Streaming Protocol**: Server-Sent Events (SSE)
- **Response Format**: JSON dengan token dan metadata
- **Timeout Handling**: 30 detik per request
- **Error Recovery**: Otomatis handle connection issues
- **Session Tracking**: Menghitung percakapan dan timestamp

### 📊 Chat Statistics:
- **Total pertanyaan**: Dihitung otomatis
- **Timestamp**: Waktu real-time untuk setiap message
- **Source tracking**: Menampilkan sumber dokumen
- **Session info**: Durasi dan aktivitas chat

### ⚡ Performance:
- **Real-time streaming**: Respons dimulai dalam <1 detik
- **Token delivery**: Smooth character-by-character display
- **Memory efficient**: Tidak menyimpan history panjang
- **Responsive**: Dapat dihentikan dengan Ctrl+C

### 🛡️ Error Handling:
- Connection timeout recovery
- API unavailable graceful handling
- Malformed response protection
- User interrupt handling (Ctrl+C)

### 🎨 UI Features:
- Emoji indicators untuk status
- Color coding untuk berbagai jenis message
- Timestamps pada setiap percakapan
- Clear visual separation antara user dan assistant
- Progress indicators untuk streaming

### 🔗 Dependencies:
- `requests` - HTTP client untuk API calls
- `json` - JSON parsing untuk SSE data
- `datetime` - Timestamp formatting
- Standard Python libraries only

---

## 🚀 Quick Start Example:

```bash
# 1. Start API server (terminal 1)
python run_streaming_api.py

# 2. Start chat interface (terminal 2) 
python chat_streaming.py

# 3. Mulai bertanya!
👤 Anda: Kapan pendaftaran ditutup?
🤖 Assistant: [streaming response...]
```

**File ini adalah solusi dedicated untuk chat streaming yang memberikan pengalaman percakapan yang optimal dengan dokumen Anda!** 🎯
