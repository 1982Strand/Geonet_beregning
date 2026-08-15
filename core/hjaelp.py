"""Hjælpetekstens kapitler — indlæsning og opdeling.

Dokumentationen vedligeholdes som markdown-filer i »Dokumenter og data/hjaelp«
og indlæses ved visning, så teksten kun findes ét sted. Modulet er frit for
Streamlit, så opdelingen kan afprøves uden at køre appen.

Filformat
---------
Hver fil indledes med et hoved mellem to linjer med tre bindestreger:

    ---
    titel: Beregningsmetoden
    resume: Fra VejDim-kørslen til den færdige lagtykkelse …
    ---

Herefter følger afsnittene som »## N Overskrift«. To blokke har særlig
betydning i teksten:

    :::formel
    T = T_basis × (1 + k_φ + k_net)
    --
    k_φ   er korrektionen for friktionsvinklen
    :::

    :::figur Figurtekst under tabellen.
    | Kolonne | Værdi |
    | --- | --- |
    | Række | 1 |
    :::

Formlen sættes i egen ramme med en »hvor:«-liste under, jf. håndbogens
fremstilling. Figuren trækkes ud af brødteksten og sættes i sidekolonnen ud
for det afsnit, den hører til.

En henvisning til en anden side skrives med sidens egen nøgle på hovedlinjen
og knapteksten som indhold:

    :::gaatil trafikklasse_korrelation
    Gå til Trafikklasse-korrelation
    :::
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

KAPITEL_MAPPE = Path(__file__).resolve().parent.parent / "Dokumenter og data" / "hjaelp"

_HOVED = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
_AFSNIT = re.compile(r"^##\s+(\S+)\s+(.+?)\s*$", re.M)
_BLOK = re.compile(
    r"^:::(formel|figur|gaatil)[ \t]*(.*?)\n(.*?)^:::[ \t]*$", re.M | re.S
)


@dataclass
class Formel:
    """En formel med den tilhørende forklaring af symbolerne."""

    udtryk: str
    hvor: list[str] = field(default_factory=list)


@dataclass
class Figur:
    """En figur: en lille tabel med figurtekst under."""

    tekst: str
    tabel: str


@dataclass
class Gaatil:
    """En henvisning til en anden side, vist som knap under afsnittet."""

    side: str
    tekst: str


@dataclass
class Afsnit:
    """Et nummereret afsnit i et kapitel."""

    nummer: str
    titel: str
    # Brødteksten opdelt i stykker: markdown-strenge og Formel-objekter i den
    # rækkefølge, de står i filen.
    indhold: list = field(default_factory=list)
    figurer: list[Figur] = field(default_factory=list)


@dataclass
class Kapitel:
    """Et kapitel med sit hoved og sine afsnit."""

    noegle: str
    nummer: int
    titel: str
    resume: str
    afsnit: list[Afsnit] = field(default_factory=list)

    @property
    def afsnit_tal(self) -> str:
        n = len(self.afsnit)
        return f"{n} afsnit" if n != 1 else "1 afsnit"


def _laes_hoved(tekst: str) -> tuple[dict, str]:
    """Skil hovedet fra brødteksten. Uden hoved returneres tomme felter."""
    m = _HOVED.match(tekst)
    if not m:
        return {}, tekst
    felter: dict[str, str] = {}
    for linje in m.group(1).split("\n"):
        if ":" in linje:
            navn, _, vaerdi = linje.partition(":")
            felter[navn.strip()] = vaerdi.strip()
    return felter, tekst[m.end():]


def _del_krop(krop: str) -> tuple[list, list[Figur]]:
    """Del et afsnits brødtekst i markdown, formler, henvisninger og figurer.

    Figurerne samles for sig, da de sættes i sidekolonnen; markdown, formler
    og henvisninger bevarer deres indbyrdes rækkefølge.
    """
    indhold: list = []
    figurer: list[Figur] = []
    pos = 0

    def _tilfoej_md(raa: str) -> None:
        raa = raa.strip()
        if raa:
            indhold.append(raa)

    for m in _BLOK.finditer(krop):
        _tilfoej_md(krop[pos:m.start()])
        slags, hoved, brod = m.group(1), m.group(2).strip(), m.group(3)
        if slags == "formel":
            udtryk, _, hvor = brod.partition("\n--\n")
            indhold.append(Formel(
                udtryk=udtryk.strip("\n"),
                hvor=[l.strip() for l in hvor.split("\n") if l.strip()],
            ))
        elif slags == "gaatil":
            indhold.append(Gaatil(side=hoved, tekst=brod.strip()))
        else:
            figurer.append(Figur(tekst=hoved, tabel=brod.strip()))
        pos = m.end()
    _tilfoej_md(krop[pos:])
    return indhold, figurer


def _del_afsnit(krop: str) -> list[Afsnit]:
    """Del brødteksten i nummererede afsnit efter »## N Overskrift«."""
    traef = list(_AFSNIT.finditer(krop))
    afsnit: list[Afsnit] = []
    for i, m in enumerate(traef):
        slut = traef[i + 1].start() if i + 1 < len(traef) else len(krop)
        indhold, figurer = _del_krop(krop[m.end():slut])
        afsnit.append(Afsnit(
            nummer=m.group(1), titel=m.group(2),
            indhold=indhold, figurer=figurer,
        ))
    return afsnit


def laes_kapitel(sti: Path) -> Kapitel:
    """Indlæs og opdel én kapitelfil.

    Kapitlets nummer og nøgle udledes af filnavnet, »01-beregningsmetoden.md«
    giver nummer 1 og nøglen »beregningsmetoden«. Nøglen anvendes, når en
    beregningsside henviser til kapitlet.
    """
    raa = sti.read_text(encoding="utf-8")
    hoved, krop = _laes_hoved(raa)
    stamme = sti.stem
    nummer_tekst, _, noegle = stamme.partition("-")
    return Kapitel(
        noegle=noegle or stamme,
        nummer=int(nummer_tekst) if nummer_tekst.isdigit() else 0,
        titel=hoved.get("titel", stamme),
        resume=hoved.get("resume", ""),
        afsnit=_del_afsnit(krop),
    )


def laes_kapitler(mappe: Path | None = None) -> list[Kapitel]:
    """Indlæs samtlige kapitler i nummerorden.

    Mappen læses ved hver visning, så en rettet markdown-fil slår igennem uden
    at appen genstartes.
    """
    mappe = mappe or KAPITEL_MAPPE
    if not mappe.is_dir():
        return []
    return [laes_kapitel(sti) for sti in sorted(mappe.glob("*.md"))]
