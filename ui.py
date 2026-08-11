"""BG Byggros — præsentationslag til Geonet-beregning.

Modulet indeholder de visuelle byggeklodser fra designgennemgangen. Ingen
beregningslogik: alle funktioner tager færdige tal og returnerer opmærkning.

Anvendelse i app.py:

    import ui

    ui.opsaet_side()                      # skal stå før alle andre st-kald
    ui.topbjaelke()
    ...
    input_col, resultat_col = st.columns([328, 1000], gap="large")

Kræver .streamlit/config.toml og assets/byggros_theme.css fra samme udrulning.
"""

from __future__ import annotations

import base64
import re
from contextlib import contextmanager
from functools import lru_cache
from html import escape
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------- konstanter

FARVE = {
    "ink": "#15211A",
    "ink_70": "#4A554E",
    "ink_45": "#7A857D",
    "ink_25": "#9AA39C",
    "linje": "#DCE1DD",
    "linje_blod": "#E6EAE6",
    "flade": "#FFFFFF",
    "laerred": "#F4F6F4",
    "gron": "#1B6B34",
    "gron_mork": "#12401F",
    "gron_lys": "#F7FBF8",
    "gron_050": "#EDF4EE",
    "advarsel": "#A8600B",
    "advarsel_flade": "#FCF5E8",
    "kritisk": "#B42318",
    "jord": "#8B7355",
    "baerelag": "#D9DDD9",
    "baerelag_kant": "#B9C0BA",
    "bundsikring": "#EDEFED",
    "bundsikring_kant": "#C4CAC5",
}

SANS = "'IBM Plex Sans',system-ui,sans-serif"
MONO = "'IBM Plex Mono',ui-monospace,monospace"

ROD = Path(__file__).parent


# ------------------------------------------------------------ talformatering

def mm(vaerdi: float | None) -> str:
    """1038 → '1.038 mm'. None → '—'."""
    if vaerdi is None:
        return "—"
    return f"{vaerdi:,.0f} mm".replace(",", ".")


def mpa(vaerdi: float | None) -> str:
    if vaerdi is None:
        return "—"
    return f"{vaerdi:,.0f} MPa".replace(",", ".")


def grader(vaerdi: float | None) -> str:
    if vaerdi is None:
        return "—"
    return f"{vaerdi:.1f}°".replace(".", ",")


def procent(vaerdi: float | None, decimaler: int = 0) -> str:
    if vaerdi is None:
        return "—"
    return f"{vaerdi:.{decimaler}f} %".replace(".", ",")


def fortegn(vaerdi: float) -> str:
    """-245 → '−245' med typografisk minus."""
    return f"{vaerdi:,.0f}".replace(",", ".").replace("-", "−")


# ------------------------------------------------------------------ opsætning

def opsaet_side(titel: str = "Geonet-dimensionering · BG Byggros") -> None:
    """Sætter sidekonfiguration og indlæser stylesheetet. Kaldes først i app.py."""
    st.set_page_config(
        page_title=titel,
        page_icon=str(ROD / "assets" / "byggros_logo.jpeg"),
        layout="wide",
        initial_sidebar_state="expanded",
    )
    css = (ROD / "assets" / "byggros_theme.css").read_text(encoding="utf-8")
    # En afsluttende style-tag i stylesheetet — også inde i en kommentar —
    # ville afbryde style-elementet, så resten af filen blev vist som tekst.
    css = re.sub(r"</\s*style", "<\\/style", css, flags=re.I)
    # Stylesheetet indsættes med st.markdown. st.html renser sit indhold, og
    # style-elementet når ikke frem til dokumentet; reglerne ville da ikke
    # gælde, og alt uden inline-opmærkning stod ustylet.
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# -------------------------------------------------------------------- topbar

@lru_cache(maxsize=1)
def _logo_data_uri() -> str:
    """Firmalogoet som data-URI.

    Logoet indlejres frem for at hentes fra static-mappen: den vej kræver, at
    serveren udstiller statiske filer, og slår fejl, når appen ikke kører fra
    dokumentroden. Filen er små 26 kB og læses én gang pr. proces.
    """
    sti = ROD / "static" / "byggros_logo.png"
    if not sti.exists():
        return ""
    data = base64.b64encode(sti.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


def topbjaelke(version: str = "v0.4") -> None:
    """Mørk bjælke med logo, værktøjsnavn og handlinger.

    Logoet ligger på en hvid brik: firmamærket er mørkt og ville forsvinde
    direkte på bjælken.
    """
    with st.container(key="bg_topbar"):
        navn_kol, handling_kol = st.columns([3, 1.5], vertical_alignment="center")
        with navn_kol:
            st.html(
                f"""
                <div style="display:flex;align-items:center;gap:14px">
                  <div style="background:#fff;border-radius:3px;padding:5px 8px;
                              display:flex;align-items:center">
                    <img src="{_logo_data_uri()}" alt="BG Byggros"
                         style="height:15px;width:auto;display:block">
                  </div>
                  <div style="width:1px;height:20px;background:rgba(255,255,255,.22)"></div>
                  <div style="font:600 13px/1 {SANS};color:#fff;letter-spacing:-.01em">
                    Geonet-dimensionering</div>
                  <div style="font:500 10px/1 {MONO};color:rgba(255,255,255,.5);
                              padding:3px 6px;border:1px solid rgba(255,255,255,.2);
                              border-radius:3px">{escape(version)}</div>
                </div>
                """
            )
        with handling_kol:
            nulstil_kol, rapport_kol = st.columns([1, 1.4], vertical_alignment="center")
            # Knapperne aflæses af app.py gennem deres nøgler, når den aktive
            # side er bestemt. Nulstil gælder dimensioneringens felter; på de
            # øvrige sider er der intet at rydde, og knappen er slået fra.
            paa_dimensionering = (
                st.session_state.get("aktiv_side", "dimensionering")
                == "dimensionering"
            )
            with nulstil_kol:
                st.button(
                    "Nulstil",
                    key="bg_nulstil",
                    width="stretch",
                    disabled=not paa_dimensionering,
                    help=(
                        "Nulstil dimensioneringens felter til standardværdierne."
                        if paa_dimensionering
                        else "Gælder dimensioneringens felter."
                    ),
                )
            with rapport_kol:
                st.button(
                    "Generér rapport",
                    key="bg_gaa_til_rapport",
                    type="primary",
                    width="stretch",
                    disabled=not paa_dimensionering,
                    help="Gå til rapportsiden med den aktuelle dimensionering.",
                )


def etiket(tekst: str) -> None:
    """Lille versal sektionsetiket — erstatter emoji-overskrifter."""
    st.html(f'<div class="bg-eyebrow">{escape(tekst.upper())}</div>')


class Trin:
    """Håndtag til et trin-kort. Sæt .opsummering inde i blokken."""

    def __init__(self) -> None:
        self.opsummering = ""


@contextmanager
def trin_kort(nummer: int, titel: str):
    """Nummereret trin-kort, jf. designgennemgangens flow A.

    Dimensioneringen føres igennem som tre trin på én side. Hvert trin står
    i sit kort med nummer og navn til venstre og en opsummering af det valgte
    til højre, så en færdig indtastning kan aflæses uden at læse trinnet
    igennem.

    Opsummeringen kendes først, når trinnets felter er aflæst. Hovedet
    reserveres derfor med en pladsholder og udfyldes, når blokken er kørt:

        with ui.trin_kort(1, "Underbund") as trin:
            eu = ...
            trin.opsummering = f"Eu {eu} MPa"
    """
    with st.container(key=f"bg_trin_{nummer}"):
        plads = st.empty()
        trin = Trin()
        try:
            yield trin
        finally:
            plads.html(
                f'<div class="bg-trin-hoved">'
                f'<div class="bg-trin-nr">{nummer}</div>'
                f'<div class="bg-trin-titel">{escape(titel)}</div>'
                f'<div class="bg-trin-opsum">{trin.opsummering}</div></div>'
            )


@contextmanager
def resultat_blok(note: str = ""):
    """Resultatet som én afgrænset blok med grøn ramme, jf. flow A.

    Blokken samler resultattallene, snittene, designdiagrammet og
    produktvalget, så beregningens udfald står som en lukket enhed under
    trinnene.
    """
    with st.container(key="bg_resultat"):
        st.html(
            f'<div class="bg-resultat-hoved-a">'
            f'<div class="bg-resultat-titel">Resultat</div>'
            f'<div class="bg-resultat-note">{note}</div></div>'
        )
        yield


def sidehoved(titel: str, beskrivelse: str = "") -> None:
    """Sidens navn og en kort beskrivelse af, hvad siden bruges til.

    Alle sider indledes ens, jf. designgennemgangens tur 5.
    """
    st.html(
        f'<div class="bg-sidehoved"><h1>{escape(titel)}</h1>'
        f'<p>{escape(beskrivelse)}</p></div>'
    )


def underhoved(
    titel: str, note: str = "", *, skillelinje: bool = False
) -> None:
    """Underoverskrift inde i resultatblokken — Opbygning, Produktvalg m.fl."""
    klasse = "bg-underhoved bg-underhoved-skillelinje" if skillelinje else "bg-underhoved"
    st.html(
        f'<div class="{klasse}"><div class="t">{escape(titel)}</div>'
        f'<div class="n">{note}</div></div>'
    )


@contextmanager
def kort(titel: str, note: str = ""):
    """Hvidt kort med sidehoved, jf. designgennemgangens option 1d.

    Resultatkolonnens afsnit — Opbygning, Designdiagram og Produktvalg —
    står hver i sit kort på lærredet, så de kan aflæses som selvstændige
    enheder. Sidehovedet bærer afsnittets navn til venstre og dets
    forudsætninger til højre.

    Anvendes som kontekst:

        with ui.kort("Opbygning", "Snit i samme lodrette skala"):
            ...
    """
    with st.container(key=f"bg_kort_{_slug(titel)}"):
        st.html(
            f'<div class="bg-kort-hoved"><div class="bg-kort-titel">'
            f'{escape(titel)}</div>'
            f'<div class="bg-kort-note">{note}</div></div>'
        )
        yield


def _slug(tekst: str) -> str:
    """Nøglevenligt navn: kun bogstaver, tal og understreg."""
    return re.sub(r"[^a-z0-9]+", "_", tekst.lower()).strip("_") or "kort"


# ------------------------------------------------------------- resultatkort

def resultatkort(kort: list[dict], badge_tekst: str = "ANBEFALET") -> None:
    """Rækken af resultattal.

    Hvert kort: {"etiket", "vaerdi", "enhed", "note", "delta", "delta_note",
                 "anbefalet": bool}
    Første kort er referencetallet uden delta.

    badge_tekst er mærket på det fremhævede kort. I standardtilstanden er der
    ingen indtastet opbygning at holde mod, og det tyndeste alternativ mærkes
    derfor TYNDEST frem for ANBEFALET.
    """
    kolonner = "1.15fr" + " 1fr" * (len(kort) - 1)
    celler = []
    for k in kort:
        anbefalet = k.get("anbefalet", False)
        flade = FARVE["gron_lys"] if anbefalet else FARVE["flade"]
        kant = f"box-shadow:inset 3px 0 0 {FARVE['gron']};" if anbefalet else ""
        etiket_farve = FARVE["gron"] if anbefalet else FARVE["ink_45"]
        tal_farve = FARVE["gron_mork"] if anbefalet else FARVE["ink"]
        badge = (
            f'<div style="font:600 9px/1 {MONO};letter-spacing:.08em;color:#fff;'
            f'background:{FARVE["gron"]};padding:4px 7px;border-radius:3px">'
            f'{escape(badge_tekst)}</div>'
            if anbefalet else ""
        )
        delta = ""
        if k.get("delta") is not None:
            delta = (
                f'<div style="display:flex;align-items:center;gap:7px;margin-top:9px">'
                f'<div style="font:600 11.5px/1 {MONO};color:{FARVE["gron"]}">{escape(k["delta"])}</div>'
                f'<div style="font:400 11.5px/1 {SANS};color:{FARVE["ink_70"]}">'
                f'{escape(k.get("delta_note", ""))}</div></div>'
            )
        elif k.get("note"):
            delta = (
                f'<div style="font:400 11.5px/1.5 {SANS};color:{FARVE["ink_45"]};'
                f'margin-top:9px">{escape(k["note"])}</div>'
            )
        celler.append(
            f"""
            <div style="background:{flade};padding:18px 20px 17px;{kant}">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:11px">
                <div style="font:600 9.5px/1 {MONO};letter-spacing:.1em;color:{etiket_farve}">
                  {escape(k['etiket'].upper())}</div>{badge}
              </div>
              <div style="display:flex;align-items:baseline;gap:6px">
                <div style="font:600 40px/1 {MONO};color:{tal_farve};
                            font-variant-numeric:tabular-nums;letter-spacing:-.02em">{escape(k['vaerdi'])}</div>
                <div style="font:500 15px/1 {SANS};color:{FARVE['ink_70']}">{escape(k.get('enhed','mm'))}</div>
              </div>
              {delta}
            </div>
            """
        )
    st.html(
        f'<div style="display:grid;grid-template-columns:{kolonner};gap:1px;'
        f'background:{FARVE["linje"]};border:1px solid {FARVE["linje"]};'
        f'border-radius:5px;overflow:hidden">{"".join(celler)}</div>'
    )


# --------------------------------------------------------- snit-visualisering

def snit(
    kolonner: list[dict],
    reference_mm: float | None = None,
    hoejde_px: int = 340,
    jord_px: int = 26,
    geonet_navn: str | None = None,
) -> None:
    """Viser opbygningssnittene.

    Selve tegningen ligger i core.diagram.byg_snit(), som rapporten
    eksporterer til PNG af. Skærm og rapport viser derfor samme figur.

    jord_px bevares i signaturen af hensyn til kaldere; jordbåndets højde
    følger nu søjlernes skala.
    """
    from core.diagram import byg_snit

    fig = byg_snit(
        kolonner,
        reference_mm=reference_mm,
        geonet_navn=geonet_navn,
        hoejde_px=hoejde_px,
    )
    if fig is None:
        st.html(
            f'<div style="font:400 11.5px/1.55 {SANS};color:{FARVE["ink_45"]};'
            f'padding:14px 0">Ingen gyldige beregninger at vise.</div>'
        )
        return

    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    # Signaturen står under figuren; Plotly-signaturen ville optage bredde,
    # der tilhører søjlerne. Hver post er (farve, kantfarve, tekst, slags),
    # hvor slags er "flade", "linje" eller "stiplet" — de to sidste tegnes,
    # som de fremtræder i figuren, så de kan skelnes fra hinanden.
    poster = [
        (FARVE["baerelag"], FARVE["baerelag_kant"], "Bærelag", "flade"),
        (FARVE["bundsikring"], FARVE["bundsikring_kant"], "Bundsikring", "flade"),
    ]
    if any(k.get("geonet_mm") for k in kolonner):
        poster.append(
            (FARVE["kritisk"], FARVE["kritisk"], geonet_navn or "Geonet", "linje")
        )
    if any(k.get("best_case_mm") for k in kolonner):
        poster.append(
            (FARVE["gron"], FARVE["gron"], "Optimal korrektion", "stiplet")
        )
    if reference_mm:
        poster.append(
            (FARVE["ink_25"], FARVE["ink_25"], "Indtastet niveau", "stiplet")
        )

    def _glyf(flade: str, kant: str, slags: str) -> str:
        if slags == "linje":
            return f'<div style="width:18px;height:2px;background:{flade}"></div>'
        if slags == "stiplet":
            return (
                f'<div style="width:18px;height:0;'
                f'border-top:2px dashed {flade}"></div>'
            )
        return (
            f'<div style="width:16px;height:9px;background:{flade};'
            f'border:1px solid {kant}"></div>'
        )

    glyffer = "".join(
        f'<div style="display:flex;align-items:center;gap:6px">'
        f'{_glyf(flade, kant, slags)}{escape(tekst)}</div>'
        for flade, kant, tekst, slags in poster
    )
    st.html(
        f'<div style="display:flex;align-items:center;gap:20px;flex-wrap:wrap;'
        f'font:400 10.5px/1.6 {SANS};color:{FARVE["ink_45"]};'
        f'margin-top:-.5rem">{glyffer}</div>'
    )



# ----------------------------------------------------------- produkttabellen

def produkttabel(raekker: list[dict], grupperet: bool = False) -> None:
    """Produktvalg.

    Hver række: {"navn", "note", "en_lag", "en_delta", "to_lag", "to_delta",
                 "indeks": str|None, "anbefalet": bool, "gruppe": str|None}
    grupperet=True indsætter en versal gruppeoverskrift, når "gruppe" skifter
    (Standard-tilstand). Alle tal er højrestillede og tabulære.
    """
    har_indeks = any(r.get("indeks") for r in raekker)
    kolonner = "1.6fr .7fr .8fr .8fr" if har_indeks else "1.5fr .8fr .8fr"

    hoved = ['<div style="font:600 9.5px/1 %s;letter-spacing:.08em;color:%s">PRODUKT</div>'
             % (MONO, FARVE["ink_45"])]
    if har_indeks:
        hoved.append('<div style="font:600 9.5px/1 %s;letter-spacing:.08em;color:%s;text-align:right">INDEKS</div>'
                     % (MONO, FARVE["ink_45"]))
    for m in ("1 LAG", "2 LAG"):
        hoved.append('<div style="font:600 9.5px/1 %s;letter-spacing:.08em;color:%s;text-align:right">%s</div>'
                     % (MONO, FARVE["ink_45"], m))

    krop, sidste_gruppe = [], None
    for r in raekker:
        if grupperet and r.get("gruppe") and r["gruppe"] != sidste_gruppe:
            sidste_gruppe = r["gruppe"]
            krop.append(
                f'<div style="padding:12px 20px 5px;font:600 9.5px/1 {MONO};'
                f'letter-spacing:.08em;color:{FARVE["ink_25"]};background:#FDFDFD">'
                f'{escape(r["gruppe"].upper())}</div>'
            )
        anbefalet = r.get("anbefalet", False)
        flade = f'background:{FARVE["gron_lys"]};box-shadow:inset 3px 0 0 {FARVE["gron"]};' if anbefalet else ""
        vaegt = 600 if anbefalet else 500
        note_farve = FARVE["gron"] if anbefalet else FARVE["ink_25"]

        indeks = (f'<div style="text-align:right;font:500 12px/1.2 {MONO};'
                  f'color:{FARVE["ink_70"]}">{escape(str(r.get("indeks","")))}</div>') if har_indeks else ""

        def tal(vaerdi, delta, groen):
            farve = FARVE["gron_mork"] if (anbefalet and groen) else FARVE["ink"]
            d_farve = FARVE["gron"] if (anbefalet and groen) else FARVE["ink_45"]
            return (
                f'<div style="text-align:right">'
                f'<div style="font:{vaegt} 13px/1.2 {MONO};color:{farve};'
                f'font-variant-numeric:tabular-nums">{vaerdi:.0f}</div>'
                f'<div style="font:400 10px/1.2 {MONO};color:{d_farve}">{fortegn(delta)}</div></div>'
            )

        krop.append(
            f'<div style="display:grid;grid-template-columns:{kolonner};padding:10px 20px;'
            f'border-bottom:1px solid #F0F2F0;align-items:baseline;{flade}">'
            f'<div><div style="font:{vaegt} 12px/1.3 {SANS};color:{FARVE["ink"]}">{escape(r["navn"])}</div>'
            f'<div style="font:400 10.5px/1.3 {SANS};color:{note_farve}">{escape(r.get("note",""))}</div></div>'
            f'{indeks}{tal(r["en_lag"], r["en_delta"], False)}{tal(r["to_lag"], r["to_delta"], True)}</div>'
        )

    st.html(
        f'<div style="display:grid;grid-template-columns:{kolonner};padding:9px 20px;'
        f'border-bottom:1px solid {FARVE["linje_blod"]};background:#FBFCFB">{"".join(hoved)}</div>'
        f'{"".join(krop)}'
    )


# ------------------------------------------------------------------ besked

def besked(tekst: str, slags: str = "info") -> None:
    """Ensartet besked. slags: info | advarsel | kritisk | ok."""
    stil = {
        "info": (FARVE["laerred"], FARVE["linje"], FARVE["ink_45"]),
        "advarsel": (FARVE["advarsel_flade"], "#F0E2C6", FARVE["advarsel"]),
        "kritisk": ("#FBF0EF", "#F2D6D3", FARVE["kritisk"]),
        "ok": (FARVE["gron_lys"], "#DDE9DF", FARVE["gron"]),
    }[slags]
    st.html(
        f'<div style="background:{stil[0]};border:1px solid {stil[1]};'
        f'border-left:3px solid {stil[2]};border-radius:4px;padding:10px 12px;margin:2px 0">'
        f'<div style="font:400 11.5px/1.55 {SANS};color:{FARVE["ink_70"]}">{tekst}</div></div>'
    )
