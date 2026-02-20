# User Story: [STORY TITLE]

**Story ID:** [US-XXX]  
**Epic:** [Epic Name or Link]  
**Status:** [Backlog/Ready/In Progress/In Review/Done]  
**Priority:** [P0/P1/P2 or High/Medium/Low]  
**Created:** [DATE]  
**Assigned To:** [TEAM MEMBER NAME]

---

## 1. User Story

**As a** [user persona/role],  
**I want** [specific action/feature],  
**so that** [business value/user benefit/outcome]

**Example:** *As a team lead, I want to assign tasks to team members, so that I can delegate work efficiently.*

---

## 2. Acceptance Criteria

Clear, testable conditions that define when this story is complete. Each criterion should be independently verifiable.

- [ ] **AC1:** [Specific, measurable condition - use "Given/When/Then" format]
  - Example: *Given a task is created, When a team lead opens the task detail page, Then they should see an "Assign" button*

- [ ] **AC2:** [Specific, measurable condition]
  - Example: *Given the team lead clicks "Assign", When they select a team member from the dropdown, Then the task should be assigned and a notification sent*

- [ ] **AC3:** [Specific, measurable condition]
  - Example: *Given a task is assigned, When the assigned user logs in, Then they should see the task in their "My Tasks" list*

- [ ] **AC4:** [Specific, measurable condition - test edge cases]
  - Example: *Given a task is already assigned, When the team lead reassigns it to another member, Then the original assignee should be notified of the change*

- [ ] **AC5:** [Specific, measurable condition - test error scenarios]
  - Example: *Given an unassigned task, When the team lead tries to assign it to an inactive user, Then an error message should appear: "User is inactive"*

---

## 3. Technical Notes (Optional)

### Implementation Hints
- [Suggested approach or technology to consider]
- [Potential libraries or existing components to reuse]
- [Database schema changes needed]

### Example:
- Use existing `TaskAssignment` modal component from the design system
- Update `tasks` table with new `assigned_to` and `assigned_at` fields
- Trigger email notification via `NotificationService.sendTaskAssigned()`

### Known Constraints
- [Any technical limitations or considerations]
- [Existing code that might need refactoring]
- [Performance considerations]

### Dependencies on Other Systems
- [APIs that need to be called]
- [Services that must be available]
- [Data that must be available first]

---

## 4. Estimation

**Story Points:** [8-13 point scale: 1, 2, 3, 5, 8, 13, 21]

**Time Estimate:** [e.g., 2-3 days]

**Complexity:** [ ] Simple / [ ] Medium / [ ] Complex

**Reasoning:** [Brief explanation of why this estimate was chosen. For example: "Requires database changes (2pts) + frontend component (3pts) + testing (1pt) = 6pts"]

---

## 5. INVEST Validation Checklist

<!-- This checklist ensures the story follows INVEST principles for good agile user stories -->

### Independent
- [ ] This story can be completed independently
- [ ] It does not depend on other stories (or dependencies are clearly noted)
- [ ] It doesn't block other stories

### Negotiable
- [ ] The story is flexible in implementation details
- [ ] Acceptance criteria can evolve based on team discussion
- [ ] The "how" is not fixed in stone

### Valuable
- [ ] Story delivers clear value to the end user
- [ ] Product owner understands and agrees with the value
- [ ] It contributes to a business goal or solves a user problem

### Estimable
- [ ] Team understands enough to estimate the story
- [ ] Acceptance criteria are clear and measurable
- [ ] No hidden complexity or unknowns
- [ ] Story is not too vague

### Small
- [ ] Story can be completed in one sprint (1-2 days for typical story)
- [ ] Story is small enough to fit in iteration planning
- [ ] If story feels too large (>13 points), consider breaking it down

### Testable
- [ ] Acceptance criteria are specific and verifiable
- [ ] QA can definitively determine when story is done
- [ ] No ambiguous requirements like "looks good" or "feels fast"

---

## 6. Definition of Done

This story is considered complete when:

- [ ] All acceptance criteria are met and verified
- [ ] Code is written and reviewed
- [ ] Code follows project coding standards
- [ ] Unit tests written with >80% code coverage
- [ ] Integration tests pass
- [ ] QA testing completed (manual and/or automated)
- [ ] Documentation updated (if needed)
- [ ] No critical bugs found
- [ ] Product owner approval received
- [ ] Story merged to main branch

---

## 7. Related Stories & Dependencies

### Blocks
- [ ] [Story ID: Story that this story enables or unblocks]
- [ ] [Story ID: Other stories waiting on this one]

### Blocked By
- [ ] [Story ID: Story that must be completed first]
- [ ] [Story ID: Story that this one depends on]

### Related Stories
- [ ] [Story ID: Similar or related functionality]
- [ ] [Story ID: Follow-up story or enhancement]

---

## 8. Business Value & Priority

**Business Value:** [Why is this important? What's the impact?]

Example: *Allows team leads to efficiently manage task assignments, improving team productivity by reducing manual communication overhead.*

**User Impact:** [How does this benefit the user?]

Example: *Team members spend less time waiting for task clarification and can get started on work immediately.*

**Priority Justification:** [Why was this prioritized?]

Example: *This is a core feature needed by 80% of our user base and will significantly improve workflow efficiency.*

---

## 9. Design & UI References

### Mockups/Wireframes
- [Link to Figma design]
- [Link to wireframe document]

### Design Checklist
- [ ] User interface reviewed by design team
- [ ] Responsive design confirmed (mobile, tablet, desktop)
- [ ] Accessibility (WCAG 2.1 AA) requirements met
- [ ] Design system components used correctly
- [ ] Consistent with existing product patterns

### Design System Components
- [Component name and link if using design system]
- Example: "Button component (blue primary)", "Modal dialog", "Dropdown select"

---

## 10. Edge Cases & Error Scenarios

Consider what happens in unusual situations:

- **Edge Case 1:** [Scenario and expected behavior]
  - Example: *What if a team member is assigned the same task twice? → System should ignore duplicate assignment*

- **Edge Case 2:** [Scenario and expected behavior]
  - Example: *What if the assigned user is deleted from the system? → Task should show "Unassigned" status*

- **Edge Case 3:** [Scenario and expected behavior]
  - Example: *What if multiple team leads try to assign the same task simultaneously? → Last update wins, or show conflict warning*

- **Error Scenario 1:** [Error condition and expected handling]
  - Example: *If the assignment API fails → Show user-friendly error message and allow retry*

- **Error Scenario 2:** [Error condition and expected handling]
  - Example: *If the email notification service is down → Log error but still complete assignment*

---

## 11. Testing Strategy

### Manual Testing
- [ ] Test on Chrome browser
- [ ] Test on Firefox browser
- [ ] Test on Safari browser
- [ ] Test on mobile devices
- [ ] Test happy path (all works)
- [ ] Test error scenarios
- [ ] Test edge cases listed above

### Automated Testing
- [ ] Unit tests for business logic
- [ ] Integration tests for API calls
- [ ] End-to-end tests for user workflows
- [ ] Test coverage: [Target %, e.g., 80%+]

### Test Data Requirements
- [Sample data needed for testing, e.g., "5 test users with different roles"]
- [Any specific setup or teardown needed]

---

## 12. Notes & Discussion

### Questions / Clarifications Needed
- [ ] [Question to clarify with stakeholders]
- [ ] [Assumption that needs validation]

### Implementation Risks
- [Potential risk or concern]
- [Any known issues that might affect this story]

### Future Enhancements (Out of Scope)
- [Nice-to-have feature not included in this story]
- [Potential improvement for a future story]

### Comments
[Any additional notes, discussions, or context about this user story]

---

