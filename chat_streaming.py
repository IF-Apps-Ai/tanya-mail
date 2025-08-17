#!/usr/bin/env python3
"""
Tanya Ma'il Streaming Chat Interface
===================================
Dedicated chat interface for real-time streaming conversations with the Tanya Ma'il API.
Focus on Ask question (streaming) functionality with enhanced user experience.
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
import pytz
from typing import Generator, Dict, Any, Optional

class TanyaMailStreamingChat:
    """Dedicated streaming chat client for Tanya Ma'il API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize streaming chat client"""
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.conversation_count = 0
        self.local_tz = self._detect_local_timezone()
        self.session_id = None  # Will be set after first request
    
    def _detect_local_timezone(self):
        """Detect local timezone automatically"""
        try:
            # Try to get system timezone
            import time
            local_tz_name = time.tzname[time.daylight]
            
            # For better detection, use platform-specific methods
            try:
                # Linux/Mac approach
                import os
                if os.path.exists('/etc/timezone'):
                    with open('/etc/timezone', 'r') as f:
                        tz_name = f.read().strip()
                        return pytz.timezone(tz_name)
                
                # Alternative approach using datetime
                from datetime import timezone
                import time
                
                # Get local timezone offset
                local_offset = time.timezone if (time.daylight == 0) else time.altzone
                local_offset = -local_offset / 3600  # Convert to hours
                
                # Map common timezone offsets to Indonesian regions
                tz_map = {
                    7: 'Asia/Jakarta',     # WIB (Waktu Indonesia Barat) - Jawa, Sumatra
                    8: 'Asia/Makassar',    # WITA (Waktu Indonesia Tengah) - Sulawesi, Bali, NTB, NTT
                    9: 'Asia/Jayapura',    # WIT (Waktu Indonesia Timur) - Papua, Maluku
                    0: 'UTC',              # UTC fallback
                }
                
                if local_offset in tz_map:
                    return pytz.timezone(tz_map[local_offset])
                
            except:
                pass
            
            # Fallback: try to detect from system
            try:
                import subprocess
                result = subprocess.run(['timedatectl', 'show', '--property=Timezone', '--value'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    tz_name = result.stdout.strip()
                    if tz_name:
                        return pytz.timezone(tz_name)
            except:
                pass
                
            # Final fallback to local system timezone
            return pytz.timezone(time.tzname[0]) if time.tzname[0] else pytz.UTC
            
        except Exception:
            # Ultimate fallback - use system local time info
            try:
                # Get local timezone using datetime
                local_dt = datetime.now()
                utc_dt = datetime.utcnow() 
                
                # Calculate offset
                offset = local_dt - utc_dt
                offset_hours = round(offset.total_seconds() / 3600)
                
                # Common Indonesian timezone mappings based on offset
                offset_to_tz = {
                    7: 'Asia/Jakarta',     # WIB - Waktu Indonesia Barat
                    8: 'Asia/Makassar',    # WITA - Waktu Indonesia Tengah  
                    9: 'Asia/Jayapura',    # WIT - Waktu Indonesia Timur
                    0: 'UTC',              # UTC fallback
                }
                
                if offset_hours in offset_to_tz:
                    return pytz.timezone(offset_to_tz[offset_hours])
                    
            except Exception:
                pass
                
            # Absolute fallback
            return pytz.UTC
        
    def health_check(self) -> Dict[str, Any]:
        """Check API health status"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
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
        if self.session_id:
            data["session_id"] = self.session_id
        
        try:
            response = self.session.post(
                f"{self.base_url}/ask",
                json=data,
                stream=True,
                headers={'Accept': 'text/event-stream'},
                timeout=30
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        try:
                            event_data = json.loads(line[6:])
                            # Capture session_id from first response
                            if event_data.get('type') == 'session':
                                self.session_id = event_data.get('session_id')
                            yield event_data
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            yield {"type": "error", "error": str(e)}
    
    def print_welcome(self):
        """Print welcome message"""
        current_time = datetime.now(self.local_tz)
        
        # Get timezone name for display
        tz_name = str(self.local_tz).split('/')[-1] if '/' in str(self.local_tz) else str(self.local_tz)
        
        print("🤖 Tanya Ma'il - Streaming Chat Interface")
        print("=" * 50)
        print("💬 Real-time conversation dengan dokumen Anda")
        print("⚡ Respons streaming untuk pengalaman yang lebih interaktif")
        print(f"🕐 Waktu: {current_time.strftime('%H:%M:%S')}, {current_time.strftime('%d %B %Y')}")
        print(f"🌏 Timezone: {tz_name} (UTC{current_time.strftime('%z')[:-2]}:{current_time.strftime('%z')[-2:]})")
        print("")
        
        # Check API health
        health = self.health_check()
        if health.get('status') == 'healthy':
            print("✅ API Status: Terhubung")
            print(f"📊 Total dokumen: {health.get('total_documents', 0)}")
            print(f"📁 File tersedia: {health.get('total_files', 0)}")
        else:
            print("❌ API Status: Tidak terhubung")
            print(f"   Error: {health.get('message', 'Unknown error')}")
            print("\nPastikan server API berjalan dengan: python run_streaming_api.py")
            return False
        
        print("\n💡 Tips:")
        print("   - Ketik pertanyaan Anda dan tekan Enter")
        print("   - Gunakan '/help' untuk melihat perintah khusus")
        print("   - Ketik '/exit' untuk keluar")
        print("   - Respons akan muncul secara real-time")
        print("=" * 50)
        return True
    
    def print_help(self):
        """Print help information"""
        print("\n📋 Perintah Chat Streaming:")
        print("─" * 40)
        print("🔹 /help         - Tampilkan bantuan ini")
        print("🔹 /clear        - Bersihkan layar")
        print("🔹 /status       - Cek status API")
        print("🔹 /stats        - Statistik percakapan")
        print("🔹 /timezone     - Info timezone saat ini")
        print("🔹 /session      - Info session saat ini")
        print("🔹 /exit         - Keluar dari chat")
        print("🔹 <pertanyaan>  - Tanyakan sesuatu tentang dokumen")
        print("─" * 40)
        
        print("\n📚 Contoh Pertanyaan:")
        print("   • Kapan pendaftaran ditutup?")
        print("   • Apa saja syarat pendaftaran?")
        print("   • Berapa biaya kuliah?")
        print("   • Bagaimana cara mendaftar?")
        print("─" * 40)
    
    def print_timezone_info(self):
        """Print detailed timezone information"""
        current_time = datetime.now(self.local_tz)
        tz_name = str(self.local_tz).split('/')[-1] if '/' in str(self.local_tz) else str(self.local_tz)
        
        print(f"\n🌏 Informasi Timezone:")
        print("─" * 30)
        print(f"📍 Timezone: {self.local_tz}")
        print(f"🏷️ Nama: {tz_name}")
        print(f"⏰ Waktu saat ini: {current_time.strftime('%H:%M:%S')}")
        print(f"📅 Tanggal: {current_time.strftime('%A, %d %B %Y')}")
        print(f"🌍 UTC Offset: UTC{current_time.strftime('%z')[:-2]}:{current_time.strftime('%z')[-2:]}")
        
        # Show UTC time for comparison
        utc_time = datetime.now(pytz.UTC)
        print(f"🌐 UTC Time: {utc_time.strftime('%H:%M:%S')}")
        print("─" * 30)
    
    def print_session_info(self):
        """Print current session information"""
        print("\n💻 Informasi Session:")
        print("─" * 30)
        if self.session_id:
            print(f"🔑 Session ID: {self.session_id}")
            print(f"📊 Percakapan: {self.conversation_count}")
            print("✅ Status: Aktif")
        else:
            print("🔑 Session ID: Belum dibuat")
            print("📊 Percakapan: 0")
            print("⏳ Status: Menunggu pertanyaan pertama")
        print("─" * 30)
    
    def print_stats(self):
        """Print conversation statistics"""
        current_time = datetime.now(self.local_tz)
        tz_name = str(self.local_tz).split('/')[-1] if '/' in str(self.local_tz) else str(self.local_tz)
        
        print("\n📊 Statistik Chat:")
        print(f"   💬 Total pertanyaan: {self.conversation_count}")
        print(f"   ⏰ Waktu saat ini: {current_time.strftime('%H:%M:%S')}")
        print(f"   📅 Tanggal: {current_time.strftime('%d %B %Y')}")
        print(f"   🌏 Timezone: {tz_name} (UTC{current_time.strftime('%z')[:-2]}:{current_time.strftime('%z')[-2:]})")
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def format_timestamp(self) -> str:
        """Get formatted timestamp with local timezone"""
        current_time = datetime.now(self.local_tz)
        return current_time.strftime("%H:%M:%S")
    
    def handle_streaming_response(self, question: str) -> bool:
        """Handle streaming response and display"""
        print(f"🤖 Pak Ma'il [{self.format_timestamp()}]: ", end="", flush=True)
        
        response_text = ""
        sources = []
        error_occurred = False
        
        try:
            for event_data in self.ask_question_stream(question):
                event_type = event_data.get('type', '')
                
                if event_type == 'content':
                    token = event_data.get('token', '')
                    print(token, end="", flush=True)
                    response_text += token
                    
                elif event_type == 'source':
                    sources = event_data.get('sources', [])
                    
                elif event_type == 'done':
                    print()  # New line after streaming
                    if sources:
                        print(f"📚 Sumber: {', '.join(sources)}")
                    break
                    
                elif event_type == 'error':
                    error_message = event_data.get('error', 'Unknown error')
                    print(f"\n❌ Error: {error_message}")
                    error_occurred = True
                    break
                    
        except KeyboardInterrupt:
            print("\n\n⚠️ Streaming dihentikan oleh pengguna")
            return False
            
        except Exception as e:
            print(f"\n❌ Error dalam streaming: {e}")
            error_occurred = True
        
        if not error_occurred and response_text:
            self.conversation_count += 1
            
        return not error_occurred
    
    def run_chat(self):
        """Main chat loop"""
        if not self.print_welcome():
            return
        
        while True:
            try:
                # Get user input
                print()
                user_input = input(f"👤 Anda [{self.format_timestamp()}]: ").strip()
                
                # Handle empty input
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['/exit', '/quit', 'exit', 'quit', 'keluar']:
                    print("\n👋 Terima kasih telah menggunakan Tanya Ma'il Chat!")
                    print(f"📊 Total pertanyaan yang diajukan: {self.conversation_count}")
                    break
                    
                elif user_input.lower() == '/help':
                    self.print_help()
                    continue
                    
                elif user_input.lower() == '/clear':
                    self.clear_screen()
                    print("🧹 Layar dibersihkan!")
                    continue
                    
                elif user_input.lower() == '/status':
                    health = self.health_check()
                    if health.get('status') == 'healthy':
                        print(f"✅ API Status: Terhubung ({health.get('total_documents', 0)} dokumen)")
                    else:
                        print(f"❌ API Status: {health.get('message', 'Error')}")
                    continue
                    
                elif user_input.lower() == '/stats':
                    self.print_stats()
                    continue
                    
                elif user_input.lower() == '/timezone':
                    self.print_timezone_info()
                    continue
                    
                elif user_input.lower() == '/session':
                    self.print_session_info()
                    continue
                
                # Handle regular questions
                if len(user_input) < 3:
                    print("⚠️ Pertanyaan terlalu pendek. Silakan ajukan pertanyaan yang lebih detail.")
                    continue
                
                # Process streaming question
                success = self.handle_streaming_response(user_input)
                
                if not success:
                    print("⚠️ Terjadi masalah saat memproses pertanyaan. Silakan coba lagi.")
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat dihentikan. Sampai jumpa!")
                break
                
            except Exception as e:
                print(f"\n❌ Error dalam chat: {e}")
                print("💡 Ketik '/help' untuk bantuan atau '/exit' untuk keluar")

def main():
    """Main entry point"""
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help' or sys.argv[1] == '-h':
            print("Tanya Ma'il Streaming Chat")
            print("========================")
            print("Usage: python chat_streaming.py [options]")
            print("")
            print("Options:")
            print("  --help, -h     Show this help message")
            print("  --url URL      Custom API URL (default: http://localhost:8000)")
            print("")
            print("Examples:")
            print("  python chat_streaming.py")
            print("  python chat_streaming.py --url http://localhost:8080")
            return
        
        elif sys.argv[1] == '--url' and len(sys.argv) > 2:
            api_url = sys.argv[2]
        else:
            print("❌ Invalid argument. Use --help for usage information.")
            return
    else:
        api_url = "http://localhost:8000"
    
    # Initialize and run chat
    chat = TanyaMailStreamingChat(base_url=api_url)
    chat.run_chat()

if __name__ == "__main__":
    main()
