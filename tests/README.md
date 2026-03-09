# Tests directory

## Static tests

> directory static_tests

These tests are mainly used for housekeeping, mainly to track down unused code which can be removed.

### Tests to prevent exceptions in static_test:

**test_debug_leftovers.py**

A call to the debug_log would fail if the app is run in "non-dev" mode, as the debug log is not composed/present in that case.

**test_query_args.py**

Ensures calls to textual its query functions always include the hash before the id.

## Smoke tests

> directory smoke_tests

Basic smoke tests.
