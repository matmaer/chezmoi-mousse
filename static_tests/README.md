## Static tests

> directory static_tests in the project root

These tests are mainly used for **housekeeping**, mainly to track down unused code which can be removed.

Uses `pytest` to report on failures.

Does not do runtime checks, just static tests with `ast`.

### Tests to prevent exceptions in static_test:

* **debug_leftovers.py**: a call to the debug_log would fail if the app is run in debug mode, as the debug log is not composed/present in that case, additionally debug mode has dependencies only present in the uv dev env.

* **query_args.py**: ensures calls to textual its query functions are formedd as intended.

### Caching

* **_cached_data.py** caches all python path and the calls from ast.parse on those paths.