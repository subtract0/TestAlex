# Agent Orchestration Protocol

This document defines the protocol for orchestrating multiple AI agents in a software development workflow, ensuring consistent task execution, proper role assignment, and conflict resolution.

## 1. Task Intake JSON Schema

All tasks entering the system must conform to this JSON schema:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "Task Intake Schema",
  "required": ["title", "description", "priority"],
  "properties": {
    "title": {
      "type": "string",
      "description": "Brief, descriptive title of the task",
      "minLength": 5,
      "maxLength": 100
    },
    "description": {
      "type": "string",
      "description": "Detailed description of what needs to be accomplished",
      "minLength": 20,
      "maxLength": 2000
    },
    "priority": {
      "type": "string",
      "enum": ["critical", "high", "medium", "low"],
      "description": "Task priority level affecting execution order"
    },
    "assignee": {
      "type": "string",
      "description": "Optional specific agent role to assign (overrides automatic selection)",
      "enum": ["software_engineer", "qa_tester", "devops_engineer", "product_owner"]
    },
    "dependencies": {
      "type": "array",
      "description": "List of task IDs that must be completed before this task",
      "items": {
        "type": "string"
      }
    },
    "tags": {
      "type": "array",
      "description": "Categorization tags for filtering and organization",
      "items": {
        "type": "string"
      }
    },
    "estimated_effort": {
      "type": "string",
      "enum": ["small", "medium", "large", "extra-large"],
      "description": "Rough estimate of task complexity"
    }
  }
}
```

### Example Task:
```json
{
  "title": "Build quick-action feature for dashboard",
  "description": "Implement a quick-action dropdown menu that allows users to perform common actions (create project, invite user, export data) directly from the main dashboard without navigation",
  "priority": "high",
  "tags": ["frontend", "ui", "dashboard"],
  "estimated_effort": "medium"
}
```

## 2. Agent Selection Rules

The orchestration system automatically assigns tasks to appropriate agent roles based on content analysis and explicit rules:

### Primary Role Templates:

#### Software Engineer (`software_engineer`)
- **Triggers**: Keywords like "implement", "develop", "build", "code", "API", "database"
- **Responsibilities**: Core development, architecture decisions, code implementation
- **Exclusions**: Testing-specific tasks, deployment tasks

#### QA Tester (`qa_tester`)  
- **Triggers**: Keywords like "test", "validate", "verify", "bug", "quality", "review"
- **Responsibilities**: Code review, test case creation, quality validation
- **Exclusions**: Initial development, infrastructure tasks

#### DevOps Engineer (`devops_engineer`)
- **Triggers**: Keywords like "deploy", "infrastructure", "CI/CD", "docker", "kubernetes", "monitoring"
- **Responsibilities**: Deployment, infrastructure, monitoring, automation
- **Exclusions**: Feature development, UI tasks

#### Product Owner (`product_owner`)
- **Triggers**: Keywords like "requirements", "specification", "user story", "acceptance criteria"
- **Responsibilities**: Requirements clarification, acceptance criteria, stakeholder communication
- **Exclusions**: Technical implementation, testing execution

### Selection Algorithm:
1. Check for explicit `assignee` in task JSON
2. If no assignee, analyze task description for trigger keywords
3. Apply priority weighting (higher priority = more specific role matching)
4. Default to `software_engineer` for ambiguous cases
5. Validate assignment doesn't violate exclusion rules

## 3. Iteration Loop Protocol

Every task follows this standardized iteration loop:

### Phase 1: Plan
- **Agent**: Primary assignee (e.g., `software_engineer`)
- **Deliverable**: Detailed implementation plan
- **Requirements**:
  - Break down task into subtasks
  - Identify technical requirements and dependencies  
  - Define acceptance criteria
  - Estimate timeline and resource needs
  - Flag potential risks or blockers

### Phase 2: Code/Execute
- **Agent**: Primary assignee
- **Deliverable**: Implementation artifacts (code, configs, docs)
- **Requirements**:
  - Follow established coding standards
  - Include inline documentation
  - Implement error handling
  - Create unit tests where applicable
  - Update relevant documentation

### Phase 3: Self-Review (QA Tester)
- **Agent**: `qa_tester` (automatic assignment)
- **Deliverable**: Quality assessment report
- **Requirements**:
  - Code quality review against standards
  - Test coverage validation
  - Security vulnerability scanning
  - Performance impact assessment
  - Documentation completeness check

### Phase 4: ACIM Vetting
- **Agent**: ACIM (Architecture, Compliance, Integration, Maintainability) specialist
- **Deliverable**: Architecture compliance report
- **Requirements**:
  - Architectural pattern compliance
  - Integration impact analysis
  - Maintainability assessment
  - Compliance with organizational standards
  - Long-term sustainability review

### Phase 5: Merge Request
- **Agent**: `devops_engineer` or designated reviewer
- **Deliverable**: Approved merge request
- **Requirements**:
  - Final integration testing
  - Deployment readiness check
  - Rollback plan preparation
  - Change documentation
  - Stakeholder notification

### Loop Controls:
- **Failure at any phase**: Return to previous phase with feedback
- **Maximum iterations**: 3 per phase before escalation
- **Emergency bypass**: Critical priority tasks can skip non-essential phases with approval

## 4. Conflict Resolution Hierarchy

When conflicts arise between agents or requirements, resolution follows this hierarchy:

### Level 1: Master Prompt Authority
- **Supremacy**: Master prompt supersedes all other instructions
- **Scope**: Fundamental behavioral rules, ethical guidelines, core methodologies
- **Resolution**: Automatic - conflicting instructions are ignored

### Level 2: Task Priority Override
- **Rule**: Higher priority tasks override lower priority conflicts
- **Scope**: Resource allocation, timeline conflicts, feature prioritization
- **Resolution**: Automatic priority-based resolution with logging

### Level 3: Role Hierarchy
- **Order**: Product Owner > Software Engineer > QA Tester > DevOps Engineer
- **Scope**: Requirements interpretation, technical decision disputes
- **Resolution**: Higher role's decision takes precedence

### Level 4: ACIM Escalation
- **Trigger**: Unresolved conflicts affecting architecture or compliance
- **Process**: ACIM specialist reviews and provides binding decision
- **Timeline**: 24-hour resolution requirement

### Level 5: Human Intervention
- **Final escalation**: Human product owner or tech lead involvement
- **Trigger**: System cannot resolve within established parameters
- **Process**: Formal conflict resolution meeting with all stakeholders

## 5. Sample Walkthrough: "Build Quick-Action Feature"

### Task Input:
```json
{
  "title": "Build quick-action feature for dashboard",
  "description": "Implement a quick-action dropdown menu that allows users to perform common actions (create project, invite user, export data) directly from the main dashboard without navigation",
  "priority": "high",
  "tags": ["frontend", "ui", "dashboard"],
  "estimated_effort": "medium"
}
```

### Agent Selection:
- **Analysis**: Keywords "build", "implement", "feature" → `software_engineer`
- **Confirmation**: No explicit assignee, frontend/UI tags support assignment
- **Result**: Primary agent = `software_engineer`

### Iteration Loop Execution:

#### Phase 1: Plan (`software_engineer`)
**Deliverable**: Implementation Plan
```
## Quick-Action Feature Implementation Plan

### Technical Requirements:
- React dropdown component with accessibility support
- Integration with existing dashboard layout
- API endpoints for: project creation, user invitation, data export
- Permission-based action visibility
- Loading states and error handling

### Subtasks:
1. Design dropdown component architecture
2. Create reusable QuickActionDropdown component
3. Implement individual action handlers
4. Add permission checking logic
5. Integrate with dashboard layout
6. Add comprehensive testing

### Dependencies:
- User permission service API
- Export service endpoints
- Dashboard layout component

### Timeline: 3-5 days
### Risks: Permission system integration complexity
```

#### Phase 2: Code (`software_engineer`)
**Deliverable**: Code Implementation
```javascript
// components/QuickActionDropdown.jsx
import React, { useState } from 'react';
import { usePermissions } from '../hooks/usePermissions';
import { createProject, inviteUser, exportData } from '../services/api';

export const QuickActionDropdown = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(null);
  const permissions = usePermissions();

  const actions = [
    {
      id: 'create-project',
      label: 'Create Project',
      permission: 'project.create',
      handler: createProject
    },
    // ... additional actions
  ];

  return (
    <div className="quick-action-dropdown">
      {/* Component implementation */}
    </div>
  );
};
```

#### Phase 3: Self-Review (`qa_tester`)
**Deliverable**: Quality Assessment
```
## QA Review Report

### Code Quality: ✅ PASS
- Follows React best practices
- Proper error handling implemented
- Accessibility attributes present

### Test Coverage: ⚠️ NEEDS IMPROVEMENT
- Unit tests: 85% (target: 90%)
- Integration tests: Missing dropdown interaction tests
- E2E tests: Not implemented

### Security: ✅ PASS  
- Permission checks properly implemented
- No XSS vulnerabilities identified

### Recommendations:
1. Add integration tests for dropdown interactions
2. Implement E2E test for full user workflow
3. Consider adding keyboard navigation tests
```

#### Phase 4: ACIM Vetting
**Deliverable**: Architecture Compliance Report
```
## ACIM Assessment

### Architecture Compliance: ✅ PASS
- Follows established component patterns
- Proper separation of concerns
- Reusable design approach

### Integration Impact: ✅ LOW RISK
- Minimal impact on existing dashboard
- Clean API integration points
- No breaking changes

### Maintainability: ✅ GOOD
- Well-documented component
- Follows naming conventions
- Easy to extend with new actions

### Recommendation: APPROVED FOR MERGE
```

#### Phase 5: Merge Request (`devops_engineer`)
**Deliverable**: Deployment Approval
```
## Merge Request Review

### Integration Testing: ✅ COMPLETE
- All automated tests passing
- Manual testing completed
- Cross-browser validation done

### Deployment Readiness: ✅ READY
- Feature flag implemented
- Rollback plan documented
- Monitoring alerts configured

### Stakeholder Notification: ✅ SENT
- Product team notified
- Documentation updated
- User training materials prepared

### Status: APPROVED FOR PRODUCTION DEPLOYMENT
```

### Final Outcome:
- **Total Duration**: 4 days
- **Iteration Count**: 1 (no rework required)
- **Quality Score**: 94/100
- **Deployment**: Successful with zero issues
- **User Adoption**: 78% feature utilization within first week

## Protocol Maintenance

This orchestration protocol should be reviewed and updated quarterly to ensure:
- Agent role definitions remain current
- Conflict resolution procedures are effective
- Task schema accommodates new requirements
- Success metrics are being met

**Version**: 1.0  
**Last Updated**: 2024  
**Next Review**: Q2 2024
