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
    byg_rapport_pdf(data)      - returnerer PDF som bytes
"""

from __future__ import annotations

import io
from dataclasses import dataclass

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


SECTION_KEYS = [
    "generelle_forudsaetninger",
    "krav_komprimering",
    "dim_sikkerhed",
    "udfoerelse",
    "kontrolplan",
    "projekteringsansvar",
]

SECTION_TITLER = {
    "generelle_forudsaetninger": "Generelle dimensioneringsforudsætninger for MSL opbygning",
    "krav_komprimering": "Krav til komprimering",
    "dim_sikkerhed": "Dimensionering og sikkerhed",
    "udfoerelse": "Udførelse",
    "kontrolplan": "Kontrolplan",
    "projekteringsansvar": "Projekteringsansvar",
}

STANDARD_TEKSTER = {
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
    "Tlf. 5948 9000 | www.byggros.com\n"
    "Skaber sikre løsninger"
)


# ---------------------------------------------------------------------------
# 2. Visualisering (matplotlib)
# ---------------------------------------------------------------------------

@dataclass
class Snit:
    titel: str
    t_baerelag_mm: float | None
    geonet_y_fracs: list[float]
    ikke_defineret_tekst: str | None = None


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
    # afgør hvor mange mm pr. tegne-enhed.
    t_max = max(
        (s.t_baerelag_mm for s in snit_liste if s.t_baerelag_mm is not None),
        default=500.0,
    )
    t_max = max(t_max, 300.0)  # mindst 300 mm-skala så små opbygninger ikke ser ekstremt små ud

    n = len(snit_liste)
    fig_w = 3.6 * n
    fig_h = 5.4
    fig, axes = plt.subplots(1, n, figsize=(fig_w, fig_h), dpi=dpi)
    if n == 1:
        axes = [axes]

    # Højde-enheder i "data": baerelag rækker fra y=0 (bund af bærelag)
    # op til t_max + lidt luft. Underbund tegnes som blok under y=0.
    underbund_h = 100.0  # mm "højde" på underbundsblokken (kun visuelt)
    top_y = t_max * 1.05
    bund_y = -underbund_h

    for ax, s in zip(axes, snit_liste):
        ax.set_xlim(0, 1)
        ax.set_ylim(bund_y, top_y)
        ax.set_aspect("auto")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

        # Titel
        ax.set_title(s.titel, fontsize=11, fontweight="bold", pad=8)

        if s.t_baerelag_mm is None:
            # Stiplet placeholder
            besked = s.ikke_defineret_tekst or "Ikke defineret"
            rect = Rectangle(
                (0.15, 0), 0.7, t_max,
                facecolor="#F5F5F5", edgecolor="#BDBDBD",
                linewidth=1, linestyle="--",
            )
            ax.add_patch(rect)
            ax.text(
                0.5, t_max / 2, besked,
                ha="center", va="center",
                fontsize=10, color="#888", style="italic",
            )
            # Underbund
            ub = Rectangle(
                (0.15, bund_y), 0.7, underbund_h,
                facecolor="#A89377", edgecolor="#5C4A33", linewidth=1,
                hatch="///",
            )
            ax.add_patch(ub)
            ax.text(
                0.5, bund_y + underbund_h * 0.45, "Underbund",
                ha="center", va="center", fontsize=10,
                fontweight="bold", color="white",
            )
            ax.text(
                0.5, bund_y + underbund_h * 0.18, f"Eu = {eu:g} MPa",
                ha="center", va="center", fontsize=9, color="white",
            )
            continue

        t = float(s.t_baerelag_mm)

        # Bærelag
        baerelag = Rectangle(
            (0.15, 0), 0.7, t,
            facecolor="#E8E8E8", edgecolor="#666", linewidth=1,
            hatch="..",
        )
        ax.add_patch(baerelag)

        # Geonet-linjer (rød, stiplet) — y_frac=0 = top af bærelag, y_frac=1 = bund
        for frac in s.geonet_y_fracs:
            y = t * (1.0 - frac)  # konverter fra "top-down" til "bund-up"
            ax.hlines(
                y, 0.13, 0.87,
                colors="#D32F2F", linestyles=(0, (4, 2)), linewidth=1.8,
            )

        # Bærelag-tekst placeret i øverste rene strækning
        if s.geonet_y_fracs:
            øverste_frac = min(s.geonet_y_fracs)
            tekst_y = t * (1.0 - øverste_frac / 2)
        else:
            tekst_y = t * 0.5
        ax.text(
            0.5, tekst_y, "Bærelag",
            ha="center", va="center",
            fontsize=10, fontweight="bold", color="#333",
        )

        # mm-label i venstre side
        ax.annotate(
            f"↕ {t:.0f} mm",
            xy=(0.06, t / 2),
            ha="center", va="center",
            fontsize=10, fontweight="bold", color="#333",
        )

        # Geonet-navn til højre ved hver geonet-linje
        for frac in s.geonet_y_fracs:
            y = t * (1.0 - frac)
            ax.annotate(
                geonet_label,
                xy=(0.88, y),
                ha="left", va="center",
                fontsize=8, color="#D32F2F",
            )

        # Underbund-blok
        ub = Rectangle(
            (0.15, bund_y), 0.7, underbund_h,
            facecolor="#A89377", edgecolor="#5C4A33", linewidth=1,
            hatch="///",
        )
        ax.add_patch(ub)
        ax.text(
            0.5, bund_y + underbund_h * 0.45, "Underbund",
            ha="center", va="center", fontsize=10,
            fontweight="bold", color="white",
        )
        ax.text(
            0.5, bund_y + underbund_h * 0.18, f"Eu = {eu:g} MPa",
            ha="center", va="center", fontsize=9, color="white",
        )

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
    geonet = dim.get("geonet") or {}
    materialer = dim.get("materialer") or []
    return [
        ("Underbundens E-modul (Eu)", f"{dim.get('eu', 0):g} MPa"),
        ("Krævet overflade E-modul (Eo)", f"{dim.get('eo', 0):g} MPa"),
        ("Belastningsklasse", str(dim.get("valgt_klasse", "—"))),
        ("Vægtet friktionsvinkel (φ)", f"{dim.get('phi', 35):.1f}°"),
        ("Materialeopbygning", _materiale_resume(materialer)),
        ("Valgt geonet", geonet.get("navn", "—")),
        ("Korrektion", f"{geonet.get('korrektion', 0):+.0%}"),
    ]


def formatér_dimensioneringsresultat(dim: dict) -> list[tuple[str, str]]:
    """Nøgle/værdi-rækker til Dimensioneringsresultat-tabellen."""
    res_1 = dim.get("res_1") or {}
    res_2 = dim.get("res_2") or {}
    geonet = dim.get("geonet") or {}

    def _mm(v):
        return f"{v:.0f} mm" if isinstance(v, (int, float)) else "—"

    def _pct(v):
        return f"{v:.1f} %" if isinstance(v, (int, float)) else "—"

    t_uarm = res_1.get("t_uarmeret_mm") or res_2.get("t_uarmeret_mm")

    return [
        ("Valgt produkt", geonet.get("navn", "—")),
        ("Uarmeret reference", _mm(t_uarm)),
        ("Armeret tykkelse — 1 lag", _mm(res_1.get("t_armeret_mm"))),
        ("Reduktion — 1 lag", _pct(res_1.get("reduktion_pct"))),
        ("Armeret tykkelse — 2 lag", _mm(res_2.get("t_armeret_mm"))),
        ("Reduktion — 2 lag", _pct(res_2.get("reduktion_pct"))),
    ]


# ---------------------------------------------------------------------------
# 4. DOCX-bygger
# ---------------------------------------------------------------------------

def byg_rapport_docx(data: dict) -> bytes:
    """Byg Word-rapporten ud fra det fælles data-dict.

    data:
      metadata: dict med projekt/beskrivelse/omfang/udfoeres_for/sagsbehandler/dato/rapportnr
      dim:      dict fra st.session_state["sidste_dim"]
      tekster:  dict[str, str] — redigerede skabelon-tekster pr. SECTION_KEYS-nøgle
      grundlag_ekstra: str — brugerfritekst i Dimensioneringsgrundlag (fx grundvandsspejl)
      visualisering_png: bytes
    """
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Pt, RGBColor

    doc = Document()

    # Sidemargener
    for section in doc.sections:
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin = Cm(2.2)
        section.right_margin = Cm(2.2)

    md = data.get("metadata", {})
    dim = data.get("dim", {})
    tekster = data.get("tekster", {})
    grundlag_ekstra = (data.get("grundlag_ekstra") or "").strip()
    visu = data.get("visualisering_png")

    # Titel
    titel_p = doc.add_paragraph()
    titel_run = titel_p.add_run(RAPPORT_TITEL)
    titel_run.bold = True
    titel_run.font.size = Pt(14)
    titel_p.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # Metadata-blok
    for label, key in [
        ("Projekt", "projekt"),
        ("Beskrivelse", "beskrivelse"),
        ("Omfang", "omfang"),
        ("Udføres for", "udfoeres_for"),
        ("Sagsbehandler", "sagsbehandler"),
        ("Rapport-nr.", "rapportnr"),
        ("Dato", "dato"),
    ]:
        v = (md.get(key) or "").strip()
        if not v:
            continue
        p = doc.add_paragraph()
        r1 = p.add_run(f"{label}: ")
        r1.bold = True
        p.add_run(v)

    doc.add_paragraph()  # luft

    # Dimensioneringsgrundlag
    _docx_overskrift(doc, "Dimensioneringsgrundlag")
    doc.add_paragraph("Følgende forudsætninger er lagt til grund for dimensioneringen:")
    _docx_tovejs_tabel(doc, formatér_dimensioneringsgrundlag(dim))
    if grundlag_ekstra:
        doc.add_paragraph()
        for linje in grundlag_ekstra.split("\n"):
            doc.add_paragraph(linje)

    # Generelle dimensioneringsforudsætninger
    _docx_overskrift(doc, SECTION_TITLER["generelle_forudsaetninger"])
    _docx_flerlinje(doc, tekster.get(
        "generelle_forudsaetninger",
        STANDARD_TEKSTER["generelle_forudsaetninger"],
    ))

    # Dimensioneringsresultat
    _docx_overskrift(doc, "Dimensioneringsresultat")
    doc.add_paragraph(
        "Baseret på ovennævnte indgangsparametre kan vi foreslå følgende "
        "MSL opbygning:"
    )
    _docx_tovejs_tabel(doc, formatér_dimensioneringsresultat(dim))
    if visu:
        doc.add_paragraph()
        doc.add_picture(io.BytesIO(visu), width=Cm(16))

    # Skabelon-sektioner
    for nøgle in ("krav_komprimering", "dim_sikkerhed", "udfoerelse",
                   "kontrolplan", "projekteringsansvar"):
        _docx_overskrift(doc, SECTION_TITLER[nøgle])
        _docx_flerlinje(doc, tekster.get(nøgle, STANDARD_TEKSTER[nøgle]))

    # Footer-linje
    doc.add_paragraph()
    foot_p = doc.add_paragraph()
    foot_r = foot_p.add_run(BYGGROS_FOOTER)
    foot_r.font.size = Pt(8)
    foot_r.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _docx_overskrift(doc, tekst: str) -> None:
    from docx.shared import Pt
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(tekst + ":")
    r.bold = True
    r.font.size = Pt(12)


def _docx_flerlinje(doc, tekst: str) -> None:
    """Tilføj en tekstblok hvor blank-linje markerer nyt afsnit."""
    afsnit = [a.strip() for a in tekst.split("\n\n") if a.strip()]
    for a in afsnit:
        doc.add_paragraph(a)


def _docx_tovejs_tabel(doc, raekker: list[tuple[str, str]]) -> None:
    from docx.shared import Cm, Pt

    tabel = doc.add_table(rows=len(raekker), cols=2)
    tabel.autofit = False
    for i, (nøgle, vaerdi) in enumerate(raekker):
        celle_a = tabel.rows[i].cells[0]
        celle_b = tabel.rows[i].cells[1]
        celle_a.width = Cm(6.0)
        celle_b.width = Cm(10.0)
        # Nøgle med fed
        p_a = celle_a.paragraphs[0]
        r_a = p_a.add_run(nøgle)
        r_a.bold = True
        r_a.font.size = Pt(10)
        # Værdi — kan indeholde linjebrud
        p_b = celle_b.paragraphs[0]
        linjer = str(vaerdi).split("\n")
        p_b.add_run(linjer[0]).font.size = Pt(10)
        for linje in linjer[1:]:
            extra = celle_b.add_paragraph()
            extra.add_run(linje).font.size = Pt(10)


# ---------------------------------------------------------------------------
# 5. PDF-bygger (reportlab)
# ---------------------------------------------------------------------------

def byg_rapport_pdf(data: dict) -> bytes:
    """Byg PDF-rapporten ud fra det fælles data-dict."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
        PageBreak,
    )
    from reportlab.lib.enums import TA_LEFT

    md = data.get("metadata", {})
    dim = data.get("dim", {})
    tekster = data.get("tekster", {})
    grundlag_ekstra = (data.get("grundlag_ekstra") or "").strip()
    visu = data.get("visualisering_png")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2.2 * cm, rightMargin=2.2 * cm,
        topMargin=2.0 * cm, bottomMargin=2.2 * cm,
        title=RAPPORT_TITEL,
    )

    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle(
        "normal_da", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10, leading=13, alignment=TA_LEFT,
    )
    style_titel = ParagraphStyle(
        "titel", parent=styles["Title"],
        fontName="Helvetica-Bold", fontSize=14, leading=18,
        spaceAfter=10, alignment=TA_LEFT,
    )
    style_overskrift = ParagraphStyle(
        "overskrift", parent=style_normal,
        fontName="Helvetica-Bold", fontSize=11.5, leading=15,
        spaceBefore=10, spaceAfter=4,
    )
    style_footer = ParagraphStyle(
        "footer", parent=style_normal,
        fontName="Helvetica", fontSize=8, leading=10,
        textColor=colors.grey,
    )

    story = []

    # Titel
    story.append(Paragraph(RAPPORT_TITEL, style_titel))

    # Metadata
    for label, key in [
        ("Projekt", "projekt"),
        ("Beskrivelse", "beskrivelse"),
        ("Omfang", "omfang"),
        ("Udføres for", "udfoeres_for"),
        ("Sagsbehandler", "sagsbehandler"),
        ("Rapport-nr.", "rapportnr"),
        ("Dato", "dato"),
    ]:
        v = (md.get(key) or "").strip()
        if not v:
            continue
        story.append(Paragraph(
            f"<b>{label}:</b> {_escape_xml(v)}", style_normal,
        ))
    story.append(Spacer(1, 0.4 * cm))

    # Dimensioneringsgrundlag
    story.append(Paragraph("Dimensioneringsgrundlag:", style_overskrift))
    story.append(Paragraph(
        "Følgende forudsætninger er lagt til grund for dimensioneringen:",
        style_normal,
    ))
    story.append(Spacer(1, 0.2 * cm))
    story.append(_pdf_tovejs_tabel(formatér_dimensioneringsgrundlag(dim)))
    if grundlag_ekstra:
        story.append(Spacer(1, 0.3 * cm))
        for linje in grundlag_ekstra.split("\n"):
            if linje.strip():
                story.append(Paragraph(_escape_xml(linje), style_normal))

    # Generelle dimensioneringsforudsætninger
    story.append(Paragraph(
        SECTION_TITLER["generelle_forudsaetninger"] + ":",
        style_overskrift,
    ))
    _pdf_flerlinje(story, tekster.get(
        "generelle_forudsaetninger",
        STANDARD_TEKSTER["generelle_forudsaetninger"],
    ), style_normal)

    # Dimensioneringsresultat
    story.append(Paragraph("Dimensioneringsresultat:", style_overskrift))
    story.append(Paragraph(
        "Baseret på ovennævnte indgangsparametre kan vi foreslå følgende "
        "MSL opbygning:",
        style_normal,
    ))
    story.append(Spacer(1, 0.2 * cm))
    story.append(_pdf_tovejs_tabel(formatér_dimensioneringsresultat(dim)))
    if visu:
        story.append(Spacer(1, 0.3 * cm))
        img = Image(io.BytesIO(visu), width=16 * cm, height=10 * cm,
                    kind="proportional")
        story.append(img)

    # Skabelon-sektioner
    for nøgle in ("krav_komprimering", "dim_sikkerhed", "udfoerelse",
                   "kontrolplan", "projekteringsansvar"):
        story.append(Paragraph(SECTION_TITLER[nøgle] + ":", style_overskrift))
        _pdf_flerlinje(
            story, tekster.get(nøgle, STANDARD_TEKSTER[nøgle]),
            style_normal,
        )

    # Footer
    story.append(Spacer(1, 1.0 * cm))
    story.append(Paragraph(_escape_xml(BYGGROS_FOOTER).replace("\n", "<br/>"),
                           style_footer))

    doc.build(story)
    return buf.getvalue()


def _pdf_tovejs_tabel(raekker: list[tuple[str, str]]):
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT

    style_celle = ParagraphStyle(
        "celle", parent=getSampleStyleSheet()["Normal"],
        fontName="Helvetica", fontSize=9.5, leading=12, alignment=TA_LEFT,
    )
    style_celle_b = ParagraphStyle(
        "celle_b", parent=style_celle,
        fontName="Helvetica-Bold",
    )

    data = [
        [
            Paragraph(_escape_xml(str(k)), style_celle_b),
            Paragraph(_escape_xml(str(v)).replace("\n", "<br/>"), style_celle),
        ]
        for k, v in raekker
    ]
    t = Table(data, colWidths=[6 * cm, 10 * cm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, colors.lightgrey),
    ]))
    return t


def _pdf_flerlinje(story, tekst: str, style) -> None:
    from reportlab.platypus import Paragraph, Spacer
    from reportlab.lib.units import cm

    afsnit = [a.strip() for a in tekst.split("\n\n") if a.strip()]
    for i, a in enumerate(afsnit):
        story.append(Paragraph(
            _escape_xml(a).replace("\n", "<br/>"), style,
        ))
        if i < len(afsnit) - 1:
            story.append(Spacer(1, 0.15 * cm))


def _escape_xml(s: str) -> str:
    """Escape de tre tegn der bryder reportlabs mini-XML."""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
