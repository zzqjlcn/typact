"""Check release metadata and archive contents before upload."""

import argparse
from email.parser import BytesParser
from pathlib import Path
import tarfile
import tomllib
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]
    version = project["version"]
    wheel = args.directory / f"typact-{version}-py3-none-any.whl"
    sdist = args.directory / f"typact-{version}.tar.gz"
    with zipfile.ZipFile(wheel) as archive:
        wheel_names = archive.namelist()
        assert "typact/py.typed" in wheel_names, "wheel is missing py.typed"
        metadata = BytesParser().parsebytes(archive.read(f"typact-{version}.dist-info/METADATA"))
        assert metadata["Name"] == "typact" and metadata["Version"] == version
        assert metadata.get_all("Project-URL"), "missing project URLs"
    with tarfile.open(sdist) as archive:
        names = [member.name.split("/", 1)[-1] for member in archive.getmembers()]
        assert "src/typact/py.typed" in names, "sdist is missing py.typed"
        assert "pyproject.toml" in names
    for name in [*names, *wheel_names]:
        parts = Path(name).parts
        assert not set(parts) & {
            "node_modules", "docs-site", ".venv", ".git", ".release-audit", ".publish-dist", "__pycache__",
        }, f"unexpected packaged file: {name}"
    print(f"Validated {wheel.name} and {sdist.name}")


if __name__ == "__main__":
    main()
