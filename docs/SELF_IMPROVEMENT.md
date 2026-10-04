# Self-Growing Skills

Nexora may propose new skills, but can never activate them itself.

Pipeline:

    problem detected
        -> skill proposal (generated source)
        -> static scanner (AST: forbidden imports/calls/network)
        -> risk analysis
        -> USER APPROVAL (System 1)
        -> activation into skills/<name>/

Rejected by static scan: subprocess, ctypes, eval/exec, network calls.
The generator writes the audit trail for both accepted and rejected proposals.
