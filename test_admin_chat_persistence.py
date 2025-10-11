#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 ADMIN CHAT PERSISTENCE TEST
================================
Test script to verify that admin chat messages are being saved to the database.

This script:
1. Creates a test conversation
2. Saves test messages
3. Verifies data persistence in the database
4. Checks that messages can be retrieved

Author: CogniForge System
Version: 1.0.0
"""

import sys
import os
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models import User, AdminConversation, AdminMessage
from app.services.admin_ai_service import AdminAIService

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


def test_conversation_persistence():
    """Test that conversations and messages are saved to the database"""
    
    print_header("🧪 ADMIN CHAT PERSISTENCE TEST")
    
    app = create_app('testing')
    
    with app.app_context():
        # Create all database tables for testing
        db.create_all()
        
        try:
            # Step 1: Get or create a test user
            print(f"{C}📝 Step 1: Getting test user...{E}")
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
                print(f"{G}✓ Found user: {user.username} (ID: {user.id}){E}")
            
            # Step 2: Create a test conversation using the service
            print(f"\n{C}📝 Step 2: Creating test conversation...{E}")
            service = AdminAIService()
            
            conversation = service.create_conversation(
                user=user,
                title="Test Conversation for Persistence Verification",
                conversation_type="test"
            )
            
            print(f"{G}✓ Created conversation #{conversation.id}{E}")
            print(f"  Title: {conversation.title}")
            print(f"  Type: {conversation.conversation_type}")
            print(f"  Created: {conversation.created_at}")
            
            # Step 3: Save test messages
            print(f"\n{C}📝 Step 3: Saving test messages...{E}")
            
            # Save user message
            service._save_message(
                conversation_id=conversation.id,
                role="user",
                content="This is a test question to verify persistence"
            )
            print(f"{G}✓ Saved user message{E}")
            
            # Save assistant message
            service._save_message(
                conversation_id=conversation.id,
                role="assistant",
                content="This is a test response to verify persistence",
                tokens_used=50,
                model_used="test-model",
                latency_ms=123.45
            )
            print(f"{G}✓ Saved assistant message{E}")
            
            # Step 4: Verify conversation exists in database
            print(f"\n{C}📝 Step 4: Verifying conversation in database...{E}")
            db_conversation = db.session.get(AdminConversation, conversation.id)
            
            if not db_conversation:
                print(f"{R}❌ Conversation not found in database!{E}")
                assert False, "Conversation not found in database"
            
            print(f"{G}✓ Conversation found in database{E}")
            print(f"  ID: {db_conversation.id}")
            print(f"  Title: {db_conversation.title}")
            print(f"  Total Messages: {db_conversation.total_messages}")
            print(f"  Total Tokens: {db_conversation.total_tokens}")
            
            # Step 5: Verify messages exist in database
            print(f"\n{C}📝 Step 5: Verifying messages in database...{E}")
            messages = AdminMessage.query.filter_by(
                conversation_id=conversation.id
            ).order_by(AdminMessage.created_at).all()
            
            assert len(messages) == 2, f"Expected 2 messages, found {len(messages)}"
            
            print(f"{G}✓ Found {len(messages)} messages{E}")
            
            for i, msg in enumerate(messages, 1):
                print(f"\n  Message {i}:")
                print(f"    ID: {msg.id}")
                print(f"    Role: {msg.role}")
                print(f"    Content: {msg.content[:50]}...")
                print(f"    Tokens: {msg.tokens_used}")
                print(f"    Model: {msg.model_used}")
                print(f"    Latency: {msg.latency_ms}ms")
                print(f"    Created: {msg.created_at}")
            
            # Step 6: Test conversation history retrieval
            print(f"\n{C}📝 Step 6: Testing conversation history retrieval...{E}")
            history = service._get_conversation_history(conversation.id)
            
            assert len(history) == 2, f"Expected 2 history items, got {len(history)}"
            
            print(f"{G}✓ Retrieved conversation history{E}")
            for i, item in enumerate(history, 1):
                print(f"  {i}. {item['role']}: {item['content'][:50]}...")
            
            # Step 7: Test conversation analytics
            print(f"\n{C}📝 Step 7: Testing conversation analytics...{E}")
            analytics = service.get_conversation_analytics(conversation.id)
            
            assert analytics.get("status") == "success", f"Failed to get analytics: {analytics.get('error')}"
            
            print(f"{G}✓ Retrieved conversation analytics{E}")
            print(f"  Total Messages: {analytics.get('total_messages')}")
            print(f"  Total Tokens: {analytics.get('total_tokens')}")
            print(f"  Avg Response Time: {analytics.get('avg_response_time_ms')}ms")
            
            # Step 8: Verify data is actually in Supabase (check via raw query)
            print(f"\n{C}📝 Step 8: Verifying data in database via raw query...{E}")
            
            from sqlalchemy import text
            
            # Check conversations table
            result = db.session.execute(
                text("SELECT COUNT(*) FROM admin_conversations WHERE id = :id"),
                {"id": conversation.id}
            )
            conv_count = result.scalar()
            
            assert conv_count > 0, "Conversation not found in raw query"
            
            print(f"{G}✓ Conversation found via raw query (count: {conv_count}){E}")
            
            # Check messages table
            result = db.session.execute(
                text("SELECT COUNT(*) FROM admin_messages WHERE conversation_id = :id"),
                {"id": conversation.id}
            )
            msg_count = result.scalar()
            
            assert msg_count == 2, f"Expected 2 messages in raw query, found {msg_count}"
            
            print(f"{G}✓ Messages found via raw query (count: {msg_count}){E}")
            
            # Success!
            print(f"\n{G}{BOLD}{'=' * 80}{E}")
            print(f"{G}{BOLD}{'✅ ALL TESTS PASSED! PERSISTENCE VERIFIED!':^80}{E}")
            print(f"{G}{BOLD}{'=' * 80}{E}\n")
            
            print(f"{M}📊 Summary:{E}")
            print(f"  • Conversation ID: {conversation.id}")
            print(f"  • Messages Saved: {msg_count}")
            print(f"  • Total Tokens: {db_conversation.total_tokens}")
            print(f"  • Database: {'Supabase' if 'supabase' in os.getenv('DATABASE_URL', '') else 'Local'}")
            
            print(f"\n{C}💡 You can now check Supabase to see this data!{E}")
            print(f"   1. Go to your Supabase project dashboard")
            print(f"   2. Navigate to Table Editor")
            print(f"   3. View 'admin_conversations' and 'admin_messages' tables")
            print(f"   4. Look for conversation ID: {conversation.id}\n")
            
        except Exception as e:
            print(f"\n{R}❌ Test failed with error:{E}")
            print(f"{R}{str(e)}{E}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    print(f"\n{Y}Starting Admin Chat Persistence Test...{E}\n")
    
    success = test_conversation_persistence()
    
    if success:
        print(f"\n{G}✅ Test completed successfully!{E}\n")
        sys.exit(0)
    else:
        print(f"\n{R}❌ Test failed!{E}\n")
        sys.exit(1)
