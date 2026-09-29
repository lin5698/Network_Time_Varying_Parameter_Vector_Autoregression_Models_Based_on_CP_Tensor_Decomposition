from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "output" / "natcs_fig2_portal_surrogate"
STANDALONE = ROOT / "output" / "natcs_evidence" / "fig_validation_recovery.png"
MANUSCRIPT_PDF = ROOT / "output" / "pdf" / "natcs_manuscript.pdf"
FIG2_CAPTION = "Query availability is necessary but does not ensure recovery"
STANDALONE_PANEL_A_CROP = (54, 70, 1212, 222)
EMBEDDED_PANEL_A_CROP = (215, 160, 1065, 315)


def require_releaseable_fig2_preview() -> None:
    """Refuse stale portal-preview packaging before it can touch preview files."""
    audits = {
        "PAPER_CLAIM_AUDIT": ROOT / "PAPER_CLAIM_AUDIT.json",
        "EMPIRICAL_IMPLEMENTATION_AUDIT": ROOT / "EMPIRICAL_IMPLEMENTATION_AUDIT.json",
    }
    inactive_sources = {
        "RCEP empirical source": (
            ROOT / "manuscript_src" / "natcs" / "results_rcep.md",
            re.compile(r"^#\\s*Inactive audit-boundary draft:\\s*RCEP protocol", re.MULTILINE | re.IGNORECASE),
        ),
        "NYC empirical source": (
            ROOT / "manuscript_src" / "natcs" / "results_generality.md",
            re.compile(r"^#\\s*Inactive audit-boundary draft:\\s*NYC protocol", re.MULTILINE | re.IGNORECASE),
        ),
    }
    failures: list[str] = []

    for label, audit_path in audits.items():
        if not audit_path.exists():
            failures.append(f"{label} is missing")
            continue
        try:
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            failures.append(f"{label} is unreadable ({error})")
            continue
        if audit.get("verdict") != "PASS":
            detail = f" ({audit['reason_code']})" if audit.get("reason_code") else ""
            failures.append(f"{label}={audit.get('verdict', 'missing')}{detail}")

    for label, (source_path, inactive_marker) in inactive_sources.items():
        if not source_path.exists():
            failures.append(f"{label} is missing")
            continue
        if inactive_marker.search(source_path.read_text(encoding="utf-8")):
            failures.append(f"{label} remains explicitly inactive")

    if failures:
        raise RuntimeError(
            "NCS_FIG2_SURROGATE_REFUSED before preview generation: "
            + "; ".join(failures)
            + ". No portal preview, figure-source or submission artifact was generated."
        )


def require_image(path: Path) -> Image.Image:
    if not path.exists():
        raise FileNotFoundError(f"Missing Fig. 2 surrogate source image: {path}")
    return Image.open(path).convert("RGB")


def command_output(args: list[str]) -> str:
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"Command failed ({' '.join(args)}): {detail}")
    return result.stdout


def locate_fig2_page() -> tuple[int, Path]:
    if not MANUSCRIPT_PDF.exists():
        raise FileNotFoundError(f"Missing manuscript PDF for Fig. 2 surrogate: {MANUSCRIPT_PDF}")
    info = command_output(["pdfinfo", str(MANUSCRIPT_PDF)])
    match = re.search(r"^Pages:\s+(\d+)", info, flags=re.MULTILINE)
    if not match:
        raise RuntimeError("Could not determine the manuscript PDF page count for the Fig. 2 surrogate")
    for page_number in range(1, int(match.group(1)) + 1):
        page_text = command_output(["pdftotext", "-f", str(page_number), "-l", str(page_number), str(MANUSCRIPT_PDF), "-"])
        if FIG2_CAPTION in page_text:
            page_path = ROOT / "tmp" / "pdfs" / "natcs_main" / f"page-{page_number:02d}.png"
            if not page_path.exists():
                raise FileNotFoundError(f"Missing rendered Fig. 2 page for surrogate: {page_path}")
            return page_number, page_path
    raise RuntimeError("Could not locate the Fig. 2 caption in the manuscript PDF")


def resize_to_width(image: Image.Image, width: int) -> Image.Image:
    ratio = width / image.width
    height = max(1, round(image.height * ratio))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def crop_box(image: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
    left, upper, right, lower = box
    left = max(0, min(left, image.width - 1))
    upper = max(0, min(upper, image.height - 1))
    right = max(left + 1, min(right, image.width))
    lower = max(upper + 1, min(lower, image.height))
    return image.crop((left, upper, right, lower))


def labelled_tile(image: Image.Image, label: str, tile_width: int = 420) -> Image.Image:
    preview = resize_to_width(image, tile_width)
    font = ImageFont.load_default()
    label_height = 28
    tile = Image.new("RGB", (tile_width, preview.height + label_height), "white")
    draw = ImageDraw.Draw(tile)
    draw.rectangle((0, 0, tile_width, label_height), fill=(245, 245, 245))
    draw.text((8, 8), label, fill=(20, 20, 20), font=font)
    tile.paste(preview, (0, label_height))
    return tile


def make_contact_sheet(items: list[tuple[str, Image.Image]], out_file: Path, tile_width: int = 420) -> None:
    tiles = [labelled_tile(image, label, tile_width=tile_width) for label, image in items]
    gap = 18
    columns = 2
    rows = (len(tiles) + columns - 1) // columns
    tile_width = max(tile.width for tile in tiles)
    row_heights = []
    for row in range(rows):
        row_tiles = tiles[row * columns : (row + 1) * columns]
        row_heights.append(max(tile.height for tile in row_tiles))
    sheet_width = columns * tile_width + (columns + 1) * gap
    sheet_height = sum(row_heights) + (rows + 1) * gap
    sheet = Image.new("RGB", (sheet_width, sheet_height), "white")
    y = gap
    for row in range(rows):
        x = gap
        for tile in tiles[row * columns : (row + 1) * columns]:
            sheet.paste(tile, (x, y))
            x += tile_width + gap
        y += row_heights[row] + gap
    sheet.save(out_file)


def save_preview_set(label: str, image: Image.Image, widths: list[int]) -> list[dict]:
    records = []
    for width in widths:
        preview = resize_to_width(image, width)
        out_file = OUT_DIR / f"{label}_w{width}.png"
        preview.save(out_file)
        records.append(
            {
                "label": label,
                "path": str(out_file.relative_to(ROOT)),
                "width_px": preview.width,
                "height_px": preview.height,
                "source_width_px": image.width,
                "source_height_px": image.height,
                "scale_vs_source": round(preview.width / image.width, 4),
            }
        )
    return records


def main() -> None:
    require_releaseable_fig2_preview()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for pattern in ("*.png", "*.json"):
        for old in OUT_DIR.glob(pattern):
            old.unlink()
    readme_file = OUT_DIR / "README.md"
    if readme_file.exists():
        readme_file.unlink()

    standalone = require_image(STANDALONE)
    embedded_page_number, embedded_page_path = locate_fig2_page()
    embedded_page = require_image(embedded_page_path)
    embedded_page_label = f"{embedded_page_number:02d}"
    standalone_panel_a = crop_box(standalone, STANDALONE_PANEL_A_CROP)
    embedded_panel_a = crop_box(embedded_page, EMBEDDED_PANEL_A_CROP)

    previews = []
    previews.extend(save_preview_set("standalone_fig2", standalone, [1260, 1000, 800, 640]))
    previews.extend(save_preview_set(f"embedded_page{embedded_page_label}", embedded_page, [1275, 1000, 800, 640]))
    previews.extend(save_preview_set("standalone_fig2_panel_a", standalone_panel_a, [1000, 800, 640]))
    previews.extend(save_preview_set(f"embedded_page{embedded_page_label}_panel_a", embedded_panel_a, [850, 700, 560]))

    contact_sheet = OUT_DIR / "fig2_portal_surrogate_contact_sheet.png"
    make_contact_sheet(
        [
            ("standalone Fig. 2, native 1260 px", resize_to_width(standalone, 1260)),
            ("standalone Fig. 2, 800 px", resize_to_width(standalone, 800)),
            (f"embedded page {embedded_page_label}, native 1275 px", resize_to_width(embedded_page, 1275)),
            (f"embedded page {embedded_page_label}, 800 px", resize_to_width(embedded_page, 800)),
        ],
        contact_sheet,
    )
    panel_a_contact_sheet = OUT_DIR / "fig2_panel_a_contact_sheet.png"
    make_contact_sheet(
        [
            ("standalone panel a, 1000 px", resize_to_width(standalone_panel_a, 1000)),
            ("standalone panel a, 640 px", resize_to_width(standalone_panel_a, 640)),
            ("embedded page panel a, 850 px", resize_to_width(embedded_panel_a, 850)),
            ("embedded page panel a, 560 px", resize_to_width(embedded_panel_a, 560)),
        ],
        panel_a_contact_sheet,
        tile_width=650,
    )

    summary = {
        "purpose": "Local surrogate previews for Fig. 2 portal-readability risk. This does not replace journal portal preview.",
        "boundary": "Generated from local PNG exports after the manuscript build; it cannot prove journal portal rendering.",
        "sources": {
            "standalone_fig2_png": str(STANDALONE.relative_to(ROOT)),
            "embedded_manuscript_page_number": embedded_page_number,
            "embedded_manuscript_page_png": str(embedded_page_path.relative_to(ROOT)),
        },
        "contact_sheet": str(contact_sheet.relative_to(ROOT)),
        "panel_a_contact_sheet": str(panel_a_contact_sheet.relative_to(ROOT)),
        "panel_a_crops": {
            "standalone_fig2_panel_a": {
                "source": str(STANDALONE.relative_to(ROOT)),
                "crop_box_px": STANDALONE_PANEL_A_CROP,
            },
            "embedded_manuscript_page_panel_a": {
                "source": str(embedded_page_path.relative_to(ROOT)),
                "crop_box_px": EMBEDDED_PANEL_A_CROP,
            },
        },
        "previews": previews,
        "decision_rule": [
            "Keep the current Fig. 2 if the portal preserves standalone PDF/SVG inspection or makes panel a readable at first view.",
            "Redesign Fig. 2 if the portal rasterizes the embedded figure at low resolution and blocks comfortable standalone inspection.",
        ],
    }
    (OUT_DIR / "fig2_portal_surrogate_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    readme_file.write_text(
        "\n".join(
            [
                "# Fig. 2 Portal Surrogate Preview",
                "",
                "This folder contains local low-width previews of standalone Fig. 2 and the embedded manuscript page that contains Fig. 2.",
                "",
                "Boundary: these images do not close the journal-portal preview gate. They only document local compression stress before upload.",
                "",
                f"- Contact sheet: `{summary['contact_sheet']}`",
                f"- Panel-a contact sheet: `{summary['panel_a_contact_sheet']}`",
                "- Summary JSON: `output/natcs_fig2_portal_surrogate/fig2_portal_surrogate_summary.json`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"out_dir": str(OUT_DIR.relative_to(ROOT)), "contact_sheet": summary["contact_sheet"]}, indent=2))


if __name__ == "__main__":
    main()
