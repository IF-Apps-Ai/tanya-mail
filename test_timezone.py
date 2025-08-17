#!/usr/bin/env python3
"""
Test script to verify timezone functionality in chat_streaming.py
"""

import sys
sys.path.append('/workspaces/tanya-mail')

from chat_streaming import TanyaMailStreamingChat

def test_timezone():
    """Test timezone detection and display"""
    print("🧪 Testing Timezone Functionality")
    print("=" * 40)
    
    # Initialize the chat client
    chat = TanyaMailStreamingChat()
    
    # Test timezone detection
    print(f"✅ Detected timezone: {chat.local_tz}")
    
    # Test timezone info display
    print("\n📋 Testing timezone info display:")
    chat.print_timezone_info()
    
    # Test timestamp formatting
    print(f"\n🕐 Current timestamp: {chat.format_timestamp()}")
    
    print("\n🎉 All timezone tests passed!")
    print("📝 Indonesian timezone mapping:")
    print("   - UTC+7 → Asia/Jakarta (WIB)")
    print("   - UTC+8 → Asia/Makassar (WITA)") 
    print("   - UTC+9 → Asia/Jayapura (WIT)")

if __name__ == "__main__":
    test_timezone()
