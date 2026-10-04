# Final Local Verification

Date: October 4, 2026. All work is within this project directory.

## Automated Results

Command: `python -B -m unittest discover -s tests -v`

```text
Ran 56 tests in 3.071s
OK
```

Coverage: seven metrics, all aliases, real source citations, deterministic
generation and checksums, shared SQL/seed parity, duplicate-allocation fanout,
line-level exposure, due-today boundaries, completed orders, empty data,
zero denominators, read-only connections, role denials and source redaction,
session isolation, malformed requests, path/Host/Origin protection, audit
hash chains, and static package completeness/parity.

Browser commands, using already installed Playwright and Chrome:

```text
python -B scripts/capture_demo.py --url http://127.0.0.1:8766
29 checks passed; 0 JavaScript/CSP errors; 0 external runtime requests

python -B scripts/capture_demo.py --url http://127.0.0.1:8767 --static
29 checks passed; 0 JavaScript/CSP errors; 0 external runtime requests
```

Checked at 1440 x 1000, 390 x 844, 320 x 780 and 1920 x 1080:
navigation, KPI and source counts, real record drawers, financial denial and
approval, role downgrade clearing, unsupported prompts, graph trace switching,
keyboard modal dismissal, catalog, audit and page-overflow constraints.
Seven numbered PNG screenshots were generated and checked as nonblank.
An earlier diagnostic failure screenshot is excluded from the successful run
reports and submission archive.

JavaScript syntax: `node --check static/app.js`,
`node --check static/replay.js`, and `node --check docs/static/app.js`
all exited 0.

Data: 163 source records, 11 tables, zero foreign-key violations,
SQLite integrity check `ok`. Static fixture: 331,760 bytes, seven answers,
163 source records per simulated role.

CLI risk query returned ORD-005, ORD-006, ORD-013 and ORD-014, with 43 distinct
source records. Revenue exposure is 6,705,000 integer USD cents.

## Boundaries

No packages were installed. No account was created. Nothing was published or
submitted. Snowflake, Cortex Analyst and CoCo account-side execution remain
unperformed. Native semantic SQL was checked against official documentation,
but has not been compiled in a Snowflake account. Local tests do not prove it.

The local and static preview servers remain bound to loopback:
- Local application: `http://127.0.0.1:8766`, PID 20192.
- Static replay: `http://127.0.0.1:8767`, PID 25804.

Browser-profile and temporary directories are disposable verification artifacts,
not submission dependencies. Cleanup was requested but the command was rejected
by execution policy; these directories may remain. The archive excludes them,
the earlier diagnostic failure screenshot, logs and bytecode.
See `FILES.md` for the exact package paths and `submission-manifest.json` for
checksums. The submission archive is generated locally and integrity-tested.
