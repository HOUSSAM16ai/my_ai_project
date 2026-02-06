
import sys
import os
import re

# Add app to path
sys.path.append(os.getcwd())

from app.services.chat.tools.retrieval import parsing
from app.services.chat.tools.retrieval.parsing import remove_solution_section, is_solution_request, normalize_semantic_text

def test_parsing_logic():
    print("--- Testing Parsing Logic ---")

    # 1. Load the specific file content
    filepath = "data/knowledge/bac_2024_probability.md"
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"ERROR: File {filepath} not found.")
        return

    # 2. Test is_solution_request with the specific user query
    user_query = "اعطني تمرين الاحتمالات بكالوريا شعبة علوم تجريبية الموضوع الاول التمرين الأول لسنة 2024 في مادة الرياضيات اعطني الاسئلة فقط بدون حل"

    is_sol = is_solution_request(user_query)
    print(f"User Query: {user_query}")
    print(f"is_solution_request: {is_sol}")

    if is_sol:
        print("FAIL: Query should NOT be interpreted as a solution request.")
    else:
        print("PASS: Query correctly interpreted as NOT a solution request.")

    # 3. Test remove_solution_section
    print("\n--- Testing remove_solution_section ---")

    # Simulate what happens in LocalKnowledgeStore:
    # It passes the content to remove_solution_section if is_solution_request is False

    cleaned_content = remove_solution_section(content)

    print(f"Original Length: {len(content)}")
    print(f"Cleaned Length: {len(cleaned_content)}")

    # Check if the solution section header is still there
    # The header in the file is: ## 2. الإجابة النموذجية مع سلم التنقيط (Model Answer & Grading)

    solution_header_fragment = "الإجابة النموذجية"
    if solution_header_fragment in cleaned_content:
        print(f"FAIL: Solution header fragment '{solution_header_fragment}' found in cleaned content.")
        # Find where it is
        idx = cleaned_content.find(solution_header_fragment)
        print(f"Context around failure: ...{cleaned_content[max(0, idx-50):min(len(cleaned_content), idx+100)]}...")
    else:
        print("PASS: Solution header fragment not found in cleaned content.")

    # Check if the content is empty
    if not cleaned_content.strip():
        print("FAIL: Cleaned content is empty!")
    else:
        print("PASS: Cleaned content is not empty.")
        print(f"Preview: {cleaned_content[:200]}...")

if __name__ == "__main__":
    test_parsing_logic()
