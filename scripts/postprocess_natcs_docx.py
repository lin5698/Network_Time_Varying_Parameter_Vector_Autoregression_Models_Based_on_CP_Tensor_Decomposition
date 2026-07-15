from __future__ import annotations

import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
CP_NS = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
VT_NS = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
EP_NS = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
CORE_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"
DCTERMS_NS = "http://purl.org/dc/terms/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"
XML_NS = {"w": W_NS}
ET.register_namespace("w", W_NS)
ET.register_namespace("r", R_NS)
ET.register_namespace("", CP_NS)
ET.register_namespace("vt", VT_NS)
ET.register_namespace("cp", CORE_NS)
ET.register_namespace("dc", DC_NS)
ET.register_namespace("dcterms", DCTERMS_NS)
ET.register_namespace("xsi", XSI_NS)
ET.register_namespace("a", A_NS)
ET.register_namespace("wp", WP_NS)
ET.register_namespace("pic", PIC_NS)

BODY_FONT = "Latin Modern Roman"
MONO_FONT = "Latin Modern Mono"
FIRST_LINE_TWIPS = "440"
CENTERED_PREFIXES = (
    "Measuring topology-dependent propagation in evolving networks",
    "When reconstructed network models retain topology-dependent responses",
    "Yilin Wu",
    "Overseas Education College",
    "Correspondence should be addressed",
)
NO_INDENT_STYLES = {
    "Title",
    "Subtitle",
    "Author",
    "Date",
    "Heading 1",
    "Heading 2",
    "Heading 3",
    "Heading 4",
    "Caption",
    "Image Caption",
    "Table Caption",
    "Abstract",
    "Bibliography",
}
STYLE_SPECS = {
    "Normal": {"size": "22", "font": "Times New Roman", "after": "120", "line": "360", "color": "000000"},
    "BodyText": {"size": "22", "font": "Times New Roman", "after": "120", "line": "360", "first": FIRST_LINE_TWIPS, "color": "000000"},
    "FirstParagraph": {"size": "22", "font": "Times New Roman", "after": "120", "line": "360", "first": FIRST_LINE_TWIPS, "color": "000000"},
    "Title": {"size": "30", "font": "Times New Roman", "before": "620", "after": "300", "line": "300", "align": "center", "bold": False, "color": "000000"},
    "Author": {"size": "22", "font": "Times New Roman", "after": "220", "line": "276", "align": "center", "bold": False, "color": "000000"},
    "Heading1": {"size": "28", "font": "Times New Roman", "before": "300", "after": "120", "line": "300", "bold": True, "color": "000000"},
    "Heading2": {"size": "24", "font": "Times New Roman", "before": "220", "after": "100", "line": "276", "bold": True, "color": "000000"},
    "Heading3": {"size": "22", "font": "Times New Roman", "before": "180", "after": "80", "line": "276", "bold": True, "color": "000000"},
    "Caption": {"size": "20", "font": "Times New Roman", "before": "80", "after": "140", "line": "252", "italic": False, "color": "000000"},
    "ImageCaption": {"size": "20", "font": "Times New Roman", "before": "80", "after": "140", "line": "252", "italic": False, "color": "000000"},
    "TableCaption": {"size": "20", "font": "Times New Roman", "before": "80", "after": "140", "line": "252", "italic": False, "color": "000000"},
    "Bibliography": {"size": "20", "font": "Times New Roman", "after": "80", "line": "240", "first": "0", "left": "360", "hanging": "360", "color": "000000"},
    "Table": {"size": "18", "font": "Times New Roman", "before": "0", "after": "40", "line": "220", "first": "0", "color": "000000"},
    "SourceCode": {"size": "20", "font": "Courier New", "color": "000000"},
    "VerbatimChar": {"size": "20", "font": "Courier New", "color": "000000"},
}


def qn(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def rn(tag: str) -> str:
    return f"{{{R_NS}}}{tag}"


def serialize(root: ET.Element, default_ns: str | None = None) -> bytes:
    if default_ns:
        ET.register_namespace("", default_ns)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def load_style_names(styles_xml: bytes) -> dict[str, str]:
    root = ET.fromstring(styles_xml)
    mapping: dict[str, str] = {}
    for style in root.findall("w:style", XML_NS):
        style_id = style.get(qn("styleId"))
        name_node = style.find("w:name", XML_NS)
        if style_id and name_node is not None:
            mapping[style_id] = name_node.get(qn("val"), "")
    return mapping


def paragraph_text(node: ET.Element) -> str:
    return "".join(t.text or "" for t in node.findall(".//w:t", XML_NS)).strip()


def replace_paragraph_text_with_tab(paragraph: ET.Element, left: str, right: str) -> None:
    ppr = paragraph.find("w:pPr", XML_NS)
    for child in list(paragraph):
        if child is not ppr:
            paragraph.remove(child)
    left_run = ET.SubElement(paragraph, qn("r"))
    ET.SubElement(left_run, qn("t")).text = left
    tab_run = ET.SubElement(paragraph, qn("r"))
    ET.SubElement(tab_run, qn("tab"))
    right_run = ET.SubElement(paragraph, qn("r"))
    ET.SubElement(right_run, qn("t")).text = right


def clear_paragraph_text(paragraph: ET.Element) -> None:
    ppr = paragraph.find("w:pPr", XML_NS)
    for child in list(paragraph):
        if child is not ppr:
            paragraph.remove(child)


def prepend_paragraph_text(paragraph: ET.Element, prefix: str) -> None:
    first_text = paragraph.find(".//w:t", XML_NS)
    if first_text is None:
        run = ET.SubElement(paragraph, qn("r"))
        set_run_props(ensure_run_props(run), STYLE_SPECS["Caption"])
        first_text = ET.SubElement(run, qn("t"))
        first_text.text = prefix.strip()
        return
    first_text.text = f"{prefix}{first_text.text or ''}"


def ensure_child(parent: ET.Element, tag: str) -> ET.Element:
    child = parent.find(f"w:{tag}", XML_NS)
    if child is None:
        child = ET.SubElement(parent, qn(tag))
    return child


def ensure_run_props(run: ET.Element) -> ET.Element:
    rpr = run.find("w:rPr", XML_NS)
    if rpr is None:
        rpr = ET.Element(qn("rPr"))
        run.insert(0, rpr)
    return rpr


def set_bool(parent: ET.Element, tag: str, enabled: bool) -> None:
    node = parent.find(f"w:{tag}", XML_NS)
    if enabled:
        if node is None:
            ET.SubElement(parent, qn(tag))
    elif node is not None:
        parent.remove(node)


def enable_para_flag(ppr: ET.Element, tag: str) -> None:
    if ppr.find(f"w:{tag}", XML_NS) is None:
        ET.SubElement(ppr, qn(tag))


def set_black(parent: ET.Element) -> None:
    color = ensure_child(parent, "color")
    color.attrib.clear()
    color.set(qn("val"), "000000")


def remove_visual_hyperlink_marks(rpr: ET.Element) -> None:
    for node in list(rpr.findall("w:u", XML_NS)):
        rpr.remove(node)


def set_run_props(rpr: ET.Element, spec: dict[str, str | bool]) -> None:
    font = spec.get("font")
    if font:
        if font == "Times New Roman":
            font = BODY_FONT
        elif font == "Courier New":
            font = MONO_FONT
        fonts = ensure_child(rpr, "rFonts")
        for key in ("ascii", "hAnsi", "cs", "eastAsia"):
            fonts.set(qn(key), str(font))
    size = spec.get("size")
    if size:
        sz = ensure_child(rpr, "sz")
        sz.set(qn("val"), str(size))
        szcs = ensure_child(rpr, "szCs")
        szcs.set(qn("val"), str(size))
    if "bold" in spec:
        set_bool(rpr, "b", bool(spec["bold"]))
        set_bool(rpr, "bCs", bool(spec["bold"]))
    if "italic" in spec:
        set_bool(rpr, "i", bool(spec["italic"]))
        set_bool(rpr, "iCs", bool(spec["italic"]))
    set_black(rpr)


def set_para_props(ppr: ET.Element, spec: dict[str, str | bool]) -> None:
    if any(key in spec for key in ("before", "after", "line")):
        spacing = ensure_child(ppr, "spacing")
        if "before" in spec:
            spacing.set(qn("before"), str(spec["before"]))
        if "after" in spec:
            spacing.set(qn("after"), str(spec["after"]))
        if "line" in spec:
            spacing.set(qn("line"), str(spec["line"]))
            spacing.set(qn("lineRule"), "auto")
    if any(key in spec for key in ("first", "left", "hanging")):
        ind = ensure_child(ppr, "ind")
        if "first" in spec:
            ind.set(qn("firstLine"), str(spec["first"]))
        if "left" in spec:
            ind.set(qn("left"), str(spec["left"]))
        if "hanging" in spec:
            ind.set(qn("hanging"), str(spec["hanging"]))
    if "align" in spec:
        jc = ensure_child(ppr, "jc")
        jc.set(qn("val"), str(spec["align"]))


def apply_direct_style(paragraph: ET.Element, spec: dict[str, str | bool]) -> None:
    ppr = ensure_child(paragraph, "pPr")
    set_para_props(ppr, spec)
    for run in paragraph.findall(".//w:r", XML_NS):
        set_run_props(ensure_run_props(run), spec)


def table_column_widths(column_count: int) -> list[int]:
    if column_count <= 0:
        return []
    if column_count == 5:
        return [3600, 1200, 900, 1500, 1500]
    if column_count == 4:
        return [2800, 2800, 1500, 1500]
    if column_count == 3:
        return [3400, 3400, 2200]
    if column_count == 2:
        return [4600, 4600]
    total = 9200
    first = min(3000, total // 2)
    remaining = total - first
    each = remaining // (column_count - 1)
    return [first] + [each] * (column_count - 1)


def table_cell_text(cell: ET.Element) -> str:
    return " ".join(
        "".join(t.text or "" for t in paragraph.findall(".//w:t", XML_NS)).strip()
        for paragraph in cell.findall(".//w:p", XML_NS)
    ).strip()


def benchmark_table_widths(table: ET.Element, column_count: int) -> list[int] | None:
    rows = table.findall("w:tr", XML_NS)
    if not rows:
        return None
    headers = [table_cell_text(cell) for cell in rows[0].findall("w:tc", XML_NS)]
    if headers == ["S", "Scenario", "M", "Method"]:
        return [900, 3900, 900, 3500]
    if headers == ["S", "M", "Eff. op.", "GIRF", "Pred"]:
        return [900, 900, 3300, 2050, 2050]
    if headers == ["S", "M", "Raw pair", "Net comp.", "Frozen"]:
        return [900, 900, 2800, 2300, 2300]
    if headers == ["S", "M", "Run s", "Mem MB"]:
        return [900, 900, 1500, 5900]
    if headers == ["S", "M", "Unst. %", "Fail %"]:
        return [1000, 1000, 3600, 3600]
    if len(headers) != column_count:
        return None
    return None


def patch_tables(root: ET.Element) -> None:
    for table in root.findall(".//w:tbl", XML_NS):
        rows = table.findall("w:tr", XML_NS)
        column_count = max((len(row.findall("w:tc", XML_NS)) for row in rows), default=0)
        widths = benchmark_table_widths(table, column_count) or table_column_widths(column_count)
        if not widths:
            continue

        tbl_pr = ensure_child(table, "tblPr")
        tbl_w = ensure_child(tbl_pr, "tblW")
        tbl_w.set(qn("type"), "pct")
        tbl_w.set(qn("w"), "5000")
        layout = ensure_child(tbl_pr, "tblLayout")
        layout.set(qn("type"), "fixed")

        old_grid = table.find("w:tblGrid", XML_NS)
        if old_grid is not None:
            table.remove(old_grid)
        grid = ET.Element(qn("tblGrid"))
        insert_at = list(table).index(tbl_pr) + 1 if tbl_pr in list(table) else 0
        table.insert(insert_at, grid)
        for width in widths:
            col = ET.SubElement(grid, qn("gridCol"))
            col.set(qn("w"), str(width))

        for row in rows:
            cells = row.findall("w:tc", XML_NS)
            for idx, cell in enumerate(cells):
                width = widths[min(idx, len(widths) - 1)]
                tc_pr = ensure_child(cell, "tcPr")
                tc_w = ensure_child(tc_pr, "tcW")
                tc_w.set(qn("type"), "dxa")
                tc_w.set(qn("w"), str(width))
                ensure_child(tc_pr, "noWrap")


def patch_styles_xml(styles_xml: bytes) -> bytes:
    root = ET.fromstring(styles_xml)

    defaults = root.find("w:docDefaults", XML_NS)
    if defaults is not None:
        rpr_default = defaults.find("w:rPrDefault/w:rPr", XML_NS)
        if rpr_default is not None:
            set_run_props(rpr_default, STYLE_SPECS["Normal"])
        ppr_default = defaults.find("w:pPrDefault/w:pPr", XML_NS)
        if ppr_default is not None:
            set_para_props(ppr_default, STYLE_SPECS["Normal"])

    for style in root.findall("w:style", XML_NS):
        style_id = style.get(qn("styleId"))
        spec = STYLE_SPECS.get(style_id or "", {"color": "000000"})
        if style.get(qn("type")) in ("paragraph", "table"):
            ppr = ensure_child(style, "pPr")
            set_para_props(ppr, spec)
        rpr = ensure_child(style, "rPr")
        set_run_props(rpr, spec)
        if style_id == "Hyperlink":
            remove_visual_hyperlink_marks(rpr)

    for color in root.findall(".//w:color", XML_NS):
        color.attrib.clear()
        color.set(qn("val"), "000000")

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def force_document_text_black(root: ET.Element) -> None:
    for rpr in root.findall(".//w:rPr", XML_NS):
        set_black(rpr)
    for run in root.findall(".//w:r", XML_NS):
        set_black(ensure_run_props(run))
    for hyperlink_run in root.findall(".//w:hyperlink/w:r", XML_NS):
        rpr = ensure_run_props(hyperlink_run)
        set_black(rpr)
        remove_visual_hyperlink_marks(rpr)


def sanitize_drawing_metadata(root: ET.Element) -> None:
    for node in root.iter():
        if node.tag in {f"{{{WP_NS}}}docPr", f"{{{PIC_NS}}}cNvPr"}:
            descr = node.get("descr", "")
            if "/" in descr or "\\" in descr or descr.lower().endswith((".png", ".pdf", ".jpg", ".jpeg", ".tif", ".tiff", ".svg")):
                node.set("descr", "Figure image")
            if node.get("title") is None:
                node.set("title", "")


def patch_word_xml(xml: bytes) -> bytes:
    root = ET.fromstring(xml)
    force_document_text_black(root)
    sanitize_drawing_metadata(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def patch_document_xml(document_xml: bytes, styles_xml: bytes, figure_caption_prefix: str = "Figure") -> bytes:
    style_names = load_style_names(styles_xml)
    root = ET.fromstring(document_xml)
    body = root.find("w:body", XML_NS)
    figure_index = 0
    table_paragraphs = {
        id(paragraph)
        for table in root.findall(".//w:tbl", XML_NS)
        for paragraph in table.findall(".//w:p", XML_NS)
    }

    for paragraph in root.findall(".//w:p", XML_NS):
        text = paragraph_text(paragraph)
        if not text:
            continue

        ppr = ensure_child(paragraph, "pPr")
        pstyle = ppr.find("w:pStyle", XML_NS)
        style_id = pstyle.get(qn("val")) if pstyle is not None else ""
        style_name = style_names.get(style_id, style_id)
        normalized_style = style_name.lower()
        if style_id == "ImageCaption" or style_name == "Image Caption":
            if not text.startswith(("Figure ", "Supplementary Figure ")):
                figure_index += 1
                prepend_paragraph_text(paragraph, f"{figure_caption_prefix} {figure_index}: ")
                text = paragraph_text(paragraph)
        ind = ensure_child(ppr, "ind")
        if id(paragraph) in table_paragraphs:
            apply_direct_style(paragraph, STYLE_SPECS["Table"])
        elif style_id in STYLE_SPECS:
            apply_direct_style(paragraph, STYLE_SPECS[style_id])
        elif style_name in STYLE_SPECS:
            apply_direct_style(paragraph, STYLE_SPECS[style_name])
        else:
            apply_direct_style(paragraph, STYLE_SPECS["Normal"])

        if style_name in NO_INDENT_STYLES or normalized_style.startswith("heading"):
            ind.set(qn("firstLine"), "0")
        else:
            ind.set(qn("firstLine"), FIRST_LINE_TWIPS)

        if any(text.startswith(prefix) for prefix in CENTERED_PREFIXES):
            ind.set(qn("firstLine"), "0")
            jc = ensure_child(ppr, "jc")
            jc.set(qn("val"), "center")
        if style_name == "Bibliography":
            ind.set(qn("firstLine"), "0")
            ind.set(qn("left"), "360")
            ind.set(qn("hanging"), "360")

        if text.startswith("Table 1 | Benchmark evidence"):
            enable_para_flag(ppr, "pageBreakBefore")
            enable_para_flag(ppr, "keepNext")

        if text.startswith("Table 2 | RCEP"):
            enable_para_flag(ppr, "pageBreakBefore")
            enable_para_flag(ppr, "keepNext")

    force_document_text_black(root)
    sanitize_drawing_metadata(root)
    patch_tables(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def page_number_footer_xml() -> bytes:
    root = ET.Element(qn("ftr"))
    paragraph = ET.SubElement(root, qn("p"))
    ppr = ET.SubElement(paragraph, qn("pPr"))
    ET.SubElement(ppr, qn("jc")).set(qn("val"), "center")
    for tag, value in (
        ("begin", None),
        ("instr", " PAGE "),
        ("separate", None),
        ("text", "1"),
        ("end", None),
    ):
        run = ET.SubElement(paragraph, qn("r"))
        set_run_props(ensure_run_props(run), {"font": "Times New Roman", "size": "20", "color": "000000"})
        if tag == "instr":
            node = ET.SubElement(run, qn("instrText"))
            node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            node.text = value
        elif tag == "text":
            ET.SubElement(run, qn("t")).text = value
        else:
            node = ET.SubElement(run, qn("fldChar"))
            node.set(qn("fldCharType"), tag)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def patch_document_relationships(rels_xml: bytes) -> tuple[bytes, str, str]:
    root = ET.fromstring(rels_xml)
    for rel in list(root.findall(f"{{{REL_NS}}}Relationship")):
        target = rel.get("Target", "")
        rel_type = rel.get("Type", "")
        if target == "comments.xml" or rel_type.endswith("/comments"):
            root.remove(rel)
    existing_targets = {
        rel.get("Target"): rel.get("Id")
        for rel in root.findall(f"{{{REL_NS}}}Relationship")
    }
    if "footer1.xml" in existing_targets:
        return serialize(root, REL_NS), str(existing_targets["footer1.xml"]), "footer1.xml"
    used = {rel.get("Id") for rel in root.findall(f"{{{REL_NS}}}Relationship")}
    idx = 1
    while f"rId{idx}" in used:
        idx += 1
    rid = f"rId{idx}"
    rel = ET.SubElement(root, f"{{{REL_NS}}}Relationship")
    rel.set("Id", rid)
    rel.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer")
    rel.set("Target", "footer1.xml")
    return serialize(root, REL_NS), rid, "footer1.xml"


def patch_content_types(content_types_xml: bytes) -> bytes:
    root = ET.fromstring(content_types_xml)
    for node in list(root.findall(f"{{{CT_NS}}}Override")):
        if node.get("PartName") in {"/word/comments.xml", "/docProps/custom.xml"}:
            root.remove(node)
    for node in root.findall(f"{{{CT_NS}}}Override"):
        if node.get("PartName") == "/word/footer1.xml":
            return serialize(root, CT_NS)
    override = ET.SubElement(root, f"{{{CT_NS}}}Override")
    override.set("PartName", "/word/footer1.xml")
    override.set("ContentType", "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml")
    return serialize(root, CT_NS)


def attach_footer_reference(document_xml: bytes, footer_rid: str) -> bytes:
    root = ET.fromstring(document_xml)
    sect_pr = root.find(".//w:sectPr", XML_NS)
    if sect_pr is None:
        body = root.find("w:body", XML_NS)
        if body is None:
            return document_xml
        sect_pr = ET.SubElement(body, qn("sectPr"))
    for node in list(sect_pr.findall("w:footerReference", XML_NS)):
        if node.get(qn("type")) == "default":
            sect_pr.remove(node)
    footer_ref = ET.Element(qn("footerReference"))
    footer_ref.set(qn("type"), "default")
    footer_ref.set(rn("id"), footer_rid)
    sect_pr.insert(0, footer_ref)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def sanitize_custom_properties(custom_xml: bytes) -> bytes:
    root = ET.Element(f"{{{CP_NS}}}Properties")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def patch_package_relationships(rels_xml: bytes) -> bytes:
    root = ET.fromstring(rels_xml)
    for rel in list(root.findall(f"{{{REL_NS}}}Relationship")):
        target = rel.get("Target", "")
        rel_type = rel.get("Type", "")
        if target == "docProps/custom.xml" or rel_type.endswith("/custom-properties"):
            root.remove(rel)
    return serialize(root, REL_NS)


def sanitize_app_properties(app_xml: bytes) -> bytes:
    root = ET.fromstring(app_xml)
    for tag in ("TotalTime", "Template", "Manager", "Company"):
        node = root.find(f"{{{EP_NS}}}{tag}")
        if node is not None:
            node.text = "0" if tag == "TotalTime" else ""
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def sanitize_core_properties(core_xml: bytes) -> bytes:
    root = ET.fromstring(core_xml)
    text_fields = (
        (DC_NS, "title"),
        (DC_NS, "subject"),
        (DC_NS, "creator"),
        (DC_NS, "description"),
        (CP_NS, "keywords"),
        (CP_NS, "lastModifiedBy"),
        (CP_NS, "revision"),
        (CP_NS, "category"),
        (CP_NS, "contentStatus"),
    )
    for ns, tag in text_fields:
        node = root.find(f"{{{ns}}}{tag}")
        if node is not None:
            node.text = "1" if tag == "revision" else ""
    for tag in ("created", "modified"):
        node = root.find(f"{{{DCTERMS_NS}}}{tag}")
        if node is not None:
            node.text = "2000-01-01T00:00:00Z"
            node.set(f"{{{XSI_NS}}}type", "dcterms:W3CDTF")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def patch_docx(path: Path) -> None:
    with zipfile.ZipFile(path, "r") as zin:
        styles_xml = zin.read("word/styles.xml")
        document_xml = zin.read("word/document.xml")
        rels_xml = zin.read("word/_rels/document.xml.rels")
        content_types_xml = zin.read("[Content_Types].xml")
        patched_package_rels = (
            patch_package_relationships(zin.read("_rels/.rels"))
            if "_rels/.rels" in zin.namelist()
            else None
        )
        patched_rels, footer_rid, footer_name = patch_document_relationships(rels_xml)
        patched_styles = patch_styles_xml(styles_xml)
        figure_caption_prefix = "Supplementary Figure" if "supplementary" in path.name.lower() else "Figure"
        patched_document = attach_footer_reference(
            patch_document_xml(document_xml, styles_xml, figure_caption_prefix),
            footer_rid,
        )
        patched_content_types = patch_content_types(content_types_xml)
        patched_footer = page_number_footer_xml()
        patched_app = (
            sanitize_app_properties(zin.read("docProps/app.xml"))
            if "docProps/app.xml" in zin.namelist()
            else None
        )
        patched_core = (
            sanitize_core_properties(zin.read("docProps/core.xml"))
            if "docProps/core.xml" in zin.namelist()
            else None
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx", dir=path.parent) as tmp:
            tmp_path = Path(tmp.name)

        try:
            with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
                for info in zin.infolist():
                    if info.filename == "word/comments.xml":
                        continue
                    if info.filename == "docProps/custom.xml":
                        continue
                    if info.filename == "word/document.xml":
                        data = patched_document
                    elif info.filename == "word/styles.xml":
                        data = patched_styles
                    elif info.filename == "word/_rels/document.xml.rels":
                        data = patched_rels
                    elif info.filename == "_rels/.rels" and patched_package_rels is not None:
                        data = patched_package_rels
                    elif info.filename == "[Content_Types].xml":
                        data = patched_content_types
                    elif info.filename == f"word/{footer_name}":
                        data = patched_footer
                    elif info.filename == "docProps/app.xml" and patched_app is not None:
                        data = patched_app
                    elif info.filename == "docProps/core.xml" and patched_core is not None:
                        data = patched_core
                    elif info.filename.startswith("word/") and info.filename.endswith(".xml"):
                        data = patch_word_xml(zin.read(info.filename))
                    else:
                        data = zin.read(info.filename)
                    zout.writestr(info, data)
                if f"word/{footer_name}" not in zin.namelist():
                    zout.writestr(f"word/{footer_name}", patched_footer)
            tmp_path.replace(path)
        finally:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        raise SystemExit("usage: python3 scripts/postprocess_natcs_docx.py <docx> [<docx> ...]")
    for arg in argv[1:]:
        patch_docx(Path(arg))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
