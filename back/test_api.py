import requests
import json
import uuid
from pprint import pprint

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("🏥 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        pprint(response.json())
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running! Please start the server first.")
        return False

def test_list_stories():
    """Test listing available stories"""
    print("\n📚 Testing story list...")
    try:
        response = requests.get(f"{BASE_URL}/stories/list")
        print(f"Status Code: {response.status_code}")
        pprint(response.json())
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_start_story(story_name="koroghlu", language="english", max_choices=10):
    """Test starting a story with new parameters"""
    print(f"\n🎭 Testing start story ({story_name}, {language}, {max_choices} choices)...")
    try:
        payload = {
            "story_name": story_name,
            "language": language,
            "max_choices": max_choices
        }
        response = requests.post(f"{BASE_URL}/stories/start", json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            pprint(result)
            print(f"\n✅ Choices available: {len(result.get('choices', []))}")
            print(f"✅ Cultural info included: {'Yes' if result.get('cultural_info') else 'No'}")
            print(f"✅ Choices remaining: {result.get('choices_remaining', 'Unknown')}")
            return result.get("session_id")
        else:
            print("❌ Error starting story:")
            pprint(response.json())
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_continue_story(session_id, story_name="koroghlu", choice="Go along the river"):
    """Test continuing a story"""
    print(f"\n📖 Testing continue story (choice: {choice})...")
    try:
        payload = {
            "story_name": story_name,
            "session_id": session_id,
            "choice_text": choice
        }
        response = requests.post(f"{BASE_URL}/stories/continue", json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            pprint(result)
            return True
        else:
            print("❌ Error continuing story:")
            pprint(response.json())
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_get_session(session_id):
    """Test getting session information"""
    print(f"\n🔍 Testing get session ({session_id})...")
    try:
        response = requests.get(f"{BASE_URL}/stories/session/{session_id}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            pprint(result)
            return True
        else:
            print("❌ Error getting session:")
            pprint(response.json())
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Enhanced Interactive Storytelling API Test Suite")
    print("=" * 60)
    
    # Test health check first
    if not test_health_check():
        print("❌ Health check failed. Exiting tests.")
        return
    
    # Test listing stories
    test_list_stories()
    
    # Test starting a story with new features
    print(f"\n🔬 Testing Enhanced Features:")
    print("- 5 choices instead of 3")
    print("- Limited story length (max choices)")
    print("- Cultural information")
    print("- Story similarity tracking")
    print("- Language selection")
    
    # Test with different parameters
    session_id = test_start_story("koroghlu", "english", 5)  # Short story for testing
    
    if session_id:
        print(f"\n✅ Story started successfully! Session ID: {session_id}")
        
        # Test getting session info
        test_get_session(session_id)
        
        # Test continuing the story multiple times to reach the end
        print("\n🎯 Testing Story Progression to End:")
        print("⚠️  Note: The following tests require a configured Gemini API key")
        print("If you see an error, make sure your GEMINI_API_KEY is set in .env file")
        
        # Make multiple choices to test the limit
        test_choices = [
            "Follow the mountain path",
            "Seek help from villagers", 
            "Rest and plan carefully",
            "Continue the journey alone",
            "Face the final challenge"
        ]
        
        for i, choice in enumerate(test_choices):
            print(f"\n📖 Making choice {i+1}: {choice}")
            success = test_continue_story(session_id, "koroghlu", choice)
            if not success:
                print(f"❌ Story ended or failed at choice {i+1}")
                break
            
            # Small delay to be nice to API
            import time
            time.sleep(1)
        
        print(f"\n📝 Final session data: {BASE_URL}/stories/session/{session_id}")
        
    else:
        print("❌ Failed to start story. Cannot continue with remaining tests.")
    
    # Test language parameter
    print(f"\n🌍 Testing Azerbaijani Language:")
    az_session = test_start_story("dedegorgud", "azerbaijani", 3)
    
    if az_session:
        print(f"✅ Azerbaijani story started: {az_session}")
    
    print(f"\n📚 API documentation is available at: {BASE_URL}/docs")
    print("\n" + "=" * 60)
    print("🏁 Enhanced tests completed!")
    
    print(f"\n🎮 You can now test the full interface at: app.html")
    print("Features to test in the UI:")
    print("✨ Language selection (English/Azerbaijani)")
    print("✨ Adjustable story length (1-50 choices)")
    print("✨ 5 choices per decision")
    print("✨ Cultural information tooltips")
    print("✨ Story similarity scoring")
    print("✨ Visual mood indicators")
    print("✨ Progress tracking")

if __name__ == "__main__":
    main()
