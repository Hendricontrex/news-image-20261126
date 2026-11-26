#!/usr/bin/env python3
"""Draw the front page for Thursday 26 November 2026.

The page is a cream broadsheet: a big serif masthead, one full-width LEAD
story with a two-line display headline and a strip of key figures, then the
other four stories in a tight 2x2 grid, and a footer that names the day
again and credits the outlets. Every figure on the page comes from the
STORIES table at the bottom of this file, and every figure there was checked
against a primary outlet on 26 Nov 2026 (Reuters, AP, CNN, Fox Business).
Anything that could not be checked was left out entirely -- nothing on this
page is invented.

The picture is built only from code plus the DejaVu fonts on this machine:
no network, no clock, no random numbers, so running the script twice gives
the same bytes. Run it from anywhere:

    python3 scripts/compose.py

It writes entry.png into the repository root (the parent of scripts/).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CANVAS = 1024
MARGIN = 36
SPAN = CANVAS - 2 * MARGIN  # 952: the width of every full-width element

INK = (24, 24, 22)        # headline black, also the rules
PAPER = (242, 236, 220)   # cream paper
SPECK = (232, 224, 203)   # dot texture on the paper
CARD = (252, 250, 244)    # story panels, near-white
CARD_LINE = (168, 158, 136)  # panel outline, warm grey
TEXT = (58, 56, 50)       # body copy
FAINT = (122, 114, 96)    # kickers that are not the lead, footer sources
HALO = (226, 216, 192)    # faint rings behind the masthead
SCARLET = (178, 34, 34)   # masthead red, lead accent
PINE = (0, 110, 105)
RUST = (180, 90, 20)
NAVY = (30, 80, 140)
WHITE = (255, 255, 255)

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")


class Type:
    """DejaVu faces, loaded once per size and then cached."""

    def __init__(self) -> None:
        self._cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}

    def _load(self, name: str, size: int) -> ImageFont.FreeTypeFont:
        key = (name, size)
        face = self._cache.get(key)
        if face is None:
            face = ImageFont.truetype(str(FONT_DIR / name), size)
            self._cache[key] = face
        return face

    def serif_bold(self, size: int) -> ImageFont.FreeTypeFont:
        return self._load("DejaVuSerif-Bold.ttf", size)

    def serif(self, size: int) -> ImageFont.FreeTypeFont:
        return self._load("DejaVuSerif.ttf", size)

    def sans_bold(self, size: int) -> ImageFont.FreeTypeFont:
        return self._load("DejaVuSans-Bold.ttf", size)

    def sans(self, size: int) -> ImageFont.FreeTypeFont:
        return self._load("DejaVuSans.ttf", size)


@dataclass
class Story:
    num: str
    section: str
    lines: tuple  # display headline, one line (grid) or two (lead)
    deck: str     # body copy, wrapped to at most two lines
    accent: tuple
    figures: str = ""  # stat strip; only the lead story carries one


def _width(draw: ImageDraw.ImageDraw, text: str, face) -> float:
    return draw.textlength(text, font=face)


def _wrap(draw, text: str, face, limit: int, tag: str) -> list:
    """Greedy word wrap; fails loudly instead of clipping silently."""
    out: list[str] = []
    current = ""
    for word in text.split():
        candidate = word if not current else current + " " + word
        if _width(draw, candidate, face) <= limit:
            current = candidate
            continue
        if not current:
            raise ValueError(f"{tag}: word {word!r} wider than {limit}px")
        out.append(current)
        current = word
    if current:
        out.append(current)
    if len(out) > 2:
        raise ValueError(f"{tag}: needs {len(out)} lines, only 2 fit: {text!r}")
    return out


def _fit(draw, fonts: Type, text: str, limit: int, top: int, floor: int,
         tag: str):
    """Largest serif-bold size that fits the headline on one line."""
    size = top
    while size >= floor:
        face = fonts.serif_bold(size)
        if _width(draw, text, face) <= limit:
            return face
        size -= 1
    raise ValueError(f"{tag}: {text!r} still too wide at {floor}pt")


def _centred(draw, cx: float, y: int, text: str, face, fill) -> None:
    draw.text((cx - _width(draw, text, face) / 2, y), text, font=face,
              fill=fill)


def _chip(draw, box, fill, label: str, face, text_fill, dy: int) -> None:
    draw.rounded_rectangle(box, radius=6, fill=fill)
    _centred(draw, (box[0] + box[2]) / 2, box[1] + dy, label, face, text_fill)


class Page:
    """A blank 1024x1024 sheet and the sections drawn onto it."""

    def __init__(self) -> None:
        self.fonts = Type()
        self.img = Image.new("RGB", (CANVAS, CANVAS))
        self.d = ImageDraw.Draw(self.img)

    def paper(self) -> None:
        d = self.d
        d.rectangle([0, 0, CANVAS, CANVAS], fill=PAPER)
        for radius in (150, 210, 270):
            d.ellipse([512 - radius, 118 - radius, 512 + radius, 118 + radius],
                      outline=HALO, width=2)
        y = 7
        while y < CANVAS:
            x = 7
            while x < CANVAS:
                d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=SPECK)
                x += 14
            y += 14

    def masthead(self) -> None:
        d = self.d
        d.rectangle([MARGIN, 36, CANVAS - MARGIN, 39], fill=INK)
        d.rectangle([MARGIN, 42, CANVAS - MARGIN, 44], fill=SCARLET)
        _centred(d, 512, 54, "WORLD NEWS", self.fonts.serif_bold(96), INK)
        _centred(d, 512, 162, "THURSDAY  \u2022  26 NOVEMBER 2026",
                 self.fonts.sans_bold(27), SCARLET)
        d.rectangle([MARGIN, 200, CANVAS - MARGIN, 202], fill=INK)
        d.rectangle([MARGIN, 205, CANVAS - MARGIN, 206], fill=SCARLET)

    def lead(self, story: Story) -> None:
        d = self.d
        top, bottom = 218, 458
        left, right = MARGIN, CANVAS - MARGIN
        d.rectangle([left, top, right, bottom], fill=CARD, outline=CARD_LINE,
                    width=1)
        d.rectangle([left, top, left + 8, bottom], fill=story.accent)
        tx = left + 26
        d.text((tx, top + 18), story.section,
               font=self.fonts.sans_bold(19), fill=story.accent)
        _chip(d, (right - 78, top + 14, right - 22, top + 50), story.accent,
              story.num, self.fonts.sans_bold(22), CARD, dy=5)
        y = top + 52
        for line in story.lines:
            d.text((tx, y), line, font=self.fonts.serif_bold(44), fill=INK)
            y += 52
        wrapped = _wrap(d, story.deck, self.fonts.sans(22), right - tx - 26,
                        "lead deck")
        y = top + 158
        for line in wrapped:
            d.text((tx, y), line, font=self.fonts.sans(22), fill=TEXT)
            y += 28
        d.text((tx, top + 218), story.figures,
               font=self.fonts.sans_bold(16), fill=FAINT)

    def card(self, story: Story, x: int, y: int) -> None:
        d = self.d
        w, h = 470, 228
        d.rectangle([x, y, x + w, y + h], fill=CARD, outline=CARD_LINE,
                    width=1)
        d.rectangle([x, y, x + 6, y + h], fill=story.accent)
        _chip(d, (x + 20, y + 18, x + 64, y + 52), story.accent, story.num,
              self.fonts.sans_bold(20), WHITE, dy=4)
        d.text((x + 76, y + 24), story.section,
               font=self.fonts.sans_bold(16), fill=story.accent)
        face = _fit(d, self.fonts, story.lines[0], w - 40, 30, 18,
                    f"story {story.num} headline")
        d.text((x + 20, y + 62), story.lines[0], font=face, fill=INK)
        d.rectangle([x + 20, y + 102, x + w - 20, y + 103], fill=CARD_LINE)
        wrapped = _wrap(d, story.deck, self.fonts.sans(19), w - 40,
                        f"story {story.num} deck")
        ty = y + 116
        for line in wrapped:
            d.text((x + 20, ty), line, font=self.fonts.sans(19), fill=TEXT)
            ty += 27

    def grid(self, stories) -> None:
        for i, story in enumerate(stories):
            col, row = i % 2, i // 2
            self.card(story, MARGIN + col * (470 + 12), 472 + row * (228 + 12))

    def footer(self) -> None:
        d = self.d
        d.rectangle([MARGIN, 950, CANVAS - MARGIN, 951], fill=INK)
        _centred(d, 512, 962, "THE DAY IN FIVE STORIES  \u2022  26 NOVEMBER 2026",
                 self.fonts.sans_bold(20), INK)
        _centred(d, 512, 988, "Sources: Reuters  \u2022  AP  \u2022  CNN  \u2022  Fox Business",
                 self.fonts.sans(15), FAINT)


# --- the five stories: every number verified 26 Nov 2026, see README -------
#  14 trading partners / China proposed 20% / 8-month Section 301 probe of
#  16 partners (Reuters, 25 Nov; Reuters follow-up, 26 Nov)
#  31 killed, 21 injured (AP, 26 Nov -- revised from 30/15)
#  Case 4000 bribery drop urged, Case 2000 reconsidered; indicted 2019,
#  trial opened May 2020 (Reuters / CNN, 25 Nov)
#  5 killed, power out in 5 regions; DTEK plant halted, Naftogaz gas site
#  ablaze in Poltava (Reuters, 25 Nov)
#  S&P 500 -2.5%, Nasdaq -3.75%, Dow -1.73% (-864 pts), Nvidia -5.1%
#  (Fox Business / AP, 25 Nov)
LEAD_STORY = Story(
    num="01",
    section="TRADE  \u2014  LEAD STORY",
    lines=("TARIFFS HIT", "14 NATIONS"),
    deck="US proposes new duties on 14 partners over excess factory "
         "capacity; China faces the highest rates.",
    accent=SCARLET,
    figures="14 ECONOMIES  \u2022  CHINA +20%  \u2022  8-MONTH PROBE",
)

GRID_STORIES = [
    Story(
        num="02",
        section="DISASTER",
        lines=("CAIRO TANKER FIRE KILLS 31",),
        deck="Fuel tanker crash ignites a Ring Road blaze; 31 killed, "
             "21 injured \u2014 CAIRO",
        accent=SCARLET,
    ),
    Story(
        num="03",
        section="ISRAEL",
        lines=("JUDGES: DROP BRIBERY CASE",),
        deck="Court urges prosecutors to drop Case 4000; reconsider "
             "Case 2000 \u2014 JERUSALEM",
        accent=PINE,
    ),
    Story(
        num="04",
        section="WAR IN UKRAINE",
        lines=("RUSSIA HITS UKRAINE GRID",),
        deck="Overnight strikes kill 5, cut power in 5 regions; gas "
             "site ablaze \u2014 KYIV",
        accent=RUST,
    ),
    Story(
        num="05",
        section="MARKETS",
        lines=("WALL ST SINKS ON AI FEARS",),
        deck="S&P -2.5%, Nasdaq -3.75%, Dow -864 pts; Nvidia -5.1% "
             "\u2014 NEW YORK",
        accent=NAVY,
    ),
]


def build() -> Path:
    """Render every section and write entry.png next to the repo root."""
    page = Page()
    page.paper()
    page.masthead()
    page.lead(LEAD_STORY)
    page.grid(GRID_STORIES)
    page.footer()
    target = Path(__file__).resolve().parent.parent / "entry.png"
    page.img.save(target, format="PNG", optimize=True)
    blob = target.read_bytes()
    if blob[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("entry.png does not start with the PNG signature")
    width = int.from_bytes(blob[16:20], "big")
    height = int.from_bytes(blob[20:24], "big")
    if (width, height) != (CANVAS, CANVAS):
        raise ValueError(f"entry.png is {width}x{height}, expected 1024x1024")
    if len(blob) > 1_048_576:
        raise ValueError(f"entry.png is {len(blob)} bytes, over the 1 MiB cap")
    print(f"wrote {target} ({len(blob)} bytes, "
          f"sha256 {hashlib.sha256(blob).hexdigest()})")
    return target


if __name__ == "__main__":
    build()
