"""Minimal HTML table reader (standard library): expands rowspan/colspan into a full grid."""
import html as _html
import re
from html.parser import HTMLParser


class Cell:
    def __init__(self):
        self.parts, self.links = [], []

    @property
    def text(self):
        s = _html.unescape("".join(self.parts)).replace("\xa0", " ")
        return re.sub(r"\s+", " ", s).strip()


class _Tables(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.tables, self._stack = [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self._stack.append({"rows": [], "row": None, "cell": None})
        elif not self._stack:
            return
        t = self._stack[-1] if self._stack else None
        if tag == "tr":
            t["row"] = []
            t["rows"].append(t["row"])
        elif tag in ("td", "th") and t["row"] is not None:
            c = Cell()
            c.rowspan, c.colspan, c.header = int(a.get("rowspan") or 1), int(a.get("colspan") or 1), tag == "th"
            t["cell"] = c
            t["row"].append(c)
        elif tag == "a" and t["cell"] is not None:
            t["cell"]._href = a.get("href", "")
            t["cell"]._atext = []
        elif tag in ("br", "li") and t["cell"] is not None:
            t["cell"].parts.append(" ")

    def handle_endtag(self, tag):
        if not self._stack:
            return
        t = self._stack[-1]
        if tag == "a" and t["cell"] is not None and hasattr(t["cell"], "_href"):
            c = t["cell"]
            c.links.append((re.sub(r"\s+", " ", "".join(c._atext)).strip(), c._href))
            del c._href
        elif tag in ("td", "th"):
            t["cell"] = None
        elif tag == "table":
            self.tables.append(self._stack.pop()["rows"])

    def handle_data(self, data):
        if self._stack and self._stack[-1]["cell"] is not None:
            c = self._stack[-1]["cell"]
            c.parts.append(data)
            if hasattr(c, "_href"):
                c._atext.append(data)

    def handle_entityref(self, name):
        self.handle_data(f"&{name};")

    def handle_charref(self, name):
        self.handle_data(f"&#{name};")


def tables(fragment):
    """Return every table in `fragment` as (header_texts, rows); rows are lists of Cell with spans expanded."""
    p = _Tables()
    p.feed(fragment)
    out = []
    for raw in p.tables:
        grid, pending = [], {}          # pending: col -> (cell, rows left)
        for r in raw:
            row, cells, col = [], list(r), 0
            while cells or any(k >= col for k in pending):
                if col in pending:
                    c, left = pending[col]
                    row.append(c)
                    if left > 1:
                        pending[col] = (c, left - 1)
                    else:
                        del pending[col]
                    col += 1
                    continue
                if not cells:
                    break
                c = cells.pop(0)
                for _ in range(c.colspan):
                    row.append(c)
                    if c.rowspan > 1:
                        pending[col] = (c, c.rowspan - 1)
                    col += 1
            grid.append(row)
        head = [c.text for c in grid[0]] if grid and all(c.header for c in grid[0]) else []
        out.append((head, grid[1:] if head else grid))
    return out
