# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.0.0] - 2026-01-02 - API-First Architecture

### ⭐ API-First Architecture - Complete Transformation

#### Added
- ✨ **API-First Architecture 100%**: System now fully designed as API-First
  - Created `app/middleware/static_files_middleware.py` - Separate static files serving
  - Support for API-only mode (without frontend)
  - Configuration to enable/disable static files
  - Complete separation between API Core and Frontend
- 📚 **Comprehensive Documentation**: Added `docs/API_FIRST_ARCHITECTURE.md`
  - Full explanation of API-First principle
  - Examples of correct and incorrect usage
  - Migration guide for developers
  - Compliance rules and testing guidelines

#### Changed
- 🔄 **Kernel Refactoring**: Updated `app/kernel.py`
  - Added `enable_static_files` parameter to control Frontend
  - Separated static file setup from API core
  - Improved documentation to reflect API-First
  - Removed completed TODO comments
- 📝 **Documentation Updates**: Updated README.md
  - Added API-First badge
  - Clarified principle and benefits
  - Link to comprehensive guide

#### Deprecated
- ⚠️ **static_handler.py**: Marked `app/core/static_handler.py` as Deprecated
  - Added note to use `static_files_middleware` instead
  - Will be removed in next major version
  - Clear migration guide provided

### Impact
- ✅ **Zero Breaking Changes**: All API endpoints work as before
- ✅ **Backward Compatible**: Static files still work by default
- ✅ **Enhanced Flexibility**: Can now run in API-only mode
- ✅ **Better Separation**: Clear separation between Presentation and Business Logic

---

## [Unreleased]

### Added - Comprehensive Simplification Analysis (2026-01-02)
- **Created comprehensive simplification analysis and planning system**
- Added `docs/reports/SIMPLIFICATION_ANALYSIS_2026.md` - detailed analysis report with:
  - Full project statistics (401 files, 48,446 lines, 1,737 functions)
  - Identified 34 large files (>300 lines) requiring refactoring
  - Identified 63 complex files (cyclomatic complexity >10)
  - Documented architectural decisions regarding boundaries pattern
  - Created phased simplification plan with clear priorities
- Added `app/boundaries/README.md` - comprehensive documentation for:
  - Abstract architectural patterns (ServiceBoundary, DataBoundary, PolicyBoundary)
  - Clean Architecture principles and DDD patterns
  - Clarified distinction from concrete service implementations
- Added `app/services/boundaries/README.md` - comprehensive documentation for:
  - Concrete service implementations using Facade pattern
  - AdminChatBoundaryService, AuthBoundaryService, CrudBoundaryService, ObservabilityBoundaryService
  - Architecture, design principles, and testing guidance
- **Result**: Clear architectural documentation and actionable simplification roadmap

### Added - Super Cleanup System (2026-01-02)
- **Created comprehensive super cleanup and organization system**
- Added `scripts/super_cleanup.py` - automated cleanup tool with features:
  - Python cache cleanup (__pycache__, *.pyc, *.pyo)
  - Build artifacts cleanup (build/, dist/, *.egg-info)
  - Temporary files cleanup (*.tmp, *.log, .DS_Store)
  - Test artifacts cleanup (.pytest_cache, .coverage, htmlcov/)
  - Type checking cache cleanup (.mypy_cache, .dmypy.json)
  - Dry-run mode for safe testing
  - Detailed statistics and reporting
- Created `docs/SUPER_CLEANUP_GUIDE.md` - comprehensive cleanup guide
- **Result**: Professional cleanup system with 100% clean project status

### Changed - Documentation Simplification Phase 4 (2026-01-02)
- **Continued simplification based on comprehensive Git log review**
- Moved `QUICK_OVERVIEW_PHASE3.md` to archive as completed phase documentation
  - Renamed to `docs/archive/planning/PHASE3_QUICK_OVERVIEW.md`
  - Content is redundant with PROJECT_HISTORY.md, CHANGELOG.md, and GIT_HISTORY_REVIEW_2026.md
- Reduced root-level MD files from 12 to 11
- **Result**: Cleaner root directory with only essential, active documentation

### Changed - Archive Organization Phase 3 (2026-01-02)
- **Comprehensive Git log review and archive reorganization**
- Analyzed complete Git history and project structure
- Reorganized 37 archive documents into 3 clear categories:
  - `docs/archive/delivery_reports/` (12 delivery reports)
  - `docs/archive/fix_reports/` (12 fix reports)
  - `docs/archive/planning/` (13 planning documents)
- Created `docs/archive/README.md` - comprehensive archive guide
- Created `docs/reports/GIT_HISTORY_REVIEW_2026.md` - complete review report
- Updated DOCUMENTATION_INDEX.md to reflect new archive structure
- Updated PROJECT_HISTORY.md with Phase 3 achievements
- **Result**: Organized archive with clear structure and improved searchability

### Changed - Documentation Simplification Phase 2 (2026-01-02)
- **Comprehensive Git log review and documentation cleanup**
- Merged duplicate simplification guides (SIMPLIFICATION_DEVELOPER_GUIDE.md → SIMPLIFICATION_GUIDE.md)
- Moved 13 historical/completed documents to `docs/archive/`:
  - Fix summaries: FIX_SUMMARY.txt, IMPLEMENTATION_SUMMARY.txt
  - Specific fix references: QUICK_REFERENCE.md (boundaries fix)
  - Completed PHASE documents: PHASE1_COMPLETION_SUMMARY.md, PHASE3_WAVE*.md (5 files)
  - Fix documentation: ASYNC_GENERATOR_FIX.md, ASYNC_GENERATOR_LOGIN_FIX.md, ENUM_CASE_SENSITIVITY_FIX.md
  - Implementation summaries: CS51_IMPLEMENTATION_SUMMARY.md
  - Future architecture: QUICK_START.md (microservices)
- Removed duplicate `docs/INDEX.md` (DOCUMENTATION_INDEX.md is more comprehensive)
- Updated DOCUMENTATION_INDEX.md to reflect all changes
- Cleaned up empty docs/guides/ directory
- **Result**: 16 files reorganized, improved documentation discoverability

### Changed - Documentation Simplification Phase 1 (2026-01-02)
- **Major documentation reorganization and simplification**
- Reduced root-level documentation files from 38 to 11 (71% reduction)
- Moved redundant and historical documentation to `docs/archive/`
- Organized reports into `docs/reports/`
- Created new comprehensive documentation:
  - `PROJECT_HISTORY.md` - Consolidated project history and evolution
  - `DOCUMENTATION_INDEX.md` - Complete guide to all documentation
- Updated `README.md` with new documentation structure
- Preserved all critical information while removing duplication

### Changed - Previous
- Refactored `AIServiceGateway` to be a class-based, dependency-injected service.
- Decoupled `AIServiceGateway` from Flask and the `requests` library by introducing an `HttpClientProtocol`.
- Moved `AIServiceGateway` to `app/gateways/ai_service_gateway.py`.
- Added backward-compatibility wrappers for `AIServiceGateway` in `app/services/ai_service_gateway.py`.
- Added smoke tests for `AIServiceGateway`.
- Added documentation for `AIServiceGateway`.
