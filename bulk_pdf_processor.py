#!/usr/bin/env python3
"""
Bulk PDF Processor CLI
Memproses semua file PDF dalam folder pdf_input secara batch

Usage:
    python bulk_pdf_processor.py
    python bulk_pdf_processor.py --folder custom_folder
    python bulk_pdf_processor.py --dry-run
    python bulk_pdf_processor.py --force
"""

import os
import sys
import argparse
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

# Import dari api.py
from api import (
    APP_NAME,
    collection,
    extract_text_from_pdf,
    split_text_into_chunks,
    get_embedding,
    get_file_hash,
    PDF_FOLDER
)

class Colors:
    """ANSI color codes untuk output terminal"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log_info(message: str):
    """Log info message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Colors.BLUE}[INFO {timestamp}]{Colors.END} {message}")

def log_success(message: str):
    """Log success message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Colors.GREEN}[SUCCESS {timestamp}]{Colors.END} {message}")

def log_warning(message: str):
    """Log warning message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Colors.YELLOW}[WARNING {timestamp}]{Colors.END} {message}")

def log_error(message: str):
    """Log error message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Colors.RED}[ERROR {timestamp}]{Colors.END} {message}")

def get_pdf_files(folder: str) -> List[str]:
    """Mendapatkan daftar file PDF dalam folder"""
    pdf_files: List[str] = []
    folder_path = Path(folder)
    
    if not folder_path.exists():
        log_error(f"Folder {folder} tidak ditemukan!")
        return pdf_files
    
    for file_path in folder_path.glob("*.pdf"):
        if file_path.is_file():
            pdf_files.append(str(file_path))
    
    # Juga cari file PDF dengan ekstensi uppercase
    for file_path in folder_path.glob("*.PDF"):
        if file_path.is_file():
            pdf_files.append(str(file_path))
    
    return sorted(pdf_files)

def is_pdf_processed(file_path: str) -> Tuple[bool, str]:
    """Cek apakah PDF sudah diproses"""
    filename = os.path.basename(file_path)
    file_hash = get_file_hash(file_path)
    
    existing_doc = collection.find_one({
        "filename": filename, 
        "file_hash": file_hash
    })
    
    if existing_doc:
        upload_date = existing_doc.get("upload_date", "Unknown")
        return True, upload_date
    
    return False, ""

def process_single_pdf(file_path: str, force: bool = False) -> bool:
    """Memproses satu file PDF"""
    try:
        filename = os.path.basename(file_path)
        
        # Cek apakah sudah diproses
        processed, upload_date = is_pdf_processed(file_path)
        if processed and not force:
            log_info(f"📄 {filename} - Sudah diproses pada {upload_date} (skip)")
            return True
        
        if processed and force:
            log_info(f"📄 {filename} - Force reprocessing (sudah diproses pada {upload_date})")
            # Hapus data lama
            file_hash = get_file_hash(file_path)
            collection.delete_many({
                "filename": filename, 
                "file_hash": file_hash
            })
        
        log_info(f"📄 {filename} - Mulai memproses...")
        
        # Copy file ke PDF_FOLDER jika belum ada
        destination = os.path.join(PDF_FOLDER, filename)
        if not os.path.exists(destination) or force:
            os.makedirs(PDF_FOLDER, exist_ok=True)
            shutil.copy2(file_path, destination)
            log_info(f"📄 {filename} - File disalin ke {PDF_FOLDER}")
        
        # Proses PDF
        file_hash = get_file_hash(file_path)
        
        # Extract text
        text = extract_text_from_pdf(file_path)
        if not text.strip():
            log_warning(f"📄 {filename} - Tidak ada teks yang dapat diekstrak")
            return False
        
        log_info(f"📄 {filename} - Teks diekstrak ({len(text)} karakter)")
        
        # Split into chunks
        documents = split_text_into_chunks(text, filename)
        log_info(f"📄 {filename} - Dibagi menjadi {len(documents)} chunk")
        
        # Process each chunk
        processed_chunks = 0
        for doc in documents:
            embedding = get_embedding(doc["text"])
            if not embedding:
                log_warning(f"📄 {filename} - Gagal membuat embedding untuk chunk {doc['chunk_id']}")
                continue
            
            mongo_doc = {
                "doc_id": f"{filename}_chunk_{doc['chunk_id']}",
                "filename": filename,
                "file_hash": file_hash,
                "text": doc["text"],
                "chunk_id": doc["chunk_id"],
                "source": doc["source"],
                "chunk_size": doc["chunk_size"],
                "embedding": embedding,
                "kategori": "pdf_document",
                "upload_date": datetime.now().isoformat()
            }
            
            collection.insert_one(mongo_doc)
            processed_chunks += 1
        
        log_success(f"📄 {filename} - Selesai diproses ({processed_chunks} chunk disimpan)")
        return True
        
    except Exception as e:
        log_error(f"📄 {os.path.basename(file_path)} - Error: {e}")
        return False

def bulk_process_pdfs(folder: str, dry_run: bool = False, force: bool = False):
    """Memproses semua PDF dalam folder secara bulk"""
    
    log_info(f"🚀 Memulai bulk processing PDF dari folder: {folder}")
    
    # Cek koneksi database
    try:
        collection.find_one()
        log_success("✅ Koneksi database berhasil")
    except Exception as e:
        log_error(f"❌ Koneksi database gagal: {e}")
        return
    
    # Dapatkan daftar file PDF
    pdf_files = get_pdf_files(folder)
    
    if not pdf_files:
        log_warning(f"📁 Tidak ada file PDF ditemukan di folder {folder}")
        return
    
    log_info(f"📊 Ditemukan {len(pdf_files)} file PDF")
    
    if dry_run:
        log_info("🔍 Mode DRY RUN - Menampilkan file yang akan diproses:")
        print()
        
    # Statistik
    stats = {
        "total": len(pdf_files),
        "processed": 0,
        "skipped": 0,
        "failed": 0,
        "already_processed": 0
    }
    
    # Proses setiap file
    for i, file_path in enumerate(pdf_files, 1):
        filename = os.path.basename(file_path)
        
        print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}[{i}/{len(pdf_files)}] {filename}{Colors.END}")
        print(f"{Colors.CYAN}{'='*60}{Colors.END}")
        
        if dry_run:
            # Mode dry run - hanya tampilkan info
            processed, upload_date = is_pdf_processed(file_path)
            file_size = os.path.getsize(file_path) / (1024*1024)  # MB
            
            print(f"📄 File: {filename}")
            print(f"📊 Size: {file_size:.2f} MB")
            print(f"📅 Status: {'Sudah diproses' if processed else 'Belum diproses'}")
            if processed:
                print(f"🕒 Diproses pada: {upload_date}")
            print()
            continue
        
        # Proses file
        try:
            # Cek status
            processed, upload_date = is_pdf_processed(file_path)
            
            if processed and not force:
                stats["already_processed"] += 1
                stats["skipped"] += 1
                log_info(f"📄 {filename} - Sudah diproses, skip")
                continue
            
            # Proses file
            success = process_single_pdf(file_path, force)
            
            if success:
                stats["processed"] += 1
            else:
                stats["failed"] += 1
                
        except KeyboardInterrupt:
            log_warning("\n⚠️  Proses dihentikan oleh user")
            break
        except Exception as e:
            log_error(f"📄 {filename} - Unexpected error: {e}")
            stats["failed"] += 1
    
    # Tampilkan statistik final
    print(f"\n{Colors.MAGENTA}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}📊 STATISTIK PROCESSING{Colors.END}")
    print(f"{Colors.MAGENTA}{'='*60}{Colors.END}")
    print(f"📁 Total file PDF: {stats['total']}")
    print(f"✅ Berhasil diproses: {Colors.GREEN}{stats['processed']}{Colors.END}")
    print(f"📋 Sudah diproses sebelumnya: {Colors.YELLOW}{stats['already_processed']}{Colors.END}")
    print(f"⏭️  Dilewati: {Colors.BLUE}{stats['skipped']}{Colors.END}")
    print(f"❌ Gagal: {Colors.RED}{stats['failed']}{Colors.END}")
    
    if not dry_run:
        success_rate = (stats['processed'] / max(stats['total'], 1)) * 100
        print(f"📈 Success rate: {success_rate:.1f}%")

def main():
    parser = argparse.ArgumentParser(
        description="Bulk PDF Processor - Memproses semua PDF dalam folder secara batch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  python bulk_pdf_processor.py                    # Proses folder pdf_input
  python bulk_pdf_processor.py --folder docs      # Proses folder docs
  python bulk_pdf_processor.py --dry-run          # Preview tanpa memproses
  python bulk_pdf_processor.py --force            # Proses ulang file yang sudah ada
        """
    )
    
    parser.add_argument(
        "--folder", 
        default="pdf_input",
        help="Folder yang berisi file PDF (default: pdf_input)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mode preview - tampilkan daftar file tanpa memproses"
    )
    
    parser.add_argument(
        "--force",
        action="store_true", 
        help="Force reprocess file yang sudah diproses sebelumnya"
    )
    
    args = parser.parse_args()
    
    # Banner
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}🚀 {APP_NAME.upper()} - BULK PDF PROCESSOR{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
    print()
    
    try:
        bulk_process_pdfs(
            folder=args.folder,
            dry_run=args.dry_run,
            force=args.force
        )
    except KeyboardInterrupt:
        log_warning("\n⚠️  Proses dibatalkan oleh user")
        sys.exit(1)
    except Exception as e:
        log_error(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
