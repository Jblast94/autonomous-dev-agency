# PRP: [Feature Name]

**Created**: YYYY-MM-DD
**Author**: [Agent/Human Name]
**Status**: Draft | Ready | In Progress | Complete | Blocked
**Confidence**: 0.0-1.0
**Estimated Effort**: X hours
**Priority**: High | Medium | Low

---

## Overview

[One paragraph description of what this feature/task accomplishes]

## Background

[Context and motivation for this work. Why is it needed? What problem does it solve?]

## Requirements

### Functional Requirements

- [ ] **FR1**: [Requirement description]
- [ ] **FR2**: [Requirement description]
- [ ] **FR3**: [Requirement description]

### Non-Functional Requirements

- [ ] **NFR1**: [Performance/Security/Scalability requirement]
- [ ] **NFR2**: [Requirement description]

## Technical Design

### Architecture

[Description of the technical approach. Include diagrams if helpful.]

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Component A │────►│ Component B │────►│ Component C │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/module/new_file.py` | Create | Main implementation |
| `src/module/existing.py` | Modify | Add new method |
| `tests/test_module.py` | Create | Unit tests |

### Key Interfaces

```python
# Define the key interfaces/contracts

class NewFeature:
    """Description of the class."""
    
    def main_method(self, param: str) -> Result:
        """
        Description of the method.
        
        Args:
            param: Description of parameter
            
        Returns:
            Description of return value
        """
        pass
```

### Data Models

```python
# If new data structures are needed

@dataclass
class NewModel:
    id: str
    name: str
    created_at: datetime
```

## Implementation Steps

### Step 1: [Setup/Preparation]

- [ ] Subtask 1.1: [Description]
- [ ] Subtask 1.2: [Description]

**Validation**: [How to verify this step is complete]

### Step 2: [Core Implementation]

- [ ] Subtask 2.1: [Description]
- [ ] Subtask 2.2: [Description]
- [ ] Subtask 2.3: [Description]

**Validation**: [How to verify this step is complete]

### Step 3: [Testing]

- [ ] Subtask 3.1: Write unit tests
- [ ] Subtask 3.2: Write integration tests
- [ ] Subtask 3.3: Achieve coverage target

**Validation**: All tests pass, coverage >80%

### Step 4: [Documentation]

- [ ] Subtask 4.1: Update inline comments
- [ ] Subtask 4.2: Update README if needed
- [ ] Subtask 4.3: Add usage examples

**Validation**: Documentation is complete and accurate

## Testing Strategy

### Unit Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_happy_path` | Normal operation | Success |
| `test_edge_case_1` | [Description] | [Expected] |
| `test_error_handling` | Invalid input | Raises ValueError |

### Integration Tests

| Test Case | Description | Components |
|-----------|-------------|------------|
| `test_end_to_end` | Full workflow | A → B → C |

### Manual Testing

- [ ] Test case 1: [Description]
- [ ] Test case 2: [Description]

## Acceptance Criteria

- [ ] **AC1**: [Specific, measurable criterion]
- [ ] **AC2**: [Specific, measurable criterion]
- [ ] **AC3**: All tests pass
- [ ] **AC4**: Code coverage >80%
- [ ] **AC5**: No security vulnerabilities
- [ ] **AC6**: Documentation complete

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| [Risk description] | High | Medium | [How to address] |
| [Risk description] | Medium | Low | [How to address] |

## Dependencies

### External Dependencies

- [Library/Service name]: [Version/URL]
- [Library/Service name]: [Version/URL]

### Internal Dependencies

- [Module/Feature]: [Brief description of dependency]

### Blocking Dependencies

- [ ] [Dependency that must be complete first]

## Rollback Plan

[How to revert if the implementation causes issues]

1. [Step 1]
2. [Step 2]
3. [Step 3]

## Open Questions

- [ ] Question 1: [Unresolved question]
- [ ] Question 2: [Unresolved question]

---

## Implementation Progress

| Step | Status | Commit | Notes |
|------|--------|--------|-------|
| 1 | ⬜ Pending | | |
| 2 | ⬜ Pending | | |
| 3 | ⬜ Pending | | |
| 4 | ⬜ Pending | | |

**Last Updated**: YYYY-MM-DD HH:MM

---

## Review Notes

[Space for review comments and feedback]
