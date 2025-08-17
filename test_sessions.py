#!/usr/bin/env python3
"""
Test script to demonstrate multi-user session management
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_multi_user_sessions():
    """Test multiple users with separate sessions"""
    print("🧪 Testing Multi-User Session Management")
    print("=" * 50)
    
    # User 1: First request (no session_id)
    print("\n👤 USER 1 - First Question")
    user1_request = {
        "question": "Apa itu PMB?",
        "stream": False
    }
    
    response1 = requests.post(f"{BASE_URL}/ask", json=user1_request)
    if response1.status_code == 200:
        data1 = response1.json()
        user1_session = data1.get('session_id')
        print(f"✅ User 1 Session ID: {user1_session}")
        print(f"📄 Answer: {data1.get('answer', '')[:100]}...")
    else:
        print(f"❌ User 1 failed: {response1.status_code}")
        return
    
    # User 2: First request (no session_id) 
    print("\n👤 USER 2 - First Question")
    user2_request = {
        "question": "Kapan pendaftaran dibuka?",
        "stream": False
    }
    
    response2 = requests.post(f"{BASE_URL}/ask", json=user2_request)
    if response2.status_code == 200:
        data2 = response2.json()
        user2_session = data2.get('session_id')
        print(f"✅ User 2 Session ID: {user2_session}")
        print(f"📄 Answer: {data2.get('answer', '')[:100]}...")
    else:
        print(f"❌ User 2 failed: {response2.status_code}")
        return
    
    # Verify sessions are different
    if user1_session != user2_session:
        print(f"\n✅ Sessions are separate: {user1_session} != {user2_session}")
    else:
        print(f"\n❌ Sessions are the same: {user1_session} == {user2_session}")
        return
    
    # User 1: Follow-up question (with session_id)
    print(f"\n👤 USER 1 - Follow-up Question")
    user1_followup = {
        "question": "Jelaskan lebih detail",
        "session_id": user1_session,
        "stream": False
    }
    
    response3 = requests.post(f"{BASE_URL}/ask", json=user1_followup)
    if response3.status_code == 200:
        data3 = response3.json()
        print(f"✅ User 1 follow-up answered")
        print(f"📄 Answer: {data3.get('answer', '')[:100]}...")
    
    # User 2: Different follow-up question (with session_id)
    print(f"\n👤 USER 2 - Follow-up Question")
    user2_followup = {
        "question": "Bagaimana cara mendaftar?",
        "session_id": user2_session,
        "stream": False
    }
    
    response4 = requests.post(f"{BASE_URL}/ask", json=user2_followup)
    if response4.status_code == 200:
        data4 = response4.json()
        print(f"✅ User 2 follow-up answered")
        print(f"📄 Answer: {data4.get('answer', '')[:100]}...")
    
    # Check conversation histories are separate
    print(f"\n📋 Checking Conversation Histories")
    
    # User 1 history
    hist1 = requests.get(f"{BASE_URL}/conversation/history/{user1_session}")
    if hist1.status_code == 200:
        hist1_data = hist1.json()
        print(f"✅ User 1 has {hist1_data.get('total_exchanges', 0)} conversations")
    
    # User 2 history
    hist2 = requests.get(f"{BASE_URL}/conversation/history/{user2_session}")
    if hist2.status_code == 200:
        hist2_data = hist2.json()
        print(f"✅ User 2 has {hist2_data.get('total_exchanges', 0)} conversations")
    
    # List all sessions
    print(f"\n📊 Active Sessions")
    sessions = requests.get(f"{BASE_URL}/sessions")
    if sessions.status_code == 200:
        sessions_data = sessions.json()
        print(f"✅ Total active sessions: {len(sessions_data.get('data', []))}")
        for session in sessions_data.get('data', []):
            print(f"   📝 Session {session['session_id'][:8]}... - {session['total_exchanges']} exchanges")
    
    print(f"\n🎉 Multi-user session test completed!")

if __name__ == "__main__":
    try:
        # Check if API is running
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        if health.status_code == 200:
            print("✅ API is running")
            test_multi_user_sessions()
        else:
            print("❌ API health check failed")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Please start the server with:")
        print("   python run_streaming_api.py")
    except Exception as e:
        print(f"❌ Test failed: {e}")
