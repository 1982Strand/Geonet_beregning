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
    hoejde_px: int = 230,
    jord_px: int = 42,
    geonet_navn: str | None = None,
) -> None:
    """Tegner opbygningssnittene i HTML — erstatter matplotlib-figuren.

    kolonner: liste af
        {"titel",
         "lag": [(navn, mm, "baerelag"|"bundsikring")],
         "geonet_mm": [kote målt fra underbundens overkant],
         "total_mm": float | None,
         "status": (tekst, "gron"|"advarsel"|"kritisk"|"neutral"),
         "underbund_tekst": str,
         "tom_tekst": str,          # vises i stedet for søjlen, når total_mm er None
         "best_case_mm": float,     # optimal tykkelse ved interval-produkter
         "advarsler": [str]}        # fx krav til geonettets placering

    Lagnavnene er frie; "slags" styrer alene fladens farve. Der kan indgå op
    til tre materialelag, og navnene tages fra materialevalget.

    reference_mm: den indtastede tykkelse; tegnes som fælles stiplet linje.
                  None i Standard-tilstand, hvor der ikke indtastes lag.
    geonet_navn:  navnet, geonet-linjerne benævnes med i signaturen.

    Alle kolonner deler skala, så søjlerne kan sammenlignes direkte.
    """
    hoejder = [k["total_mm"] for k in kolonner if k.get("total_mm")]
    hoejder += [k["best_case_mm"] for k in kolonner if k.get("best_case_mm")]
    if reference_mm:
        hoejder.append(reference_mm)
    if not hoejder:
        st.html(
            f'<div style="font:400 11.5px/1.55 {SANS};color:{FARVE["ink_45"]};'
            f'padding:14px 0">Ingen gyldige beregninger at vise.</div>'
        )
        return
    maks = max(hoejder)
    skala = (hoejde_px - jord_px - 8) / maks          # px pr. mm

    def px(v: float) -> float:
        return round(v * skala, 1)

    ref_linje = ""
    if reference_mm:
        ref_linje = (
            f'<div style="position:absolute;left:0;right:0;'
            f'bottom:{px(reference_mm) + jord_px}px;'
            f'border-top:1.5px dashed {FARVE["ink_25"]};'
            f'z-index:20;pointer-events:none"></div>'
        )

    celler = []
    for i, k in enumerate(kolonner):
        lag_html = []
        for navn, tykkelse, slags in k.get("lag", []):
            flade = FARVE["baerelag"] if slags == "baerelag" else FARVE["bundsikring"]
            kant = FARVE["baerelag_kant"] if slags == "baerelag" else FARVE["bundsikring_kant"]
            h = px(tykkelse)
            indhold = (
                f'<div style="font:500 10px/1.2 {SANS};color:{FARVE["ink"]};text-align:center">{escape(navn)}</div>'
                f'<div style="font:600 10px/1 {MONO};color:{FARVE["ink"]}">{tykkelse:.0f}</div>'
            ) if h >= 34 else ""
            # Lagene støder op til hinanden; kun det nederste beholder sin
            # underkant, så grænsen mellem to lag ikke tegnes dobbelt.
            sidste = (navn, tykkelse, slags) == k["lag"][-1]
            bund = "" if sidste else "border-bottom:none;"
            lag_html.append(
                f'<div style="height:{h}px;background:{flade};border:1px solid {kant};'
                f'{bund}display:flex;flex-direction:column;align-items:center;'
                f'justify-content:center;box-sizing:border-box;gap:1px;'
                f'overflow:hidden">{indhold}</div>'
            )

        geonet_html = "".join(
            f'<div style="position:absolute;left:50%;transform:translateX(-50%);'
            f'bottom:{px(kote) + jord_px - 1}px;width:112px;height:2px;'
            f'background:{FARVE["kritisk"]}"></div>'
            for kote in k.get("geonet_mm", [])
        )

        jord_tekst = (
            f'<div style="font:600 9px/1 {MONO};color:#fff;letter-spacing:.05em">'
            f'{escape(k["underbund_tekst"]).replace(chr(10), "<br>")}</div>'
            if k.get("underbund_tekst") else ""
        )

        status_tekst, status_slags = k.get("status", ("", "neutral"))
        status_farve = {
            "gron": FARVE["gron"],
            "advarsel": FARVE["advarsel"],
            "kritisk": FARVE["kritisk"],
        }.get(status_slags, FARVE["ink_45"])
        vaegt = 600 if status_slags == "gron" else 500

        titel_farve = FARVE["gron"] if status_slags == "gron" else FARVE["ink"]

        # Den optimale tykkelse ved produkter med korrektionsinterval markeres
        # med en fin stiplet linje inde i søjlen, så spændet kan aflæses.
        best = k.get("best_case_mm")
        best_html = ""
        if best and k.get("total_mm") and best < k["total_mm"]:
            best_html = (
                f'<div style="position:absolute;left:50%;transform:translateX(-50%);'
                f'bottom:{px(best) + jord_px}px;width:104px;'
                f'border-top:1px dashed {FARVE["gron"]}"></div>'
                f'<div style="position:absolute;left:calc(50% + 58px);'
                f'bottom:{px(best) + jord_px - 5}px;font:500 9px/1 {MONO};'
                f'color:{FARVE["gron"]};white-space:nowrap">{mm(best)} optimalt</div>'
            )

        # Søjler uden gyldig beregning tegnes som en tom, stiplet ramme.
        if not k.get("total_mm"):
            soejle_html = (
                f'<div style="position:absolute;left:50%;transform:translateX(-50%);'
                f'bottom:{jord_px}px;width:104px;height:{hoejde_px - jord_px - 8}px;'
                f'border:1px dashed {FARVE["linje"]};display:flex;'
                f'align-items:center;justify-content:center;padding:6px;'
                f'box-sizing:border-box">'
                f'<div style="font:400 9.5px/1.35 {SANS};color:{FARVE["ink_45"]};'
                f'text-align:center">{escape(k.get("tom_tekst", "Ikke defineret"))}</div>'
                f'</div>'
            )
            maal_html = ""
        else:
            soejle_html = (
                f'<div style="position:absolute;left:50%;transform:translateX(-50%);'
                f'bottom:{jord_px}px;width:104px;display:flex;flex-direction:column">'
                f'{"".join(lag_html)}</div>'
                f'{geonet_html}{best_html}'
            )
            maal_html = (
                f'<div style="position:absolute;left:calc(50% + 58px);'
                f'bottom:{px(k["total_mm"]) / 2 + jord_px}px;'
                f'font:600 10.5px/1 {MONO};color:{FARVE["ink"]};white-space:nowrap">'
                f'{mm(k["total_mm"])}</div>'
            )

        advarsel_html = "".join(
            f'<div style="font:400 9.5px/1.4 {SANS};color:{FARVE["advarsel"]};'
            f'text-align:center;max-width:150px">{escape(a)}</div>'
            for a in k.get("advarsler", [])
        )

        celler.append(
            f"""
            <div style="display:flex;flex-direction:column;align-items:center;gap:12px">
              <div style="font:600 11.5px/1 {SANS};color:{titel_farve}">{escape(k['titel'])}</div>
              <div style="position:relative;width:100%;height:{hoejde_px}px">
                {ref_linje}
                {soejle_html}
                <div style="position:absolute;left:50%;transform:translateX(-50%);
                            width:104px;bottom:0;height:{jord_px}px;
                            background:repeating-linear-gradient(45deg,{FARVE['jord']},{FARVE['jord']} 3px,#7A6449 3px,#7A6449 6px);
                            display:flex;align-items:center;justify-content:center">{jord_tekst}</div>
                {maal_html}
              </div>
              <div style="display:flex;flex-direction:column;align-items:center;gap:4px">
                <div style="font:{vaegt} 10.5px/1 {SANS};color:{status_farve}">{escape(status_tekst)}</div>
                {advarsel_html}
              </div>
            </div>
            """
        )

    har_geonet = any(k.get("geonet_mm") for k in kolonner)
    har_best = any(k.get("best_case_mm") for k in kolonner)

    har_baerelag = any(
        slags == "baerelag"
        for kolonne in kolonner
        for _, _, slags in kolonne.get("lag", [])
    )
    har_bundsikring = any(
        slags == "bundsikring"
        for kolonne in kolonner
        for _, _, slags in kolonne.get("lag", [])
    )
    signatur = []
    if har_baerelag:
        signatur.append(
            (f'<div style="width:16px;height:9px;background:{FARVE["baerelag"]};'
             f'border:1px solid {FARVE["baerelag_kant"]}"></div>', "Bærelag")
        )
    if har_bundsikring:
        signatur.append(
            (f'<div style="width:16px;height:9px;background:{FARVE["bundsikring"]};'
             f'border:1px solid {FARVE["bundsikring_kant"]}"></div>', "Bundsikring")
        )
    if har_geonet:
        signatur.append(
            (f'<div style="width:16px;height:2px;background:{FARVE["kritisk"]}"></div>',
             geonet_navn or "Geonet")
        )
    if har_best:
        signatur.append(
            (f'<div style="width:16px;border-top:1px dashed {FARVE["gron"]}"></div>',
             "Optimal korrektion")
        )
    if reference_mm:
        signatur.append(
            (f'<div style="width:16px;border-top:1.5px dashed {FARVE["ink_25"]}"></div>',
             "Indtastet niveau")
        )
    signatur_html = "".join(
        f'<div style="display:flex;align-items:center;gap:6px">{glyf}{escape(tekst)}</div>'
        for glyf, tekst in signatur
    )

    # bg-snit-rulle tillader vandret scroll på smalle skærme, hvor søjlerne
    # ellers ville blive klemt så tæt sammen, at lagteksten forsvinder.
    st.html(
        f"""
        <div class="bg-snit-rulle">
          <div class="bg-snit" style="padding:26px 0 14px;display:grid;
                      grid-template-columns:repeat({len(kolonner)},minmax(0,1fr));
                      gap:22px">{''.join(celler)}</div>
        </div>
        <div style="display:flex;align-items:center;gap:20px;flex-wrap:wrap;
                    font:400 10.5px/1.6 {SANS};color:{FARVE['ink_45']}">{signatur_html}</div>
        """
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
