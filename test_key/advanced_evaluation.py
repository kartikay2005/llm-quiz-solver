"""Advanced Evaluation Metrics for LLM Quiz Solver.

This test suite goes beyond basic functionality to evaluate:
- Performance under load
- Edge case handling
- Data processing accuracy
- Error recovery
- Memory efficiency
- Concurrent request handling
"""
import os
import sys
import time
import json
import requests
import threading
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()

EMAIL = "23f3002264@ds.study.iitm.ac.in"
SECRET = os.getenv("QUIZ_SECRET")
ENDPOINT = "http://127.0.0.1:8000/solving"
DEMO_URL = "https://tds-llm-analysis.s-anand.net/demo"

# Test results tracking
results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "warnings": 0,
    "tests": []
}

def log_test(name, passed, details="", warning=False):
    """Log test result."""
    results["total"] += 1
    if warning:
        results["warnings"] += 1
        status = "⚠️  WARN"
    elif passed:
        results["passed"] += 1
        status = "✅ PASS"
    else:
        results["failed"] += 1
        status = "❌ FAIL"
    
    results["tests"].append({
        "name": name,
        "status": status,
        "details": details
    })
    print(f"{status} - {name}")
    if details:
        print(f"      {details}")


def print_section(title):
    """Print section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


# =============================================================================
# METRIC 1: Response Time Performance
# =============================================================================
def metric_1_response_time_performance():
    print_section("METRIC 1: Response Time Performance")
    print("Testing response times across multiple requests")
    
    times = []
    for i in range(3):
        payload = {"email": EMAIL, "secret": SECRET, "url": DEMO_URL}
        
        start = time.time()
        try:
            r = requests.post(ENDPOINT, json=payload, timeout=120)
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"  Request {i+1}: {elapsed:.2f}s")
        except Exception as e:
            log_test(f"Response Time - Request {i+1}", False, str(e))
            return False
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"\n  Average: {avg_time:.2f}s")
    print(f"  Min: {min_time:.2f}s")
    print(f"  Max: {max_time:.2f}s")
    
    # All requests should complete within 3 minutes
    if max_time <= 180:
        log_test("Response Time - Max time < 3 minutes", True, f"{max_time:.2f}s")
    else:
        log_test("Response Time - Max time < 3 minutes", False, f"{max_time:.2f}s")
    
    # Average should be reasonable (< 1.5 minutes)
    if avg_time <= 90:
        log_test("Response Time - Average < 1.5 minutes", True, f"{avg_time:.2f}s")
    else:
        log_test("Response Time - Average < 1.5 minutes", False, f"{avg_time:.2f}s", warning=True)
    
    # Performance consistency (max should not be > 2x min)
    if max_time <= min_time * 2.5:
        log_test("Response Time - Consistency", True, f"Ratio: {max_time/min_time:.2f}x")
    else:
        log_test("Response Time - Consistency", False, f"Ratio: {max_time/min_time:.2f}x", warning=True)
    
    return True


# =============================================================================
# METRIC 2: Large Data Handling
# =============================================================================
def metric_2_large_data_handling():
    print_section("METRIC 2: Large Data Handling")
    print("Testing with large datasets")
    
    # Create HTML with large table
    large_html = """<!DOCTYPE html>
<html>
<head><title>Large Data Quiz</title></head>
<body>
    <h1>Calculate the sum of all numbers</h1>
    <form action="https://httpbin.org/post"></form>
    <script>
        const numbers = Array.from({length: 1000}, (_, i) => i + 1);
        const sum = numbers.reduce((a, b) => a + b, 0);
        window.quizData = {
            question: "What is the sum of all numbers from 1 to 1000?",
            data: numbers,
            expected_answer: sum,
            submit_url: "https://httpbin.org/post"
        };
        document.querySelector('h1').textContent = window.quizData.question;
    </script>
</body>
</html>"""
    
    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(large_html)
        temp_file = f.name
    
    try:
        file_url = f"file:///{temp_file.replace(chr(92), '/')}"
        payload = {"email": EMAIL, "secret": SECRET, "url": file_url}
        
        start = time.time()
        r = requests.post(ENDPOINT, json=payload, timeout=120)
        elapsed = time.time() - start
        
        if r.status_code == 200:
            result = r.json()
            answer = result.get("answer")
            expected = 500500  # Sum of 1 to 1000
            
            if answer == expected:
                log_test("Large Data - Correct calculation", True, f"Processed 1000 numbers in {elapsed:.2f}s")
            else:
                log_test("Large Data - Correct calculation", False, f"Expected {expected}, got {answer}")
        else:
            log_test("Large Data - Request handling", False, f"Status {r.status_code}")
        
        # Check response size
        if r.status_code == 200:
            response_size = len(r.content)
            if response_size < 1024 * 1024:  # < 1MB
                log_test("Large Data - Response size < 1MB", True, f"{response_size/1024:.2f} KB")
            else:
                log_test("Large Data - Response size < 1MB", False, f"{response_size/1024/1024:.2f} MB")
    
    except Exception as e:
        log_test("Large Data - Processing", False, str(e))
    finally:
        os.unlink(temp_file)
    
    return True


# =============================================================================
# METRIC 3: Malformed Input Handling
# =============================================================================
def metric_3_malformed_input_handling():
    print_section("METRIC 3: Malformed Input Handling")
    print("Testing edge cases and invalid inputs")
    
    test_cases = [
        # Missing required fields
        ({"email": EMAIL, "secret": SECRET}, "Missing URL field", 422),
        ({"email": EMAIL, "url": DEMO_URL}, "Missing secret field", [403, 422]),  # Either validation or auth
        ({"secret": SECRET, "url": DEMO_URL}, "Missing email field", 422),
        
        # Invalid data types
        ({"email": 12345, "secret": SECRET, "url": DEMO_URL}, "Email as number", [400, 422]),
        ({"email": EMAIL, "secret": SECRET, "url": 12345}, "URL as number", [400, 422]),
        
        # Invalid URLs
        ({"email": EMAIL, "secret": SECRET, "url": "not-a-url"}, "Invalid URL format", [400, 422]),
        ({"email": EMAIL, "secret": SECRET, "url": "ftp://example.com"}, "Unsupported protocol", [400, 422]),
        
        # Empty values
        ({"email": "", "secret": SECRET, "url": DEMO_URL}, "Empty email", [400, 422]),
        ({"email": EMAIL, "secret": "", "url": DEMO_URL}, "Empty secret", [403, 422]),  # Either validation or auth
        ({"email": EMAIL, "secret": SECRET, "url": ""}, "Empty URL", [400, 422]),
        
        # Very long values
        ({"email": "a" * 1000 + "@test.com", "secret": SECRET, "url": DEMO_URL}, "Very long email", [200, 400, 422]),
    ]
    
    for payload, description, expected_status in test_cases:
        try:
            r = requests.post(ENDPOINT, json=payload, timeout=30)
            
            if isinstance(expected_status, list):
                if r.status_code in expected_status:
                    log_test(f"Malformed Input - {description}", True, f"Status {r.status_code}")
                else:
                    log_test(f"Malformed Input - {description}", False, f"Expected {expected_status}, got {r.status_code}")
            else:
                if r.status_code == expected_status:
                    log_test(f"Malformed Input - {description}", True, f"Status {r.status_code}")
                else:
                    log_test(f"Malformed Input - {description}", False, f"Expected {expected_status}, got {r.status_code}")
        
        except Exception as e:
            log_test(f"Malformed Input - {description}", False, str(e))
    
    return True


# =============================================================================
# METRIC 4: Concurrent Request Handling
# =============================================================================
def metric_4_concurrent_requests():
    print_section("METRIC 4: Concurrent Request Handling")
    print("Testing multiple simultaneous requests")
    
    num_requests = 3
    results_list = []
    errors = []
    
    def make_request(idx):
        try:
            payload = {"email": EMAIL, "secret": SECRET, "url": DEMO_URL}
            start = time.time()
            r = requests.post(ENDPOINT, json=payload, timeout=120)
            elapsed = time.time() - start
            results_list.append((idx, r.status_code, elapsed))
        except Exception as e:
            errors.append((idx, str(e)))
    
    threads = []
    start_time = time.time()
    
    for i in range(num_requests):
        t = threading.Thread(target=make_request, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    total_time = time.time() - start_time
    
    print(f"\n  Sent {num_requests} concurrent requests")
    print(f"  Total time: {total_time:.2f}s")
    
    if not errors:
        log_test("Concurrent - No errors", True, f"All {num_requests} requests succeeded")
    else:
        log_test("Concurrent - No errors", False, f"{len(errors)} requests failed")
    
    success_count = len([r for r in results_list if r[1] == 200])
    if success_count == num_requests:
        log_test("Concurrent - All successful", True, f"{success_count}/{num_requests} returned 200")
    else:
        log_test("Concurrent - All successful", False, f"Only {success_count}/{num_requests} returned 200")
    
    # Check if concurrent execution saves time (should be faster than sequential)
    avg_individual = sum(r[2] for r in results_list) / len(results_list) if results_list else 0
    expected_sequential = avg_individual * num_requests
    
    if total_time < expected_sequential * 0.7:  # At least 30% faster
        log_test("Concurrent - Performance benefit", True, f"Saved {expected_sequential - total_time:.1f}s")
    else:
        log_test("Concurrent - Performance benefit", False, "No significant speedup", warning=True)
    
    return True


# =============================================================================
# METRIC 5: Data Type Handling
# =============================================================================
def metric_5_data_type_handling():
    print_section("METRIC 5: Data Type Handling")
    print("Testing various answer data types")
    
    test_cases = [
        # Integer answer
        ("""<html><body><h1>What is 2+2?</h1><form action="https://httpbin.org/post"></form>
        <script>window.quizData = {question: "What is 2+2?", data: [2, 2], submit_url: "https://httpbin.org/post"};</script>
        </body></html>""", "Integer", 4),
        
        # String answer
        ("""<html><body><h1>What color is the sky?</h1><form action="https://httpbin.org/post"></form>
        <script>window.quizData = {question: "What color is the sky?", answer: "blue", submit_url: "https://httpbin.org/post"};</script>
        </body></html>""", "String", "blue"),
        
        # Float answer
        ("""<html><body><h1>What is the average?</h1><form action="https://httpbin.org/post"></form>
        <script>window.quizData = {question: "Average of [1,2,3]?", data: [1,2,3], submit_url: "https://httpbin.org/post"};</script>
        </body></html>""", "Float", [2, 2.0]),
        
        # Boolean answer
        ("""<html><body><h1>Is 5 > 3?</h1><form action="https://httpbin.org/post"></form>
        <script>window.quizData = {question: "Is 5 > 3?", data: {a: 5, b: 3}, submit_url: "https://httpbin.org/post"};</script>
        </body></html>""", "Boolean", [True, "true", "yes"]),
    ]
    
    for html_content, data_type, expected in test_cases:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            temp_file = f.name
        
        try:
            file_url = f"file:///{temp_file.replace(chr(92), '/')}"
            payload = {"email": EMAIL, "secret": SECRET, "url": file_url}
            
            r = requests.post(ENDPOINT, json=payload, timeout=60)
            
            if r.status_code == 200:
                result = r.json()
                answer = result.get("answer")
                
                if isinstance(expected, list):
                    if answer in expected:
                        log_test(f"Data Type - {data_type}", True, f"Answer: {answer}")
                    else:
                        log_test(f"Data Type - {data_type}", False, f"Expected one of {expected}, got {answer}", warning=True)
                else:
                    if answer == expected or str(answer).lower() == str(expected).lower():
                        log_test(f"Data Type - {data_type}", True, f"Answer: {answer}")
                    else:
                        log_test(f"Data Type - {data_type}", False, f"Expected {expected}, got {answer}", warning=True)
            else:
                log_test(f"Data Type - {data_type}", False, f"Status {r.status_code}", warning=True)
        
        except Exception as e:
            log_test(f"Data Type - {data_type}", False, str(e))
        finally:
            os.unlink(temp_file)
    
    return True


# =============================================================================
# METRIC 6: Error Recovery
# =============================================================================
def metric_6_error_recovery():
    print_section("METRIC 6: Error Recovery")
    print("Testing system stability after errors")
    
    # Test 1: Invalid URL should not crash server
    try:
        payload = {"email": EMAIL, "secret": SECRET, "url": "https://nonexistent-domain-12345.com/quiz"}
        r = requests.post(ENDPOINT, json=payload, timeout=60)
        
        if r.status_code in [200, 400, 500]:
            log_test("Error Recovery - Invalid domain", True, f"Server responded with {r.status_code}")
        else:
            log_test("Error Recovery - Invalid domain", False, f"Unexpected status {r.status_code}")
    except requests.exceptions.Timeout:
        log_test("Error Recovery - Invalid domain", False, "Request timed out")
    except Exception as e:
        log_test("Error Recovery - Invalid domain", False, str(e))
    
    # Test 2: Server should still work after error
    try:
        payload = {"email": EMAIL, "secret": SECRET, "url": DEMO_URL}
        r = requests.post(ENDPOINT, json=payload, timeout=120)
        
        if r.status_code == 200:
            log_test("Error Recovery - Server operational after error", True, "Server recovered successfully")
        else:
            log_test("Error Recovery - Server operational after error", False, f"Status {r.status_code}")
    except Exception as e:
        log_test("Error Recovery - Server operational after error", False, str(e))
    
    # Test 3: Malformed HTML should not crash
    malformed_html = """<html><body><h1>Broken HTML<form><script>window.quizData = {broken"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(malformed_html)
        temp_file = f.name
    
    try:
        file_url = f"file:///{temp_file.replace(chr(92), '/')}"
        payload = {"email": EMAIL, "secret": SECRET, "url": file_url}
        
        r = requests.post(ENDPOINT, json=payload, timeout=60)
        
        if r.status_code in [200, 400, 500]:
            log_test("Error Recovery - Malformed HTML", True, f"Handled gracefully ({r.status_code})")
        else:
            log_test("Error Recovery - Malformed HTML", False, f"Unexpected status {r.status_code}")
    except Exception as e:
        log_test("Error Recovery - Malformed HTML", False, str(e))
    finally:
        os.unlink(temp_file)
    
    return True


# =============================================================================
# METRIC 7: Security & Validation
# =============================================================================
def metric_7_security_validation():
    print_section("METRIC 7: Security & Validation")
    print("Testing security measures")
    
    # Test 1: Secret validation is enforced
    test_secrets = [
        (None, "Null secret", [403, 422]),  # Can be validation or auth error
        ("wrong-secret", "Wrong secret", 403),
        ("a" * 1000, "Very long secret", 403),
    ]
    
    for test_secret, description, expected_status in test_secrets:
        try:
            payload = {"email": EMAIL, "url": DEMO_URL}
            if test_secret is not None:
                payload["secret"] = test_secret
            
            r = requests.post(ENDPOINT, json=payload, timeout=10)
            
            if isinstance(expected_status, list):
                if r.status_code in expected_status:
                    log_test(f"Security - {description} rejected", True, f"{r.status_code} response")
                else:
                    log_test(f"Security - {description} rejected", False, f"Got {r.status_code} instead of {expected_status}")
            else:
                if r.status_code == expected_status:
                    log_test(f"Security - {description} rejected", True, "403 Forbidden")
                else:
                    log_test(f"Security - {description} rejected", False, f"Got {r.status_code} instead of 403")
        except Exception as e:
            log_test(f"Security - {description} rejected", False, str(e))
    
    # Test 2: Email format validation
    test_emails = [
        ("not-an-email", "Invalid format"),
        ("@example.com", "Missing local part"),
        ("test@", "Missing domain"),
    ]
    
    for test_email, description in test_emails:
        try:
            payload = {"email": test_email, "secret": SECRET, "url": DEMO_URL}
            r = requests.post(ENDPOINT, json=payload, timeout=60)
            
            # Should either reject (422) or process (200)
            if r.status_code in [200, 422]:
                log_test(f"Security - Email validation ({description})", True, f"Status {r.status_code}")
            else:
                log_test(f"Security - Email validation ({description})", False, f"Unexpected {r.status_code}")
        except Exception as e:
            log_test(f"Security - Email validation ({description})", False, str(e))
    
    return True


# =============================================================================
# Main Execution
# =============================================================================
def main():
    print("\n" + "="*70)
    print("  ADVANCED EVALUATION METRICS")
    print("  LLM Quiz Solver - Comprehensive Testing")
    print("="*70)
    print(f"Endpoint: {ENDPOINT}")
    print(f"Student: {EMAIL}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Check server availability
    try:
        r = requests.get("http://127.0.0.1:8000/healthz", timeout=2)
        if r.status_code != 200:
            print("\n❌ ERROR: Server is not responding correctly")
            print("   Start server with: python -m uvicorn app.server.main:app --host 127.0.0.1 --port 8000")
            return
        print("✅ Server is running\n")
    except:
        print("\n❌ ERROR: Cannot connect to server")
        print("   Start server with: python -m uvicorn app.server.main:app --host 127.0.0.1 --port 8000")
        return
    
    # Run all metrics
    start_time = time.time()
    
    metric_1_response_time_performance()
    metric_2_large_data_handling()
    metric_3_malformed_input_handling()
    metric_4_concurrent_requests()
    metric_5_data_type_handling()
    metric_6_error_recovery()
    metric_7_security_validation()
    
    total_time = time.time() - start_time
    
    # Print summary
    print("\n" + "="*70)
    print("  EVALUATION SUMMARY")
    print("="*70)
    print(f"Total Tests: {results['total']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"⚠️  Warnings: {results['warnings']}")
    print(f"\nSuccess Rate: {results['passed']/results['total']*100:.1f}%")
    print(f"Total Evaluation Time: {total_time:.2f}s")
    print("="*70)
    
    if results['failed'] == 0:
        print("\n🎉 EXCELLENT! All critical tests passed!")
        if results['warnings'] > 0:
            print(f"⚠️  Note: {results['warnings']} warning(s) - review for optimization")
    else:
        print(f"\n⚠️  {results['failed']} test(s) failed - review required")
    
    print(f"\nEvaluation completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)


if __name__ == "__main__":
    main()
