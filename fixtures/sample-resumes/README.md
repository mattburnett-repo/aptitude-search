# Sample resumes

Plain-text resumes for manual testing and demos. Upload in the UI or pass to `POST /v1/pipeline` via curl (see [docs/TESTING.md](../../docs/TESTING.md)).

| File | Profile | Use when |
|------|---------|----------|
| [`career-changer-mixed-stack.txt`](career-changer-mixed-stack.txt) | Full-stack developer, legacy modernization | Pipeline regression, tech-adjacent roles; has golden Stage 1/2 output under [`fixtures/example-outputs/`](../example-outputs/) |
| [`senior-backend-engineer.txt`](senior-backend-engineer.txt) | Staff/senior backend IC, distributed systems | Senior individual-contributor profiles |
| [`marketing-operations-lead.txt`](marketing-operations-lead.txt) | Marketing ops director, CRM/analytics | Non-engineering leadership and ops roles |
| [`pre-college-retail-service.txt`](pre-college-retail-service.txt) | Recent high-school grad, retail/food service | Entry-level, small-town, thin resume |
| [`long-unemployment-gap-admin-coordinator.txt`](long-unemployment-gap-admin-coordinator.txt) | Admin coordinator, 6+ month unemployment gap | Long job search, layoff + temp-agency work, mid-career office/support roles |
| [`prompt-injection-ignore-instructions.txt`](prompt-injection-ignore-instructions.txt) | Malicious override text embedded in resume | Input-safety rejection test (expect **400**) |

Pre-built request bodies:

- Entry-level profile with constraints: [`fixtures/pipeline-request-pre-college.json`](../pipeline-request-pre-college.json)
- Injection blocklist smoke test: [`fixtures/pipeline-request-injection-test.json`](../pipeline-request-injection-test.json)
