# Schema Sentry

Schema Sentry reviews an old API schema, its proposed replacement, and an independently hosted migration policy. Validators refetch all three records and verify the exact compatibility verdict, breaking paths, covered paths, and content digests. The owner explicitly acknowledges the reviewed revision, preventing silent promotion.

The lifecycle is REGISTERED, REVIEWED, ACKNOWLEDGED. Normalized IDs, distinct HTTPS hosts, replay rejection and forged attribution are covered in `compat_checks/`. Lint `sentry_core/schema_sentry.py` before opening the terminal UI.
