import os

# Tests must not depend on SGU's map service; geology is tested separately with a mocked lookup
os.environ.setdefault("GEOLOGY_DISABLED", "1")
