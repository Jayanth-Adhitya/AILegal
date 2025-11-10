"""Debug script to see the actual structure of analysis results."""

import requests
import json
from pprint import pprint

API_URL = "http://localhost:8000"

def check_job_structure(job_id):
    """Check the actual structure of job results."""
    url = f"{API_URL}/api/contracts/{job_id}/status"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            result = data.get('result', {})
            analysis = result.get('analysis_results', [])
            summary = result.get('summary', {})

            print("=" * 60)
            print("JOB STRUCTURE ANALYSIS")
            print("=" * 60)

            print("\n1. SUMMARY STRUCTURE:")
            print("-" * 40)
            pprint(summary)

            print("\n2. FIRST CLAUSE STRUCTURE:")
            print("-" * 40)
            if analysis:
                first_clause = analysis[0]
                pprint(first_clause)

                print("\n3. KEY FIELDS IN FIRST CLAUSE:")
                print("-" * 40)
                print(f"  - compliant: {first_clause.get('compliant')} (type: {type(first_clause.get('compliant'))})")
                print(f"  - compliance_status: {first_clause.get('compliance_status')} (type: {type(first_clause.get('compliance_status'))})")
                print(f"  - issues: {first_clause.get('issues')}")
                print(f"  - risk_level: {first_clause.get('risk_level')}")

            print("\n4. COMPLIANCE STATUS DISTRIBUTION:")
            print("-" * 40)
            compliant_count = 0
            non_compliant_count = 0

            for clause in analysis:
                # Check different possible fields
                if 'compliant' in clause:
                    if clause['compliant']:
                        compliant_count += 1
                    else:
                        non_compliant_count += 1
                elif 'compliance_status' in clause:
                    if clause['compliance_status'] == 'Compliant':
                        compliant_count += 1
                    elif clause['compliance_status'] == 'Non-Compliant':
                        non_compliant_count += 1

            print(f"  Compliant: {compliant_count}")
            print(f"  Non-Compliant: {non_compliant_count}")
            print(f"  Total: {len(analysis)}")

            # Show a non-compliant clause if exists
            print("\n5. SAMPLE NON-COMPLIANT CLAUSE (if any):")
            print("-" * 40)
            for i, clause in enumerate(analysis):
                is_non_compliant = False

                # Check both possible fields
                if 'compliant' in clause and not clause['compliant']:
                    is_non_compliant = True
                elif 'compliance_status' in clause and clause['compliance_status'] == 'Non-Compliant':
                    is_non_compliant = True

                if is_non_compliant:
                    print(f"Clause {i+1}:")
                    pprint(clause)
                    break

            return True
        else:
            print(f"Job {job_id} not found")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("Enter job ID to debug: ")
    job_id = input().strip()

    if job_id:
        check_job_structure(job_id)
    else:
        print("No job ID provided")

if __name__ == "__main__":
    main()