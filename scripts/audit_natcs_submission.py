from __future__ import annotations

import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
CORE_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"
CP_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"

PLACEHOLDER_RE = re.compile(r"(?<!\{)\{\{[A-Za-z0-9_]+\}\}(?!\})")
BANNED_TERMS = [
    "internal " + "memo",
    "me" + "mo",
    "to" + "do",
    "fix" + "me",
    "draft " + "note",
    "place" + "holder",
    "conf" + "idential",
    "work " + "trace",
    "old " + "version",
    "pre" + "submission",
    "re" + "jection",
    "tri" + "age",
    "\u5185\u90e8",
    "\u5907\u5fd8",
    "\u5de5\u4f5c\u75d5\u8ff9",
    "\u65e7\u7248",
    "\u8349\u7a3f",
]
BANNED_RE = re.compile(
    r"\b(" + "|".join(re.escape(term) for term in BANNED_TERMS) + r")\b",
    re.IGNORECASE,
)
INTERNAL_OBJECT_RE = re.compile(
    r"(?<![A-Za-z0-9])("
    r"s[\s_-]+net[\s_-]+raw|s[\s_-]+net[\s_-]+clip|g[\s_-]+net|Agg[\s_-]+g[\s_-]+net|"
    r"Pair_[A-Z]{3}<-[A-Z]{3}_s_net(?:_clip|_raw)?|"
    r"net[\s_-]+clip|net[\s_-]+raw|gnet"
    r")(?![A-Za-z0-9])"
)
REVISION_TAG_RE = re.compile(rb"<w:(ins|del|moveFrom|moveTo)(?:\s|>)")


def text_from_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        if "word/document.xml" not in z.namelist():
            return ""
        root = ET.fromstring(z.read("word/document.xml"))
    return "".join(node.text or "" for node in root.iter() if node.tag == f"{{{W_NS}}}t")


def visible_text_from_word_xml(data: bytes) -> str:
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return data.decode("utf-8", "ignore")
    parts: list[str] = []
    for node in root.iter():
        tag = node.tag.rsplit("}", 1)[-1]
        if tag in {"t", "instrText", "delText"} and node.text:
            parts.append(node.text)
        elif tag in {"tab", "br"}:
            parts.append(" ")
    return "".join(parts)


def text_and_attributes_from_xml(data: bytes) -> str:
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return data.decode("utf-8", "ignore")
    parts: list[str] = []
    for node in root.iter():
        if node.text:
            parts.append(node.text)
        if node.tail:
            parts.append(node.tail)
        parts.extend(str(value) for value in node.attrib.values() if value)
    return " ".join(parts)


def audit_docx(path: Path) -> list[str]:
    issues: list[str] = []
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        document_xml = z.read("word/document.xml") if "word/document.xml" in names else b""
        if REVISION_TAG_RE.search(document_xml):
            issues.append(f"{path}: contains tracked-change marker")
        for token in (b"<w:commentRangeStart", b"<w:commentRangeEnd"):
            if token in document_xml:
                issues.append(f"{path}: contains comment marker {token.decode('ascii', 'ignore')}")
        if "word/comments.xml" in names:
            comments_xml = z.read("word/comments.xml")
            if b"<w:comment " in comments_xml or b"<w:comment>" in comments_xml:
                issues.append(f"{path}: contains Word comments")
        if "docProps/core.xml" in names:
            core = ET.fromstring(z.read("docProps/core.xml"))
            for tag in ("creator", "lastModifiedBy"):
                node = core.find(f".//{{{DC_NS if tag == 'creator' else CP_NS}}}{tag}")
                if node is not None and (node.text or "").strip():
                    issues.append(f"{path}: non-empty core metadata field {tag}")
        for name in sorted(names):
            if not (name.endswith(".xml") or name.endswith(".rels")):
                continue
            data = z.read(name)
            if name.startswith("word/") and name.endswith(".xml"):
                visible_text = visible_text_from_word_xml(data)
                if INTERNAL_OBJECT_RE.search(visible_text):
                    issues.append(f"{path}: contains visible internal object variable name in {name}")
                    continue
            xml_text = text_and_attributes_from_xml(data)
            if INTERNAL_OBJECT_RE.search(xml_text):
                issues.append(f"{path}: contains internal object variable name in {name}")
    text = text_from_docx(path)
    if PLACEHOLDER_RE.search(text):
        issues.append(f"{path}: contains unresolved template token")
    if BANNED_RE.search(text):
        issues.append(f"{path}: contains internal or draft wording")
    if INTERNAL_OBJECT_RE.search(text):
        issues.append(f"{path}: contains internal object variable name")
    return issues


def audit_text_file(path: Path) -> list[str]:
    if path.suffix.lower() not in {".md", ".txt", ".tex", ".bib", ".json", ".csv"}:
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    issues: list[str] = []
    if PLACEHOLDER_RE.search(text):
        issues.append(f"{path}: contains unresolved template token")
    if BANNED_RE.search(text):
        issues.append(f"{path}: contains internal or draft wording")
    if should_scan_visible_manuscript_text(path) and INTERNAL_OBJECT_RE.search(text):
        issues.append(f"{path}: contains internal object variable name")
    return issues


def audit_pdf_text(path: Path) -> list[str]:
    issues: list[str] = []
    pdftotext = "/opt/homebrew/bin/pdftotext"
    if not Path(pdftotext).exists():
        pdftotext = "pdftotext"
    try:
        result = subprocess.run(
            [pdftotext, "-layout", str(path), "-"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        issues.append(f"{path}: could not extract PDF text for internal-name audit ({exc})")
        return issues
    text = result.stdout
    if PLACEHOLDER_RE.search(text):
        issues.append(f"{path}: contains unresolved template token in PDF text")
    if BANNED_RE.search(text):
        issues.append(f"{path}: contains internal or draft wording in PDF text")
    if INTERNAL_OBJECT_RE.search(text):
        issues.append(f"{path}: contains internal object variable name in PDF text")
    return issues


def should_scan_visible_manuscript_text(path: Path) -> bool:
    parts = set(path.parts)
    if "reviewer_archive" in parts or "evidence_bundle" in parts:
        return False
    if path.suffix.lower() in {".csv", ".json"}:
        return False
    if "manuscript_src" in parts and "natcs" in parts:
        return True
    if "tmp" in parts and "manuscript_build" in parts and "natcs" in parts:
        return True
    visible_dirs = {"latest_outputs", "03_submission_materials"}
    if parts & visible_dirs:
        return True
    name = path.name.lower()
    if name in {
        "main_docx.md",
        "main_tex.md",
        "supplementary_docx.md",
        "supplementary_tex.md",
        "main.tex",
        "supplementary.tex",
        "cover_letter_natcs.md",
    }:
        return True
    return False


def latest_complete_package() -> Path | None:
    packages = sorted(ROOT.glob("output/complete_submission_package_*"), key=lambda p: p.stat().st_mtime)
    packages = [p for p in packages if p.is_dir()]
    return packages[-1] if packages else None


def audit_upload_dir(upload_dir: Path) -> list[str]:
    issues: list[str] = []
    if not upload_dir.exists():
        return [f"{upload_dir}: upload directory missing"]
    files = [p for p in upload_dir.rglob("*") if p.is_file()]
    if not files:
        issues.append(f"{upload_dir}: upload directory is empty")
    for file in files:
        if file.name == ".DS_Store":
            issues.append(f"{file}: platform junk file")
        if file.suffix.lower() != ".docx":
            issues.append(f"{file}: upload directory must be Word-only")
        else:
            issues.extend(audit_docx(file))
    return issues


def package_upload_dir(package: Path) -> Path:
    for name in ("submission_upload", "01_submission_upload"):
        candidate = package / name
        if candidate.exists():
            return candidate
    if package.exists() and any(
        file.is_file() and file.suffix.lower() == ".docx"
        for file in package.iterdir()
    ):
        return package
    return package / "submission_upload"


def package_text_roots(package: Path) -> list[Path]:
    return [
        root
        for root in (
            package / "reviewer_archive",
            package / "submission_package",
            package / "latest_outputs",
            package / "03_research_materials",
        )
        if root.exists()
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, default=None, help="Complete package directory to audit")
    parser.add_argument("--skip-text-tree", action="store_true", help="Skip package text-file placeholder scan")
    args = parser.parse_args()

    package = args.package or latest_complete_package()
    if package is None:
        print("No complete submission package found", file=sys.stderr)
        return 2
    package = package.resolve()
    issues: list[str] = []

    issues.extend(audit_upload_dir(package_upload_dir(package)))

    for docx in [
        ROOT / "output/doc/natcs_manuscript.docx",
        ROOT / "output/doc/natcs_supplementary.docx",
        package / "02_manuscript_files/doc/natcs_manuscript.docx",
        package / "02_manuscript_files/doc/natcs_supplementary.docx",
        ROOT / "output/submission_package/natcs_current/01_main_manuscript/main_manuscript.docx",
        ROOT / "output/submission_package/natcs_current/02_supporting_materials/supplementary_information.docx",
    ]:
        if docx.exists():
            issues.extend(audit_docx(docx))

    for pdf in [
        ROOT / "output/pdf/natcs_manuscript.pdf",
        ROOT / "output/pdf/natcs_supplementary.pdf",
        ROOT / "output/submission_package/natcs_current/01_main_manuscript/main_manuscript.pdf",
        ROOT / "output/submission_package/natcs_current/02_supporting_materials/supplementary_information.pdf",
    ]:
        if pdf.exists():
            issues.extend(audit_pdf_text(pdf))

    for md in [
        ROOT / "tmp/manuscript_build/natcs/main_docx.md",
        ROOT / "tmp/manuscript_build/natcs/main_tex.md",
        ROOT / "tmp/manuscript_build/natcs/supplementary_docx.md",
        ROOT / "tmp/manuscript_build/natcs/supplementary_tex.md",
    ]:
        if md.exists():
            issues.extend(audit_text_file(md))

    if not args.skip_text_tree:
        for root in package_text_roots(package):
            for file in root.rglob("*"):
                if file.is_file():
                    issues.extend(audit_text_file(file))

    if issues:
        print("NatCS submission audit failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print(f"NatCS submission audit passed: {package}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
