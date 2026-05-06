"""
Quick test to verify the second attempt doesn't error.
"""
import asyncio
import httpx
import json

async def test_math_flow():
    """Test the math problem flow: first and second attempts."""
    base_url = "http://localhost:8000/api"
    
    # Step 1: Register/login a test user
    print("1️⃣  Signing up test user...")
    async with httpx.AsyncClient() as client:
        signup_resp = await client.post(
            f"{base_url}/auth/signup",
            json={"email": "test@test.com", "password": "test123", "name": "Test User", "grade_level": "10", "role": "student"},
        )
        print(f"   Signup: {signup_resp.status_code}")
        if signup_resp.status_code == 200:
            user_data = signup_resp.json()
            token = user_data.get("access_token")
            print(f"   Got token: {token[:20]}...")
        elif signup_resp.status_code == 400:
            # User already exists, try login
            print("   User already exists, logging in...")
            login_resp = await client.post(
                f"{base_url}/auth/login",
                json={"email": "test@test.com", "password": "test123", "role": "student"},
            )
            print(f"   Login: {login_resp.status_code}")
            token_data = login_resp.json()
            token = token_data.get("access_token")
            print(f"   Got token: {token[:20]}...")
        else:
            print(f"   Error: {signup_resp.text}")
            return
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 3: Start session with math problem
        print("\n2️⃣  Starting session with: 'Solve for x in 2x+4=64'")
        start_resp = await client.post(
            f"{base_url}/session/start",
            json={"question": "Solve for x in 2x+4=64"},
            headers=headers,
        )
        print(f"   Status: {start_resp.status_code}")
        if start_resp.status_code != 200:
            print(f"   Error: {start_resp.text}")
            return
        session_data = start_resp.json()
        session_id = session_data.get("session_id")
        print(f"   Session ID: {session_id}")
        print(f"   Hint: {session_data.get('hint')[:50]}...")
        print(f"   Hint Level: {session_data.get('hint_level')}")
        
        # Step 4: Submit first attempt (wrong)
        print("\n3️⃣  Submitting first attempt: '10' (wrong)")
        attempt1_resp = await client.post(
            f"{base_url}/session/{session_id}/attempt",
            json={"attempt_text": "10"},
            headers=headers,
        )
        print(f"   Status: {attempt1_resp.status_code}")
        if attempt1_resp.status_code == 200:
            resp_data = attempt1_resp.json()
            print(f"   Status: {resp_data.get('status')}")
            print(f"   Hint Level: {resp_data.get('hint_level')}")
            print(f"   ✅ First attempt succeeded!")
        else:
            print(f"   ❌ Error: {attempt1_resp.text}")
            return
        
        # Step 5: Submit second attempt (still wrong)
        print("\n4️⃣  Submitting second attempt: '15' (still wrong)")
        attempt2_resp = await client.post(
            f"{base_url}/session/{session_id}/attempt",
            json={"attempt_text": "15"},
            headers=headers,
        )
        print(f"   Status: {attempt2_resp.status_code}")
        if attempt2_resp.status_code == 200:
            resp_data = attempt2_resp.json()
            print(f"   Status: {resp_data.get('status')}")
            print(f"   Hint Level: {resp_data.get('hint_level')}")
            print(f"   ✅ Second attempt succeeded!")
        else:
            print(f"   ❌ Error: {attempt2_resp.text}")
            print(f"\n❌ TEST FAILED! Second attempt errored!")
            return
        
        # Step 6: Submit third attempt (correct)
        print("\n5️⃣  Submitting third attempt: '30' (correct)")
        attempt3_resp = await client.post(
            f"{base_url}/session/{session_id}/attempt",
            json={"attempt_text": "30"},
            headers=headers,
        )
        print(f"   Status: {attempt3_resp.status_code}")
        if attempt3_resp.status_code == 200:
            resp_data = attempt3_resp.json()
            print(f"   Status: {resp_data.get('status')}")
            print(f"   Message: {resp_data.get('message')}")
            print("\n✅ TEST PASSED! All attempts succeeded without errors!")
        else:
            print(f"   Error: {attempt3_resp.text}")
            print("\n❌ TEST FAILED!")

if __name__ == "__main__":
    asyncio.run(test_math_flow())
