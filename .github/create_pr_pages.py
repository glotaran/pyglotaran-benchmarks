from __future__ import annotations

import subprocess
from pathlib import Path
import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).parent
INDEX_TEMPLATE = SCRIPT_DIR / "pr_index_template.html"
PR_INDEX_FILE = (SCRIPT_DIR / "../html/prs/index.html").resolve()


def pr_branches() -> list[str]:
    """List of branches that start with 'pr-'"""
    out = subprocess.run(
        [
            "git",
            "for-each-ref",
            "--shell",
            '--format="%(refname:strip=3)"',
            "refs/remotes/origin/pr-*",
        ],
        capture_output=True,
    )
    branches = out.stdout.decode().splitlines()
    return [branch.replace('"', "").replace("'", "") for branch in branches]


def create_worktrees(branches: list[str]):
    """Create folders for pr-* branches inside of html/prs/"""
    for branch in branches:
        subprocess.run(
            ["git", "worktree", "add", str(PR_INDEX_FILE.parent / branch), branch]
        )


def clean_pr_benchmark_branches(branch: str):
    """Remove benchmark branches odf closed PRs"""
    subprocess.run(["git", "push", "origin", "--delete", branch])


def pr_info(branch: str):
    """Get PR title and link from github api"""
    _, _, pr_nr = branch.partition("-")
    try:
        response = requests.get(
            f"https://api.github.com/repos/glotaran/pyglotaran/pulls/{pr_nr}",
        ).json()
        return response["title"], response["html_url"], response["state"]
    except Exception:
        return pr_nr, f"https://github.com/glotaran/pyglotaran/pull/{pr_nr}", "unknown"


def create_pr_index_page(branches: list[str]):
    """Writes index page for prs folder."""
    template = BeautifulSoup(INDEX_TEMPLATE.read_text(encoding="utf8"), features="lxml")
    for branch in branches:
        title, link, state = pr_info(branch)
        if state == "closed":
            clean_pr_benchmark_branches(branch)
            continue
        li = template.new_tag("li")
        pr_link = template.new_tag("a", href=link)
        pr_link.append(title)
        li.append(pr_link)
        li.append(" ( ")
        benchmark_link = template.new_tag(
            "a", href=f"https://glotaran.github.io/pyglotaran-benchmarks/prs/{branch}"
        )
        benchmark_link.append("benchmark")
        li.append(benchmark_link)
        li.append(" )")
        template.ul.append(li)
    PR_INDEX_FILE.write_text(str(template), encoding="utf8")


if __name__ == "__main__":
    branches = pr_branches()
    create_worktrees(branches)
    if PR_INDEX_FILE.parent.exists():
        create_pr_index_page(branches)
