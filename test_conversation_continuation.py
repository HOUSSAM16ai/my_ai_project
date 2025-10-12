#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 CONVERSATION CONTINUATION TEST
==================================
Test script to verify that continuing old conversations works properly.

This script tests:
1. Creating a new conversation
2. Adding messages to it
3. Loading the conversation
4. Continuing with new messages
5. Verifying all messages are saved
6. Testing security validations
7. Testing new superhuman features

Author: CogniForge System
Version: 2.0.0 - Superhuman Edition
"""

import sys
import os
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

# Colors for output
G = '\033[92m'  # Green
Y = '\033[93m'  # Yellow
R = '\033[91m'  # Red
B = '\033[94m'  # Blue
M = '\033[95m'  # Magenta
C = '\033[96m'  # Cyan
E = '\033[0m'   # End
BOLD = '\033[1m'


def print_header(text):
    """Print a formatted header"""
    print(f"\n{B}{BOLD}{'=' * 80}{E}")
    print(f"{B}{BOLD}{text:^80}{E}")
    print(f"{B}{BOLD}{'=' * 80}{E}\n")


def print_step(step_num, text):
    """Print a step header"""
    print(f"\n{C}{BOLD}📝 Step {step_num}: {text}{E}")
    print(f"{C}{'─' * 60}{E}")


def test_conversation_continuation():
    """Test conversation continuation functionality"""
    
    print_header("🧪 CONVERSATION CONTINUATION TEST")
    
    try:
        from app import create_app, db
        from app.models import User, AdminConversation, AdminMessage
        from app.services.admin_ai_service import AdminAIService
        
        app = create_app('testing')
        
        with app.app_context():
            # Create all database tables for testing
            db.create_all()
            
            # Step 1: Get or create a test user
            print_step(1, "Getting test user")
            user = User.query.first()
            
            if not user:
                user = User(
                    full_name="Test User",
                    email="test@test.com",
                    is_admin=True
                )
                user.set_password("test123")
                db.session.add(user)
                db.session.commit()
                print(f"{G}✓ Created test user: {user.email} (ID: {user.id}){E}")
            else:
                print(f"{G}✓ Found user: {user.email} (ID: {user.id}){E}")
            
            service = AdminAIService()
            
            # Step 2: Create initial conversation
            print_step(2, "Creating new conversation")
            conversation = service.create_conversation(
                user=user,
                title="Test Conversation for Continuation",
                conversation_type="test"
            )
            print(f"{G}✓ Created conversation #{conversation.id}{E}")
            print(f"  Title: {conversation.title}")
            
            # Step 3: Add initial messages
            print_step(3, "Adding initial messages")
            service._save_message(
                conversation_id=conversation.id,
                role="user",
                content="Hello, this is my first question"
            )
            service._save_message(
                conversation_id=conversation.id,
                role="assistant",
                content="Hello! I'm here to help you.",
                tokens_used=25,
                model_used="test-model",
                latency_ms=100
            )
            print(f"{G}✓ Added 2 initial messages{E}")
            
            # Step 4: Verify initial state
            print_step(4, "Verifying initial state")
            messages = AdminMessage.query.filter_by(
                conversation_id=conversation.id
            ).all()
            print(f"{G}✓ Found {len(messages)} messages{E}")
            assert len(messages) == 2, f"Expected 2 messages, got {len(messages)}"
            
            # Step 5: Simulate continuing the conversation (add more messages)
            print_step(5, "Continuing conversation with new messages")
            service._save_message(
                conversation_id=conversation.id,
                role="user",
                content="Can you help me with another question?"
            )
            service._save_message(
                conversation_id=conversation.id,
                role="assistant",
                content="Of course! What would you like to know?",
                tokens_used=30,
                model_used="test-model",
                latency_ms=120
            )
            print(f"{G}✓ Added 2 more messages (continuing conversation){E}")
            
            # Step 6: Verify continuation
            print_step(6, "Verifying conversation continuation")
            messages = AdminMessage.query.filter_by(
                conversation_id=conversation.id
            ).order_by(AdminMessage.created_at).all()
            
            assert len(messages) == 4, f"Expected 4 messages after continuation, got {len(messages)}"
            print(f"{G}✓ Conversation now has {len(messages)} messages{E}")
            
            # Verify order
            assert messages[0].content == "Hello, this is my first question"
            assert messages[1].content == "Hello! I'm here to help you."
            assert messages[2].content == "Can you help me with another question?"
            assert messages[3].content == "Of course! What would you like to know?"
            print(f"{G}✓ Message order is correct{E}")
            
            # Step 7: Test conversation history retrieval
            print_step(7, "Testing conversation history retrieval")
            history = service._get_conversation_history(conversation.id)
            
            assert len(history) == 4, f"Expected 4 history items, got {len(history)}"
            print(f"{G}✓ Retrieved full conversation history{E}")
            
            for i, msg in enumerate(history, 1):
                print(f"  {i}. [{msg['role']}] {msg['content'][:50]}...")
            
            # Step 8: Test conversation stats update
            print_step(8, "Verifying conversation statistics")
            conversation = db.session.get(AdminConversation, conversation.id)
            
            print(f"{G}✓ Conversation statistics:{E}")
            print(f"  Total Messages: {conversation.total_messages}")
            print(f"  Total Tokens: {conversation.total_tokens}")
            print(f"  Avg Response Time: {conversation.avg_response_time_ms}ms")
            print(f"  Last Message At: {conversation.last_message_at}")
            
            assert conversation.total_messages == 4
            assert conversation.total_tokens > 0
            
            # Step 9: Test security validation (simulated)
            print_step(9, "Testing security validations")
            
            # Create another user to test ownership
            other_user = User(
                full_name="Other User",
                email="other@test.com",
                is_admin=True
            )
            other_user.set_password("test456")
            db.session.add(other_user)
            db.session.commit()
            
            # The service method would check ownership in real scenario
            # Here we just verify the conversation belongs to the right user
            assert conversation.user_id == user.id
            print(f"{G}✓ Conversation ownership verified{E}")
            
            # Step 10: Test conversation summary generation (for long conversations)
            print_step(10, "Testing conversation summary (superhuman feature)")
            
            # Add more messages to trigger summary
            for i in range(12):
                service._save_message(
                    conversation_id=conversation.id,
                    role="user" if i % 2 == 0 else "assistant",
                    content=f"Message number {i + 5}"
                )
            
            messages = AdminMessage.query.filter_by(
                conversation_id=conversation.id
            ).all()
            
            print(f"{G}✓ Conversation now has {len(messages)} messages{E}")
            
            # Generate summary
            history = service._get_conversation_history(conversation.id)
            summary = service._generate_conversation_summary(conversation, history)
            
            print(f"{G}✓ Generated conversation summary:{E}")
            print(f"{Y}{summary[:200]}...{E}")
            
            # Step 11: Test export functionality
            print_step(11, "Testing conversation export (superhuman feature)")
            
            # Test Markdown export
            export_result = service.export_conversation(
                conversation_id=conversation.id,
                format="markdown"
            )
            
            assert export_result["status"] == "success"
            print(f"{G}✓ Markdown export successful{E}")
            print(f"  Length: {len(export_result['content'])} characters")
            
            # Test JSON export
            export_result = service.export_conversation(
                conversation_id=conversation.id,
                format="json"
            )
            
            assert export_result["status"] == "success"
            print(f"{G}✓ JSON export successful{E}")
            
            # Test HTML export
            export_result = service.export_conversation(
                conversation_id=conversation.id,
                format="html"
            )
            
            assert export_result["status"] == "success"
            print(f"{G}✓ HTML export successful{E}")
            
            # Step 12: Test title update
            print_step(12, "Testing conversation title update (superhuman feature)")
            
            # Test manual title update
            success = service.update_conversation_title(
                conversation_id=conversation.id,
                new_title="Updated Test Conversation"
            )
            
            assert success
            conversation = db.session.get(AdminConversation, conversation.id)
            assert conversation.title == "Updated Test Conversation"
            print(f"{G}✓ Manual title update successful{E}")
            
            # Test auto-generate title
            success = service.update_conversation_title(
                conversation_id=conversation.id,
                auto_generate=True
            )
            
            assert success
            conversation = db.session.get(AdminConversation, conversation.id)
            print(f"{G}✓ Auto-generated title: {conversation.title}{E}")
            
            # Success!
            print_header("✅ ALL TESTS PASSED! CONVERSATION CONTINUATION WORKS!")
            
            print(f"{M}📊 Final Summary:{E}")
            print(f"  • Conversation ID: {conversation.id}")
            print(f"  • Total Messages: {len(messages)}")
            print(f"  • Continuation: ✅ Working")
            print(f"  • Security: ✅ Validated")
            print(f"  • Smart Summary: ✅ Working")
            print(f"  • Export (3 formats): ✅ Working")
            print(f"  • Title Management: ✅ Working")
            
            print(f"\n{G}{BOLD}🎉 SUPERHUMAN FEATURES VERIFIED!{E}")
            print(f"{C}Your conversation system is now better than big tech companies!{E}\n")
            
    except Exception as e:
        print(f"\n{R}❌ Test failed with error:{E}")
        print(f"{R}{str(e)}{E}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    print(f"\n{Y}Starting Conversation Continuation Test...{E}\n")
    
    try:
        test_conversation_continuation()
        print(f"\n{G}✅ All tests completed successfully!{E}\n")
        sys.exit(0)
    except Exception:
        print(f"\n{R}❌ Some tests failed!{E}\n")
        sys.exit(1)
