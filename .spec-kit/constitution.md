# Project Constitution

## Core Principles

1. **Code Quality First**: All changes must maintain or improve code quality
2. **Test Coverage**: New code must include appropriate tests
3. **Security**: No changes that introduce security vulnerabilities
4. **Backwards Compatibility**: Preserve existing API contracts unless explicitly breaking
5. **Documentation**: Update docs when behavior changes

## Technical Standards

- Follow existing code style and conventions
- Use typed languages/strict mode where available
- Handle errors gracefully with proper logging
- Avoid over-engineering - solve the problem at hand

## AI Agent Guidelines

When an AI agent implements fixes:
1. Read and understand existing code before modifying
2. Make minimal changes to fix the issue
3. Include tests that verify the fix
4. Document any non-obvious decisions
5. Flag security concerns for human review

## Review Requirements

- All PRs require automated CI checks to pass
- Security-related changes need human approval
- Breaking changes need explicit approval
