"""
Local Knowledge Base Retrieval (Fallback Mechanism).
Infrastructure Layer.
"""

from pathlib import Path

import yaml

from app.core.logging import get_logger
from app.services.chat.tools.retrieval import parsing

logger = get_logger("tool-retrieval-local")

# Directories to search for content
SEARCH_DIRECTORIES = [
    Path("knowledge_base"),
    Path("data/knowledge"),
    Path("content"),  # Recursive search might be needed here
]


def search_local_knowledge_base(
    query: str,
    year: str | None,
    subject: str | None,
    branch: str | None,
    exam_ref: str | None,
) -> str:
    """
    بحث احتياطي في الملفات المحلية في حال تعطل خدمة الذاكرة أو عدم وجود نتائج.
    """
    matches = []

    # Collect all MD files from all directories
    md_files = []
    for directory in SEARCH_DIRECTORIES:
        if not directory.exists():
            continue
        # Use rglob for recursive search (especially for 'content/')
        md_files.extend(directory.rglob("*.md"))

    if not md_files:
        return "قاعدة المعرفة المحلية غير موجودة أو فارغة."

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")

            # Extract frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter_raw = parts[1]
                    body = parts[2]

                    try:
                        metadata = yaml.safe_load(frontmatter_raw)
                        meta_dict = metadata.get("metadata", {})

                        # Handle flat metadata (some files might not have 'metadata' key nested)
                        if (
                            not meta_dict
                            and isinstance(metadata, dict)
                            and ("year" in metadata or "subject" in metadata)
                        ):
                            # Check if keys like 'year' are at root
                            meta_dict = metadata

                        # Flexible Matching Logic for Fallback

                        # 1. Check Year
                        if year and str(meta_dict.get("year", "")) != str(year):
                            continue

                        # 2. Check Subject
                        if subject:
                            file_subject = str(meta_dict.get("subject", "")).lower()
                            if (
                                subject.lower() not in file_subject
                                and file_subject not in subject.lower()
                            ):
                                continue

                        # 3. Check Branch
                        if branch:
                            file_branch = meta_dict.get("branch", "")
                            branch_query = branch.lower().replace("_", " ")

                            if isinstance(file_branch, list):
                                # Normalize file branches too
                                file_branches_norm = [
                                    str(b).lower().replace("_", " ") for b in file_branch
                                ]
                                if not any(
                                    b in branch_query or branch_query in b
                                    for b in file_branches_norm
                                ):
                                    continue
                            else:
                                file_branch_norm = str(file_branch).lower().replace("_", " ")
                                if (
                                    file_branch_norm not in branch_query
                                    and branch_query not in file_branch_norm
                                ):
                                    continue

                        # 4. Check Exam Ref
                        # Exam Ref might be 'set' in some files
                        if exam_ref:
                            file_ref = str(
                                meta_dict.get("exam_ref", "") or meta_dict.get("set", "")
                            ).lower()
                            if (
                                exam_ref.lower() not in file_ref
                                and file_ref not in exam_ref.lower()
                            ):
                                continue

                        # 5. Extract Specific Exercise if requested
                        extracted_exercise = parsing.extract_specific_exercise(body, query)

                        is_specific = parsing.is_specific_request(query)

                        if extracted_exercise:
                            matches.append(extracted_exercise)
                        elif not is_specific:
                            # Only append full body if request was NOT specific
                            matches.append(body.strip())

                    except yaml.YAMLError:
                        logger.error(f"Failed to parse YAML in {md_file}")
                        continue

            # Support files without frontmatter or with different format?
            # For now, we stick to frontmatter-based files as per original logic,
            # but 'content/' files often have frontmatter too.

        except Exception as e:
            logger.error(f"Error reading file {md_file}: {e}")
            continue

    if not matches:
        return "لم يتم العثور على محتوى مطابق في الملفات المحلية (وضع عدم الاتصال)."

    # Deduplicate matches
    unique_matches = parsing.deduplicate_contents(matches)

    return "\n\n".join(unique_matches[:3]).strip()
