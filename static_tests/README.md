# Static tests

These tests are solely used for housekeeping, mainly to track down unused code which
can be removed although some checks also lower the risk for exceptions.

## Tests that could prevent an exception

### test_debug_leftovers.py

A call to the debug_log would fail if the app is run in "non-dev" mode, as the debug
log is not composed/present in that case.

### test_query_args.py

Ensures calls to textual its query functions always include the hash before the id.

## Tests purely for housekeeping

All other tests.