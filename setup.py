"""setup.py."""

from __future__ import annotations

from pathlib import Path

from setuptools import find_packages, setup

PROJECT = "rematch-au"

__author__ = "Alex Boul"
__version__ = (
    (Path(__file__).parent / PROJECT.replace("-", "_") / "VERSION")
    .read_text()
    .strip()
)
__license__ = (
    (Path(__file__).parent / "LICENSE").read_text().splitlines()[0].strip()
)

REPO_URL = "https://github.com/alexbou1/rematch-au"
REQUIRES_PYTHON = ">=3.11.0"


# ------------------------------------------------------------------------------
def looks_like_script(path: Path) -> bool:
    """Check if a file looks like a script."""

    if not (
        path.is_file()
        and (stat := path.stat()).st_size > 2
        and stat.st_mode & 0o100
    ):  # noqa
        return False

    with open(path) as f:
        return f.read(2) == "#!"


# ------------------------------------------------------------------------------
def find_cli_entry_points(
    *cli_pkg: str, entry_point: str = "main"
) -> list[str]:
    """Find CLI entry point scripts in the specified CLI packages."""

    entry_points = []
    for pkg in cli_pkg:
        pkg_path = Path(pkg.replace(".", "/"))
        if not pkg_path.is_dir():
            continue
        entry_points.extend(
            [
                f"{f.stem.replace('_', '-')}={pkg}.{f.stem}:{entry_point}"
                for f in pkg_path.glob("*.py")
                if not f.name.startswith("_")
            ]
        )
    return entry_points


# ------------------------------------------------------------------------------
# Import README.md and use it as the long-description. Must be in MANIFEST.in
with open("README.md") as fp:
    long_description = "\n" + fp.read()

# ------------------------------------------------------------------------------
# Get pre-requisites from requirements.txt. Must be in MANIFEST.in
with open("requirements.txt") as fp:
    required = [s.strip() for s in fp.readlines()]

# Optional extras -- none for this project
extras = {"all": []}
for x in []:
    with open(f"requirements-{x}.txt") as fp:
        extras[x] = [s.strip() for s in fp.readlines()]
        extras["all"].extend(extras[x])

# ------------------------------------------------------------------------------
packages = find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"])
setup(
    name=PROJECT,
    version=__version__,
    packages=packages,
    entry_points={
        "console_scripts": find_cli_entry_points(
            *(p for p in packages if p.endswith(".cli"))
        )
    },
    # package_data={PROJECT: ["sql/*.sql"]},
    url=REPO_URL,
    license=__license__,
    author=__author__,
    description="GNAF address matching tool",
    long_description=long_description,
    platforms=["Mac OS X", "Linux"],
    python_requires=REQUIRES_PYTHON,
    install_requires=required,
    extras_require=extras,
    include_package_data=True,
)
