"""Enheden for viste lagtykkelser: mm eller cm.

Beregningen føres altid i mm. Enheden vælges under Indstillinger, afsnit 2,
og anvendes alene ved visningen af lagtykkelser, dæklag og afstande i
resultater, mellemregninger, figurer og rapport. Indtastningsfelter,
indstillinger og datatabeller angives fortsat i mm, og kornstørrelser og
maskestørrelser angives altid i mm.

I cm vises én decimal mere end i mm, så visningen bevarer millimeterens
nøjagtighed; en decimal, der er nul, udelades: 650 mm → »65 cm«, 648 mm →
»64,8 cm«.

Modulet er frit for Streamlit, så figurer og rapport kan anvende det.
"""

from __future__ import annotations

import re

ENHED_MM = "mm"
ENHED_CM = "cm"
ENHEDER: tuple[str, ...] = (ENHED_MM, ENHED_CM)
STANDARD_ENHED = ENHED_MM


def normaliser(enhed) -> str:
    """Enheden, eller standardenheden ved en ugyldig værdi."""
    return enhed if enhed in ENHEDER else STANDARD_ENHED


def tal(v_mm: float | None, enhed: str = ENHED_MM, decimaler: int = 0) -> str:
    """Lagtykkelsen i enheden uden enhedsbetegnelse, med dansk
    tusindtalsseparator og decimalkomma: 1038 → »1.038« / »103,8«.

    decimaler gælder mm; i cm vises én decimal mere, og afsluttende nuller
    efter kommaet udelades. None → »—«.
    """
    if v_mm is None:
        return "—"
    v = float(v_mm)
    if normaliser(enhed) == ENHED_CM:
        v /= 10.0
        decimaler += 1
    s = f"{v:,.{decimaler}f}"
    heltal, _, dec = s.partition(".")
    if normaliser(enhed) == ENHED_CM:
        dec = dec.rstrip("0")
    ud = heltal.replace(",", ".")
    if dec:
        ud = f"{ud},{dec}"
    if ud in ("-0", "−0"):
        ud = "0"
    return "−" + ud[1:] if ud.startswith("-") else ud


def laengde(
    v_mm: float | None, enhed: str = ENHED_MM, decimaler: int = 0,
) -> str:
    """Lagtykkelsen med enhed: 1038 → »1.038 mm« / »103,8 cm«. None → »—«."""
    if v_mm is None:
        return "—"
    return f"{tal(v_mm, enhed, decimaler)} {normaliser(enhed)}"


def fortegn(v_mm: float, enhed: str = ENHED_MM, decimaler: int = 0) -> str:
    """Forskellen med fortegn og enhed: −375 mm / +4,9 cm."""
    s = tal(v_mm, enhed, decimaler)
    if not s.startswith("−") and s != "0":
        s = "+" + s
    return f"{s} {normaliser(enhed)}"


# Et tal efterfulgt af »mm« i en færdig tekst, fx »1.050 mm« eller »32,5 mm«.
_MM_I_TEKST = re.compile(r"(?<![\d,.])(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))? mm\b")


def konverter_tekst(tekst: str, enhed: str) -> str:
    """Omregn lagtykkelser i en færdig tekst fra mm til enheden.

    Anvendes alene på tekster, hvis mm-angivelser alle er lagtykkelser,
    dæklag eller afstande — fx placeringsadvarslerne fra core.placement —
    idet kornstørrelser ikke må omregnes.
    """
    if normaliser(enhed) == ENHED_MM or not tekst:
        return tekst

    def _om(m: re.Match) -> str:
        v = float(m.group(1).replace(".", "") + (
            "." + m.group(2) if m.group(2) else ""
        ))
        return laengde(v, enhed, len(m.group(2) or ""))

    return _MM_I_TEKST.sub(_om, tekst)
