# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
