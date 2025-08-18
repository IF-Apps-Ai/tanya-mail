# Bulk PDF Processor

Script CLI untuk memproses file PDF secara bulk (batch processing) untuk sistem Tanya Mail API.

## 📁 Folder Structure

```
tanya-mail/
├── pdf_input/              # Folder untuk file PDF yang akan diproses
├── pdf_documents/          # Folder penyimpanan PDF yang sudah diproses
├── bulk_pdf_processor.py   # Script utama bulk processor
├── process_bulk_pdf.sh     # Script wrapper bash
└── README_BULK_PDF.md     # Dokumentasi ini
```

## 🚀 Cara Penggunaan

### 1. Menggunakan Script Wrapper (Recommended)

```bash
# Tampilkan help
./process_bulk_pdf.sh

# Preview file yang akan diproses (dry run)
./process_bulk_pdf.sh --dry-run

# Proses semua PDF di folder pdf_input
./process_bulk_pdf.sh

# Proses PDF di folder custom
./process_bulk_pdf.sh --folder documents

# Force reprocess file yang sudah ada
./process_bulk_pdf.sh --force
```

### 2. Menggunakan Python Script Langsung

```bash
# Aktifkan virtual environment
source .venv/bin/activate

# Tampilkan help
python bulk_pdf_processor.py --help

# Preview file yang akan diproses
python bulk_pdf_processor.py --dry-run

# Proses semua PDF di folder pdf_input
python bulk_pdf_processor.py

# Proses PDF di folder custom
python bulk_pdf_processor.py --folder custom_folder

# Force reprocess file yang sudah ada
python bulk_pdf_processor.py --force
```

## 📋 Fitur

### ✅ Yang Dilakukan Script:

1. **Scan Folder**: Mencari semua file PDF (*.pdf dan *.PDF) dalam folder
2. **Check Status**: Mengecek file mana yang sudah diproses berdasarkan hash
3. **Extract Text**: Mengekstrak teks dari PDF menggunakan PyMuPDF atau PyPDF2
4. **Chunking**: Membagi teks menjadi chunk-chunk kecil untuk processing
5. **Embedding**: Membuat embedding vector menggunakan OpenAI API
6. **Database**: Menyimpan ke MongoDB dengan metadata lengkap
7. **Copy Files**: Menyalin file PDF ke folder `pdf_documents`
8. **Progress Tracking**: Menampilkan progress dan statistik real-time

### 🔍 Mode Dry Run:

Mode preview yang menampilkan:
- Daftar file PDF yang ditemukan
- Status pemrosesan (sudah diproses/belum)
- Ukuran file
- Tanggal pemrosesan terakhir

### ⚡ Smart Processing:

- **Skip Duplicate**: Otomatis skip file yang sudah diproses (berdasarkan hash)
- **Force Mode**: Option untuk reprocess file yang sudah ada
- **Error Handling**: Robust error handling dengan logging detail
- **Resume Capability**: Bisa di-interrupt dan di-resume

## 📊 Output Examples

### Dry Run Mode:
```
🚀 TANYA MAIL - BULK PDF PROCESSOR
============================================================

[INFO 2025-08-18 10:30:15] 🚀 Memulai bulk processing PDF dari folder: pdf_input
[SUCCESS 2025-08-18 10:30:15] ✅ Koneksi database berhasil
[INFO 2025-08-18 10:30:15] 📊 Ditemukan 5 file PDF
[INFO 2025-08-18 10:30:15] 🔍 Mode DRY RUN - Menampilkan file yang akan diproses:

============================================================
[1/5] document1.pdf
============================================================
📄 File: document1.pdf
📊 Size: 2.34 MB
📅 Status: Belum diproses
```

### Normal Processing:
```
============================================================
[1/5] document1.pdf
============================================================
[INFO 2025-08-18 10:35:20] 📄 document1.pdf - Mulai memproses...
[INFO 2025-08-18 10:35:21] 📄 document1.pdf - File disalin ke pdf_documents
[INFO 2025-08-18 10:35:23] 📄 document1.pdf - Teks diekstrak (15420 karakter)
[INFO 2025-08-18 10:35:23] 📄 document1.pdf - Dibagi menjadi 8 chunk
[SUCCESS 2025-08-18 10:35:35] 📄 document1.pdf - Selesai diproses (8 chunk disimpan)

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

## ⚙️ Configuration

Script menggunakan konfigurasi yang sama dengan API utama:

- **Database**: MongoDB connection dari MONGO_URI
- **Collection**: Collection name dari COLLECTION_NAME
- **OpenAI**: API key dari OPENAI_API_KEY
- **PDF Storage**: Folder pdf_documents

## 🔧 Troubleshooting

### Error: "ModuleNotFoundError"
```bash
# Pastikan virtual environment aktif
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Error: "Koneksi database gagal"
```bash
# Cek file .env
cat .env | grep MONGO_URI

# Test koneksi
python -c "from api import collection; print(collection.find_one())"
```

### Error: "OpenAI API error"
```bash
# Cek API key
cat .env | grep OPENAI_API_KEY

# Test API
python -c "from api import get_embedding; print(get_embedding('test'))"
```

## 📈 Performance Tips

1. **Batch Size**: Proses dalam batch kecil untuk menghindari memory issues
2. **Network**: Pastikan koneksi internet stabil untuk OpenAI API calls
3. **Storage**: Pastikan cukup disk space untuk PDF dan database
4. **Monitoring**: Gunakan `follow_logs` untuk monitor API dalam real-time

## 🔗 Integration dengan API

Setelah processing selesai, file PDF akan tersedia untuk:

1. **Query Endpoint**: `/ask` - Tanya jawab dengan PDF
2. **List Endpoint**: `/files` - Lihat daftar file yang sudah diproses
3. **Chat Endpoint**: `/chat` - Conversation dengan context PDF

## 📝 Notes

- Script menggunakan hashing untuk detect duplicate files
- Processing berjalan sequentially untuk stability
- Embedding menggunakan OpenAI text-embedding-ada-002
- Chunk size dan overlap dapat dikustomisasi di `api.py`
