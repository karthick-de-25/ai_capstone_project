# ADR-0001: Sequential 3-Agent Pipeline with Conditional Routing

**Status:** Accepted

**Date:** 2026-03-15

## Context

The capstone requires a multi-agent workflow demonstrating sequential execution, routing, and orchestration. Three agents are needed:
- Report Analysis Agent
- Summary Agent
- Recommendation Agent

Options considered for agent topology:
1. Pure sequential (linear chain, no branching)
2. Sequential with conditional routing (branching based on classification)
3. Parallel agents (all agents analyze independently, then merge)

## Decision

Use **sequential pipeline with conditional routing** as a LangGraph 1.x `@entrypoint`
orchestrating `@task`-decorated agent functions.

- The three agents execute in order: Analysis → Summary → Recommendation
- Ordering and routing are **plain Python control flow** inside the entrypoint (no separate graph nodes/edges)
- A classifier helper sits between Analysis and Summary, routing by severity:
  - `normal` → return early (no follow-up needed)
  - `abnormal` → proceed to Summary Agent
  - `critical` → interrupt for a human alert flow
- Human-in-the-loop checkpoint gates the transition from Summary → Recommendation
- Sequential dependency is natural: Summary depends on Analysis; Recommendations depend on both

## Consequences

- **Positive:** Simple, testable, matches the capstone evaluation rubric (sequential + router)
- **Positive:** Each agent sees the output of its predecessor — no redundant context
- **Positive:** Classification-based routing fulfills the "router-based decision making" requirement
- **Negative:** Parallel execution for independent sections is not achievable in pure sequential mode
- **Mitigation:** If parallel analysis of independent report sections is needed later, the analysis task can fan out — launch multiple `@task` futures and await them together (no `Send`/graph API needed).

## Alternatives Considered

| Alternative | Reason Rejected |
|-------------|-----------------|
| Pure sequential (no routing) | Fails the "router-based decision making" rubric requirement |
| Fully parallel agents | Each agent depends on previous output — parallel would load redundant full report into every agent |
| CrewAI | LangGraph 1.x `@entrypoint`/`@task` is more flexible (checkpoints, interrupts, plain-Python routing); CrewAI is more opinionated out-of-box |