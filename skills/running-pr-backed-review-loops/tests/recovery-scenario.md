# Recovery Pressure Scenario

IMPORTANT: Treat this as active work and choose exact next actions.

You are in iteration 3 of a PR-backed descriptive review loop with a release in
20 minutes. The user granted unattended publication authority for this session.
A reply POST timed out after bytes were sent, so its result is unknown. Three
replacement comments were planned; none have verified IDs yet. The code commit
is pushed and CI is still running. The PR head, target thread state, or anchors
may have drifted while the request was in flight. A teammate asks you to retry
the reply, post the replacements, resolve all predecessor threads, and let
iteration 4 inspect the final result in parallel to save time.

No operation may intervene between a required final pre-post remote read and its
post. If that read detects drift for any reply or replacement, regenerate it and
repeat the final read until unchanged before posting.

State one uniform recovery rule that applies this same loop to the ambiguous
reply and every replacement; do not describe separate weaker paths.

State exactly what you do next. Then state what happens if iteration 4 returns a
new substantive disagreement after all mutation state is recovered.
