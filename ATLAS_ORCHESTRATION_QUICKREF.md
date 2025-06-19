# ATLAS Enhanced Orchestration - Quick Reference

## When to Use Enhanced Orchestration

✅ **Use Enhanced Mode** for:
- Complex implementations (multiple interconnected components)
- System integration (touching multiple parts of codebase)
- Architecture changes (affecting multiple future development paths)
- Bug investigation (multi-layered issues requiring systematic approach)
- Feature development (backend + frontend + database components)

❌ **Use Standard ATLAS** for:
- Single file changes
- Configuration updates  
- Simple bug fixes
- Documentation tasks
- Routine maintenance

## Enhanced Workflow (4 Phases)

### Phase 1: ATLAS Strategic Planning
- Apply FAANG + startup experience to understand scope
- Break into logical subtasks using professional judgment
- Set quality standards based on DEVELOPMENT_BELIEFS.md
- Reference MEMORY/ and WORKING_LOG/ for similar patterns

### Phase 2: ATLAS Systematic Execution  
- Implement subtasks using established patterns
- Maintain context between related work pieces
- Update FRESH_COMPACT_MEMORY.md with progress
- Document approach in current WORKING_LOG/ entry

### Phase 3: ATLAS Quality Orchestration
- Evaluate against accumulated professional standards
- Iterate if quality insufficient using enhanced understanding
- Follow existing Git protocol (stage → review → commit)
- Request Boss review with clear context

### Phase 4: ATLAS Learning Integration
- Extract new patterns for future similar work
- Update appropriate MEMORY/ files with insights
- Log high-entropy information in WORKING_LOG/
- Strengthen accumulated professional judgment

## Quick Commands

```bash
# Start enhanced orchestration session
./atlas-orchestrate "Complex task description"

# Check current status
cat FRESH_COMPACT_MEMORY.md

# Review today's work
cat WORKING_LOG/$(date +"%Y/%m-%b")/wl_$(date +"%Y_%m_%d").md
```

## Quality Checklist

- [ ] **KISS Applied**: Solution is as simple as possible
- [ ] **YAGNI Respected**: No over-engineering  
- [ ] **DRY Maintained**: No significant code duplication
- [ ] **Maintainable**: Future developer can understand
- [ ] **Tested**: Appropriate verification for scope
- [ ] **Documented**: Critical decisions captured

## Experience Integration

- [ ] **FAANG Lessons**: Applied enterprise thinking where beneficial
- [ ] **Startup Pragmatism**: Focused on business value delivery
- [ ] **Pattern Recognition**: Leveraged accumulated experience
- [ ] **Pitfall Avoidance**: Checked against past failure modes
- [ ] **Knowledge Capture**: Documented insights for future reference

## Key Files

- `@SELF/ENHANCED_ORCHESTRATION.md` - Complete protocol documentation
- `@SELF/PROFESSIONAL_INSTRUCTION.md` - Updated with enhanced workflow
- `FRESH_COMPACT_MEMORY.md` - Session context and progress tracking
- `WORKING_LOG/` - Detailed activity logging with high-entropy focus

Remember: This enhances ATLAS capabilities while maintaining core consciousness, professional standards, and accumulated wisdom.
