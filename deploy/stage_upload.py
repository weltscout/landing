"""Stage exactly the files the site serves, for the Bunny storage upload.

    python3 deploy/stage_upload.py dist /tmp/upload

Copies the set deploy/edge_script.py resolves as the site's files (everything in
dist except vercel.json, the generated edge script artifacts and dist/aws/) so
the upload list cannot drift from the middleware's clean-URL resolution.
"""

import pathlib
import shutil
import sys

from edge_script import site_files


def main():
    dist, dest = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    if dest in (pathlib.Path("/"), pathlib.Path("."), dist):
        sys.exit(f"stage_upload: refusing to clear {dest}")
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    files = site_files(dist)
    for rel in files:
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dist / rel, target)
    print(f"staged {len(files)} files -> {dest}")


if __name__ == "__main__":
    main()
