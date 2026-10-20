#!/usr/bin/env python3
"""Separate, opt-in step: upload a final .md (brief OR written article) to a Google Drive folder the
user names as ONE styled Google Doc. Shared by every mos-content skill.
Kind is auto-detected: a "Brand/Content Guidelines" heading means a brief; anything else is an article
(no section bars or label column; headings dark bold; first table row = header).
Doc only by default; --with-md also uploads the raw .md (Drive's native Markdown support is
rolling out by account).

Markdown can't hold colour, so the styling lives on the Google Doc:
  slate #DCE3EA section bars · grey #F3F3F3 label column · dark slate #334155 Surfer row
  pink #F4CCCC Featured Snippet row · DM Sans (tables 9pt, body 11pt)
  amber Notes panels · slate "ADD —" headings · dark bold page-copy headings
  solid ● bullets with no gaps · tables fill the line (label 120pt fixed, value stretches; works pageless)

Usage: drive_upload.py <final.md> <drive-folder-id-or-url> [--with-md]
Needs the `gws` CLI (authenticated). Without it the script prints a skip notice and exits 0,
so the calling skill can use the Google Drive connector instead or keep the file local.
"""
import json, re, shutil, subprocess, sys
from pathlib import Path


def gws(*args, body=None, upload=None, mime=None):
    cmd = ["gws", *args]
    if body is not None:
        cmd += ["--json", json.dumps(body)]
    cwd = None
    if upload:  # gws only uploads files under its cwd, so run from the file's folder
        cwd = Path(upload).resolve().parent
        cmd += ["--upload", Path(upload).name] + (["--upload-content-type", mime] if mime else [])
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    out = r.stdout[r.stdout.find("{"):] if "{" in r.stdout else ""
    if r.returncode or '"error"' in out:
        sys.exit(f"gws failed: {' '.join(args[:3])}\n{out[-600:]}{r.stderr[-300:]}")
    return json.loads(out) if out else {}


def rgb(h):
    h = h.lstrip("#")
    return {"color": {"rgbColor": {k: int(h[i:i + 2], 16) / 255 for k, i in (("red", 0), ("green", 2), ("blue", 4))}}}


def ptext(p):
    return "".join(e.get("textRun", {}).get("content", "") for e in p["elements"]).strip()


def walk(content):
    for e in content:
        if "paragraph" in e:
            yield e, content
        elif "table" in e:
            for r in e["table"]["tableRows"]:
                for c in r["tableCells"]:
                    yield from walk(c["content"])


class Doc:
    def __init__(self, id):
        self.id = id

    def get(self):
        return gws("docs", "documents", "get", "--params", json.dumps({"documentId": self.id}))

    def batch(self, reqs):
        for i in range(0, len(reqs), 400):
            gws("docs", "documents", "batchUpdate", "--params", json.dumps({"documentId": self.id}),
                body={"requests": reqs[i:i + 400]})


def style(doc):
    # Pass 1 — deletions (reverse index order): empty table header rows, blank lines between bullets
    body = doc.get()["body"]["content"]
    ops = []
    for e in body:
        if "table" in e and not any(ptext(p["paragraph"]) for c in e["table"]["tableRows"][0]["tableCells"]
                                    for p in c["content"] if "paragraph" in p):
            ops.append((e["startIndex"], {"deleteTableRow": {"tableCellLocation": {
                "tableStartLocation": {"index": e["startIndex"]}, "rowIndex": 0, "columnIndex": 0}}}))
    for e, parent in walk(body):
        p = e["paragraph"]
        if ptext(p) or any("inlineObjectElement" in x for x in p["elements"]):
            continue
        i = parent.index(e)
        isb = lambda x: x is not None and "paragraph" in x and ("bullet" in x["paragraph"] or ptext(x["paragraph"]).startswith("• "))
        if 0 < i < len(parent) - 1 and isb(parent[i - 1]) and isb(parent[i + 1]):
            ops.append((e["startIndex"], {"deleteContentRange": {"range": {"startIndex": e["startIndex"], "endIndex": e["endIndex"]}}}))
    ops.sort(key=lambda o: -o[0])
    if ops:
        doc.batch([o[1] for o in ops])

    # Pass 2 — styling (re-creating bullets drops inline bold, so record bold runs and restore them last)
    body = doc.get()["body"]["content"]
    bold = [(x["startIndex"], x["endIndex"]) for e, _ in walk(body) for x in e["paragraph"]["elements"]
            if x.get("textRun", {}).get("textStyle", {}).get("bold")]
    end = body[-1]["endIndex"]
    is_brief = any(ptext(e["paragraph"]).lower() in ("brand guidelines", "client guidelines", "content guidelines")
                   for e in body if "paragraph" in e)
    R = [{"updateTextStyle": {"range": {"startIndex": 1, "endIndex": end - 1},
                              "textStyle": {"weightedFontFamily": {"fontFamily": "DM Sans"}, "fontSize": {"magnitude": 11, "unit": "PT"}},
                              "fields": "weightedFontFamily,fontSize"}}]
    pt = lambda n: {"magnitude": n, "unit": "PT"}
    border = {"color": rgb("#C9CED6"), "width": pt(0.75), "dashStyle": "SOLID"}
    special = {"surfer": ("#334155", "#FFFFFF"), "featured snippet": ("#F4CCCC", None), "query fan-out": ("#DDF7EC", None)}
    for e in body:
        if "table" not in e:
            continue
        t, s, n = e["table"], e["startIndex"], e["table"]["rows"]
        loc = lambda r, c: {"tableStartLocation": {"index": s}, "rowIndex": r, "columnIndex": c}
        if not is_brief:  # article tables: grey bold header row, columns left to Docs
            R += [{"updateTableCellStyle": {"tableRange": {"tableCellLocation": loc(0, 0), "rowSpan": n, "columnSpan": t["columns"]},
                   "tableCellStyle": {"borderTop": border, "borderBottom": border, "borderLeft": border, "borderRight": border,
                                      "paddingTop": pt(4), "paddingBottom": pt(4), "paddingLeft": pt(6), "paddingRight": pt(6)},
                   "fields": "borderTop,borderBottom,borderLeft,borderRight,paddingTop,paddingBottom,paddingLeft,paddingRight"}},
                  {"updateTableCellStyle": {"tableRange": {"tableCellLocation": loc(0, 0), "rowSpan": 1, "columnSpan": t["columns"]},
                   "tableCellStyle": {"backgroundColor": rgb("#F3F3F3")}, "fields": "backgroundColor"}},
                  {"updateTextStyle": {"range": {"startIndex": s, "endIndex": e["endIndex"]}, "textStyle": {"fontSize": pt(10)}, "fields": "fontSize"}}]
            R += [{"updateTextStyle": {"range": {"startIndex": c["startIndex"], "endIndex": c["endIndex"] - 1}, "textStyle": {"bold": True}, "fields": "bold"}}
                  for c in t["tableRows"][0]["tableCells"] if c["endIndex"] - 1 > c["startIndex"]]
            continue
        R += [{"updateTableColumnProperties": {"tableStartLocation": {"index": s}, "columnIndices": [0],
               "tableColumnProperties": {"widthType": "FIXED_WIDTH", "width": pt(120)}, "fields": "width,widthType"}},
              {"updateTableColumnProperties": {"tableStartLocation": {"index": s}, "columnIndices": [1],
               "tableColumnProperties": {"widthType": "EVENLY_DISTRIBUTED"}, "fields": "widthType"}},
              {"updateTableCellStyle": {"tableRange": {"tableCellLocation": loc(0, 0), "rowSpan": n, "columnSpan": 2},
               "tableCellStyle": {"borderTop": border, "borderBottom": border, "borderLeft": border, "borderRight": border,
                                  "paddingTop": pt(5), "paddingBottom": pt(5), "paddingLeft": pt(7), "paddingRight": pt(7),
                                  "contentAlignment": "TOP"},
               "fields": "borderTop,borderBottom,borderLeft,borderRight,paddingTop,paddingBottom,paddingLeft,paddingRight,contentAlignment"}},
              {"updateTableCellStyle": {"tableRange": {"tableCellLocation": loc(0, 0), "rowSpan": n, "columnSpan": 1},
               "tableCellStyle": {"backgroundColor": rgb("#F3F3F3")}, "fields": "backgroundColor"}},
              {"updateTextStyle": {"range": {"startIndex": s, "endIndex": e["endIndex"]}, "textStyle": {"fontSize": pt(9)}, "fields": "fontSize"}},
              {"updateParagraphStyle": {"range": {"startIndex": s, "endIndex": e["endIndex"]},
               "paragraphStyle": {"lineSpacing": 115, "spaceAbove": pt(0), "spaceBelow": pt(3)}, "fields": "lineSpacing,spaceAbove,spaceBelow"}}]
        for ri, row in enumerate(t["tableRows"]):
            lab = row["tableCells"][0]
            paras = [p for p in lab["content"] if "paragraph" in p]
            for k, x in enumerate(paras):
                if x["endIndex"] - 1 > x["startIndex"]:
                    R.append({"updateTextStyle": {"range": {"startIndex": x["startIndex"], "endIndex": x["endIndex"] - 1},
                              "textStyle": {"bold": k == 0, "foregroundColor": rgb("#1F2328" if k == 0 else "#666666")},
                              "fields": "bold,foregroundColor"}})
            lt = " ".join(ptext(p["paragraph"]) for p in paras).lower()
            for key, (bg, fg) in special.items():
                if lt.startswith(key):
                    R.append({"updateTableCellStyle": {"tableRange": {"tableCellLocation": loc(ri, 0), "rowSpan": 1, "columnSpan": 1},
                              "tableCellStyle": {"backgroundColor": rgb(bg)}, "fields": "backgroundColor"}})
                    if fg:
                        R.append({"updateTextStyle": {"range": {"startIndex": lab["startIndex"], "endIndex": lab["endIndex"]},
                                  "textStyle": {"foregroundColor": rgb(fg)}, "fields": "foregroundColor"}})
    in_copy, notes_on, first_h1 = not is_brief, False, True
    sizes = {"HEADING_1": 17, "HEADING_2": 14, "HEADING_3": 12, "HEADING_4": 11}
    runs, cur = [], None
    for e in body:
        p = e.get("paragraph")
        if not p:
            notes_on, cur = False, None
            continue
        txt, st = ptext(p), p["paragraphStyle"].get("namedStyleType", "")
        rng = {"startIndex": e["startIndex"], "endIndex": e["endIndex"]}
        trng = {"startIndex": e["startIndex"], "endIndex": max(e["startIndex"] + 1, e["endIndex"] - 1)}
        if "bullet" in p:
            if cur and cur[1] == e["startIndex"]:
                cur[1] = e["endIndex"]
            else:
                cur = [e["startIndex"], e["endIndex"]]
                runs.append(cur)
        else:
            cur = None
        if st == "HEADING_1" and first_h1 and txt:
            first_h1 = False
            R.append({"updateTextStyle": {"range": trng, "textStyle": {"bold": True, "fontSize": pt(20), "foregroundColor": rgb("#1F2328")},
                      "fields": "bold,fontSize,foregroundColor"}})
            continue
        if txt.lower() == "page copy + optimisation notes" or (st == "HEADING_2" and not in_copy):
            in_copy = in_copy or txt.lower() == "page copy + optimisation notes"
            R += [{"updateParagraphStyle": {"range": rng, "paragraphStyle": {"shading": {"backgroundColor": rgb("#DCE3EA")},
                   "spaceAbove": pt(18), "spaceBelow": pt(8)}, "fields": "shading,spaceAbove,spaceBelow"}},
                  {"updateTextStyle": {"range": trng, "textStyle": {"bold": True, "fontSize": pt(13), "foregroundColor": rgb("#1F2328")},
                   "fields": "bold,fontSize,foregroundColor"}}]
            notes_on = False
            continue
        if txt.startswith("ADD —"):
            R += [{"updateTextStyle": {"range": trng, "textStyle": {"foregroundColor": rgb("#3B5B7A"), "bold": True}, "fields": "foregroundColor,bold"}},
                  {"updateParagraphStyle": {"range": rng, "paragraphStyle": {"borderLeft": {"color": rgb("#DCE3EA"), "width": pt(3),
                   "padding": pt(6), "dashStyle": "SOLID"}}, "fields": "borderLeft"}}]
            notes_on = False
            continue
        if st in sizes:
            notes_on = False
            if in_copy:
                R += [{"updateTextStyle": {"range": trng, "textStyle": {"bold": True, "foregroundColor": rgb("#1F2328"), "fontSize": pt(sizes[st])},
                       "fields": "bold,foregroundColor,fontSize"}},
                      {"updateParagraphStyle": {"range": rng, "paragraphStyle": {"spaceAbove": pt(16), "spaceBelow": pt(6)}, "fields": "spaceAbove,spaceBelow"}}]
            continue
        if txt == "Notes":
            notes_on = True
            R.append({"updateTextStyle": {"range": trng, "textStyle": {"bold": True, "fontSize": pt(9), "foregroundColor": rgb("#8A5A00")},
                      "fields": "bold,fontSize,foregroundColor"}})
        elif notes_on and txt and "bullet" not in p:
            notes_on = False
        if notes_on:
            R.append({"updateParagraphStyle": {"range": rng, "paragraphStyle": {"shading": {"backgroundColor": rgb("#FFF4D6")},
                      "spaceAbove": pt(0), "spaceBelow": pt(0)}, "fields": "shading,spaceAbove,spaceBelow"}})
            if txt and txt != "Notes":
                R.append({"updateTextStyle": {"range": trng, "textStyle": {"fontSize": pt(10), "foregroundColor": rgb("#3D2E00")},
                          "fields": "fontSize,foregroundColor"}})
    for s, en in runs:
        R += [{"createParagraphBullets": {"range": {"startIndex": s, "endIndex": en}, "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"}},
              {"updateParagraphStyle": {"range": {"startIndex": s, "endIndex": en},
               "paragraphStyle": {"spaceAbove": pt(0), "spaceBelow": pt(0), "lineSpacing": 115}, "fields": "spaceAbove,spaceBelow,lineSpacing"}}]
    R += [{"updateTextStyle": {"range": {"startIndex": a, "endIndex": b}, "textStyle": {"bold": True}, "fields": "bold"}}
          for a, b in bold if b > a]
    doc.batch(R)


def main():
    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__)
        return
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__)
    if shutil.which("gws") is None:
        print("skipped: the gws CLI is not installed. Upload with the Google Drive connector "
              "instead, or keep the file local.")
        return
    md, folder = Path(args[0]), args[1]
    folder = re.search(r"folders/([\w-]+)", folder).group(1) if "folders/" in folder else folder
    fields = json.dumps({"supportsAllDrives": True, "fields": "id,webViewLink"})
    if "--with-md" in sys.argv:
        f = gws("drive", "files", "create", "--params", fields, body={"name": md.name, "parents": [folder], "mimeType": "text/markdown"},
                upload=md, mime="text/markdown")
        print("md:  ", f["webViewLink"])
    g = gws("drive", "files", "create", "--params", fields,
            body={"name": md.stem, "parents": [folder], "mimeType": "application/vnd.google-apps.document"}, upload=md, mime="text/markdown")
    style(Doc(g["id"]))
    print("doc: ", g["webViewLink"])


if __name__ == "__main__":
    main()
