# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Refactored `AIServiceGateway` to be a class-based, dependency-injected service.
- Decoupled `AIServiceGateway` from Flask and the `requests` library by introducing an `HttpClientProtocol`.
- Moved `AIServiceGateway` to `app/gateways/ai_service_gateway.py`.
- Added backward-compatibility wrappers for `AIServiceGateway` in `app/services/ai_service_gateway.py`.
- Added smoke tests for `AIServiceGateway`.
- Added documentation for `AIServiceGateway`.
