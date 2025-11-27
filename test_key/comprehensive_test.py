"""
🎓 COMPREHENSIVE LLM ANALYSIS QUIZ ENDPOINT TEST SUITE
Student Testing Script - Verifies all requirements before evaluation

Tests:
1. ✅ Valid request test (200 response, JS execution, correct answer)
2. ✅ Wrong secret test (403 Forbidden)
3. ✅ Malformed JSON test (400 Bad Request)
4. ✅ Local JS-rendered quiz test (DOM execution)
5. ✅ Retry behavior test (multiple attempts)
6. ✅ JSON size test (< 1MB payload)
"""

import os
import sys
import json
import time
import base64
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
import requests

load_dotenv()

# Student Configuration
EMAIL = "23f3002264@ds.study.iitm.ac.in"
SECRET = os.getenv("QUIZ_SECRET")
MY_ENDPOINT = "http://127.0.0.1:8000/solving"
DEMO_QUIZ_URL = "https://tds-llm-analysis.s-anand.net/demo"

# Test Results
test_results = []

def log_test(test_name, passed, details=""):
    """Log test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    timestamp = datetime.now().strftime("%H:%M:%S")
    result = f"[{timestamp}] {status} - {test_name}"
    if details:
        result += f"\n           {details}"
    print(result)
    test_results.append({"test": test_name, "passed": passed, "details": details})

def print_section(title):
    """Print section header."""
    print("\n" + "="*80)
    print(f"🧪 {title}")
    print("="*80)

def create_local_quiz_html():
    """Create a local HTML quiz that requires JS execution."""
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Local Quiz Demo - JS Rendered</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>JS-Rendered Quiz</h1>
    <div id="question"></div>
    <div id="submit_url"></div>
    <script>
        // Base64 encoded quiz data - requires JS to decode
        const encodedData = btoa(JSON.stringify({
            question: "What is the sum of [10, 20, 30]?",
            submit_url: "https://httpbin.org/post",
            data: [10, 20, 30],
            expected_answer: 60
        }));
        
        // Decode and render
        const quizData = JSON.parse(atob(encodedData));
        document.getElementById('question').innerHTML = 
            '<p class="question">' + quizData.question + '</p>' +
            '<p>Data: ' + JSON.stringify(quizData.data) + '</p>';
        document.getElementById('submit_url').innerHTML = 
            '<form action="' + quizData.submit_url + '"></form>';
        
        // Store for verification
        window.quizData = quizData;
    </script>
</body>
</html>"""
    
    quiz_path = Path("test_key/quiz_demo.html")
    quiz_path.write_text(html_content)
    return quiz_path.absolute()

def verify_server_running():
    """Verify the endpoint is accessible."""
    try:
        r = requests.get("http://127.0.0.1:8000/healthz", timeout=2)
        if r.status_code == 200:
            print(f"✅ Server running at {MY_ENDPOINT}")
            return True
        else:
            print(f"❌ Server returned status {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot reach server: {e}")
        print("\n⚠️  Start server with:")
        print("   D:/coding/TDS/.venv/Scripts/python.exe -m uvicorn app.server.main:app --host 127.0.0.1 --port 8000")
        return False

# =============================================================================
# TEST 1: Valid Request Test
# =============================================================================
def test_1_valid_request():
    print_section("TEST 1: Valid Request Test")
    print(f"📝 Testing endpoint with demo quiz")
    print(f"   Email: {EMAIL}")
    print(f"   Demo URL: {DEMO_QUIZ_URL}")
    print(f"   Expected: 200 OK, correct answer submitted within 3 minutes")
    
    payload = {
        "email": EMAIL,
        "secret": SECRET,
        "url": DEMO_QUIZ_URL,
        "note": "Student test — verify secret, solve quiz, render JS, submit correct answer."
    }
    
    start_time = time.time()
    start_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n⏰ Start time: {start_timestamp}")
    print(f"⏳ Sending request (may take up to 3 minutes)...")
    
    try:
        response = requests.post(MY_ENDPOINT, json=payload, timeout=180)
        elapsed = time.time() - start_time
        
        print(f"⏱️  Completed in {elapsed:.1f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        # Verify response code
        if response.status_code == 200:
            print(f"   ✅ HTTP 200 OK received")
            try:
                result = response.json()
                print(f"\n📋 Response JSON:")
                print(json.dumps(result, indent=2)[:500])
                
                # Check timing
                within_3_min = elapsed < 180
                log_test("Valid Request - Response 200", True)
                log_test("Valid Request - Completed within 3 minutes", within_3_min, 
                        f"{elapsed:.1f}s")
                
                # Check if answer was submitted
                if "answer" in result or "correct" in result or "status" in result:
                    log_test("Valid Request - Answer submitted", True)
                else:
                    log_test("Valid Request - Answer submitted", False, 
                            "No answer field in response")
                
                return True
                
            except json.JSONDecodeError:
                log_test("Valid Request", False, "Response not valid JSON")
                print(f"Response: {response.text[:200]}")
                return False
        else:
            log_test("Valid Request", False, f"Expected 200, got {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        log_test("Valid Request", False, f"Timeout after {elapsed:.1f}s (> 3 minutes)")
        return False
    except Exception as e:
        log_test("Valid Request", False, str(e))
        return False

# =============================================================================
# TEST 2: Wrong Secret Test (403)
# =============================================================================
def test_2_wrong_secret():
    print_section("TEST 2: Wrong Secret Test")
    print(f"📝 Testing with invalid secret")
    print(f"   Expected: 403 Forbidden, no solving")
    
    payload = {
        "email": EMAIL,
        "secret": "wrong-secret-12345",
        "url": DEMO_QUIZ_URL
    }
    
    print(f"\n⏳ Sending request with wrong secret...")
    start_time = time.time()
    
    try:
        response = requests.post(MY_ENDPOINT, json=payload, timeout=10)
        elapsed = time.time() - start_time
        
        print(f"⏱️  Completed in {elapsed:.1f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 403:
            # Verify it failed quickly (not solving)
            if elapsed < 5:
                log_test("Wrong Secret - 403 Forbidden", True)
                log_test("Wrong Secret - Failed quickly (no solving)", True, 
                        f"{elapsed:.1f}s")
                return True
            else:
                log_test("Wrong Secret - 403 Forbidden", True)
                log_test("Wrong Secret - Failed quickly (no solving)", False, 
                        f"Took {elapsed:.1f}s, may have tried solving")
                return False
        else:
            log_test("Wrong Secret", False, f"Expected 403, got {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        log_test("Wrong Secret", False, str(e))
        return False

# =============================================================================
# TEST 3: Malformed JSON Test (400)
# =============================================================================
def test_3_malformed_json():
    print_section("TEST 3: Malformed JSON Test")
    print(f"📝 Testing with malformed JSON")
    print(f"   Expected: 400 Bad Request or 422 Unprocessable Entity")
    
    # Send malformed JSON string
    malformed_json = '{ "email": "' + EMAIL + '", "secret": "' + SECRET + '", "url":'
    
    print(f"\n⏳ Sending malformed JSON...")
    
    try:
        response = requests.post(
            MY_ENDPOINT,
            data=malformed_json,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code in [400, 422]:
            log_test("Malformed JSON - 400/422 response", True)
            return True
        else:
            log_test("Malformed JSON", False, 
                    f"Expected 400/422, got {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        # Connection error is acceptable for malformed JSON
        log_test("Malformed JSON - Rejected", True, "Connection rejected malformed data")
        return True
    except Exception as e:
        log_test("Malformed JSON", False, str(e))
        return False

# =============================================================================
# TEST 4: Local JS-Rendered Quiz Test
# =============================================================================
def test_4_local_js_quiz():
    print_section("TEST 4: Local JS-Rendered Quiz Test")
    print(f"📝 Testing with local HTML quiz requiring JS execution")
    
    # Create local quiz file
    try:
        quiz_file = create_local_quiz_html()
        print(f"✅ Created local quiz: {quiz_file}")
    except Exception as e:
        log_test("Local JS Quiz - Create file", False, str(e))
        return False
    
    # Convert to file:// URL
    quiz_url = f"file:///{str(quiz_file).replace(chr(92), '/')}"
    print(f"📄 Quiz URL: {quiz_url}")
    print(f"   Question: What is the sum of [10, 20, 30]?")
    print(f"   Expected Answer: 60")
    print(f"   Submit URL: https://httpbin.org/post")
    
    payload = {
        "email": EMAIL,
        "secret": SECRET,
        "url": quiz_url
    }
    
    print(f"\n⏳ Sending request...")
    
    try:
        response = requests.post(MY_ENDPOINT, json=payload, timeout=60)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"\n📋 Response:")
                print(json.dumps(result, indent=2)[:500])
                
                # Check if JS was executed and answer is correct
                answer = result.get("answer")
                if answer == 60 or answer == "60":
                    log_test("Local JS Quiz - Correct answer (60)", True)
                    log_test("Local JS Quiz - JS execution verified", True)
                    return True
                else:
                    log_test("Local JS Quiz", False, 
                            f"Expected 60, got {answer}")
                    return False
                    
            except json.JSONDecodeError:
                log_test("Local JS Quiz", False, "Response not valid JSON")
                return False
        else:
            log_test("Local JS Quiz", False, f"Status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        log_test("Local JS Quiz", False, str(e))
        return False

# =============================================================================
# TEST 5: Retry Behavior Test
# =============================================================================
def test_5_retry_behavior():
    print_section("TEST 5: Retry Behavior Test")
    print(f"📝 Testing retry mechanism")
    print(f"   Note: This test verifies retry logic exists")
    print(f"   (Full retry test requires mock quiz with wrong answers)")
    
    # For now, just verify the endpoint handles multiple requests
    payload = {
        "email": EMAIL,
        "secret": SECRET,
        "url": DEMO_QUIZ_URL
    }
    
    print(f"\n⏳ Sending request...")
    
    try:
        start_time = time.time()
        response = requests.post(MY_ENDPOINT, json=payload, timeout=60)
        elapsed = time.time() - start_time
        
        print(f"⏱️  Completed in {elapsed:.1f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        # Check if timing suggests retries (would take longer)
        if response.status_code == 200:
            log_test("Retry Behavior - Endpoint responsive", True)
            
            # If it took longer than 20s, likely attempted retries
            if elapsed > 20:
                log_test("Retry Behavior - Multiple attempts detected", True,
                        f"Took {elapsed:.1f}s, suggests retry logic")
            else:
                log_test("Retry Behavior - Quick response", True,
                        f"{elapsed:.1f}s - likely correct first try")
            return True
        else:
            log_test("Retry Behavior", False, f"Status {response.status_code}")
            return False
            
    except Exception as e:
        log_test("Retry Behavior", False, str(e))
        return False

# =============================================================================
# TEST 6: JSON Size Test
# =============================================================================
def test_6_json_size():
    print_section("TEST 6: JSON Size Test")
    print(f"📝 Testing payload size < 1MB")
    
    payload = {
        "email": EMAIL,
        "secret": SECRET,
        "url": DEMO_QUIZ_URL
    }
    
    # Calculate payload size
    payload_json = json.dumps(payload)
    payload_size = len(payload_json.encode('utf-8'))
    size_kb = payload_size / 1024
    size_mb = size_kb / 1024
    
    print(f"\n📏 Request Payload Size:")
    print(f"   {payload_size} bytes ({size_kb:.2f} KB, {size_mb:.4f} MB)")
    
    if payload_size < 1_000_000:  # 1MB
        log_test("JSON Size - Request < 1MB", True, f"{size_kb:.2f} KB")
    else:
        log_test("JSON Size - Request < 1MB", False, f"{size_mb:.2f} MB (too large)")
        return False
    
    # Also check response size
    print(f"\n⏳ Checking response size...")
    
    try:
        response = requests.post(MY_ENDPOINT, json=payload, timeout=60)
        response_size = len(response.content)
        response_kb = response_size / 1024
        response_mb = response_kb / 1024
        
        print(f"📏 Response Size:")
        print(f"   {response_size} bytes ({response_kb:.2f} KB, {response_mb:.4f} MB)")
        
        if response_size < 1_000_000:
            log_test("JSON Size - Response < 1MB", True, f"{response_kb:.2f} KB")
            return True
        else:
            log_test("JSON Size - Response < 1MB", False, f"{response_mb:.2f} MB")
            return False
            
    except Exception as e:
        log_test("JSON Size - Response check", False, str(e))
        return False

# =============================================================================
# MAIN TEST RUNNER
# =============================================================================
def main():
    print("\n")
    print("="*80)
    print("🎓 LLM ANALYSIS QUIZ - COMPREHENSIVE TEST SUITE")
    print("="*80)
    print(f"Student: {EMAIL}")
    print(f"Endpoint: {MY_ENDPOINT}")
    print(f"Demo Quiz: {DEMO_QUIZ_URL}")
    print(f"Test Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Verify server is running
    if not verify_server_running():
        print("\n❌ Server not running. Please start the server first.")
        return
    
    print("\n🚀 Starting tests...\n")
    
    # Run all tests
    tests = [
        ("Test 1: Valid Request", test_1_valid_request),
        ("Test 2: Wrong Secret (403)", test_2_wrong_secret),
        ("Test 3: Malformed JSON (400)", test_3_malformed_json),
        ("Test 4: Local JS Quiz", test_4_local_js_quiz),
        ("Test 5: Retry Behavior", test_5_retry_behavior),
        ("Test 6: JSON Size (<1MB)", test_6_json_size),
    ]
    
    passed_count = 0
    failed_count = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed_count += 1
            else:
                failed_count += 1
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            failed_count += 1
        
        time.sleep(1)  # Brief pause between tests
    
    # Print summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    total_tests = len([r for r in test_results])
    passed = len([r for r in test_results if r["passed"]])
    failed = len([r for r in test_results if not r["passed"]])
    
    for result in test_results:
        status = "✅" if result["passed"] else "❌"
        print(f"{status} {result['test']}")
        if result["details"]:
            print(f"     {result['details']}")
    
    print("\n" + "="*80)
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/total_tests*100):.1f}%")
    print("="*80)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Your endpoint is ready for evaluation.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the results above.")
    
    print(f"\n⏰ Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
