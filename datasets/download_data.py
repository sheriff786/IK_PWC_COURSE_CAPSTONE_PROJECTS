#!/usr/bin/env python3
"""
Download datasets from the PwC Agentic AI Capstone datasets repository.

Usage:
    python download_data.py --all                          # Download all projects
    python download_data.py --project healthcare           # Download one project
    python download_data.py --project healthcare --dest .  # Download to custom path
    python download_data.py --list                         # List available projects
"""

import argparse
import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

REPO_URL = "https://github.com/InfinitelyAsymptotic/ik-pwc-agenticai-datasets.git"

PROJECTS = [
    "contract_intelligence",
    "ecommerce",
    "healthcare",
    "regulatory_compliance",
]


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command and handle errors."""
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result


def check_git():
    """Ensure git is available."""
    if shutil.which("git") is None:
        print("Error: git is not installed. Install it from https://git-scm.com/", file=sys.stderr)
        sys.exit(1)


def download_project(project: str, dest: Path, tag: str | None = None):
    """Download a single project's dataset using git sparse-checkout."""
    dest = dest / project
    if dest.exists() and any(dest.iterdir()):
        print(f"  {project}/ already exists at {dest}, skipping (delete to re-download)")
        return

    print(f"  Downloading {project}/ ...")

    with tempfile.TemporaryDirectory() as tmpdir:
        clone_args = ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse"]
        if tag:
            clone_args += ["--branch", tag]
        clone_args += [REPO_URL, tmpdir]
        run(clone_args)
        run(["git", "sparse-checkout", "set", project], cwd=tmpdir)

        src = Path(tmpdir) / project
        if not src.exists():
            print(f"Error: project '{project}' not found in repository", file=sys.stderr)
            sys.exit(1)

        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dest)

    file_count = sum(1 for _ in dest.rglob("*") if _.is_file())
    print(f"  Done: {file_count} files -> {dest}")


def download_all(dest: Path, tag: str | None = None):
    """Download all project datasets."""
    for project in PROJECTS:
        download_project(project, dest, tag)


def list_projects():
    """List available projects."""
    print("Available projects:")
    for p in PROJECTS:
        print(f"  - {p}")


def main():
    parser = argparse.ArgumentParser(
        description="Download PwC Agentic AI Capstone datasets"
    )
    parser.add_argument("--project", choices=PROJECTS, help="Project to download")
    parser.add_argument("--all", action="store_true", help="Download all projects")
    parser.add_argument("--dest", type=Path, default=Path("./datasets"), help="Destination directory (default: ./datasets)")
    parser.add_argument("--tag", type=str, default=None, help="Git tag/version to download (default: latest)")
    parser.add_argument("--list", action="store_true", help="List available projects")
    args = parser.parse_args()

    if args.list:
        list_projects()
        return

    if not args.project and not args.all:
        parser.print_help()
        sys.exit(1)

    check_git()
    args.dest = args.dest.resolve()
    print(f"Downloading to: {args.dest}")

    if args.all:
        download_all(args.dest, args.tag)
    else:
        download_project(args.project, args.dest, args.tag)

    print(f"\nAll done! Datasets are in: {args.dest}")


if __name__ == "__main__":
    main()
