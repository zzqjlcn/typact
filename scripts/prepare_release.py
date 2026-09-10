"""Create a draft for an existing tag; never publish or overwrite a release."""

import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import tomllib

from packaging.version import Version


def main():
    tag = os.environ["RELEASE_TAG"]
    version = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    if tag != f"v{version}":
        raise SystemExit("Tag must match the package version")
    subprocess.run(["git", "show-ref", "--verify", f"refs/tags/{tag}"], check=True)
    tagged = subprocess.check_output(["git", "rev-parse", f"refs/tags/{tag}^{{commit}}"], text=True).strip()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if tagged != head:
        raise SystemExit("Checkout does not match the release tag")
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## |\Z)", changelog, re.M | re.S)
    if not match:
        raise SystemExit("Missing version entry in CHANGELOG.md")
    releases = json.loads(subprocess.check_output(
        ["gh", "release", "list", "--limit", "1000", "--json", "tagName,isDraft"], text=True,
    ))
    if any(release["tagName"] == tag for release in releases):
        raise SystemExit("A release already exists; inspect it manually before making changes")
    with tempfile.TemporaryDirectory() as directory:
        notes = Path(directory) / "notes.md"
        notes.write_text(match.group(1).strip() + "\n", encoding="utf-8")
        args = ["gh", "release", "create", tag, "--verify-tag", "--draft", "--title", tag,
                "--notes-file", str(notes), f"dist/typact-{version}-py3-none-any.whl",
                f"dist/typact-{version}.tar.gz"]
        if Version(version).is_prerelease:
            args.append("--prerelease")
        subprocess.run(args, check=True)


if __name__ == "__main__":
    main()
