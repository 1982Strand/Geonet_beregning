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
    "    • Dimensionsgivende trafikbelastning: T6\n"
    "    • Vingestyrke, Cv, skønnet i planum: > 100 kPa\n"
    "    • Grundvandsspejl: ikke oplyst/ikke relevant\n"
    "    • Bærelagsmaterialer:\n"
    "            o Genbrugsstabil"
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
    materialer = dim.get("materialer") or []
    return [
        ("Underbundens E-modul (Eu)", f"{dim.get('eu', 0):g} MPa"),
        ("Forventet overflademodul (Eo)", f"{dim.get('eo', 0):g} MPa"),
        ("Belastningsklasse", str(dim.get("valgt_klasse", "—"))),
        ("Materialeopbygning", _materiale_resume(materialer)),
        ("Vægtet friktionsvinkel (φ)", f"{dim.get('phi', 35):.1f}°"),
    ]


def formatér_dimensioneringsresultat(dim: dict) -> list[tuple[str, str]]:
    """Nøgle/værdi-rækker til Dimensioneringsresultat-tabellen."""
    res_1 = dim.get("res_1") or {}
    res_2 = dim.get("res_2") or {}
    geonet = dim.get("geonet") or {}

    def _mm(v):
        return f"{v:.0f} mm" if isinstance(v, (int, float)) else "—"

    t_uarm = res_1.get("t_uarmeret_mm") or res_2.get("t_uarmeret_mm")

    return [
        ("Valgt geonet", geonet.get("navn", "—")),
        ("Uarmeret reference", _mm(t_uarm)),
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
      visualisering_png: bytes
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

    # Visualiseringsbilledet pakkes som InlineImage så docxtpl kan
    # indsætte det hvor {{ visualisering }} står i skabelonen.
    visu_obj = None
    if visu:
        visu_obj = InlineImage(doc, io.BytesIO(visu), width=Cm(16))

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
