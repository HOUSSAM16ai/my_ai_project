"""
======================================================================================
==                    API USAGE EXAMPLES (v1.0)                                    ==
======================================================================================
PRIME DIRECTIVE:
    أمثلة عملية شاملة للـ API - Comprehensive practical API examples

This file contains working examples for all API operations.
Run this file to see the API in action!
"""

import json
from typing import Any

import requests

# Base URL - Change this to your API URL
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/admin/api/database"


# Colors for console output
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_section(title: str):
    """Print a section header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title:^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")


def print_info(message: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")


def print_json(data: dict[Any, Any]):
    """Pretty print JSON data"""
    print(f"{Colors.OKBLUE}{json.dumps(data, indent=2, ensure_ascii=False)}{Colors.ENDC}")


# ======================================================================================
# EXAMPLE 1: HEALTH CHECKS
# ======================================================================================


def example_health_checks():
    """Example: Health check endpoints"""
    print_section("EXAMPLE 1: Health Checks")

    # Database health check
    print_info("Checking database health...")
    response = requests.get(f"{API_BASE}/health")

    if response.status_code == 200:
        print_success("Database is healthy!")
        print_json(response.json())
    else:
        print_error(f"Health check failed: {response.status_code}")

    # Database statistics
    print_info("\nGetting database statistics...")
    response = requests.get(f"{API_BASE}/stats")

    if response.status_code == 200:
        print_success("Statistics retrieved!")
        print_json(response.json())
    else:
        print_error(f"Stats request failed: {response.status_code}")

    # List all tables
    print_info("\nListing all tables...")
    response = requests.get(f"{API_BASE}/tables")

    if response.status_code == 200:
        data = response.json()
        print_success(f"Found {len(data.get('tables', []))} tables!")
        for table in data.get("tables", [])[:3]:  # Show first 3
            print(f"  {table.get('icon', '📁')} {table['name']}: {table['count']} records")
    else:
        print_error(f"Tables request failed: {response.status_code}")


# ======================================================================================
# EXAMPLE 2: CREATE (POST)
# ======================================================================================


def example_create_operations():
    """Example: Creating new records"""
    print_section("EXAMPLE 2: Create Operations (POST)")

    # Create a new user
    print_info("Creating a new user...")
    user_data = {
        "email": "demo_user@example.com",
        "username": "demo_user",
        "password": "secure_password_123",
    }

    response = requests.post(f"{API_BASE}/record/users", json=user_data)

    if response.status_code == 200:
        data = response.json()
        print_success(f"User created with ID: {data.get('id')}")
        print_json(data)
        return data.get("id")
    else:
        print_error(f"User creation failed: {response.status_code}")
        print_json(response.json())
        return None


# ======================================================================================
# EXAMPLE 3: READ (GET)
# ======================================================================================


def example_read_operations():
    """Example: Reading records"""
    print_section("EXAMPLE 3: Read Operations (GET)")

    # Read all users with pagination
    print_info("Reading users (page 1, 10 per page)...")
    response = requests.get(
        f"{API_BASE}/table/users",
        params={"page": 1, "per_page": 10, "order_by": "created_at", "order_dir": "desc"},
    )

    if response.status_code == 200:
        data = response.json()
        print_success(f"Found {data.get('total')} users total")
        print_info(f"Showing page {data.get('page')} of {data.get('pages')}")
        print_json(
            {
                "total": data.get("total"),
                "page": data.get("page"),
                "pages": data.get("pages"),
                "rows_count": len(data.get("rows", [])),
            }
        )
    else:
        print_error(f"Read failed: {response.status_code}")

    # Read a single user
    print_info("\nReading a single user (ID: 1)...")
    response = requests.get(f"{API_BASE}/record/users/1")

    if response.status_code == 200:
        print_success("User found!")
        print_json(response.json())
    else:
        print_error(f"Read failed: {response.status_code}")


# ======================================================================================
# EXAMPLE 4: UPDATE (PUT)
# ======================================================================================


def example_update_operations(user_id: int = None):
    """Example: Updating records"""
    print_section("EXAMPLE 4: Update Operations (PUT)")

    if not user_id:
        print_info("Using default user ID: 1")
        user_id = 1

    print_info(f"Updating user ID: {user_id}...")
    update_data = {"username": "updated_demo_user"}

    response = requests.put(f"{API_BASE}/record/users/{user_id}", json=update_data)

    if response.status_code == 200:
        print_success("User updated successfully!")
        print_json(response.json())
    else:
        print_error(f"Update failed: {response.status_code}")
        print_json(response.json())


# ======================================================================================
# EXAMPLE 5: DELETE (DELETE)
# ======================================================================================


def example_delete_operations(user_id: int = None):
    """Example: Deleting records"""
    print_section("EXAMPLE 5: Delete Operations (DELETE)")

    if not user_id:
        print_info("Skipping delete (no user ID provided)")
        return

    print_info(f"Deleting user ID: {user_id}...")
    response = requests.delete(f"{API_BASE}/record/users/{user_id}")

    if response.status_code == 200:
        print_success("User deleted successfully!")
        print_json(response.json())
    else:
        print_error(f"Delete failed: {response.status_code}")
        print_json(response.json())


# ======================================================================================
# EXAMPLE 6: SEARCH AND FILTERING
# ======================================================================================


def example_search_and_filter():
    """Example: Search and filtering"""
    print_section("EXAMPLE 6: Search and Filtering")

    # Search for users
    print_info("Searching for users with 'admin' in their data...")
    response = requests.get(
        f"{API_BASE}/table/users", params={"search": "admin", "page": 1, "per_page": 5}
    )

    if response.status_code == 200:
        data = response.json()
        print_success(f"Found {len(data.get('rows', []))} matching users")
        print_json(data)
    else:
        print_error(f"Search failed: {response.status_code}")


# ======================================================================================
# EXAMPLE 7: CUSTOM SQL QUERIES
# ======================================================================================


def example_custom_queries():
    """Example: Custom SQL queries"""
    print_section("EXAMPLE 7: Custom SQL Queries")

    print_info("Executing custom SQL query...")
    query_data = {
        "sql": "SELECT id, username, email, is_admin FROM users WHERE is_admin = true LIMIT 5"
    }

    response = requests.post(f"{API_BASE}/query", json=query_data)

    if response.status_code == 200:
        print_success("Query executed successfully!")
        print_json(response.json())
    else:
        print_error(f"Query failed: {response.status_code}")
        print_json(response.json())


# ======================================================================================
# EXAMPLE 8: ERROR HANDLING
# ======================================================================================


def example_error_handling():
    """Example: Error handling"""
    print_section("EXAMPLE 8: Error Handling")

    # Invalid email validation
    print_info("Testing validation error (invalid email)...")
    invalid_user = {"email": "not-an-email", "username": "test", "password": "test"}

    response = requests.post(f"{API_BASE}/record/users", json=invalid_user)

    if response.status_code != 200:
        print_success("Validation error caught correctly!")
        print_json(response.json())

    # Missing required fields
    print_info("\nTesting validation error (missing fields)...")
    incomplete_user = {"email": "test@example.com"}

    response = requests.post(f"{API_BASE}/record/users", json=incomplete_user)

    if response.status_code != 200:
        print_success("Missing fields error caught correctly!")
        print_json(response.json())

    # Not found error
    print_info("\nTesting not found error...")
    response = requests.get(f"{API_BASE}/record/users/999999")

    if response.status_code != 200:
        print_success("Not found error handled correctly!")
        print_json(response.json())


# ======================================================================================
# EXAMPLE 9: WORKING WITH MISSIONS
# ======================================================================================


def example_mission_operations():
    """Example: Working with missions"""
    print_section("EXAMPLE 9: Mission Operations")

    # Create a mission
    print_info("Creating a new mission...")
    mission_data = {
        "objective": "تطوير نظام API خارق احترافي يتفوق على الشركات العملاقة",
        "status": "IN_PROGRESS",
        "priority": "HIGH",
    }

    response = requests.post(f"{API_BASE}/record/missions", json=mission_data)

    if response.status_code == 200:
        data = response.json()
        print_success(f"Mission created with ID: {data.get('id')}")
        print_json(data)

        # Read the mission
        mission_id = data.get("id")
        if mission_id:
            print_info(f"\nReading mission ID: {mission_id}...")
            response = requests.get(f"{API_BASE}/record/missions/{mission_id}")

            if response.status_code == 200:
                print_success("Mission retrieved!")
                print_json(response.json())
    else:
        print_error(f"Mission creation failed: {response.status_code}")


# ======================================================================================
# EXAMPLE 10: PAGINATION DEMO
# ======================================================================================


def example_pagination_demo():
    """Example: Pagination demonstration"""
    print_section("EXAMPLE 10: Pagination Demo")

    print_info("Getting page 1 of users (5 per page)...")
    response = requests.get(f"{API_BASE}/table/users", params={"page": 1, "per_page": 5})

    if response.status_code == 200:
        data = response.json()
        print_success(f"Page 1/{data.get('pages')} retrieved")
        print_info(f"Total records: {data.get('total')}")
        print_info(f"Records on this page: {len(data.get('rows', []))}")

        # Get next page if available
        if data.get("pages", 0) > 1:
            print_info("\nGetting page 2...")
            response = requests.get(f"{API_BASE}/table/users", params={"page": 2, "per_page": 5})

            if response.status_code == 200:
                data = response.json()
                print_success(f"Page 2/{data.get('pages')} retrieved")
                print_info(f"Records on this page: {len(data.get('rows', []))}")


# ======================================================================================
# MAIN FUNCTION
# ======================================================================================


def main():
    """Run all examples"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("=" * 70)
    print("     CogniForge API - Comprehensive Usage Examples")
    print("     نظام API الخارق - أمثلة شاملة للاستخدام")
    print("=" * 70)
    print(f"{Colors.ENDC}\n")

    print_info(f"API Base URL: {API_BASE}")
    print_info("Make sure the API is running before executing these examples!")
    print_info("You may need to be logged in as an admin user.\n")

    input("Press Enter to start the examples...")

    try:
        # Run all examples
        example_health_checks()
        input("\nPress Enter to continue...")

        user_id = example_create_operations()
        input("\nPress Enter to continue...")

        example_read_operations()
        input("\nPress Enter to continue...")

        example_update_operations(user_id)
        input("\nPress Enter to continue...")

        example_search_and_filter()
        input("\nPress Enter to continue...")

        example_custom_queries()
        input("\nPress Enter to continue...")

        example_error_handling()
        input("\nPress Enter to continue...")

        example_mission_operations()
        input("\nPress Enter to continue...")

        example_pagination_demo()

        # Clean up (optional)
        if user_id:
            print_info("\n\nCleaning up demo user...")
            example_delete_operations(user_id)

        print_section("ALL EXAMPLES COMPLETED! 🎉")
        print_success("You've seen all the main API operations!")
        print_info("Check the documentation for more details:")
        print_info("  - CRUD_API_GUIDE_AR.md")
        print_info("  - CRUD_API_QUICK_START.md")
        print_info("  - DEPLOYMENT_GUIDE.md")

    except requests.exceptions.ConnectionError:
        print_error("\n\n❌ Connection Error!")
        print_info("Make sure the API is running at: http://localhost:5000")
        print_info("Run: flask run")
    except Exception as e:
        print_error(f"\n\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
