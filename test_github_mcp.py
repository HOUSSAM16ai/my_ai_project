#!/usr/bin/env python3
"""
GitHub MCP Server - Test & Example Script
==========================================

This script demonstrates how to use the GitHub API with the MCP Server's
authentication token. It provides examples of common GitHub operations.

Usage:
    python test_github_mcp.py

Requirements:
    - GITHUB_PERSONAL_ACCESS_TOKEN in .env file
    - requests library (pip install requests)
"""

import os
import sys
from datetime import datetime

try:
    import requests
except ImportError:
    print("❌ Error: 'requests' library not found")
    print("Install with: pip install requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print("⚠️  Warning: 'python-dotenv' not found, using environment variables only")


class GitHubMCPTester:
    """GitHub MCP Server Test Client"""

    def __init__(self):
        self.token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }

        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        else:
            print("⚠️  Warning: GITHUB_PERSONAL_ACCESS_TOKEN not found in environment")
            print("Some tests may fail without authentication")

    def print_header(self, text: str):
        """Print a formatted header"""
        print(f"\n{'=' * 70}")
        print(f"  {text}")
        print(f"{'=' * 70}\n")

    def print_success(self, text: str):
        """Print success message"""
        print(f"✅ {text}")

    def print_error(self, text: str):
        """Print error message"""
        print(f"❌ {text}")

    def print_info(self, text: str):
        """Print info message"""
        print(f"ℹ️  {text}")

    def test_authentication(self) -> bool:
        """Test 1: Verify authentication and get user info"""
        self.print_header("Test 1: Authentication & User Info")

        try:
            response = requests.get(f"{self.base_url}/user", headers=self.headers)

            if response.status_code == 200:
                user = response.json()
                self.print_success(f"Authenticated as: {user['login']}")
                self.print_info(f"Name: {user.get('name', 'N/A')}")
                self.print_info(f"Email: {user.get('email', 'N/A')}")
                self.print_info(f"Public Repos: {user.get('public_repos', 0)}")
                self.print_info(f"Followers: {user.get('followers', 0)}")
                self.print_info(f"Following: {user.get('following', 0)}")
                return True
            elif response.status_code == 401:
                self.print_error("Authentication failed - Invalid token")
                return False
            else:
                self.print_error(f"Unexpected status code: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Exception: {e!s}")
            return False

    def test_rate_limit(self) -> bool:
        """Test 2: Check API rate limit"""
        self.print_header("Test 2: API Rate Limit")

        try:
            response = requests.get(f"{self.base_url}/rate_limit", headers=self.headers)

            if response.status_code == 200:
                data = response.json()
                core = data["resources"]["core"]

                self.print_success("Rate limit information retrieved")
                self.print_info(f"Limit: {core['limit']} requests/hour")
                self.print_info(f"Used: {core['used']} requests")
                self.print_info(f"Remaining: {core['remaining']} requests")

                reset_time = datetime.fromtimestamp(core["reset"])
                self.print_info(f"Resets at: {reset_time.strftime('%Y-%m-%d %H:%M:%S')}")

                # Calculate percentage used
                if core["limit"] > 0:
                    percentage_used = (core["used"] / core["limit"]) * 100
                    self.print_info(f"Usage: {percentage_used:.1f}%")

                return True
            else:
                self.print_error(f"Failed to get rate limit: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Exception: {e!s}")
            return False

    def test_list_repositories(self, max_repos: int = 5) -> bool:
        """Test 3: List user repositories"""
        self.print_header("Test 3: List Repositories")

        try:
            params = {"per_page": max_repos, "sort": "updated"}
            response = requests.get(
                f"{self.base_url}/user/repos", headers=self.headers, params=params
            )

            if response.status_code == 200:
                repos = response.json()

                if repos:
                    self.print_success(
                        f"Found {len(repos)} repositories (showing up to {max_repos})"
                    )
                    for repo in repos:
                        print(f"\n📦 {repo['full_name']}")
                        print(f"   Description: {repo.get('description', 'N/A')}")
                        print(f"   Language: {repo.get('language', 'N/A')}")
                        print(f"   Stars: ⭐ {repo['stargazers_count']}")
                        print(f"   Forks: 🔱 {repo['forks_count']}")
                        print(f"   Private: {'🔒 Yes' if repo['private'] else '🌐 No'}")
                        print(f"   URL: {repo['html_url']}")
                else:
                    self.print_info("No repositories found")

                return True
            elif response.status_code == 401:
                self.print_error("Authentication required for this operation")
                return False
            else:
                self.print_error(f"Failed to list repositories: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Exception: {e!s}")
            return False

    def test_search_repositories(
        self, query: str = "language:python stars:>1000", max_results: int = 5
    ) -> bool:
        """Test 4: Search repositories"""
        self.print_header(f"Test 4: Search Repositories ('{query}')")

        try:
            params = {"q": query, "per_page": max_results, "sort": "stars"}
            response = requests.get(
                f"{self.base_url}/search/repositories", headers=self.headers, params=params
            )

            if response.status_code == 200:
                data = response.json()
                repos = data["items"]

                self.print_success(
                    f"Found {data['total_count']} repositories (showing {len(repos)})"
                )

                for i, repo in enumerate(repos, 1):
                    print(f"\n{i}. 📦 {repo['full_name']}")
                    print(f"   Description: {repo.get('description', 'N/A')[:80]}")
                    print(f"   Language: {repo.get('language', 'N/A')}")
                    print(f"   Stars: ⭐ {repo['stargazers_count']:,}")
                    print(f"   Forks: 🔱 {repo['forks_count']:,}")
                    print(f"   URL: {repo['html_url']}")

                return True
            else:
                self.print_error(f"Search failed: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Exception: {e!s}")
            return False

    def test_get_repository_info(self, owner: str, repo: str) -> bool:
        """Test 5: Get repository information"""
        self.print_header(f"Test 5: Repository Info ({owner}/{repo})")

        try:
            response = requests.get(f"{self.base_url}/repos/{owner}/{repo}", headers=self.headers)

            if response.status_code == 200:
                repo_data = response.json()

                self.print_success(f"Repository found: {repo_data['full_name']}")
                print("\n📋 Information:")
                print(f"   Description: {repo_data.get('description', 'N/A')}")
                print(f"   Language: {repo_data.get('language', 'N/A')}")
                print(f"   Created: {repo_data['created_at']}")
                print(f"   Updated: {repo_data['updated_at']}")
                print(f"   Default Branch: {repo_data['default_branch']}")
                print(f"   Stars: ⭐ {repo_data['stargazers_count']:,}")
                print(f"   Watchers: 👁️  {repo_data['watchers_count']:,}")
                print(f"   Forks: 🔱 {repo_data['forks_count']:,}")
                print(f"   Open Issues: 🐛 {repo_data['open_issues_count']:,}")
                print(f"   Size: {repo_data['size']:,} KB")
                print(f"   Private: {'🔒 Yes' if repo_data['private'] else '🌐 No'}")
                print(f"   URL: {repo_data['html_url']}")

                return True
            elif response.status_code == 404:
                self.print_error("Repository not found")
                return False
            else:
                self.print_error(f"Failed to get repository: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Exception: {e!s}")
            return False

    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "=" * 70)
        print("  🚀 GitHub MCP Server - Comprehensive Test Suite")
        print("  مجموعة اختبارات شاملة لخادم GitHub MCP")
        print("=" * 70)

        results = []

        # Test 1: Authentication
        results.append(("Authentication", self.test_authentication()))

        # Test 2: Rate Limit
        results.append(("Rate Limit", self.test_rate_limit()))

        # Test 3: List Repositories
        results.append(("List Repositories", self.test_list_repositories()))

        # Test 4: Search Repositories
        results.append(("Search Repositories", self.test_search_repositories()))

        # Test 5: Get Repository Info
        # Using github/github-mcp-server as an example
        results.append(
            ("Get Repository Info", self.test_get_repository_info("github", "github-mcp-server"))
        )

        # Summary
        self.print_header("📊 Test Summary")

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")

        print(f"\n{'=' * 70}")
        print(f"Results: {passed}/{total} tests passed ({(passed / total) * 100:.1f}%)")
        print(f"{'=' * 70}\n")

        if passed == total:
            print("🎉 All tests passed! GitHub MCP Server is working perfectly!")
            return True
        else:
            print("⚠️  Some tests failed. Check the errors above for details.")
            return False


def main():
    """Main function"""
    # Check for token
    token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")

    if not token:
        print("\n" + "=" * 70)
        print("  ⚠️  WARNING: GitHub Token Not Found")
        print("=" * 70)
        print("\nThe GITHUB_PERSONAL_ACCESS_TOKEN environment variable is not set.")
        print("\nTo run these tests, you need to:")
        print("  1. Get a token from: https://github.com/settings/tokens")
        print("  2. Add it to your .env file:")
        print('     GITHUB_PERSONAL_ACCESS_TOKEN="ghp_your_token_here"')
        print("\nSome tests will run with limited functionality.")
        print("\nPress Enter to continue with limited tests, or Ctrl+C to exit...")
        input()

    # Create tester instance
    tester = GitHubMCPTester()

    # Run all tests
    success = tester.run_all_tests()

    # Exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
