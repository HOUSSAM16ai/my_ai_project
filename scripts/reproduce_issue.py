import asyncio
from app.services.boundaries.customer_chat_boundary_service import CustomerChatBoundaryService

def test_looks_like_content_request():
    service = CustomerChatBoundaryService(None) # Mock DB session

    # 1. The original failing query (Educational follow-up)
    failing_query = "لم افهم من أين جاءت 27/55"
    if service._looks_like_content_request(failing_query):
        print(f"PASS: Recognized '{failing_query}'")
    else:
        print(f"FAIL: Did not recognize '{failing_query}'")

    # 2. English educational query
    eng_query = "Can you explain the result?"
    if service._looks_like_content_request(eng_query):
        print(f"PASS: Recognized '{eng_query}'")
    else:
        print(f"FAIL: Did not recognize '{eng_query}'")

    # 3. False positive check (should NOT match)
    false_pos = "However, I think we should proceed differently."
    if not service._looks_like_content_request(false_pos):
        print(f"PASS: Correctly ignored '{false_pos}'")
    else:
        print(f"FAIL: Incorrectly flagged '{false_pos}' (likely matched 'how' inside 'however')")

    # 4. Another False positive check
    false_pos_2 = "Show me the list."
    if not service._looks_like_content_request(false_pos_2):
        print(f"PASS: Correctly ignored '{false_pos_2}'")
    else:
        # Note: "show" was previously matching "how" if using substrings
        print(f"FAIL: Incorrectly flagged '{false_pos_2}'")

if __name__ == "__main__":
    test_looks_like_content_request()
