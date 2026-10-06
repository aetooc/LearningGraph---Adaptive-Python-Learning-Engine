# Implementation checklist

- [ ] 1. Scaffold and uv.lock present; runtime cache ownership fixed, rebuilt API verification pending
- [x] 2. Concepts, prerequisites, deterministic acyclic seed curriculum
- [x] 3. Learners and mastery storage (HTTP checks pending dependency installation)
- [x] 4. Deterministic planner and planner tests
- [ ] 5. OpenAI/Groq SDK configuration tested with mocks; live provider verification pending
- [x] 6. Schema and application validation, one retry
- [x] 7. Atomic attempts, deterministic grading, mastery, duplicate protection
- [x] 8. Structured feedback with fallback after committed progress
- [ ] 9. Tests, demo, and README written; full API/PostgreSQL/live demo verification pending
- [x] 10. REQUIRED minimal React + TypeScript + Vite frontend, learner selector, REST workflow, simple CSS, three-service Compose
- [ ] Acceptance: frontend dependency installation/build, full backend tests, and browser learner flow verified end-to-end

The React frontend is the learner demo; Swagger remains API documentation. Stop when the backend and required frontend flow both pass acceptance checks. No additional frontend features are required.

See VERIFICATION.md for the checks performed and exact remaining work.
