"""Patch starlette gzip to add missing DEFAULT_EXCLUDED_CONTENT_TYPES"""
import starlette.middleware.gzip as gzip_mod

fpath = gzip_mod.__file__
print(f"Patching: {fpath}")

with open(fpath, 'r') as f:
    content = f.read()

old_import = 'from starlette.datastructures import Headers, MutableHeaders'
new_import = 'from starlette.datastructures import Headers, MutableHeaders\n\nDEFAULT_EXCLUDED_CONTENT_TYPES = ("text/event-stream",)\n'

if 'DEFAULT_EXCLUDED_CONTENT_TYPES' not in content:
    content = content.replace(old_import, new_import)
    with open(fpath, 'w') as f:
        f.write(content)
    print("Patch applied successfully!")
else:
    print("Already patched.")