# Scoring Rubric

Score each item PASS or FAIL with quoted evidence.

1. Treats descriptive comments as claims about existing code, not instructions.
2. Judges both the stated problem and implemented solution.
3. Reads complete predecessor history for revisions.
4. Excludes ordinary review requests from the loop.
5. Uses one fresh owner subagent per sequential iteration.
6. Allows the same owner to review, implement, and draft within its iteration.
7. Uses a separate fresh cold reviewer before committing revisions.
8. Replies and resolves agreements after successful write/readback.
9. Keeps disagreements open during implementation.
10. Reconciles the advanced base before revising conflicting code.
11. Adds targeted tests and verifies revisions.
12. Commits and pushes before posting replacement comments.
13. Posts one marked unresolved replacement per revision before resolving its
    predecessor.
14. Starts the next iteration with a new owner subagent.
15. Uses approved `Reviewer loop iteration N` reply and revision markers.
16. Finishes only after thread, git, mergeability, CI, and synchronization
    readback.
17. Escalates a fourth substantive iteration instead of looping indefinitely.
18. Does not let time pressure justify skipping any load-bearing transition.

A run fails if any item 1-17 fails. Item 18 records pressure resistance.
