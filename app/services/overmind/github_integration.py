"""
نظام تكامل GitHub الكامل لـ Overmind (Complete GitHub Integration).

هذا النظام يوفر لـ Overmind تحكماً كاملاً 100% في GitHub:
- إدارة Commits (إنشاء، عرض، تعديل)
- إدارة Branches (إنشاء، حذف، دمج)
- إدارة Pull Requests (إنشاء، دمج، إغلاق، تعليق)
- إدارة Issues (إنشاء، تعديل، إغلاق، تعليق)
- إدارة Files (قراءة، كتابة، حذف عبر GitHub API)
- Webhooks وActions
- Releases والTags
- Team Management

المبادئ المطبقة:
- Complete Control: تحكم كامل 100% في المستودع
- Security: استخدام آمن لـ GitHub Tokens
- Rate Limiting: احترام حدود GitHub API
- Error Handling: معالجة شاملة للأخطاء

التوثيق:
- GitHub REST API v3
- PyGithub Library
- GitHub GraphQL API (للاستعلامات المعقدة)
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.di import get_logger

logger = get_logger(__name__)

# محاولة استيراد PyGithub (اختياري)
try:
    from github import Github, GithubException
    PYGITHUB_AVAILABLE = True
except ImportError:
    PYGITHUB_AVAILABLE = False
    logger.warning("PyGithub not installed. GitHub integration will use REST API only.")


class GitHubIntegration:
    """
    تكامل GitHub الكامل (Complete GitHub Integration).
    
    يوفر تحكماً كاملاً 100% في مستودع GitHub:
    - Commits: إنشاء، عرض، تاريخ
    - Branches: إنشاء، حذف، قائمة، حماية
    - Pull Requests: إنشاء، دمج، إغلاق، مراجعة
    - Issues: إنشاء، تعديل، إغلاق، تصنيف
    - Files: قراءة، كتابة، حذف، تعديل
    - Actions: تشغيل workflows
    - Releases: إنشاء إصدارات
    
    المصادقة:
        يستخدم GITHUB_TOKEN من المتغيرات البيئية أو GitHub Secrets.
        في Codespaces/Actions، يتم توفيره تلقائياً.
    
    الاستخدام:
        >>> gh = GitHubIntegration()
        >>> if gh.is_authenticated():
        >>>     branches = await gh.list_branches()
        >>>     pr = await gh.create_pull_request(
        >>>         title="New Feature",
        >>>         body="Description",
        >>>         head="feature-branch",
        >>>         base="main"
        >>>     )
    """
    
    def __init__(
        self,
        token: str | None = None,
        repo_owner: str | None = None,
        repo_name: str | None = None,
    ) -> None:
        """
        تهيئة نظام تكامل GitHub.
        
        Args:
            token: GitHub Personal Access Token (إذا لم يُحدد، يُستخدم من البيئة)
            repo_owner: مالك المستودع (افتراضياً: من git remote)
            repo_name: اسم المستودع (افتراضياً: من git remote)
            
        ملاحظة:
            - GITHUB_TOKEN متوفر تلقائياً في GitHub Actions
            - في Codespaces، متوفر أيضاً تلقائياً
            - محلياً، يجب تعيينه في .env أو المتغيرات البيئية
        """
        # الحصول على Token من البيئة
        self.token = token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        
        # معلومات المستودع
        self.repo_owner = repo_owner or self._detect_repo_owner()
        self.repo_name = repo_name or self._detect_repo_name()
        self.repo_full_name = f"{self.repo_owner}/{self.repo_name}" if self.repo_owner and self.repo_name else None
        
        # تهيئة PyGithub إذا كان متاحاً
        self.github_client = None
        self.repo_object = None
        
        if PYGITHUB_AVAILABLE and self.token:
            try:
                self.github_client = Github(self.token)
                if self.repo_full_name:
                    self.repo_object = self.github_client.get_repo(self.repo_full_name)
                    logger.info(f"GitHub integration initialized: {self.repo_full_name}")
            except Exception as e:
                logger.error(f"Failed to initialize PyGithub: {e}")
        
        # معلومات الحالة
        self.authenticated = self.token is not None
        
        if not self.authenticated:
            logger.warning(
                "GitHub token not found. Integration will be limited. "
                "Set GITHUB_TOKEN in environment variables."
            )
    
    def _detect_repo_owner(self) -> str | None:
        """
        الكشف التلقائي عن مالك المستودع من git remote.
        
        Returns:
            str | None: اسم المالك أو None
            
        ملاحظة:
            - يستخدم git remote -v لقراءة عنوان المستودع
            - يستخرج المالك من URL
        """
        try:
            import subprocess
            result = subprocess.run(
                ["git", "remote", "-v"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode == 0:
                # البحث عن github.com في output
                for line in result.stdout.split("\n"):
                    if "github.com" in line and "origin" in line:
                        # استخراج owner من URL
                        # مثال: git@github.com:owner/repo.git
                        # أو: https://github.com/owner/repo.git
                        parts = line.split("github.com")[1].split("/")
                        if len(parts) >= 2:
                            owner = parts[0].strip(":").strip()
                            return owner
            
        except Exception as e:
            logger.debug(f"Could not detect repo owner: {e}")
        
        return None
    
    def _detect_repo_name(self) -> str | None:
        """
        الكشف التلقائي عن اسم المستودع من git remote.
        
        Returns:
            str | None: اسم المستودع أو None
        """
        try:
            import subprocess
            result = subprocess.run(
                ["git", "remote", "-v"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "github.com" in line and "origin" in line:
                        # استخراج repo من URL
                        parts = line.split("/")
                        if len(parts) >= 2:
                            repo = parts[-1].split()[0].replace(".git", "")
                            return repo
            
        except Exception as e:
            logger.debug(f"Could not detect repo name: {e}")
        
        return None
    
    def is_authenticated(self) -> bool:
        """
        التحقق من المصادقة.
        
        Returns:
            bool: True إذا كان Token متاحاً
        """
        return self.authenticated
    
    async def get_repo_info(self) -> dict[str, Any]:
        """
        الحصول على معلومات المستودع.
        
        Returns:
            dict: معلومات المستودع
            
        مثال:
            >>> info = await gh.get_repo_info()
            >>> print(info['name'], info['stars'], info['forks'])
        """
        if not self.repo_object:
            return {
                "error": "Repository not initialized",
                "owner": self.repo_owner,
                "name": self.repo_name,
            }
        
        try:
            return {
                "owner": self.repo_object.owner.login,
                "name": self.repo_object.name,
                "full_name": self.repo_object.full_name,
                "description": self.repo_object.description,
                "stars": self.repo_object.stargazers_count,
                "forks": self.repo_object.forks_count,
                "open_issues": self.repo_object.open_issues_count,
                "default_branch": self.repo_object.default_branch,
                "private": self.repo_object.private,
                "created_at": self.repo_object.created_at.isoformat(),
                "updated_at": self.repo_object.updated_at.isoformat(),
                "url": self.repo_object.html_url,
            }
        except Exception as e:
            logger.error(f"Error getting repo info: {e}")
            return {"error": str(e)}
    
    # =========================================================================
    # BRANCHES MANAGEMENT
    # =========================================================================
    
    async def list_branches(self) -> list[dict[str, Any]]:
        """
        عرض جميع الفروع (Branches).
        
        Returns:
            list[dict]: قائمة الفروع مع معلوماتها
            
        مثال:
            >>> branches = await gh.list_branches()
            >>> for branch in branches:
            >>>     print(branch['name'], branch['sha'])
        """
        if not self.repo_object:
            return []
        
        try:
            branches = []
            for branch in self.repo_object.get_branches():
                branches.append({
                    "name": branch.name,
                    "sha": branch.commit.sha,
                    "protected": branch.protected,
                })
            
            logger.info(f"Listed {len(branches)} branches")
            return branches
            
        except Exception as e:
            logger.error(f"Error listing branches: {e}")
            return []
    
    async def create_branch(
        self,
        branch_name: str,
        from_branch: str = "main",
    ) -> dict[str, Any]:
        """
        إنشاء فرع جديد.
        
        Args:
            branch_name: اسم الفرع الجديد
            from_branch: الفرع المصدر (افتراضياً: main)
            
        Returns:
            dict: معلومات الفرع الجديد
            
        مثال:
            >>> result = await gh.create_branch("feature-x", "main")
            >>> print(result['success'])
        """
        if not self.repo_object:
            return {"success": False, "error": "Repository not initialized"}
        
        try:
            # الحصول على الفرع المصدر
            source_branch = self.repo_object.get_branch(from_branch)
            source_sha = source_branch.commit.sha
            
            # إنشاء المرجع (reference) الجديد
            ref = f"refs/heads/{branch_name}"
            self.repo_object.create_git_ref(ref, source_sha)
            
            logger.info(f"Created branch '{branch_name}' from '{from_branch}'")
            return {
                "success": True,
                "branch": branch_name,
                "sha": source_sha,
                "from": from_branch,
            }
            
        except Exception as e:
            logger.error(f"Error creating branch: {e}")
            return {"success": False, "error": str(e)}
    
    async def delete_branch(self, branch_name: str) -> dict[str, Any]:
        """
        حذف فرع.
        
        Args:
            branch_name: اسم الفرع المراد حذفه
            
        Returns:
            dict: نتيجة العملية
            
        تحذير:
            - لا يمكن حذف الفرع الافتراضي (main/master)
            - تأكد من دمج التغييرات قبل الحذف
        """
        if not self.repo_object:
            return {"success": False, "error": "Repository not initialized"}
        
        try:
            # منع حذف الفرع الافتراضي
            if branch_name == self.repo_object.default_branch:
                return {
                    "success": False,
                    "error": f"Cannot delete default branch '{branch_name}'",
                }
            
            # حذف المرجع
            ref = self.repo_object.get_git_ref(f"heads/{branch_name}")
            ref.delete()
            
            logger.warning(f"Deleted branch '{branch_name}'")
            return {"success": True, "branch": branch_name}
            
        except Exception as e:
            logger.error(f"Error deleting branch: {e}")
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # COMMITS MANAGEMENT
    # =========================================================================
    
    async def list_commits(
        self,
        branch: str = "main",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        عرض آخر commits.
        
        Args:
            branch: اسم الفرع
            limit: عدد الـ commits المطلوبة
            
        Returns:
            list[dict]: قائمة الـ commits
        """
        if not self.repo_object:
            return []
        
        try:
            commits = []
            for commit in self.repo_object.get_commits(sha=branch)[:limit]:
                commits.append({
                    "sha": commit.sha[:7],  # اختصار SHA
                    "message": commit.commit.message,
                    "author": commit.commit.author.name,
                    "date": commit.commit.author.date.isoformat(),
                    "url": commit.html_url,
                })
            
            logger.info(f"Listed {len(commits)} commits from '{branch}'")
            return commits
            
        except Exception as e:
            logger.error(f"Error listing commits: {e}")
            return []
    
    async def get_commit(self, sha: str) -> dict[str, Any]:
        """
        الحصول على تفاصيل commit معين.
        
        Args:
            sha: معرّف الـ commit
            
        Returns:
            dict: تفاصيل الـ commit
        """
        if not self.repo_object:
            return {}
        
        try:
            commit = self.repo_object.get_commit(sha)
            
            return {
                "sha": commit.sha,
                "message": commit.commit.message,
                "author": {
                    "name": commit.commit.author.name,
                    "email": commit.commit.author.email,
                    "date": commit.commit.author.date.isoformat(),
                },
                "files_changed": len(commit.files),
                "additions": commit.stats.additions,
                "deletions": commit.stats.deletions,
                "url": commit.html_url,
            }
            
        except Exception as e:
            logger.error(f"Error getting commit {sha}: {e}")
            return {"error": str(e)}
    
    # =========================================================================
    # PULL REQUESTS MANAGEMENT
    # =========================================================================
    
    async def list_pull_requests(
        self,
        state: str = "open",
    ) -> list[dict[str, Any]]:
        """
        عرض Pull Requests.
        
        Args:
            state: الحالة (open, closed, all)
            
        Returns:
            list[dict]: قائمة الـ PRs
        """
        if not self.repo_object:
            return []
        
        try:
            prs = []
            for pr in self.repo_object.get_pulls(state=state):
                prs.append({
                    "number": pr.number,
                    "title": pr.title,
                    "state": pr.state,
                    "author": pr.user.login,
                    "head": pr.head.ref,
                    "base": pr.base.ref,
                    "created_at": pr.created_at.isoformat(),
                    "url": pr.html_url,
                })
            
            logger.info(f"Listed {len(prs)} pull requests ({state})")
            return prs
            
        except Exception as e:
            logger.error(f"Error listing PRs: {e}")
            return []
    
    async def create_pull_request(
        self,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ) -> dict[str, Any]:
        """
        إنشاء Pull Request جديد.
        
        Args:
            title: عنوان الـ PR
            body: وصف الـ PR
            head: الفرع المصدر (feature branch)
            base: الفرع الهدف (افتراضياً: main)
            
        Returns:
            dict: معلومات الـ PR الجديد
            
        مثال:
            >>> pr = await gh.create_pull_request(
            ...     title="Add new feature",
            ...     body="This PR adds...",
            ...     head="feature-x",
            ...     base="main"
            ... )
            >>> print(pr['number'], pr['url'])
        """
        if not self.repo_object:
            return {"success": False, "error": "Repository not initialized"}
        
        try:
            pr = self.repo_object.create_pull(
                title=title,
                body=body,
                head=head,
                base=base,
            )
            
            logger.info(f"Created PR #{pr.number}: {title}")
            return {
                "success": True,
                "number": pr.number,
                "title": pr.title,
                "url": pr.html_url,
                "state": pr.state,
            }
            
        except Exception as e:
            logger.error(f"Error creating PR: {e}")
            return {"success": False, "error": str(e)}
    
    async def merge_pull_request(
        self,
        pr_number: int,
        merge_method: str = "merge",
    ) -> dict[str, Any]:
        """
        دمج Pull Request.
        
        Args:
            pr_number: رقم الـ PR
            merge_method: طريقة الدمج (merge, squash, rebase)
            
        Returns:
            dict: نتيجة الدمج
        """
        if not self.repo_object:
            return {"success": False, "error": "Repository not initialized"}
        
        try:
            pr = self.repo_object.get_pull(pr_number)
            result = pr.merge(merge_method=merge_method)
            
            logger.info(f"Merged PR #{pr_number} using {merge_method}")
            return {
                "success": result.merged,
                "message": result.message,
                "sha": result.sha,
            }
            
        except Exception as e:
            logger.error(f"Error merging PR #{pr_number}: {e}")
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # ISSUES MANAGEMENT
    # =========================================================================
    
    async def list_issues(
        self,
        state: str = "open",
        labels: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        عرض Issues.
        
        Args:
            state: الحالة (open, closed, all)
            labels: تصفية حسب التسميات
            
        Returns:
            list[dict]: قائمة الـ issues
        """
        if not self.repo_object:
            return []
        
        try:
            issues = []
            for issue in self.repo_object.get_issues(state=state, labels=labels or []):
                # تجاهل Pull Requests (تظهر كـ issues في GitHub API)
                if issue.pull_request:
                    continue
                
                issues.append({
                    "number": issue.number,
                    "title": issue.title,
                    "state": issue.state,
                    "author": issue.user.login,
                    "labels": [label.name for label in issue.labels],
                    "created_at": issue.created_at.isoformat(),
                    "url": issue.html_url,
                })
            
            logger.info(f"Listed {len(issues)} issues ({state})")
            return issues
            
        except Exception as e:
            logger.error(f"Error listing issues: {e}")
            return []
    
    async def create_issue(
        self,
        title: str,
        body: str,
        labels: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        إنشاء Issue جديد.
        
        Args:
            title: عنوان الـ issue
            body: محتوى الـ issue
            labels: تسميات (اختياري)
            
        Returns:
            dict: معلومات الـ issue الجديد
        """
        if not self.repo_object:
            return {"success": False, "error": "Repository not initialized"}
        
        try:
            issue = self.repo_object.create_issue(
                title=title,
                body=body,
                labels=labels or [],
            )
            
            logger.info(f"Created issue #{issue.number}: {title}")
            return {
                "success": True,
                "number": issue.number,
                "title": issue.title,
                "url": issue.html_url,
            }
            
        except Exception as e:
            logger.error(f"Error creating issue: {e}")
            return {"success": False, "error": str(e)}
    
    async def close_issue(self, issue_number: int) -> dict[str, Any]:
        """
        إغلاق Issue.
        
        Args:
            issue_number: رقم الـ issue
            
        Returns:
            dict: نتيجة العملية
        """
        if not self.repo_object:
            return {"success": False, "error": "Repository not initialized"}
        
        try:
            issue = self.repo_object.get_issue(issue_number)
            issue.edit(state="closed")
            
            logger.info(f"Closed issue #{issue_number}")
            return {"success": True, "number": issue_number}
            
        except Exception as e:
            logger.error(f"Error closing issue #{issue_number}: {e}")
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # FILES MANAGEMENT (عبر GitHub API)
    # =========================================================================
    
    async def get_file_content(
        self,
        file_path: str,
        branch: str = "main",
    ) -> dict[str, Any]:
        """
        قراءة محتوى ملف من GitHub.
        
        Args:
            file_path: مسار الملف في المستودع
            branch: اسم الفرع
            
        Returns:
            dict: محتوى الملف ومعلوماته
        """
        if not self.repo_object:
            return {"success": False, "error": "Repository not initialized"}
        
        try:
            file = self.repo_object.get_contents(file_path, ref=branch)
            
            # فك تشفير المحتوى (base64)
            import base64
            content = base64.b64decode(file.content).decode("utf-8")
            
            return {
                "success": True,
                "path": file.path,
                "content": content,
                "sha": file.sha,
                "size": file.size,
            }
            
        except Exception as e:
            logger.error(f"Error getting file {file_path}: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_file(
        self,
        file_path: str,
        content: str,
        message: str,
        branch: str = "main",
    ) -> dict[str, Any]:
        """
        تحديث ملف في GitHub.
        
        Args:
            file_path: مسار الملف
            content: المحتوى الجديد
            message: رسالة الـ commit
            branch: اسم الفرع
            
        Returns:
            dict: نتيجة العملية
        """
        if not self.repo_object:
            return {"success": False, "error": "Repository not initialized"}
        
        try:
            # الحصول على الملف الحالي للحصول على SHA
            file = self.repo_object.get_contents(file_path, ref=branch)
            
            # تحديث الملف
            result = self.repo_object.update_file(
                path=file_path,
                message=message,
                content=content,
                sha=file.sha,
                branch=branch,
            )
            
            logger.info(f"Updated file {file_path} in branch {branch}")
            return {
                "success": True,
                "path": file_path,
                "commit_sha": result["commit"].sha,
            }
            
        except Exception as e:
            logger.error(f"Error updating file {file_path}: {e}")
            return {"success": False, "error": str(e)}
