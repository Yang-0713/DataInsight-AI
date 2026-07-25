import re
from pathlib import Path

from app.main import app


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_OPEN_SOURCE_FILES = [
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "docs/installation.md",
    "docs/api.md",
    "examples/README.md",
    "examples/datasets/retail_sales.csv",
    ".github/workflows/ci.yml",
    ".github/pull_request_template.md",
]
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def test_required_open_source_files_exist() -> None:
    for relative_path in REQUIRED_OPEN_SOURCE_FILES:
        path = PROJECT_ROOT / relative_path
        assert path.is_file(), f"missing open-source artifact: {relative_path}"
        assert path.stat().st_size > 0, f"empty open-source artifact: {relative_path}"


def test_relative_markdown_links_resolve() -> None:
    markdown_files = [
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "CONTRIBUTING.md",
        PROJECT_ROOT / "SECURITY.md",
        PROJECT_ROOT / "CHANGELOG.md",
        PROJECT_ROOT / "CODE_OF_CONDUCT.md",
        *sorted((PROJECT_ROOT / "docs").glob("*.md")),
        PROJECT_ROOT / "examples" / "README.md",
    ]

    broken_links: list[str] = []
    for markdown_file in markdown_files:
        content = markdown_file.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK.findall(content):
            path_text = target.split("#", maxsplit=1)[0].strip()
            if (
                not path_text
                or "://" in path_text
                or path_text.startswith(("mailto:", "#"))
            ):
                continue
            resolved = (markdown_file.parent / path_text).resolve()
            if not resolved.exists():
                broken_links.append(
                    f"{markdown_file.relative_to(PROJECT_ROOT)} -> {target}"
                )

    assert not broken_links, "broken documentation links:\n" + "\n".join(
        broken_links
    )


def test_api_documentation_lists_every_public_endpoint() -> None:
    documented = (PROJECT_ROOT / "docs" / "api.md").read_text(encoding="utf-8")
    undocumented = [
        path
        for path in app.openapi()["paths"]
        if path != "/api" and path not in documented
    ]

    assert not undocumented, "endpoints missing from docs/api.md:\n" + "\n".join(
        undocumented
    )
