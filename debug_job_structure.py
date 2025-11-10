"""Debug script to examine the actual job data structure."""

import requests
import json
from pprint import pprint

API_URL = "http://localhost:8000"

def deep_inspect_job(job_id):
    """Deeply inspect the job structure to find where the data really is."""

    # First, get the raw status
    url = f"{API_URL}/api/contracts/{job_id}/status"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Error: Job {job_id} not found")
        return

    data = response.json()

    print("=" * 80)
    print("COMPLETE JOB STRUCTURE")
    print("=" * 80)

    # Show top-level keys
    print("\n1. TOP-LEVEL KEYS:")
    print("-" * 40)
    for key in data.keys():
        value_type = type(data[key]).__name__
        value_preview = str(data[key])[:100] if not isinstance(data[key], (dict, list)) else f"{value_type} with {len(data[key])} items" if isinstance(data[key], (dict, list)) else value_type
        print(f"  - {key}: {value_preview}")

    # Check the result structure
    if 'result' in data:
        result = data['result']
        print("\n2. RESULT STRUCTURE:")
        print("-" * 40)
        for key in result.keys():
            value_type = type(result[key]).__name__
            if isinstance(result[key], list):
                print(f"  - {key}: list with {len(result[key])} items")
            elif isinstance(result[key], dict):
                print(f"  - {key}: dict with keys: {list(result[key].keys())[:5]}")
            else:
                print(f"  - {key}: {result[key][:100] if isinstance(result[key], str) else result[key]}")

        # Look for analysis results in different possible locations
        print("\n3. SEARCHING FOR ANALYSIS DATA:")
        print("-" * 40)

        # Common field names that might contain the analysis
        possible_fields = [
            'analysis_results',
            'analysisResults',
            'results',
            'clauses',
            'analysis',
            'data',
            'contract_analysis',
            'clause_analysis'
        ]

        for field in possible_fields:
            if field in result:
                print(f"  ✓ Found '{field}': {type(result[field]).__name__}")
                if isinstance(result[field], list):
                    print(f"    - Length: {len(result[field])}")
                    if len(result[field]) > 0:
                        print(f"    - First item keys: {list(result[field][0].keys()) if isinstance(result[field][0], dict) else 'Not a dict'}")
                elif isinstance(result[field], dict):
                    print(f"    - Keys: {list(result[field].keys())[:10]}")

        # Check if analysis_results exists and examine its structure
        if 'analysis_results' in result:
            analysis_results = result['analysis_results']
            if len(analysis_results) > 0:
                print("\n4. FIRST ANALYSIS RESULT ITEM:")
                print("-" * 40)
                first_item = analysis_results[0]
                for key, value in first_item.items():
                    print(f"  - {key}: {type(value).__name__} = {str(value)[:100] if not isinstance(value, (dict, list)) else f'{type(value).__name__}'}")

                # Check compliance status
                print("\n5. COMPLIANCE FIELD CHECK:")
                print("-" * 40)
                compliant_fields = ['compliant', 'compliance_status', 'is_compliant', 'status']
                for field in compliant_fields:
                    if field in first_item:
                        print(f"  ✓ Found '{field}': {first_item[field]}")

    # Also check the raw data without the 'result' wrapper
    print("\n6. RAW DATA ANALYSIS FIELDS:")
    print("-" * 40)
    for key in data.keys():
        if 'analysis' in key.lower() or 'result' in key.lower() or 'clause' in key.lower():
            print(f"  - {key}: {type(data[key]).__name__}")
            if isinstance(data[key], list) and len(data[key]) > 0:
                print(f"    Length: {len(data[key])}")
                if isinstance(data[key][0], dict):
                    print(f"    First item has keys: {list(data[key][0].keys())[:5]}")

    # Save full response to file for inspection
    with open('job_debug_output.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("\n✓ Full response saved to 'job_debug_output.json'")

    return data

def check_context_endpoint(job_id):
    """Check what the context endpoint returns."""
    url = f"{API_URL}/api/chat/{job_id}/context"
    response = requests.get(url)

    if response.status_code == 200:
        print("\n" + "=" * 80)
        print("CONTEXT ENDPOINT RESPONSE")
        print("=" * 80)
        data = response.json()
        pprint(data)
    else:
        print(f"\nContext endpoint error: {response.status_code}")

def main():
    print("Enter job ID to debug: ")
    job_id = input().strip()

    if not job_id:
        # Use the one from the logs
        job_id = "d38af3f5-30ee-4a35-9839-1f30595d67fc"
        print(f"Using job ID from logs: {job_id}")

    data = deep_inspect_job(job_id)
    check_context_endpoint(job_id)

    # Additional check: print the actual path to analysis results
    if data and 'result' in data:
        print("\n" + "=" * 80)
        print("ANALYSIS RESULTS PATH")
        print("=" * 80)
        result = data['result']

        # Try to find where the actual clause data is
        def find_clauses(obj, path=""):
            """Recursively find arrays that might contain clauses."""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    if isinstance(value, list) and len(value) > 0:
                        # Check if this looks like clause data
                        first_item = value[0] if value else {}
                        if isinstance(first_item, dict):
                            # Look for clause-like fields
                            clause_indicators = ['clause', 'text', 'compliant', 'compliance', 'type', 'risk']
                            matches = sum(1 for indicator in clause_indicators if any(indicator in k.lower() for k in first_item.keys()))
                            if matches >= 2:
                                print(f"  Potential clause data at: result.{new_path}")
                                print(f"    - Contains {len(value)} items")
                                print(f"    - First item keys: {list(first_item.keys())[:8]}")
                    elif isinstance(value, dict):
                        find_clauses(value, new_path)

        find_clauses(result)

if __name__ == "__main__":
    main()