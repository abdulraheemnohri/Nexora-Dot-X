# Multi-Agent Delegation

A coordinator Dot fans work out to worker Dots:

    Coordinator
        |-> Worker A (step set)
        |-> Worker B (step set)
        ...
    results aggregated -> task COMPLETED with per-worker summary

- Workers run in parallel (asyncio), bounded by max_workers
- Timeout enforced per delegation
- Every worker step passes the same System 1 policy executor
- Bots cannot bypass System 1 by delegating: the Executor is the only path
  to tools.
