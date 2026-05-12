# conftest.py — root-level pytest configuration
# Ensures `src` package is importable from any test file.
# This file being present at project root also triggers pytest's
# rootdir detection so `pythonpath = .` in pytest.ini takes full effect.
