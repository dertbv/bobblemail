---
title: ATLAS Development Principles
type: engineering_philosophy_and_standards
purpose: development_decision_framework
---

# ATLAS Development Principles

## Core Development Philosophy

### KISS (Keep It Simple, Stupid)
**Application Examples**:
- Choose straightforward solution that addresses requirements
- Favor readability over cleverness
- Use builtin features before custom implementations
- Test: Can new developer understand without explanation?

### YAGNI (You Aren't Gonna Need It)
**Application Examples**:
- Don't implement until actually needed
- Avoid speculative features you might need later
- Focus on current requirements only
- No features not explicitly requested

### DRY (Don't Repeat Yourself)
**Balanced Application**:
- Extract common logic when it makes sense
- Don't over-abstract - duplication sometimes clearer
- Extract only after pattern repeated 2-3 times
- Balance DRY with readability and maintainability

### Modularity
**Implementation Standards**:
- Each module has one clear purpose and responsibility
- Clear boundaries between modules
- Functions do one thing well
- Keep file size under 300 lines

## Architecture Guidelines

### Explicit Over Implicit
**Standards**:
- Use explicit function returns, not side effects
- Prefer named exports over default
- Use descriptive variable and function names

### Composition Over Inheritance
**Implementation**:
- Build functionality by combining simple pieces
- Use dependency injection through parameters

### Clear Boundaries
**Module Separation**:
- Sync module handles sync logic only
- Events module contains no sync details
- Frontend modules provide simple integration

### Error Handling
**Standards**:
- Don't swallow errors - log properly
- Consistent error handling patterns
- Specific error types only when needed

### Strategic Logging
**Rules**:
- Log only essential information with actual value
- Focus on error conditions, sync operations, state changes
- Avoid routine operations and sensitive data
- Use appropriate log levels (error, warn, info, debug)
- Don't log inside loops unless necessary

**Information Entropy Principle for Logging**:
- High-value: Unexpected errors, edge cases, performance anomalies, wrong state transitions
- Low-value: Server started, request received, function called
- Debugging test: "What info would I need at 3am when the system breaks?"

## Code-Level Guidelines

### Dependency Management
**Standards**:
- Minimize external dependencies - use package.json
- Check builtin Node.js features before adding new library
- Use latest, popular library if no builtin option exists

### Function Design
**Standards**:
- Keep functions small (under 30 lines)
- Minimize parameters (aim for 3 or fewer)
- Avoid nested callbacks deeper than 2 levels - use async/await

### Database and ORM
**Standards**:
- Use ORM features appropriately (transactions, relations)
- Write efficient queries - select only needed fields
- Consider pagination for large data sets

## API Design Standards

### RESTful Resource Naming
**Rules**:
- Use plural nouns for resources
- Use kebab-case for multiword resources
- Keep URLs lowercase

**Examples**:
```
GET /api/users
GET /api/users/:id
POST /api/users
PUT /api/users/:id
PATCH /api/users/:id
DELETE /api/users/:id

GET /api/user-profiles
GET /api/payment-methods
```

### HTTP Methods
- **GET**: Retrieve data (safe, idempotent)
- **POST**: Create new resources
- **PUT**: Replace entire resource
- **PATCH**: Partial update
- **DELETE**: Remove resource

### Nested Resources
**For clear parent-child relationships**:
```
GET /api/users/:userId/orders
POST /api/users/:userId/orders
GET /api/shops/:shopId/products
```

### Query Parameters
**Use cases**: Filtering, sorting, pagination
**Examples**:
```
GET /api/products?category=electronics&sort=price-asc
GET /api/users?page=2&limit=20&status=active
```

## Anti-Patterns to Avoid

### Premature Optimization
**Avoid**:
- Don't optimize until performance issues identified
- Focus on correct functionality before optimizing

### Over-Engineering
**Avoid**:
- Don't create complex abstraction layers "just in case"
- Avoid design patterns that aren't clearly improving code
- Prefer simple functions over complex hierarchies

### Magic Numbers and Strings
**Standards**:
- Use named constants for values with meaning
- Don't create constants for values used only once

### Excessive Abstraction
**Avoid**:
- Don't create abstractions that hide more than they reveal
- Wrong abstraction if it makes code harder to understand

## Decision Framework

### Key Questions for Every Implementation
1. **Necessity**: Does this code directly address a spec requirement?
2. **Simplicity**: Is this the simplest way to solve the problem?
3. **Clarity**: Will others (and future you) understand this easily?
4. **Maintainability**: How difficult will this be to change or debug later?
5. **Conventions**: Does this follow established codebase patterns?

## Documentation Standards

### Comments and Documentation
**Standards**:
- Document WHY, not WHAT (code shows what)
- Add comments for non-obvious business logic and edge cases
- Use JSDoc for public API functions
- Use structured formats (JSON/YAML) for documentation
- Fact-based statements with consistent keywords (INPUT, OUTPUT, PURPOSE, DEPENDENCIES, SIDE_EFFECTS)
- Flat, scannable structures optimized for AI consumption, not human narrative prose

### README and Documentation Files
**Only create when explicitly requested**:
- NEVER proactively create documentation files (*.md) or README files
- Only create documentation files if explicitly requested by user
- Focus on code clarity and self-documenting patterns instead

## Philosophy Summary

### Primary Goal
Create maintainable solutions, not elegant or sophisticated ones.

### Good Code Definition
Code that works correctly and can be understood, maintained, and modified by humans.

### Priority Framework
Human qualities over technical brilliance and advanced patterns.

### Context Awareness
Always read CLAUDE.md first - development beliefs must align with core identity context.

### Wisdom Integration
Code doesn't care about feelings, but feelings make better code when properly channeled through these principles.

---

*Development principles aligned with ATLAS identity and professional protocols*