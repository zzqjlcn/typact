"""Publish an existing draft from the artifacts already verified by PyPI."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import tomllib
from urllib.request import Request, urlopen

from packaging.version import Version


def _read_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "typact-release"})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def main():
    tag = os.environ["RELEASE_TAG"]
    tagged_pyproject = subprocess.check_output(
        ["git", "show", f"{tag}:pyproject.toml"], text=True,
    )
    version = tomllib.loads(tagged_pyproject)["project"]["version"]
    if tag != f"v{version}":
        raise SystemExit("Tag must match the package version")

    release = json.loads(subprocess.check_output(
        ["gh", "release", "view", tag, "--json", "isDraft,isPrerelease"], text=True,
    ))
    if not release["isDraft"]:
        raise SystemExit("Release must still be a draft")

    package = _read_json(f"https://pypi.org/pypi/typact/{version}/json")
    expected_names = {
        f"typact-{version}-py3-none-any.whl",
        f"typact-{version}.tar.gz",
    }
    files = {item["filename"]: item for item in package["urls"]}
    if set(files) != expected_names:
        raise SystemExit(f"Unexpected PyPI files: {sorted(files)}")

    with tempfile.TemporaryDirectory() as directory:
        paths = []
        for name in sorted(expected_names):
            item = files[name]
            path = Path(directory) / name
            request = Request(item["url"], headers={"User-Agent": "typact-release"})
            with urlopen(request, timeout=60) as response:
                path.write_bytes(response.read())
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != item["digests"]["sha256"]:
                raise SystemExit(f"SHA-256 mismatch for {name}")
            paths.append(str(path))

        subprocess.run(["gh", "release", "upload", tag, "--clobber", *paths], check=True)

    args = ["gh", "release", "edit", tag, "--draft=false"]
    if Version(version).is_prerelease:
        args.extend(["--prerelease", "--latest=false"])
    subprocess.run(args, check=True)

    published = json.loads(subprocess.check_output(
        ["gh", "release", "view", tag, "--json", "isDraft,isPrerelease,url"], text=True,
    ))
    if published["isDraft"] or published["isPrerelease"] != Version(version).is_prerelease:
        raise SystemExit("Published release state does not match the package version")
    print(published["url"])


if __name__ == "__main__":
    main()
