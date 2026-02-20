# Agent Guidelines — [PROJECT_NAME]

> Project-specific rules and role definitions for AI agents working on the [PROJECT_NAME] project.

**Project:** [PROJECT_NAME] v[VERSION]  
**Stack:** [CORE_TECHNOLOGIES_e.g._React_Node_Python]  
**Last Updated:** [YYYY-MM-DD]

---

## 1. Project Context

### What This Project Is
[Briefly describe the project's main purpose, target audience, and primary functionality.]

### Key Constraints
- **[Constraint 1]:** [Description. e.g., No backend. All data lives locally.]
- **[Constraint 2]:** [Description. e.g., Desktop only. No mobile support.]
- **[Constraint 3]:** [Description. e.g., Offline-first. Zero network requests.]

### Tech Stack (Non-Negotiable)
| Layer | Technology | Notes |
|-------|-----------|-------|
| Framework | [e.g., React 18 / Django] | [Specific usage notes] |
| Build/Env | [e.g., Vite / Docker] | [Specific usage notes] |
| Language | [e.g., TypeScript / Python] | [Specific usage notes] |
| Styling | [e.g., Tailwind CSS / SCSS] | [Specific usage notes] |
| State/DB | [e.g., Redux / PostgreSQL] | [Specific usage notes] |
| Testing | [e.g., Jest / PyTest] | [Coverage requirements] |

**Do NOT introduce:** [List tools, frameworks, or methodologies that are strictly forbidden in this project].

---

## 2. Code Conventions

### [Primary Language] Rules
- [Rule 1. e.g., Strict mode always enabled]
- [Rule 2. e.g., No 'any' types allowed]

### [Framework] Rules
- [Rule 1. e.g., Functional components only]
- [Rule 2. e.g., All business logic in custom hooks/services]

### Custom Architecture / Patterns
| Pattern | Purpose |
|---------|---------|
| [e.g., Custom Hook] | [Purpose] |
| [e.g., Service Layer] | [Purpose] |

### Naming Conventions
| Item | Convention | Example |
|------|-----------|---------|
| Components/Classes | [e.g., PascalCase] | `UserProfile` |
| Functions/Methods | [e.g., camelCase] | `getUserData` |
| Files | [e.g., kebab-case] | `user-profile.ts` |
| Constants | [e.g., UPPER_SNAKE_CASE] | `MAX_LIMIT` |

### Styling Guidelines
- [Guideline 1. e.g., Theme requirements (Light/Dark mode)]
- [Guideline 2. e.g., Standardized spacing/color tokens]

---

## 3. Data Model

All agents must adhere to these schemas/interfaces:

~~~typescript
// Insert core interfaces, types, or database schemas here
interface [EntityName] {
  id: string;
  // ...properties
}
~~~

### Validation Rules
- [Rule 1. e.g., Usernames must be unique]
- [Rule 2. e.g., Dates must be ISO-8601 strings]

---

## 4. Performance Requirements

| Metric | Target | How to Verify |
|--------|--------|---------------|
| [e.g., Page Load] | [e.g., < 1s] | [e.g., Lighthouse] |
| [e.g., Test Coverage] | [e.g., > 80%] | [e.g., CI/CD pipeline] |

---

## 5. Agent Role Definitions

### PM Agent
**Context:** You are the product manager for [PROJECT_NAME].
**Your responsibilities:**
- Write and refine PRD sections
- Create and decompose epics and user stories
**Rules:**
- Always reference the PRD at `[PATH_TO_PRD]`
- Acceptance criteria must use Given/When/Then format
**Key files:** `[PATH_TO_PRD]`, `[PATH_TO_TEMPLATES]`

### Developer Agent
**Context:** You are a [Frontend/Backend/Fullstack] developer building [PROJECT_NAME].
**Your responsibilities:**
- Implement user stories
- Write application code and unit tests
**Rules:**
- Follow the tech stack exactly (Section 1)
- Follow code conventions (Section 2)
**Key files:** `[PATH_TO_ARCHITECTURE_DOCS]`, `[PATH_TO_STORIES]`

### QA Agent
**Context:** You are a QA engineer testing [PROJECT_NAME].
**Your responsibilities:**
- Verify acceptance criteria
- Write test cases and test edge scenarios
**Rules:**
- Test across [Target Browsers/Environments]
- Verify performance and error handling
**Key files:** `[PATH_TO_TEST_STRATEGY]`

---

## 6. Project Structure Reference

~~~text
[PROJECT_ROOT]/
├── docs/                # Architecture, PRDs, specs
├── src/                 # Application source code
│   ├── [MODULE_1]/
│   └── [MODULE_2]/
├── tests/               # Test suites
└── package.json         # or equivalent config file
~~~

---

## 7. Common Mistakes to Avoid

| Mistake | Why It's Wrong | Do This Instead |
|---------|---------------|-----------------|
| [Mistake 1] | [Reason] | [Correct approach] |
| [Mistake 2] | [Reason] | [Correct approach] |

---

*This file is the single source of truth for agent behavior on this project. When in doubt, check the primary specification at `[PATH_TO_MAIN_DOC]`.*