"""Test script to verify chatbot context is working properly."""

import requests
import json

# Configuration
API_URL = "http://localhost:8000"
JOB_ID = "test-job-123"  # Replace with actual job ID

def test_chat_endpoint(job_id, message):
    """Test the chat endpoint with a message."""
    url = f"{API_URL}/api/chat/{job_id}"

    payload = {
        "message": message,
        "history": []
    }

    try:
        response = requests.post(url, json=payload, stream=True)

        if response.status_code == 200:
            print(f"✓ Chat endpoint working for job {job_id}")
            print("Response stream:")

            # Process SSE stream
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            if 'content' in data:
                                print(data['content'], end='', flush=True)
                            elif 'done' in data:
                                print("\n✓ Stream completed")
                                break
                        except json.JSONDecodeError:
                            pass
        else:
            error_data = response.json()
            print(f"✗ Error {response.status_code}: {error_data.get('detail', 'Unknown error')}")

    except Exception as e:
        print(f"✗ Connection error: {e}")

def check_job_status(job_id):
    """Check if a job exists and has results."""
    url = f"{API_URL}/api/contracts/{job_id}/status"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            result = data.get('result', {})
            analysis = result.get('analysis_results', [])

            print(f"✓ Job {job_id} found")
            print(f"  Status: {data.get('status')}")
            print(f"  Contract: {result.get('contract_name', 'Unknown')}")
            print(f"  Clauses analyzed: {len(analysis)}")

            # Count non-compliant clauses
            non_compliant = [c for c in analysis if not c.get('compliant', True)]
            print(f"  Non-compliant clauses: {len(non_compliant)}")

            return True
        else:
            print(f"✗ Job {job_id} not found")
            return False

    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False

def main():
    print("=" * 60)
    print("CHATBOT CONTEXT TEST")
    print("=" * 60)

    # First check if API is running
    try:
        health = requests.get(f"{API_URL}/health")
        if health.status_code == 200:
            print("✓ API is running")
        else:
            print("✗ API health check failed")
            return
    except:
        print("✗ API is not running at", API_URL)
        print("Please start the backend with: python -m uvicorn src.api:app --reload")
        return

    print("\nEnter a job ID to test (or press Enter to skip): ")
    job_id_input = input().strip()

    if job_id_input:
        JOB_ID = job_id_input
    else:
        print(f"Using default job ID: {JOB_ID}")

    print(f"\nChecking job {JOB_ID}...")

    if check_job_status(JOB_ID):
        print("\n" + "=" * 60)
        print("TESTING CHATBOT QUESTIONS")
        print("=" * 60)

        test_questions = [
            "What are the non-compliant clauses?",
            "List all compliance issues found",
            "What is the overall risk level?",
        ]

        for i, question in enumerate(test_questions, 1):
            print(f"\n[Question {i}] {question}")
            print("-" * 40)
            test_chat_endpoint(JOB_ID, question)
            print("\n")

            # Ask if user wants to continue
            if i < len(test_questions):
                cont = input("Press Enter to test next question (or 'q' to quit): ")
                if cont.lower() == 'q':
                    break
    else:
        print("\n⚠️  No valid job found. Please:")
        print("1. Upload a contract at http://localhost:3000/analyze")
        print("2. Start the analysis")
        print("3. Copy the job ID from the URL")
        print("4. Run this script again with that job ID")

if __name__ == "__main__":
    main()