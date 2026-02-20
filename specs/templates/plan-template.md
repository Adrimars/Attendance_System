# Implementation Plan — [PROJECT_NAME]

**Project:** [PROJECT_NAME] v[VERSION]  
**Developer:** [DEVELOPER_NAME]  
**PRD:** `[PATH_TO_PRD]`  
**Status:** [Draft | Active | Complete]  
**Last Updated:** [YYYY-MM-DD]

---

## 1. Goal & Approach

### What We're Building
[One paragraph describing what this plan covers — which phase(s), what the end state looks like, and what "done" means.]

### Strategy
[Describe the implementation order rationale. E.g., "Build the data layer first, then controllers, then UI — bottom-up." or "Build vertically slice by slice — each feature end-to-end before moving to the next."]

### Out of Scope for This Plan
- [Feature or phase explicitly deferred]
- [Feature or phase explicitly deferred]

---

## 2. Environment Setup Checklist

> Complete before writing any application code.

- [ ] Python [VERSION] installed and verified (`python --version`)
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Project folder structure created (see Section 5)
- [ ] [Any hardware/device setup steps, e.g., RFID reader connected and tested]
- [ ] [Any API credentials or config files in place]

---

## 3. Phase Breakdown

### Phase [N] — [Phase Name]
**Goal:** [What this phase delivers at a high level.]  
**Timeline:** [e.g., Day 1 | Week 1 | Sprint 1]

#### Tasks

| # | Task | Layer | PRD Ref | Done |
|---|------|-------|---------|------|
| [N.1] | [Task description] | [Model/View/Controller/Infra] | [FR-X.X] | [ ] |
| [N.2] | [Task description] | [Model/View/Controller/Infra] | [FR-X.X] | [ ] |
| [N.3] | [Task description] | [Model/View/Controller/Infra] | [FR-X.X] | [ ] |

#### Phase [N] Exit Criteria
- [ ] [Verifiable condition that proves this phase is complete]
- [ ] [Verifiable condition that proves this phase is complete]

---

### Phase [N+1] — [Phase Name]
**Goal:** [What this phase delivers at a high level.]  
**Timeline:** [e.g., Day 2 | Week 2 | Sprint 2]

#### Tasks

| # | Task | Layer | PRD Ref | Done |
|---|------|-------|---------|------|
| [N+1.1] | [Task description] | [Model/View/Controller/Infra] | [FR-X.X] | [ ] |
| [N+1.2] | [Task description] | [Model/View/Controller/Infra] | [FR-X.X] | [ ] |

#### Phase [N+1] Exit Criteria
- [ ] [Verifiable condition]
- [ ] [Verifiable condition]

---

## 4. Architecture Decisions

> Record key decisions made during planning so future agents don't re-litigate them.

| Decision | Choice | Reason |
|----------|--------|--------|
| [e.g., DB access pattern] | [e.g., Raw sqlite3, no ORM] | [e.g., Minimal dependencies; project is simple enough] |
| [e.g., UI navigation] | [e.g., Tab-based single window] | [e.g., PRD specifies single-window design] |
| [e.g., RFID input method] | [e.g., Hidden Entry widget + Enter key event] | [e.g., USB HID reader emulates keyboard] |

---

## 5. Project Structure

```text
[PROJECT_ROOT]/
├── [folder]/               # [Purpose]
│   ├── [file]              # [Purpose]
│   └── [file]              # [Purpose]
├── [folder]/               # [Purpose]
└── [config file]           # [Purpose]
```

---

## 6. Risks & Mitigations (Active)

| Risk | Severity | Mitigation |
|------|----------|-----------|
| [Risk description] | High / Medium / Low | [How to handle it] |

---

## 7. Testing Approach

- **Scope:** [What will be tested — unit, integration, manual, etc.]
- **RFID simulation:** [How to test without physical hardware, e.g., type card ID into input field manually]
- **DB verification:** [How to inspect SQLite state, e.g., DB Browser for SQLite or sqlite3 CLI]
- **Key scenarios to verify manually:**
  - [ ] [Scenario 1]
  - [ ] [Scenario 2]

---

## 8. Definition of Done

A feature is **done** when:
1. Code is written and follows the conventions in `specs/agents.md`.
2. The feature works end-to-end on Windows 10/11.
3. All acceptance criteria from the PRD user story are met.
4. Error states show user-friendly dialogs (no raw tracebacks).
5. Relevant events are logged to the local log file.

---

*Primary specification: `[PATH_TO_PRD]`*  
*Agent guidelines: `specs/agents.md`*
