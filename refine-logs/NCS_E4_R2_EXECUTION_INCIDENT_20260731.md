# NCS E4 r2 Execution Incident

**Date:** 2026-07-31  
**Candidate:** `e4-domain-stable-v4-20260731-candidate-r2`  
**Candidate SHA-256:**
`9213cec8e947a4919aa8ca603ba5514471e7e6293136051826f234c66fbce964`  
**Authorization SHA-256:**
`15f9789dc72574dd644f6a8b6133b9021cb1e431c08129091d2808620cea70f8`  
**Classification:** infrastructure execution incomplete; no scientific
outcome

## What happened

Exact-SHA preflight passed without creating the quarantine root. The authorized
executor then reserved the frozen r2 root and wrote
`execution-manifest.json`. The process remained active at approximately one
CPU core with low memory use for at least 48 minutes. It subsequently
disappeared without writing `e3-results.json`, `execution-complete.json` or
`execution-failure.json`.

The root contains exactly one 408-byte file:

- `execution-manifest.json`, SHA-256
  `6a9109b410536d66c0cf08a2d1dee20f70ea2f3f9f31fc8c2eafb69a03cb4a7a`

The frozen inventory is
`refine-logs/E4_R2_INCOMPLETE_OUTPUT_INVENTORY_20260731.json`.

## Root-cause evidence

- The machine did not reboot.
- No sleep/wake transition was found around the observed interruption window.
- No matching kernel or launchd OOM/kill record was found.
- Python wrote no caught-exception failure record.
- The last live observation showed PID 4252 in state `Rs+`, approximately
  100% CPU and 0.1% memory.
- The process was attached to the interactive execution PTY rather than a
  detached durable local job.

The exact terminating signal is not recoverable from the available logs. The
most supported operational explanation is an external, non-catchable
termination of the attached PTY job. This is not evidence about recovery,
uncertainty, stability or method quality.

## Governance decision

The r2 authorization is consumed. The occupied r2 output root must remain
untouched, and neither the same authorization nor the same root may be reused.
E4-R006 remains `BLOCKED`; it is not marked scientific `FAIL` because no result
payload exists.

Any subsequent attempt requires a new candidate identity, a new absent
quarantine root and a new exact-SHA authorization. The launch must be detached
from the conversation PTY and independently monitored. No result value from r2
is available for analysis or manuscript use.
