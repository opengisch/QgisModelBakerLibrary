"""Generate the API reference pages of the modelbaker package."""

from pathlib import Path

import mkdocs_gen_files

root = Path(__file__).resolve().parents[2]
src = root / "modelbaker"
excluded = {"libs"}

nav = mkdocs_gen_files.Nav()

for path in sorted(src.rglob("*.py")):
    module_path = path.relative_to(root).with_suffix("")
    parts = tuple(module_path.parts)

    if excluded.intersection(parts[1:]):
        continue

    doc_path = path.relative_to(src).with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1].startswith("_"):
        continue

    nav[parts[1:] or ("modelbaker",)] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        fd.write(f"::: {'.'.join(parts)}\n")

    mkdocs_gen_files.set_edit_path(full_doc_path, path.relative_to(root))

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
