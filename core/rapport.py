"""
Rapportgenerering til Geonet Dimensioneringsværktøj.

Producerer Word (.docx) og PDF (.pdf) rapporter ud fra en gennemført
dimensionering. Standardtekster fra BG Byggros eksempelrapport bevares
som default, men kan redigeres pr. rapport via UI'en.

Offentlig API:
    SECTION_KEYS               - rækkefølge af redigerbare sektioner
    SECTION_TITLER             - dansk overskriftstekst pr. nøgle
    STANDARD_TEKSTER           - default-tekst pr. nøgle
    render_opbygning_png(...)  - matplotlib-visualisering som PNG bytes
    byg_rapport_docx(data)     - returnerer Word-dokument som bytes
    konverter_docx_til_pdf(...) - konverterer Word-bytes til PDF-bytes
    byg_rapport_pdf(data)      - bygger Word og konverterer til PDF-bytes
"""

from __future__ import annotations

import io
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# 0. Brand-styling og repo-assets
# ---------------------------------------------------------------------------

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
DOCX_SKABELON_PATH = ASSETS_DIR / "rapport_skabelon.docx"


def _format_dato_dk(iso_dato: str) -> str:
    """Konverter ISO-dato (YYYY-MM-DD) til dansk format DD/MM/YYYY.
    Returnerer input uændret hvis det ikke er en ISO-dato."""
    if not iso_dato or len(iso_dato) != 10 or iso_dato[4] != "-" or iso_dato[7] != "-":
        return iso_dato
    yyyy, mm, dd = iso_dato[:4], iso_dato[5:7], iso_dato[8:10]
    return f"{dd}/{mm}/{yyyy}"


# ---------------------------------------------------------------------------
# 1. Standardtekster (kilde: eksempelrapport "Arkil ... 060520")
# ---------------------------------------------------------------------------

GENERELLE_FORUDSAETNINGER_TEKST = (
    "Dimensioneringen af MSL opbygningen (mekanisk stabiliseret bærelag) er "
    "baseret på resultaterne fra mere en 20 års feltforsøg udført i "
    "Skandinavien. Det ubundne bærelag fastholdes af et eller flere lag "
    "geonet, som låser og fastholder bærelaget hvormed trykspredningsvinklen "
    "forøges i lighed. I praksis betyder det, at bærelaget kan reduceres i "
    "forhold til den ikke-stabiliserede ubundne opbygning. Alternativt vil "
    "der kunne opnås en betydelig forøgelse af bæreevne for en MSL opbygning "
    "i forhold til en traditionel opbygning.\n\n"
    "Differenssætninger vil i stort omfang blive udjævnet, ligesom den "
    "stabiliserede randzone for specielt flerlagsopbygninger vil blive "
    "mindre sårbar i forhold til sætninger. Selvom erfaringerne viser "
    "betydelige reduktioner i sætninger, så vil der kun sjældent kunne "
    "opnås en sætningsfri ombygning. Ligeledes bør der tages højde for evt. "
    "frostfølsomhed, selvom MSL-opbygningen vil udjævne eventuelle "
    "hævninger.\n\n"
    "MSL-løsninger kan kombineres med letfyld, som dermed kan være med til "
    "at kompensere for eventuelle sætninger.\n\n"
    "MSL-løsninger kan ligeledes håndtere og kompensere for bæreevnesvigt "
    "forårsaget af midlertidig kortvarig vandpåvirkning, eksempelvis i "
    "forbindelse med LAR-opbygninger.\n\n"
    "For særligt sætningsgivende bundforhold vil det være en fordel at "
    "afvente med belægningsarbejde til sætningsforløbet har stabiliseret "
    "sig. Tidshorisonten er variabel, og kan vare op til et år."
)

KRAV_TIL_KOMPRIMERING_TEKST = (
    "Det forudsættes, at der ved indbygning af de ubundne bærelag opnås og "
    "eftervises en komprimeringsgrad på middel 95 % og mindst 92 % målt ved "
    "Vibrationsforsøg."
)

DIMENSIONERING_OG_SIKKERHED_TEKST = (
    "Dimensionering og kontrol af bæreevne kan være forbundet med en nogen "
    "måleusikkerhed.\n\n"
    "Ved kontrol af bæreevnen for MSL opbygningen vil en eventuel negativ "
    "variation normalt være maksimalt 10 %."
)

UDFOERELSE_TEKST = (
    "MSL-opbygninger kan udføres hele året. I visse situationer kan det "
    "være en fordel at arbejdet tilrettelægges således, at det udføres i "
    "frostperioder, hvor fremkommeligheden i terrænet kan være mere "
    "gunstig.\n\n"
    "Geonettenes formstabile struktur nødvendiggør at udlægningen sker på "
    "et relativt jævnt underlag. Eventuelt bevoksning skal som udgangspunkt "
    "fjernes. På meget sætningsgivende blød underbund kan rødder fra træer "
    "og buske med fordel blive stående, ligesom intakt tørv bør bevares. "
    "Det er dog vigtigt, at rødder og stubbe skæres helt ned, således at "
    "der maksimalt er en terrænforskel på +/- 5 cm.\n\n"
    "Overlæg på geonet bør være minimum 0,4 m. Anlæg på udvendige skråninger "
    "bør normalt udføres med maksimalt anlæg 1,5."
)

KONTROLPLAN_TEKST = (
    "Det anbefales at udføre supplerende geoteknisk sondering og indmåling "
    "af E-modul på planum, således at eventuelt behov for korrektion af "
    "opbygning kan foretages før indbygning.\n\n"
    "Kontrol af bæreevne på oversiden af de indbyggede bærelag kan ske ved "
    "pladebelastningsforsøg suppleret med dynamisk minifaldlodsmåling.\n\n"
    "Omfanget af kontrolplan vurderes på det enkelte projekt."
)

PROJEKTERINGSANSVAR_TEKST = (
    "Såfremt der foreligger skriftligt aftale med præcisering af omfang og "
    "krav til konstruktionen samt honorar og ansvarsforpligtelse for "
    "projekteringen, kan ansvaret for dimensioneringen være omfattet af "
    "vores rådgiveransvarsforsikring.\n\n"
    "Såfremt der ikke foreligger en skriftlige aftale omkring ansvarsforhold, "
    "og dersom dimensioneringen i tillæg er udarbejdet som en vederlagsfri "
    "service, fraskriver Byggros sig ansvaret for anvendelsen af "
    "beregninger, konstruktionsforslag og anden relateret rådgivning."
)

OPLYSTE_FORUDSAETNINGER_TEKST = (
    "   • Dimensionsgivende trafikbelastning: T6\n"
    "   • Vingestyrke, Cv, skønnet i planum: > 100 kPa\n"
    "   • Grundvandsspejl: ikke oplyst/ikke relevant\n"
    "   • Bærelagsmaterialer:\n"
    "           o Genbrugsstabil"
)


SECTION_KEYS = [
    "oplyste_forudsaetninger",
    "generelle_forudsaetninger",
    "krav_komprimering",
    "dim_sikkerhed",
    "udfoerelse",
    "kontrolplan",
    "projekteringsansvar",
]

SECTION_TITLER = {
    "oplyste_forudsaetninger": "Oplyste forudsætninger",
    "generelle_forudsaetninger": "Generelle dimensioneringsforudsætninger for MSL opbygning",
    "krav_komprimering": "Krav til komprimering",
    "dim_sikkerhed": "Dimensionering og sikkerhed",
    "udfoerelse": "Udførelse",
    "kontrolplan": "Kontrolplan",
    "projekteringsansvar": "Projekteringsansvar",
}

STANDARD_TEKSTER = {
    "oplyste_forudsaetninger": OPLYSTE_FORUDSAETNINGER_TEKST,
    "generelle_forudsaetninger": GENERELLE_FORUDSAETNINGER_TEKST,
    "krav_komprimering": KRAV_TIL_KOMPRIMERING_TEKST,
    "dim_sikkerhed": DIMENSIONERING_OG_SIKKERHED_TEKST,
    "udfoerelse": UDFOERELSE_TEKST,
    "kontrolplan": KONTROLPLAN_TEKST,
    "projekteringsansvar": PROJEKTERINGSANSVAR_TEKST,
}

RAPPORT_TITEL = "NOTAT – MSL opbygning veje/pladser"
BYGGROS_FOOTER = (
    "BG Byggros A/S | Egegårdsvej 5 | 5260 Odense S | "
    "Tlf. 5948 9000 | www.byggros.com"
)


# ---------------------------------------------------------------------------
# 2. Visualisering (matplotlib)
# ---------------------------------------------------------------------------

@dataclass
class Snit:
    titel: str
    t_baerelag_mm: float | None
    geonet_y_fracs: list[float]
    sub_lag: list[dict] | None = None  # liste af {"navn": str, "tykkelse_mm": float}
    ikke_defineret_tekst: str | None = None
    best_case_mm: float | None = None  # NX750/NX850-interval; kun vist i dim-preview
    placement: dict | None = None
    # Koncept A: krav-søjle felter — når er_krav_soejle=True tegnes søjlen som
    # neutral grå blok ("φ-vægtet bærelag") uden materialefordeling, og
    # status_tekst vises under søjlen til sammenligning med indtastet opbygning.
    er_krav_soejle: bool = False
    t_indtastet_mm: float | None = None  # til sammenligningslinje på tværs af søjler
    status_tekst: str | None = None      # fx "Mangler 77 mm" eller "✓ +6 mm besparelse"
    status_farve: str | None = None      # "danger" | "warning" | "success" | None


def upper_geonet_frac_for_sub_lag(sub_lag: list[dict] | None) -> float:
    """Y-frac (0=top, 1=bund af bærelag) for det øverste net ved 2-lag.

    Hvis sub_lag indeholder 2 eller flere lag, placeres det øverste net ved
    grænsen mellem lag 0 (øverst) og lag 1. Ellers returneres 0.5
    (midt i bærelaget) — fald-tilbage når der kun er ét materialelag.
    """
    if not sub_lag:
        return 0.5
    sl = [l for l in sub_lag if (l.get("tykkelse_mm") or 0) > 0]
    if len(sl) < 2:
        return 0.5
    total = sum(l["tykkelse_mm"] for l in sl)
    if total <= 0:
        return 0.5
    frac = sl[0]["tykkelse_mm"] / total
    return max(0.05, min(0.95, frac))


def render_opbygning_png(
    eu: float,
    snit_liste: list[Snit],
    geonet_label: str,
    *,
    dpi: int = 150,
) -> bytes:
    """Render N opbygnings-tværsnit som en samlet PNG.

    Replikerer logikken i app._opbygnings_snit_svg, men i matplotlib —
    så det kan embeddes direkte i både .docx og .pdf.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    import textwrap

    if not snit_liste:
        # Tom figur — bør ikke ske fra UI'en (mindst ét snit kræves), men
        # vi returnerer noget gyldigt for robusthed.
        fig, ax = plt.subplots(figsize=(1, 1), dpi=dpi)
        ax.axis("off")
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)
        return buf.getvalue()

    # Beregn fælles skala på tværs af alle snit — det største bærelag
    # afgør hvor mange mm pr. tegne-enhed. Sammenligningslinjen (t_indtastet_mm)
    # skal også passe ind i skalaen.
    t_max = max(
        (s.t_baerelag_mm for s in snit_liste if s.t_baerelag_mm is not None),
        default=500.0,
    )
    t_indtastet_max = max(
        (s.t_indtastet_mm for s in snit_liste if s.t_indtastet_mm is not None),
        default=0.0,
    )
    t_max = max(t_max, t_indtastet_max, 300.0)

    n = len(snit_liste)
    fig_w = 4.2 * n   # lidt bredere så total-label kan stå udenfor boksen
    fig_h = 5.6
    fig, axes = plt.subplots(1, n, figsize=(fig_w, fig_h), dpi=dpi)
    if n == 1:
        axes = [axes]

    # Højde-enheder i "data": baerelag rækker fra y=0 (bund af bærelag)
    # op til t_max + lidt luft. Underbund tegnes som blok under y=0.
    underbund_h = 100.0  # mm "højde" på underbundsblokken (kun visuelt)
    top_y = t_max * 1.05
    bund_y = -underbund_h

    # Koordinater i akse-data (x går fra 0 til 1)
    BOX_X1, BOX_X2 = 0.26, 0.78
    LABEL_X = BOX_X1 - 0.035  # total-label højrestilles lige udenfor boksen
    GEONET_LBL_X = 0.80       # geonet-navn til højre for boksen

    def _wrap_material_label(navn: str, tykkelse_mm: float, label_h_mm: float) -> tuple[str, float]:
        navn = str(navn or "Lag").strip()
        navn = navn.replace("Bundsikringssand", "Bundsikrings-\nsand")
        linjer: list[str] = []
        for deltekst in navn.splitlines():
            linjer.extend(textwrap.wrap(
                deltekst,
                width=13,
                break_long_words=True,
                break_on_hyphens=True,
            ) or [deltekst])

        max_name_lines = 3 if label_h_mm >= 130 else 2
        linjer = linjer[:max_name_lines]
        linjer.append(f"{tykkelse_mm:.0f} mm")

        if label_h_mm < 55:
            return f"{tykkelse_mm:.0f} mm", 7.0
        if label_h_mm < 90:
            return "\n".join(linjer[-2:]), 7.2
        return "\n".join(linjer), 7.8

    def _draw_underbund(ax):
        ub = Rectangle(
            (BOX_X1, bund_y), BOX_X2 - BOX_X1, underbund_h,
            facecolor="#A89377", edgecolor="#5C4A33", linewidth=1,
            hatch="///",
        )
        ax.add_patch(ub)
        ax.text(
            (BOX_X1 + BOX_X2) / 2, bund_y + underbund_h * 0.45, "Underbund",
            ha="center", va="center", fontsize=10,
            fontweight="bold", color="white",
        )
        ax.text(
            (BOX_X1 + BOX_X2) / 2, bund_y + underbund_h * 0.18, f"Eu = {eu:g} MPa",
            ha="center", va="center", fontsize=9, fontweight="bold", color="white",
        )

    for ax, s in zip(axes, snit_liste):
        ax.set_xlim(0, 1)
        ax.set_ylim(bund_y, top_y)
        ax.set_aspect("auto")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.set_title(s.titel, fontsize=11, fontweight="bold", pad=8)

        if s.t_baerelag_mm is None:
            # Stiplet placeholder
            besked = s.ikke_defineret_tekst or "Ikke defineret"
            rect = Rectangle(
                (BOX_X1, 0), BOX_X2 - BOX_X1, t_max,
                facecolor="#F5F5F5", edgecolor="#BDBDBD",
                linewidth=1, linestyle="--",
            )
            ax.add_patch(rect)
            ax.text(
                (BOX_X1 + BOX_X2) / 2, t_max / 2, besked,
                ha="center", va="center",
                fontsize=10, color="#888", style="italic",
            )
            _draw_underbund(ax)
            continue

        t = float(s.t_baerelag_mm)

        # Krav-søjle (Koncept A): neutral grå blok mærket "φ-vægtet bærelag".
        # Materialer fordeles IKKE — diagrammet kender ikke til lagopdeling.
        if s.er_krav_soejle:
            baerelag = Rectangle(
                (BOX_X1, 0), BOX_X2 - BOX_X1, t,
                facecolor="#E0E0E0", edgecolor="#666", linewidth=1,
                hatch=None,
            )
            ax.add_patch(baerelag)
            # Interval-bånd: tegn best-case som ekstra horisontal markering
            if s.best_case_mm is not None and 0 < s.best_case_mm < t:
                # Tonet zone mellem best-case og konservativ (= t)
                interval_zone = Rectangle(
                    (BOX_X1, s.best_case_mm),
                    BOX_X2 - BOX_X1, t - s.best_case_mm,
                    facecolor="#FFE0B2", edgecolor="none", alpha=0.5,
                )
                ax.add_patch(interval_zone)
                # Stiplet linje ved best-case
                ax.hlines(
                    s.best_case_mm, BOX_X1, BOX_X2,
                    colors="#888", linestyles=(0, (3, 2)), linewidth=0.9,
                )
                ax.text(
                    (BOX_X1 + BOX_X2) / 2, s.best_case_mm + (t - s.best_case_mm) / 2,
                    "interval", ha="center", va="center",
                    fontsize=6.5, color="#666", style="italic",
                )
            ax.text(
                (BOX_X1 + BOX_X2) / 2, t * 0.5, "φ-vægtet\nbærelag",
                ha="center", va="center",
                fontsize=9, color="#444", linespacing=1.35,
            )
            # Geonet-linjer
            placement = s.placement or {}
            for frac in s.geonet_y_fracs:
                y = t * (1.0 - frac)
                ax.hlines(
                    y, BOX_X1 - 0.015, BOX_X2 + 0.015,
                    colors="#D32F2F", linestyles=(0, (4, 2)), linewidth=1.8,
                )
                ax.annotate(
                    geonet_label,
                    xy=(GEONET_LBL_X + 0.03, y),
                    ha="left", va="center",
                    fontsize=8, color="#D32F2F",
                )
            # Total-label
            t_label_str = f"{t:.0f} mm"
            if s.best_case_mm is not None and round(s.best_case_mm) < round(t):
                t_label_str = f"{s.best_case_mm:.0f}–{t:.0f} mm"
            ax.annotate(
                f"↕ {t_label_str}",
                xy=(LABEL_X, t / 2),
                ha="right", va="center",
                fontsize=9.5, fontweight="bold", color="#333",
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 1.5},
            )
            # Status-tekst under søjlen (bund af underbund-blokken)
            if s.status_tekst:
                farve_map = {
                    "danger": "#C62828",
                    "warning": "#EF6C00",
                    "success": "#2E7D32",
                }
                farve = farve_map.get(s.status_farve or "", "#444")
                ax.text(
                    (BOX_X1 + BOX_X2) / 2, bund_y - underbund_h * 0.25,
                    s.status_tekst,
                    ha="center", va="top",
                    fontsize=9, fontweight="bold", color=farve,
                )
            _draw_underbund(ax)
            continue

        # Bærelagets ydre rektangel (ingen hatch — sub-lag tegnes ovenpå)
        baerelag = Rectangle(
            (BOX_X1, 0), BOX_X2 - BOX_X1, t,
            facecolor="#E8E8E8", edgecolor="#666", linewidth=1,
            hatch=".." if not s.sub_lag else None,
        )
        ax.add_patch(baerelag)

        # Sub-lag: tegn separator-linjer og materialeetiketter inden i bærelaget
        if s.sub_lag:
            # Filtrér 0/None væk og normaliser
            sl = [
                {"navn": l.get("navn", "Lag"), "tykkelse_mm": float(l.get("tykkelse_mm") or 0)}
                for l in s.sub_lag
                if l.get("tykkelse_mm")
            ]
            sum_lag = sum(l["tykkelse_mm"] for l in sl)
            if sum_lag > 0:
                # Skift hatch-mønster pr. lag for visuel adskillelse.
                hatches = [".", "..", "...", "x", "//"]
                y_top = t
                for idx, lag in enumerate(sl):
                    h = lag["tykkelse_mm"]
                    y_bot = max(0.0, y_top - h)
                    # Fyld med subtil hatch — viser at det er sub-lag
                    lag_rect = Rectangle(
                        (BOX_X1, y_bot), BOX_X2 - BOX_X1, y_top - y_bot,
                        facecolor="#EEEEEE", edgecolor="none",
                        hatch=hatches[idx % len(hatches)],
                        alpha=0.6,
                    )
                    ax.add_patch(lag_rect)
                    # Separator-linje under (undtagen bunden af bærelaget)
                    if idx < len(sl) - 1 and y_bot > 0.5:
                        ax.hlines(y_bot, BOX_X1, BOX_X2,
                                  colors="#555", linewidth=0.8)
                    # Etiket centreret i lag — kun hvis der er plads
                    label_h_mm = y_top - y_bot
                    label_txt, label_fs = _wrap_material_label(
                        lag["navn"], h, label_h_mm
                    )
                    ax.text(
                        (BOX_X1 + BOX_X2) / 2, (y_top + y_bot) / 2,
                        label_txt,
                        ha="center", va="center",
                        fontsize=label_fs, color="#222",
                        linespacing=1.35,
                    )
                    y_top = y_bot
        else:
            # Fald-tilbage: "Bærelag" centreret hvis ingen sub-lag oplyst
            if s.geonet_y_fracs:
                tekst_y = t * (1.0 - min(s.geonet_y_fracs) / 2)
            else:
                tekst_y = t * 0.5
            ax.text(
                (BOX_X1 + BOX_X2) / 2, tekst_y, "Bærelag",
                ha="center", va="center",
                fontsize=10, fontweight="bold", color="#333",
            )

        # Geonet-linjer ovenpå sub-lag
        placement = s.placement or {}
        for frac in s.geonet_y_fracs:
            y = t * (1.0 - frac)
            ax.hlines(
                y, BOX_X1 - 0.015, BOX_X2 + 0.015,
                colors="#D32F2F", linestyles=(0, (4, 2)), linewidth=1.8,
            )
            ax.annotate(
                geonet_label,
                xy=(GEONET_LBL_X + 0.03, y),
                ha="left", va="center",
                fontsize=8, color="#D32F2F",
            )

        # Total-tykkelse label UDENFOR boksen, til venstre
        ax.annotate(
            f"↕ {t:.0f} mm",
            xy=(LABEL_X, t / 2),
            ha="right", va="center",
            fontsize=9.5, fontweight="bold", color="#333",
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 1.5},
        )
        # Interval-produkter (NX750/NX850): vis best-case under hovedtallet.
        # Kun sat fra dim-preview — rapporten lader feltet være None.
        if (s.best_case_mm is not None
                and round(s.best_case_mm) < round(t)):
            ax.annotate(
                f"↓ {s.best_case_mm:.0f} mm",
                xy=(LABEL_X, t / 2),
                xytext=(0, -16), textcoords="offset points",
                ha="right", va="center",
                fontsize=8, color="#555",
            )
            ax.annotate(
                "under optimale\nforhold",
                xy=(LABEL_X, t / 2),
                xytext=(0, -32), textcoords="offset points",
                ha="right", va="center",
                fontsize=7, color="#777", style="italic",
            )

        # Status-tekst under "Indtastet opbygning" (kun hvis sat)
        if s.status_tekst and not s.er_krav_soejle:
            farve_map = {
                "danger": "#C62828",
                "warning": "#EF6C00",
                "success": "#2E7D32",
            }
            farve = farve_map.get(s.status_farve or "", "#444")
            ax.text(
                (BOX_X1 + BOX_X2) / 2, bund_y - underbund_h * 0.25,
                s.status_tekst,
                ha="center", va="top",
                fontsize=9, fontweight="bold", color=farve,
            )

        _draw_underbund(ax)

    # Sammenligningslinje: t_indtastet_mm trækkes som stiplet blå linje
    # henover alle søjler (også 'Indtastet opbygning'-søjlen selv) som
    # gennemgående reference. Det første søjle der har t_indtastet_mm sat
    # definerer linjens niveau.
    t_indtastet = next(
        (s.t_indtastet_mm for s in snit_liste if s.t_indtastet_mm is not None),
        None,
    )
    if t_indtastet is not None and t_indtastet > 0:
        for ax in axes:
            ax.hlines(
                t_indtastet, 0.02, 0.98,
                colors="#1565C0", linestyles=(0, (5, 3)), linewidth=1.4,
                zorder=10,
            )

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=dpi)
    plt.close(fig)
    return buf.getvalue()


def render_personligt_designdiagram_png(
    *,
    eu: float,
    eo: float,
    klasse: int | None,
    phi: float,
    geonet: dict | None,
    t_indtastet_mm: float | None,
    t_basis_table: dict,
    dpi: int = 150,
) -> bytes:
    """Designdiagram tilpasset brugerens opbygning + geonet.

    Tegner tre φ-(og evt. net-)korrigerede kurver (uarmeret, 1 lag, 2 lag)
    for det valgte Eo, sammen med brugerens Eu og opbygning som referencer.
    For interval-produkter (NX750/NX850) tegnes 1-lag og 2-lag som tonet
    bånd mellem best-case og konservativ ende.

    Stilen mimer de originale designdiagrammer (gul/blå/lilla farveskema,
    Eu på y-akse, tykkelse i cm på x-akse).
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Lokal import for at undgå cirkulær afhængighed
    from .data import K_PHI

    phi_kor = K_PHI * (phi - 35.0)

    # Net-korrektion: konservativ værdi + best-case for interval-produkter
    net_kor_kons = float(geonet.get("korrektion", 0.0)) if geonet else 0.0
    interval = geonet.get("korrektion_interval") if geonet else None
    net_kor_best = float(interval[0]) if interval else None

    eu_vals = sorted(t_basis_table.keys())

    def _kurve(lag_mode: str, faktor: float) -> tuple[list[float], list[float]]:
        xs: list[float] = []
        ys: list[float] = []
        for eu_v in eu_vals:
            v = t_basis_table.get(eu_v, {}).get(eo, {}).get(lag_mode)
            if v is not None:
                xs.append(v * faktor)  # cm
                ys.append(eu_v)
        return xs, ys

    fig, ax = plt.subplots(figsize=(9.0, 5.5), dpi=dpi)

    # Farveskema matcher de originale diagrambilleder
    farve_uarm = "#E0BB00"   # gul
    farve_1lag = "#1F4E9C"   # blå
    farve_2lag = "#7B1FA2"   # lilla

    # Kurver — uarmeret (φ-korrigeret)
    f_uarm = 1.0 + phi_kor
    xs_u, ys_u = _kurve("uarmeret", f_uarm)
    if xs_u:
        ax.plot(
            xs_u, ys_u, "-", color=farve_uarm, linewidth=2.2,
            marker="^", markersize=5,
            label="Uarmeret (φ-kor.)",
        )

    geonet_navn = (geonet or {}).get("navn", "Reference")

    def _plot_armeret(lag_mode: str, color: str, marker: str, label_prefix: str):
        # Konservativ kurve (altid)
        f_kons = 1.0 + phi_kor + net_kor_kons
        xs_k, ys_k = _kurve(lag_mode, f_kons)
        if not xs_k:
            return
        if net_kor_best is not None:
            f_best = 1.0 + phi_kor + net_kor_best
            xs_b, ys_b = _kurve(lag_mode, f_best)
            # Tonet bånd mellem best-case og konservativ. fill_betweenx
            # kræver fælles y-koordinater — vi kører over fælles eu-rækker.
            if xs_b and ys_b == ys_k:
                ax.fill_betweenx(
                    ys_k, xs_b, xs_k, color=color, alpha=0.15,
                    label=None,
                )
            # Stiplet linje ved best-case-kanten
            ax.plot(
                xs_b, ys_b, ":", color=color, linewidth=1.3,
                label=None,
            )
        # Heltrukken konservativ kurve med marker
        ax.plot(
            xs_k, ys_k, "-", color=color, linewidth=2.2,
            marker=marker, markersize=5,
            label=f"{label_prefix} {geonet_navn}",
        )

    _plot_armeret("1_lag", farve_1lag, "D", "1 lag")
    _plot_armeret("2_lag", farve_2lag, "s", "2 lag")

    # Brugerens build (lodret) — kun hvis sat
    if t_indtastet_mm is not None and t_indtastet_mm > 0:
        t_cm = t_indtastet_mm / 10.0
        ax.axvline(
            t_cm, color="#1565C0", linestyle=(0, (5, 3)), linewidth=1.6,
            label=f"Indtastet opbygning: {t_cm:.0f} cm",
            zorder=5,
        )

    # Brugerens Eu (vandret)
    ax.axhline(
        eu, color="#388E3C", linestyle=(0, (5, 3)), linewidth=1.6,
        label=f"Eu = {eu:g} MPa",
        zorder=5,
    )

    # Skæringspunkt — kun hvis begge referencer er sat
    if t_indtastet_mm is not None and t_indtastet_mm > 0:
        t_cm = t_indtastet_mm / 10.0
        ax.plot(
            [t_cm], [eu], "o", color="#D32F2F", markersize=10,
            zorder=11, markeredgecolor="white", markeredgewidth=1.5,
            label="Din opbygning",
        )

    # Akse-grænser: dækker hele datasættet plus lidt luft
    alle_xs: list[float] = []
    for mode, faktor in (
        ("uarmeret", f_uarm),
        ("1_lag", 1.0 + phi_kor + net_kor_kons),
        ("2_lag", 1.0 + phi_kor + net_kor_kons),
    ):
        xs, _ = _kurve(mode, faktor)
        alle_xs.extend(xs)
    if t_indtastet_mm is not None:
        alle_xs.append(t_indtastet_mm / 10.0)
    if alle_xs:
        x_max = max(alle_xs) * 1.08
        ax.set_xlim(0, max(x_max, 80))
    else:
        ax.set_xlim(0, 160)
    ax.set_ylim(0, max(max(eu_vals) * 1.05, eu * 1.2, 50))

    ax.set_xlabel("Bærelagstykkelse [cm]", fontsize=11, fontweight="bold")
    ax.set_ylabel(r"Bundmodul $E_u$ [MN/m²]", fontsize=11, fontweight="bold")

    klasse_str = f"Klasse {klasse}" if klasse is not None else f"Eo = {eo:g}"
    phi_str = f"{phi:.1f}".replace(".", ",")
    ax.set_title(
        f"Designdiagram — Eo = {eo:g} MN/m² · {klasse_str}\n"
        f"Materialer: φ = {phi_str}° · Geonet: {geonet_navn}",
        fontsize=11,
    )
    ax.grid(True, alpha=0.4)
    ax.legend(loc="upper right", fontsize=8.5, framealpha=0.92)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=dpi)
    plt.close(fig)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 3. Formatering — dimensioneringsgrundlag og resultat
# ---------------------------------------------------------------------------

def _materiale_resume(materialer: list[dict]) -> str:
    """Linjebrudt resume af materialelagene til dimensioneringsgrundlag."""
    if not materialer:
        return "—"
    linjer = []
    for i, m in enumerate(materialer, start=1):
        navn = m.get("navn", "?")
        phi = m.get("phi")
        korn = m.get("max_korn")
        tyk = m.get("tykkelse_mm")
        pct = m.get("pct")
        dele = [f"Lag {i}: {navn}"]
        if phi is not None:
            dele.append(f"φ = {phi}°")
        if korn is not None:
            dele.append(f"max korn = {korn} mm")
        if tyk is not None:
            dele.append(f"{tyk:.0f} mm")
        elif pct is not None:
            dele.append(f"{pct:.0f} %")
        linjer.append(" · ".join(dele))
    return "\n".join(linjer)


def formatér_dimensioneringsgrundlag(dim: dict) -> list[tuple[str, str]]:
    """Returnér nøgle/værdi-rækker til Dimensioneringsgrundlag-tabellen."""
    materialer = dim.get("materialer") or []
    return [
        ("Underbundens E-modul (Eu)", f"{dim.get('eu', 0):g} MPa"),
        ("Belastningsklasse", str(dim.get("valgt_klasse", "—"))),
        ("Materialeopbygning", _materiale_resume(materialer)),
        ("Vægtet friktionsvinkel (φ)", f"{dim.get('phi', 35):.1f}°"),
    ]


def formatér_dimensioneringsresultat(dim: dict) -> list[tuple[str, str]]:
    """Nøgle/værdi-rækker til Dimensioneringsresultat-tabellen."""
    res_1 = dim.get("res_1") or {}
    res_2 = dim.get("res_2") or {}
    geonet = dim.get("geonet") or {}
    materialer = dim.get("materialer") or []

    def _mm(v):
        return f"{v:.0f} mm" if isinstance(v, (int, float)) else "—"

    # Uarmeret reference vises som φ-korrigeret værdi (konsistent med
    # resultat-bannerne og snittene i visualiseringen).
    t_uarm_ref = (
        res_1.get("t_uarmeret_phi_kor_mm")
        or res_2.get("t_uarmeret_phi_kor_mm")
        or res_1.get("t_uarmeret_mm")
        or res_2.get("t_uarmeret_mm")
    )

    # Samlet tykkelse af brugerens indtastede opbygning (sum af lagene).
    t_indtastet = sum(
        float(m.get("tykkelse_mm") or 0) for m in materialer
    ) or None

    return [
        ("Valgt geonet", geonet.get("navn", "—")),
        ("Uarmeret referenceopbygning", _mm(t_uarm_ref)),
        ("Samlet tykkelse af valgt opbygning", _mm(t_indtastet)),
        ("Armeret tykkelse — 1 lag", _mm(res_1.get("t_armeret_mm"))),
        ("Armeret tykkelse — 2 lag", _mm(res_2.get("t_armeret_mm"))),
    ]


# ---------------------------------------------------------------------------
# 4. Skabelon-normalisering (workaround for docxtpl 0.20-bug)
# ---------------------------------------------------------------------------

_NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _forbered_skabelon(docx_bytes: bytes) -> bytes:
    """Normaliser skabelonen så docxtpl kan rendere row-loops korrekt.

    Workaround for to kendte docxtpl-problemer:
      1. Word splitter Jinja-tags på tværs af flere <w:r>/<w:t>-elementer
         (med <w:proofErr/> imellem). docxtpl genkender ikke tags der ikke
         er sammenhængende — så vi konsoliderer dem programmatisk.
      2. docxtpl 0.20.x fjerner hele <w:tr> hvis både {%tr for%} og
         {%tr endfor %} står i samme række. Vi splitter sådanne 1-rækkers
         løkker til 3 rækker (start-marker / dataræk / slut-marker).
    """
    import zipfile
    from lxml import etree

    with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as zin:
        entries = [(item, zin.read(item.filename)) for item in zin.infolist()]

    for i, (item, data) in enumerate(entries):
        if item.filename != "word/document.xml":
            continue
        # Fjern proofErr-tags der ofte ligger mellem fragmenterede runs.
        ren_xml = re.sub(r"<w:proofErr[^/]*/>", "", data.decode("utf-8"))
        root = etree.fromstring(ren_xml.encode("utf-8"))

        _konsolider_jinja_tags(root)
        _normaliser_tr_syntax(root)
        _split_row_loops(root)

        entries[i] = (item, etree.tostring(
            root, xml_declaration=True, encoding="UTF-8", standalone=True,
        ))
        break

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for item, data in entries:
            zout.writestr(item, data)
    return buf.getvalue()


def _konsolider_jinja_tags(root) -> None:
    """Slå Jinja-tags sammen til ét <w:t>-element pr. tag."""
    w_p = f"{{{_NS_W}}}p"
    w_t = f"{{{_NS_W}}}t"
    pat = re.compile(r"\{\{[^}]*\}\}|\{%[^%]*%\}")
    xml_space = "{http://www.w3.org/XML/1998/namespace}space"

    for p in list(root.iter(w_p)):
        # Loop indtil ingen flere fragmenterede tags i denne paragraf
        while True:
            ts = p.findall(f".//{w_t}")
            if not ts:
                break
            positions = []
            kombineret = ""
            for idx, t in enumerate(ts):
                tx = t.text or ""
                positions.append((len(kombineret), len(kombineret) + len(tx), idx))
                kombineret += tx
            fundet = False
            for m in pat.finditer(kombineret):
                start, end = m.start(), m.end()
                first_idx = last_idx = None
                for ps, pe, idx in positions:
                    if first_idx is None and ps <= start < pe:
                        first_idx = idx
                    if ps < end <= pe:
                        last_idx = idx
                        break
                if first_idx is None or last_idx is None or first_idx == last_idx:
                    continue
                first_off = start - positions[first_idx][0]
                last_off = end - positions[last_idx][0]
                before = (ts[first_idx].text or "")[:first_off]
                after = (ts[last_idx].text or "")[last_off:]
                ny_tekst = before + m.group(0)
                ts[first_idx].text = ny_tekst
                if ny_tekst != ny_tekst.strip():
                    ts[first_idx].set(xml_space, "preserve")
                for j in range(first_idx + 1, last_idx):
                    ts[j].text = ""
                ts[last_idx].text = after
                fundet = True
                break
            if not fundet:
                break


def _normaliser_tr_syntax(root) -> None:
    """Sørg for at {%tr ...%}-tags har ingen mellemrum mellem {% og tr."""
    w_t = f"{{{_NS_W}}}t"
    for t in root.iter(w_t):
        if t.text and "{%" in t.text:
            t.text = re.sub(r"\{%\s+tr\s+", "{%tr ", t.text)


def _split_row_loops(root) -> None:
    """Hvis en <w:tr> indeholder BÅDE {%tr for ...%} og {%tr endfor %},
    så splittes rækken til 3: en marker-række med for-tagget, dataræk
    uden tags, og marker-række med endfor-tagget.

    docxtpl 0.20 fjerner ellers hele rækken og taber for-direktivet.
    """
    from copy import deepcopy

    w_tr = f"{{{_NS_W}}}tr"
    w_t = f"{{{_NS_W}}}t"
    w_p = f"{{{_NS_W}}}p"

    re_for = re.compile(r"\{%tr\s+for\s[^%]*%\}")
    re_endfor = re.compile(r"\{%tr\s+endfor\s*%\}")

    for tr in list(root.iter(w_tr)):
        # Saml al tekst i denne række
        ts = tr.findall(f".//{w_t}")
        samlet = "".join(t.text or "" for t in ts)
        m_for = re_for.search(samlet)
        m_endfor = re_endfor.search(samlet)
        if not (m_for and m_endfor):
            continue  # Ingen 1-rækker-loop — skip

        for_tag = m_for.group(0)
        endfor_tag = m_endfor.group(0)

        # Dataræk: original kopi med for/endfor-tags fjernet fra cellerne
        data_row = deepcopy(tr)
        for t in data_row.findall(f".//{w_t}"):
            if not t.text:
                continue
            t.text = re_for.sub("", t.text)
            t.text = re_endfor.sub("", t.text)

        # Start-marker række: kopi af data_row, men med kun for-tagget
        start_row = deepcopy(data_row)
        for_indsat = False
        for t in start_row.findall(f".//{w_t}"):
            if not for_indsat:
                t.text = for_tag
                for_indsat = True
            else:
                t.text = ""
        # Fjern alle andre paragraffer end den første i hver celle
        # (for at undgå tomme linjer i markørrækken)
        # Faktisk: bare lad dem være, de skader ikke

        # Slut-marker række: tilsvarende med endfor-tagget
        end_row = deepcopy(data_row)
        end_indsat = False
        for t in end_row.findall(f".//{w_t}"):
            if not end_indsat:
                t.text = endfor_tag
                end_indsat = True
            else:
                t.text = ""

        # Erstat den oprindelige tr med 3 nye
        parent = tr.getparent()
        idx = list(parent).index(tr)
        parent.remove(tr)
        parent.insert(idx, end_row)
        parent.insert(idx, data_row)
        parent.insert(idx, start_row)


# ---------------------------------------------------------------------------
# 5. DOCX-bygger
# ---------------------------------------------------------------------------

def byg_rapport_docx(data: dict) -> bytes:
    """Byg Word-rapporten ud fra det fælles data-dict.

    data:
      metadata: dict med projekt/beskrivelse/omfang/udfoeres_for/sagsbehandler/sagsbehandler_mail/dato
      dim:      dict fra st.session_state["sidste_dim"]
      tekster:  dict[str, str] — redigerede skabelon-tekster pr. SECTION_KEYS-nøgle
      visualisering_png: bytes  (opbygnings-snittene)
      designdiagram_png: bytes | None  (personligt designdiagram, valgfrit)
    """
    from docxtpl import DocxTemplate, InlineImage
    from docx.shared import Cm

    if not DOCX_SKABELON_PATH.exists():
        raise RuntimeError(
            "Rapport-skabelonen mangler: "
            f"{DOCX_SKABELON_PATH}. Gendan filen før der genereres."
        )

    # docxtpl 0.20 fjerner hele rækken hvis {%tr for%} og {%tr endfor%} står
    # i samme <w:tr>. Vi normaliserer skabelonen i hukommelsen så hver
    # row-loop er fordelt over 3 rækker (start-marker / dataræk / slut-marker).
    skabelon_bytes = _forbered_skabelon(DOCX_SKABELON_PATH.read_bytes())
    doc = DocxTemplate(io.BytesIO(skabelon_bytes))

    md = data.get("metadata", {})
    dim = data.get("dim", {})
    tekster = data.get("tekster", {})
    visu = data.get("visualisering_png")
    designdiagram = data.get("designdiagram_png")

    # Visualiseringsbilledet pakkes som InlineImage så docxtpl kan
    # indsætte det hvor {{ visualisering }} står i skabelonen.
    visu_obj = None
    if visu:
        visu_obj = InlineImage(doc, io.BytesIO(visu), width=Cm(16))

    # Personligt designdiagram (valgfrit). Indsættes hvor {{ designdiagram }}
    # står i skabelonen. Hvis None bliver placeholderen til tom streng.
    designdiagram_obj = None
    if designdiagram:
        designdiagram_obj = InlineImage(
            doc, io.BytesIO(designdiagram), width=Cm(16),
        )

    # Bring tabel-rækker på det format docxtpl forventer for {%tr ... %}-løkken.
    def _rows(par_funktion) -> list[dict]:
        return [{"label": k, "vaerdi": v} for k, v in par_funktion(dim)]

    # Hjælper: returner brugerredigeret tekst, eller standardtekst hvis ingen.
    def _tekst(nøgle: str) -> str:
        return tekster.get(nøgle) or STANDARD_TEKSTER.get(nøgle, "")

    context = {
        # Header / projekt-metadata
        "projekt": (md.get("projekt") or "").strip(),
        "beskrivelse": (md.get("beskrivelse") or "").strip(),
        "omfang": (md.get("omfang") or "").strip(),
        "udfoeres_for": (md.get("udfoeres_for") or "").strip(),
        "sagsbehandler": (md.get("sagsbehandler") or "").strip(),
        "sagsbehandler_mail": (md.get("sagsbehandler_mail") or "").strip(),
        "dato": _format_dato_dk(md.get("dato", "")),

        # Tabeller (rendered af {%tr for r in ... %}-løkker i skabelonen)
        "dim_grundlag": _rows(formatér_dimensioneringsgrundlag),
        "dim_resultat": _rows(formatér_dimensioneringsresultat),

        # Editerbare skabelon-tekster
        "tekst_oplyste_forudsaetninger": _tekst("oplyste_forudsaetninger"),
        "tekst_generelle_forudsaetninger": _tekst("generelle_forudsaetninger"),
        "tekst_krav_komprimering": _tekst("krav_komprimering"),
        "tekst_dim_sikkerhed": _tekst("dim_sikkerhed"),
        "tekst_udfoerelse": _tekst("udfoerelse"),
        "tekst_kontrolplan": _tekst("kontrolplan"),
        "tekst_projekteringsansvar": _tekst("projekteringsansvar"),

        # Visualisering — tom streng hvis ingen snit valgt
        "visualisering": visu_obj if visu_obj is not None else "",
        # Personligt designdiagram — tom streng hvis ikke valgt
        "designdiagram": designdiagram_obj if designdiagram_obj is not None else "",
    }

    doc.render(context)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 5. PDF-konvertering (DOCX er eneste layout-kilde)
# ---------------------------------------------------------------------------

def konverter_docx_til_pdf(docx_bytes: bytes) -> bytes:
    """Konverter Word-bytes til PDF-bytes via Microsoft Word/docx2pdf.

    Streamlit kører i en baggrundstråd hvor Windows COM-systemet ikke er
    initialiseret. docx2pdf styrer Word gennem COM, så vi initialiserer det
    selv via pythoncom (kommer med pywin32 som docx2pdf afhænger af).
    """
    try:
        from docx2pdf import convert
    except ImportError as exc:
        raise RuntimeError(
            "PDF-konvertering kræver pakken 'docx2pdf'. Installer "
            "requirements.txt og prøv igen."
        ) from exc

    # COM-initialisering på Windows. Idempotent — sikker at kalde flere
    # gange i samme tråd.
    com_initialiseret = False
    try:
        import pythoncom  # type: ignore
        pythoncom.CoInitialize()
        com_initialiseret = True
    except ImportError:
        pass  # pythoncom kun tilgængelig på Windows
    except Exception:
        pass  # allerede initialiseret eller anden COM-fejl — gå videre

    try:
        with tempfile.TemporaryDirectory(prefix="geonet_rapport_") as tmp_dir:
            tmp_path = Path(tmp_dir)
            docx_path = tmp_path / "rapport.docx"
            pdf_path = tmp_path / "rapport.pdf"
            docx_path.write_bytes(docx_bytes)

            try:
                convert(str(docx_path), str(pdf_path))
            except Exception as exc:
                # Behold den oprindelige fejlbesked så brugeren kan se hvad
                # der gik galt (typisk Word-licens/dialog/låst fil).
                raise RuntimeError(
                    f"docx2pdf-fejl: {exc.__class__.__name__}: {exc}"
                ) from exc

            if not pdf_path.exists():
                raise RuntimeError(
                    "Konverteringen kørte uden fejl, men der blev ikke "
                    "skrevet en PDF-fil. Tjek at Microsoft Word ikke kørte "
                    "med dialog/license-prompt åben."
                )

            return pdf_path.read_bytes()
    finally:
        if com_initialiseret:
            try:
                import pythoncom  # type: ignore
                pythoncom.CoUninitialize()
            except Exception:
                pass


def byg_rapport_pdf(data: dict) -> bytes:
    """Byg Word-rapporten og konverter samme dokument til PDF."""
    return konverter_docx_til_pdf(byg_rapport_docx(data))
