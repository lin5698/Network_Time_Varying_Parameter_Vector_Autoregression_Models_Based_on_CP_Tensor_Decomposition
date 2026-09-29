#!/usr/bin/env python3
"""Generate Fig.2 contact-sheet PNGs for the submission materials package."""
import os, sys
from PIL import Image, ImageDraw

def contact_sheet(src, dst, label):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    im = Image.open(src).convert("RGB")
    im.thumbnail((1200, 900))
    bar = 56
    sheet = Image.new("RGB", (im.width, im.height + bar), "white")
    sheet.paste(im, (0, bar))
    d = ImageDraw.Draw(sheet)
    d.rectangle([0, 0, im.width, bar], fill=(24, 24, 24))
    d.text((12, 18), label, fill="white")
    sheet.save(dst, "PNG")
    print("wrote", dst)

if __name__ == "__main__":
    src = sys.argv[1]
    out_dir = sys.argv[2]
    contact_sheet(src, f"{out_dir}/fig2_panel_a_contact_sheet.png",
                  "Fig. 2 panel-a contact sheet - query certificate rendering")
    contact_sheet(src, f"{out_dir}/fig2_portal_surrogate_contact_sheet.png",
                  "Fig. 2 portal surrogate contact sheet - portal preview proxy")
