"""
Datatabeller til Geonet Dimensioneringsværktøj.

Hver tabel angiver sin kilde i sit afsnitshoved. None svarer til "—" og
betyder, at kombinationen ligger uden for diagrammets gyldighedsområde.

Ingen imports herfra må være UI-relaterede (Streamlit, Flask, osv.).
"""

import math

# Gyldige Eo-værdier (svarer til de 6 belastningsklasser)
EO_KOLONNER = [30, 45, 60, 80, 120, 150]


# ---------------------------------------------------------------------------
# 1. Diagramdata og opslagstabel
#    Kilde: designdiagram 1–6 i designmanualerne for Tensar og GS-GRID
#    (side 10), aflæst af manualernes vektorgrafik, jf.
#    diagrambilleder/kontrol_aflaesning.md.
#
#    DESIGNDIAGRAM_AFLAESTE_PUNKTER er de markerede punkter på kurverne som
#    (t [cm], Eu [MPa]). Tykkelserne ligger på hele 10 cm, og Eu er afrundet
#    til nærmeste 0,5 MPa. Diagramtabellerne dannes heraf ved lineær
#    interpolation til hele Eu, jf. _interpoler_kurve(). Kurverne er i
#    manualen tegnet som rette linjestykker mellem punkterne, så
#    interpolationen gengiver den tegnede kurve. Der ekstrapoleres ikke.
#
#    Diagramdataene er eneste grundlag; opslagstabellen T_BASIS_TABLE dannes
#    af dem nedenfor, jf. _t_basis_table_from_designdiagrammer(). Redigeres
#    diagrammerne i appen, dannes tabellen på ny af de redigerede værdier,
#    jf. generer_t_basis_table_fra_diagrammer() i app.py.
# ---------------------------------------------------------------------------

DESIGNDIAGRAM_AFLAESTE_PUNKTER = {
    1: {
        # Punktet ved 100 cm er ved gennemsyn fastsat til Eu = 4 MPa;
        # vektorgrafikken giver 3,42 MPa, jf. kontrolfilens afsnit 7.
        "t_uarmeret_cm": [(0, 30), (10, 25), (20, 21), (30, 18), (40, 14.5), (50, 12),
                          (60, 9.5), (70, 8), (80, 6), (90, 5), (100, 4), (110, 3)],
        "t_1_lag_cm": [(20, 15), (30, 11.5), (40, 9), (50, 6.5), (60, 5), (70, 3),
                       (80, 2), (90, 0.5)],
        "t_2_lag_cm": [],
    },
    2: {
        "t_uarmeret_cm": [(0, 45), (10, 36), (20, 29), (30, 23), (40, 18.5), (50, 15),
                          (60, 12), (70, 10), (80, 8), (90, 6), (100, 5), (110, 3.5),
                          (120, 3), (130, 2.5)],
        "t_1_lag_cm": [(20, 20), (30, 16), (40, 12), (50, 9), (60, 6), (70, 4.5),
                       (80, 3), (90, 2), (100, 1)],
        "t_2_lag_cm": [(50, 6.5), (60, 4.5), (70, 3), (80, 2), (90, 1)],
    },
    3: {
        "t_uarmeret_cm": [(10, 45), (20, 36), (30, 29), (40, 23), (50, 18.5), (60, 15),
                          (70, 12), (80, 10), (90, 8), (100, 6), (110, 5), (120, 3.5),
                          (130, 3), (140, 2.5)],
        "t_1_lag_cm": [(20, 27), (30, 20), (40, 16), (50, 12), (60, 9), (70, 6.5),
                       (80, 4.5), (90, 3), (100, 1.5), (110, 1)],
        "t_2_lag_cm": [(50, 9), (60, 6.5), (70, 4.5), (80, 2.5), (90, 1.5), (100, 1)],
    },
    4: {
        "t_uarmeret_cm": [(20, 45), (30, 36), (40, 29), (50, 23), (60, 18.5), (70, 15),
                          (80, 12), (90, 10), (100, 8), (110, 6), (120, 5), (130, 3.5),
                          (140, 3), (150, 2.5)],
        "t_1_lag_cm": [(20, 33), (30, 26), (40, 20), (50, 14), (60, 10.5), (70, 7.5),
                       (80, 5.5), (90, 4), (100, 3), (110, 2), (120, 1)],
        "t_2_lag_cm": [(60, 8), (70, 6), (80, 4), (90, 3), (100, 2), (110, 1)],
    },
    5: {
        "t_uarmeret_cm": [(30, 45), (40, 36), (50, 29), (60, 23), (70, 18.5), (80, 15),
                          (90, 12), (100, 10), (110, 8), (120, 6), (130, 5), (140, 3.5),
                          (150, 3), (160, 2.5)],
        "t_1_lag_cm": [(30, 33), (40, 25), (50, 19), (60, 13.5), (70, 9.5), (80, 8),
                       (90, 6), (100, 4.5), (110, 2.5), (120, 2), (130, 1)],
        "t_2_lag_cm": [(50, 14), (60, 10), (70, 8), (80, 6), (90, 4.5), (100, 3),
                       (110, 2), (120, 1)],
    },
    6: {
        "t_uarmeret_cm": [(40, 45), (50, 36), (60, 29), (70, 23), (80, 18.5), (90, 15),
                          (100, 12), (110, 10), (120, 8), (130, 6), (140, 5), (150, 3.5),
                          (160, 3), (170, 2.5)],
        "t_1_lag_cm": [(40, 32), (50, 24), (60, 17), (70, 12), (80, 8.5), (90, 6),
                       (100, 4.5), (110, 3.5), (120, 2.5), (130, 1.5), (140, 1)],
        "t_2_lag_cm": [(50, 18), (60, 12), (70, 9), (80, 6.5), (90, 4.5), (100, 3),
                       (110, 2.5), (120, 1.5), (130, 0.5)],
    },
}

# Diagrammets Eo [MPa] og den største Eu [MPa], tabellen opstilles for.
_DIAGRAM_AKSER = {1: (30, 30), 2: (45, 45), 3: (60, 45), 4: (80, 45),
                  5: (120, 45), 6: (150, 45)}
_DIAGRAM_FELTER = ("t_uarmeret_cm", "t_1_lag_cm", "t_2_lag_cm")


def _interpoler_kurve(punkter: list[tuple[float, float]], eu: float) -> float | None:
    """Kurvens tykkelse [cm] ved eu, afrundet til én decimal.

    Tykkelsen bestemmes ved lineær interpolation mellem de to aflæste
    punkter, der omslutter eu. Ligger eu uden for kurvens første eller
    sidste punkt, returneres None.
    """
    pts = sorted((e, t) for t, e in punkter)
    if not pts or not pts[0][0] <= eu <= pts[-1][0]:
        return None
    for (e1, t1), (e2, t2) in zip(pts, pts[1:]):
        if e1 <= eu <= e2:
            t = t1 + (eu - e1) / (e2 - e1) * (t2 - t1)
            return math.floor(round(t * 10, 6) + 0.5) / 10
    return float(pts[0][1])


DESIGNDIAGRAM_RAW_TABLES = [
    {
        "diagram_nr": nr,
        "eo": eo,
        "klasse": nr,
        "image_name": f"Diagram {nr}.png",
        "rows": [
            {"eu": eu, **{
                felt: _interpoler_kurve(DESIGNDIAGRAM_AFLAESTE_PUNKTER[nr][felt], eu)
                for felt in _DIAGRAM_FELTER
            }}
            for eu in range(1, eu_max + 1)
        ],
    }
    for nr, (eo, eu_max) in _DIAGRAM_AKSER.items()
]

# Tabelcellerne, der ligger i et aflæst punkt og derfor ikke er interpoleret:
#    DESIGNDIAGRAM_AFLAESTE_CELLER[diagram_nr] → {(eu, felt), ...}
DESIGNDIAGRAM_AFLAESTE_CELLER = {
    nr: {
        (int(e), felt)
        for felt, punkter in kurver.items()
        for _, e in punkter
        if e == int(e) and 1 <= e <= _DIAGRAM_AKSER[nr][1]
    }
    for nr, kurver in DESIGNDIAGRAM_AFLAESTE_PUNKTER.items()
}


def _t_basis_table_from_designdiagrammer(diagrammer: list[dict]) -> dict:
    """Byg beregningstabellen direkte fra diagramtabellernes Eu-rækker."""
    table: dict = {}
    tom = {"uarmeret": None, "1_lag": None, "2_lag": None}

    for diagram in diagrammer:
        eo = diagram["eo"]
        for row in diagram["rows"]:
            eu = row["eu"]
            table.setdefault(eu, {})
            table[eu][eo] = {
                "uarmeret": row.get("t_uarmeret_cm"),
                "1_lag": row.get("t_1_lag_cm"),
                "2_lag": row.get("t_2_lag_cm"),
            }

    for eu_data in table.values():
        for eo in EO_KOLONNER:
            eu_data.setdefault(eo, tom.copy())

    return {eu: table[eu] for eu in sorted(table)}


# Opslagstabellen, beregningerne slår op i.
#    Struktur: T_BASIS_TABLE[eu_mpa][eo_mpa][lag_type] → tykkelse i cm
#    lag_type: "uarmeret" | "1_lag" | "2_lag"
#    None = "—" = uden for diagrammets gyldighedsområde
#    Eu-rækker (MPa): 1-45 i hele trin · Eo-kolonner (MPa): 30, 45, 60, 80,
#    120, 150
T_BASIS_TABLE = _t_basis_table_from_designdiagrammer(DESIGNDIAGRAM_RAW_TABLES)

# Sorteret liste over alle Eu-nøgler.
EU_RAEKKER = sorted(T_BASIS_TABLE.keys())


# ---------------------------------------------------------------------------
# 2. BELASTNINGSKLASSER
# ---------------------------------------------------------------------------

BELASTNINGSKLASSER = {
    1: {
        "eo": 30,
        "navn": "Klasse 1 - Begrænset belastning",
        "belastning": "Begrænset belastning",
        "anvendelse": "Cykelstier, midlertidige byggeveje",
    },
    2: {
        "eo": 45,
        "navn": "Klasse 2 - Større belastning",
        "belastning": "Større belastning",
        "anvendelse": "Markveje, midlertidige byggeveje med større belastning",
    },
    3: {
        "eo": 60,
        "navn": "Klasse 3 - Let trafik",
        "belastning": "Let trafik (akseltryk ≤ 6 t)",
        "anvendelse": "Villaveje, p-pladser for personbiler",
    },
    4: {
        "eo": 80,
        "navn": "Klasse 4 - Middel trafik",
        "belastning": "Middel trafik (akseltryk ≤ 8 t)",
        "anvendelse": "Middel trafikerede veje, p-arealer, flydende gulve i lagerhaller",
    },
    5: {
        "eo": 120,
        "navn": "Klasse 5 - Tung trafik",
        "belastning": "Tung trafik (akseltryk ≤ 12 t)",
        "anvendelse": "Hovedveje, amtsveje, containerpladser",
    },
    6: {
        "eo": 150,
        "navn": "Klasse 6 - Meget tung trafik",
        "belastning": "Meget tung trafik (akseltryk ≤ 15 t)",
        "anvendelse": "Landingsbaner, p-arealer for meget tunge køretøjer",
    },
}


# ---------------------------------------------------------------------------
# 2c. TRAFIKKLASSER + KORRELATION_T_EO
#
#     Dokumenteret bro fra Vejdirektoratets trafikklasser (T1–T6) til appens
#     designdiagrammer. Dette er en beregnet/tilbageberegnet korrelation —
#     ikke en vurdering ud fra anvendelse: for hver (trafikklasse, Eu) er den
#     ækvivalente Eo fundet
#     som den Eo, hvis ustabiliserede diagram-tykkelse netop svarer til
#     VejDims krævede ubundne lagtykkelse (SG + BL). Reduktionen aflæses
#     derefter som diagrammets EGEN feltdokumenterede værdi ved (Eo_ækv, Eu).
#     Der blandes ingen kriterier fra de to metoder — VejDim placerer kun
#     driftspunktet, geonet-diagrammet leverer reduktionen.
#
#     Grundlag: 36 VejDim-kørsler (standard E-værdier), juli 2026. Fuld
#     dokumentation: "Dokumenter og data/Korrelation_trafikklasse_Eo.md".
#     Reproducerbart script: "Dokumenter og data/korrelation_final.py".
#
#     Værdier = Eo_ækv i MPa (1-decimals præcision, bag den afrundede tabel i
#     notatets §4). Strengene UNDER/OVER = uden for diagrammets dækning:
#       UNDER: VejDim kræver mindre end diagrammets Eo=30-kurve (blød bund ×
#              lav klasse).
#       OVER:  VejDim kræver mere end Eo=150-kurven (stiv bund × høj klasse).
#     Håndteringen fastlægges af reglerne under »Håndtering uden for
#     diagrammets område« nedenfor.
# ---------------------------------------------------------------------------

TRAFIK_UNDER = "under"
TRAFIK_OVER = "over"
# Cellen har ingen kørselsdata endnu (ubundet tykkelse = 0).
TRAFIK_MANGLER = "mangler"

# De Eu-værdier (MPa) korrelationen er tabuleret ved. Eu = 3 og 4 er medtaget,
# fordi designdiagrammerne dækker dem (ved Eu ≤ 2 findes ingen uarmeret kurve,
# så en tilbageberegning er umulig dér uanset kørsler).
TRAFIK_EU_PUNKTER = [3, 4, 5, 10, 15, 20, 30, 40]

# ---------------------------------------------------------------------------
# VEJDIM_KOERSLER — datagrundlaget (de rå kørsler)
#
#   De 36 kørsler ligger som standardrækker herunder og redigeres direkte i
#   appen (🚦 Trafikklasse-korrelation). Brugerens ændringer gemmes af appen;
#   "Nulstil til standard" bringer tabellen tilbage til rækkerne herunder.
#
#   VEJDIM_KOERSLER_STANDARD_RAEKKER: én dict pr. (T, Eu) med alle rådata —
#       asfaltpakke (navn + tykkelse pr. lag), vist asfalt-E, de ubundne lag
#       (navn + tykkelse: sg = stabilgrus SG II, bl = bundsikring BL II),
#       styrende levetid og bemærkning. Totaler er IKKE gemt: de udledes af
#       berig_koersel_raekker, så de aldrig kan komme i modstrid med
#       lagtykkelserne.
#
#   Eo_ækv tilbageberegnes af korrelation_fra_koersler ud fra sg + bl.
#   Fuld dokumentation: "Dokumenter og data/Korrelation_trafikklasse_Eo.md".
# ---------------------------------------------------------------------------

# De ubundne materialer er de samme i alle kørsler, jf. forudsætningerne:
# SG II (E = 300) over BL II U≤3 (E = 100). Navnene indgår som redigerbare
# felter, så en kørsel med andre materialer kan indtastes.
UBUNDET_BAERELAG_STANDARD = "SG II"
BUNDSIKRING_STANDARD = "BL II U≤3"


def _kd(T, eu, slid, t_slid, binde, t_binde, bundet, t_bundet, e_asf, sg, bl,
        levetid, bem="", ubundet_baerelag=UBUNDET_BAERELAG_STANDARD,
        bundsikring=BUNDSIKRING_STANDARD):
    return {
        "T": T, "eu": eu,
        "slidlag": slid, "t_slid_mm": float(t_slid),
        "bindelag": binde, "t_bindelag_mm": float(t_binde),
        "bundet_baerelag": bundet, "t_bundet_mm": float(t_bundet),
        "E_asf_vist_MPa": float(e_asf),
        "ubundet_baerelag": ubundet_baerelag, "t_SG_mm": float(sg),
        "bundsikring": bundsikring, "t_BL_mm": float(bl),
        "levetid_styrende_aar": float(levetid), "bemaerkning": bem,
    }


_SG_MIN = "SGII begrænset til minimumstykkelse 100"
_SG_BL_MIN = _SG_MIN + " og BLII begrænset til minimumstykkelse 200"
_VEJDIM_BEREGNER = "VejDim beregner tykkelsen af det bundne bærelag"

VEJDIM_KOERSLER_STANDARD_RAEKKER = [
    _kd("T1",  3, "AB 1000", 40, "-", 0, "-", 0, 1000, 170, 448, 0),
    _kd("T1",  4, "AB 1000", 40, "-", 0, "-", 0, 1000, 120, 470, 0),
    _kd("T1",  5, "AB 1000", 40, "-", 0, "-", 0, 1000, 110, 450, 20.2),
    _kd("T1", 10, "AB 1000", 40, "-", 0, "-", 0, 1000, 100, 356, 20, _SG_MIN),
    _kd("T1", 15, "AB 1000", 40, "-", 0, "-", 0, 1000, 100, 292, 20.2, _SG_MIN),
    _kd("T1", 20, "AB 1000", 40, "-", 0, "-", 0, 1000, 100, 243, 20.1, _SG_MIN),
    _kd("T1", 30, "AB 1000", 40, "-", 0, "-", 0, 1000, 100, 200, 29.6, _SG_BL_MIN),
    _kd("T1", 40, "AB 1000", 40, "-", 0, "-", 0, 1000, 100, 200, 30.1, _SG_BL_MIN),
    _kd("T2",  3, "AB 1000", 40, "-", 0, "GAB 0 2000", 74, 1690, 180, 866, 0),
    _kd("T2",  4, "AB 1000", 40, "-", 0, "GAB 0 2000", 74, 1690, 180, 797, 0),
    _kd("T2",  5, "AB 1000", 40, "-", 0, "GAB 0 2000", 74, 1690, 170, 757, 20.1),
    _kd("T2", 10, "AB 1000", 40, "-", 0, "GAB 0 2000", 74, 1690, 170, 590, 20),
    _kd("T2", 15, "AB 1000", 40, "-", 0, "GAB 0 2000", 73, 1680, 160, 508, 20.1),
    _kd("T2", 20, "AB 1000", 40, "-", 0, "GAB 0 2000", 73, 1680, 160, 439, 20.1),
    _kd("T2", 30, "AB 1000", 40, "-", 0, "GAB 0 2000", 72, 1671, 160, 337, 20.2),
    _kd("T2", 40, "AB 1000", 40, "-", 0, "GAB 0 2000", 72, 1671, 160, 264, 20.1),
    _kd("T3",  3, "AB 1000", 40, "-", 0, "GAB 0 2000", 95, 1862, 200, 957, 0),
    _kd("T3",  4, "AB 1000", 40, "-", 0, "GAB 0 2000", 95, 1862, 200, 879, 0),
    _kd("T3",  5, "AB 1000", 40, "-", 0, "GAB 0 2000", 95, 1862, 200, 818, 20),
    _kd("T3", 10, "AB 1000", 40, "-", 0, "GAB 0 2000", 94, 1854, 190, 649, 20.1),
    _kd("T3", 15, "AB 1000", 40, "-", 0, "GAB 0 2000", 94, 1854, 190, 539, 20.1),
    _kd("T3", 20, "AB 1000", 40, "-", 0, "GAB 0 2000", 94, 1854, 190, 460, 20),
    _kd("T3", 30, "AB 1000", 40, "-", 0, "GAB 0 2000", 94, 1854, 200, 334, 20),
    _kd("T3", 40, "AB 1000", 40, "-", 0, "GAB 0 2000", 94, 1854, 200, 255, 20.1),
    _kd("T4",  3, "AB 2000", 40, "-", 0, "GAB 0 2000", 125, 2362, 240, 1107, 0, _VEJDIM_BEREGNER),
    _kd("T4",  4, "AB 2000", 40, "-", 0, "GAB 0 2000", 125, 2362, 240, 1014, 0, _VEJDIM_BEREGNER),
    _kd("T4",  5, "AB 2000", 40, "-", 0, "GAB 0 2000", 125, 2362, 240, 944, 20, _VEJDIM_BEREGNER),
    _kd("T4", 10, "AB 2000", 40, "-", 0, "GAB 0 2000", 125, 2362, 230, 739, 20, _VEJDIM_BEREGNER),
    _kd("T4", 15, "AB 2000", 40, "-", 0, "GAB 0 2000", 123, 2355, 220, 629, 20.1, _VEJDIM_BEREGNER),
    _kd("T4", 20, "AB 2000", 40, "-", 0, "GAB 0 2000", 123, 2355, 220, 537, 20, _VEJDIM_BEREGNER),
    _kd("T4", 30, "AB 2000", 40, "-", 0, "GAB 0 2000", 123, 2355, 230, 392, 20.1, _VEJDIM_BEREGNER),
    _kd("T4", 40, "AB 2000", 40, "-", 0, "GAB 0 2000", 123, 2355, 230, 301, 20, _VEJDIM_BEREGNER),
    _kd("T5",  3, "AB 2000", 40, "-", 0, "GAB I 3000", 132, 3456, 270, 1224, 0, _VEJDIM_BEREGNER),
    _kd("T5",  4, "AB 2000", 40, "-", 0, "GAB I 3000", 132, 3456, 270, 1119, 0, _VEJDIM_BEREGNER),
    _kd("T5",  5, "AB 2000", 40, "-", 0, "GAB I 3000", 132, 3456, 270, 1042, 20, _VEJDIM_BEREGNER),
    _kd("T5", 10, "AB 2000", 40, "-", 0, "GAB I 3000", 131, 3448, 260, 818, 20.1, _VEJDIM_BEREGNER),
    _kd("T5", 15, "AB 2000", 40, "-", 0, "GAB I 3000", 131, 3448, 250, 689, 20, _VEJDIM_BEREGNER),
    _kd("T5", 20, "AB 2000", 40, "-", 0, "GAB I 3000", 130, 3440, 250, 590, 20.1, _VEJDIM_BEREGNER),
    _kd("T5", 30, "AB 2000", 40, "-", 0, "GAB I 3000", 130, 3440, 240, 459, 20.1, _VEJDIM_BEREGNER),
    _kd("T5", 40, "AB 2000", 40, "-", 0, "GAB I 3000", 129, 3432, 240, 360, 20.1, _VEJDIM_BEREGNER),
    _kd("T6",  3, "SMA 3000", 40, "-", 0, "GAB II 3000", 144, 3829, 290, 1290, 0, _VEJDIM_BEREGNER),
    _kd("T6",  4, "SMA 3000", 40, "-", 0, "GAB II 3000", 143, 3823, 280, 1199, 0, _VEJDIM_BEREGNER),
    _kd("T6",  5, "SMA 3000", 40, "-", 0, "GAB II 3000", 142, 3817, 280, 1117, 20, _VEJDIM_BEREGNER),
    _kd("T6", 10, "SMA 3000", 40, "-", 0, "GAB II 3000", 141, 3811, 270, 876, 20, _VEJDIM_BEREGNER),
    _kd("T6", 15, "SMA 3000", 40, "-", 0, "GAB II 3000", 141, 3811, 270, 723, 20, _VEJDIM_BEREGNER),
    _kd("T6", 20, "SMA 3000", 40, "-", 0, "GAB II 3000", 141, 3811, 260, 629, 20, _VEJDIM_BEREGNER),
    _kd("T6", 30, "SMA 3000", 40, "-", 0, "GAB II 3000", 140, 3805, 260, 478, 20, _VEJDIM_BEREGNER),
    _kd("T6", 40, "SMA 3000", 40, "-", 0, "GAB II 3000", 140, 3805, 260, 370, 20.1, _VEJDIM_BEREGNER),
]


def berig_koersel_raekker(raekker: list[dict]) -> list[dict]:
    """Tilføj de afledte totaler til hver række.

    "t_ubundet_total_mm" = SG + BL (indgår i tilbageberegningen af Eo_ækv)
    "t_befaestelse_total_mm" = alle lag (asfaltpakke + SG + BL) — relevant for
    frostkontrollen. Begge udledes altid, så de ikke kan blive forældede.
    """
    ud = []
    for r in raekker:
        sg = float(r.get("t_SG_mm") or 0)
        bl = float(r.get("t_BL_mm") or 0)
        bundne = (
            float(r.get("t_slid_mm") or 0)
            + float(r.get("t_bindelag_mm") or 0)
            + float(r.get("t_bundet_mm") or 0)
        )
        ud.append({
            **r,
            "t_ubundet_total_mm": sg + bl,
            "t_befaestelse_total_mm": bundne + sg + bl,
        })
    return ud


def koersler_fra_raekker(raekker: list[dict]) -> dict:
    """Byg {T: {Eu: {"sg", "bl"}}} fra rækkerne — det korrelationen bruger."""
    ud: dict = {}
    for r in raekker:
        t = str(r.get("T") or "").strip()
        try:
            eu = int(float(r.get("eu")))
        except (TypeError, ValueError):
            continue
        if not t:
            continue
        ud.setdefault(t, {})[eu] = {
            "sg": float(r.get("t_SG_mm") or 0),
            "bl": float(r.get("t_BL_mm") or 0),
        }
    return ud


VEJDIM_KOERSLER_RAEKKER = berig_koersel_raekker(VEJDIM_KOERSLER_STANDARD_RAEKKER)
VEJDIM_KOERSLER = koersler_fra_raekker(VEJDIM_KOERSLER_RAEKKER)


def back_beregn_eo_aekv(
    eu: float, ubundet_mm: float, t_basis_table: dict | None = None
) -> tuple[float | None, str, float]:
    """Tilbageberegn den ækvivalente Eo for en ubundet tykkelse ved given Eu.

    Finder den Eo, hvis ustabiliserede diagram-tykkelse (uarmeret) ved eu netop
    svarer til ``ubundet_mm``, ved lineær interpolation mellem Eo-kolonnerne.
    Returnerer (eo_aekv, zone, skala):
        "ok":      eo_aekv er et tal, og skala er 1,0.
        "under":   ubundet < diagrammets tyndeste kurve (blød bund × lav klasse).
        "over":    ubundet > den tykkeste kurve (stiv bund × høj klasse).
        "udenfor": Eu-rækken findes ikke / ingen uarmeret-data.

    Uden for diagrammets område er eo_aekv den nærmeste randkurve, og skala er
    forholdet mellem VejDims krævede tykkelse og randkurvens egen tykkelse.
    Aflæses randkurven og ganges den med skala, fås en opbygning, hvis
    ustabiliserede tykkelse er VejDims — mens reduktionen forbliver
    diagrammets egen, jf. afsnittet om yderområderne i
    "Korrelation_trafikklasse_Eo.md". I zonen ok er skala per konstruktion
    1,0, og opslaget er dermed uændret.

    Randkurverne findes som de yderste Eo-kolonner **med data** — ikke som
    faste 30/150 — så en redigeret diagramtabel ikke kan give et opslag i en
    tom kolonne.
    """
    table = t_basis_table or T_BASIS_TABLE
    row = table.get(eu)
    if not row:
        return None, "udenfor", 1.0
    pts = sorted(
        [(eo, row[eo]["uarmeret"] * 10.0)
         for eo in EO_KOLONNER
         if row.get(eo, {}).get("uarmeret") is not None],
        key=lambda p: p[1],
    )
    if not pts:
        return None, "udenfor", 1.0
    if ubundet_mm < pts[0][1]:
        eo_rand, t_rand = pts[0]
        return float(eo_rand), TRAFIK_UNDER, ubundet_mm / t_rand
    if ubundet_mm > pts[-1][1]:
        eo_rand, t_rand = pts[-1]
        return float(eo_rand), TRAFIK_OVER, ubundet_mm / t_rand
    for (e1, t1), (e2, t2) in zip(pts, pts[1:]):
        if t1 <= ubundet_mm <= t2:
            eo = (e1 + (ubundet_mm - t1) / (t2 - t1) * (e2 - e1)) if t2 > t1 else float(e1)
            return eo, "ok", 1.0
    return None, "udenfor", 1.0


# ---------------------------------------------------------------------------
# Håndtering uden for diagrammets område (zonerne under og over)
#
#   Ligger VejDims ubundne tykkelse uden for diagrammets ustabiliserede
#   kurver, afgør reglerne herunder, hvad der regnes med. Afvigelsen måles i
#   procent af randkurvens tykkelse:
#
#       over:   (t_VejDim − t_rand) / t_rand
#       under:  (t_rand − t_VejDim) / t_rand
#
#   og holdes op mod en tolerance for hver retning. Mulige håndteringer:
#
#       vejdim   den ustabiliserede tykkelse er VejDims; randkurvens
#                tykkelser skaleres med t_VejDim / t_rand, så geonettets
#                procentvise reduktion er randkurvens
#       laveste  diagrammets laveste kurve anvendes uændret (kun under)
#       afvis    intet driftspunkt; opbygningen kræver manuel vurdering
#
#   Over inden for tolerancen regnes altid med VejDims tykkelse. Reglerne
#   indstilles under Indstillinger, jf. app.render_indstillinger og
#   PLAN_korrelation_over_under.md.
# ---------------------------------------------------------------------------

YDER_VEJDIM = "vejdim"
YDER_LAVESTE = "laveste"
YDER_AFVIS = "afvis"

UNDER_INDEN_VALG: tuple[str, ...] = (YDER_LAVESTE, YDER_VEJDIM)
OVER_UDEN_VALG: tuple[str, ...] = (YDER_AFVIS, YDER_VEJDIM)
UNDER_UDEN_VALG: tuple[str, ...] = (YDER_AFVIS, YDER_LAVESTE, YDER_VEJDIM)

MAKS_TOLERANCE_PCT = 50.0

STANDARD_YDER_REGLER: dict = {
    "tolerance_over_pct": 5.0,
    "tolerance_under_pct": 5.0,
    "under_inden": YDER_LAVESTE,
    "over_uden": YDER_AFVIS,
    "under_uden": YDER_AFVIS,
}

# Regler, hvor alt uden for kurverne afvises. Anvendes, hvor der skal vises
# en gennemført tilbageberegning mellem to kurver, fx regneeksemplet på
# korrelationssiden.
STRENGE_YDER_REGLER: dict = {
    **STANDARD_YDER_REGLER,
    "tolerance_over_pct": 0.0,
    "tolerance_under_pct": 0.0,
}


def normaliser_yder_regler(regler: dict | None) -> dict:
    """Udfyld manglende felter og afvis ugyldige værdier."""
    ud = dict(STANDARD_YDER_REGLER)
    if not isinstance(regler, dict):
        return ud
    for felt in ("tolerance_over_pct", "tolerance_under_pct"):
        v = regler.get(felt)
        if (
            isinstance(v, (int, float)) and not isinstance(v, bool)
            and not math.isnan(v)
        ):
            ud[felt] = float(min(max(v, 0.0), MAKS_TOLERANCE_PCT))
    for felt, valg in (
        ("under_inden", UNDER_INDEN_VALG),
        ("over_uden", OVER_UDEN_VALG),
        ("under_uden", UNDER_UDEN_VALG),
    ):
        if regler.get(felt) in valg:
            ud[felt] = regler[felt]
    return ud


def _opslag_for_tykkelse(
    eu: float,
    tykkelse: float,
    t_basis_table: dict | None,
    yder_regler: dict | None,
) -> dict:
    """Opslagspunktet for VejDims ubundne tykkelse ved eu, jf. trafik_opslag()."""
    ud = {
        "eo": None, "zone": "udenfor", "skala": 1.0,
        "afvigelse_pct": None, "tolerance_pct": None,
        "inden_tolerance": None, "handling": None,
        "t_vejdim_mm": tykkelse, "t_rand_mm": None, "eo_rand": None,
    }
    eo, zone, skala_raa = back_beregn_eo_aekv(float(eu), tykkelse, t_basis_table)
    ud["zone"] = zone
    if zone == "ok":
        ud["eo"] = eo
        return ud
    if zone not in (TRAFIK_UNDER, TRAFIK_OVER) or eo is None or not skala_raa:
        return ud
    regler = normaliser_yder_regler(yder_regler)
    if zone == TRAFIK_OVER:
        afvigelse = (skala_raa - 1.0) * 100.0
        tolerance = regler["tolerance_over_pct"]
        inden = afvigelse <= tolerance + 1e-9
        handling = YDER_VEJDIM if inden else regler["over_uden"]
    else:
        afvigelse = (1.0 - skala_raa) * 100.0
        tolerance = regler["tolerance_under_pct"]
        inden = afvigelse <= tolerance + 1e-9
        handling = regler["under_inden"] if inden else regler["under_uden"]
    ud.update(
        eo_rand=float(eo), t_rand_mm=tykkelse / skala_raa,
        afvigelse_pct=afvigelse, tolerance_pct=tolerance,
        inden_tolerance=inden, handling=handling,
    )
    if handling != YDER_AFVIS:
        ud["eo"] = float(eo)
        ud["skala"] = skala_raa if handling == YDER_VEJDIM else 1.0
    return ud


def trafik_opslag(
    t_klasse: str,
    eu: float,
    koersler: dict | None = None,
    t_basis_table: dict | None = None,
    yder_regler: dict | None = None,
) -> dict:
    """Opslagspunktet for en trafikklasse ved given Eu, med håndteringen uden
    for diagrammets område.

    Returnerer en dict:

        eo               Eₒ,ækv i MPa, eller None, når der ikke er noget
                         driftspunkt (uden for de kørte punkter, eller
                         afvist uden for kurverne)
        zone             "ok" | "under" | "over" | "udenfor"
        skala            faktoren på randkurvens tykkelser, jf.
                         calculator.beregn(); 1,0 inden for kurverne og ved
                         håndteringen »laveste«
        afvigelse_pct    afvigelsen fra randkurven i procent (under/over)
        tolerance_pct    tolerancen for retningen
        inden_tolerance  om afvigelsen er inden for tolerancen
        handling         "vejdim" | "laveste" | "afvis" (under/over)
        t_vejdim_mm      VejDims krævede ubundne tykkelse
        t_rand_mm        randkurvens ustabiliserede tykkelse (under/over)
        eo_rand          randkurvens Eₒ (under/over)

    yder_regler er reglerne for zonerne under og over; None giver
    standardreglerne, jf. STANDARD_YDER_REGLER.
    """
    tykkelse = trafik_ubundet_tykkelse(t_klasse, eu, koersler)
    if tykkelse is None:
        return {
            "eo": None, "zone": "udenfor", "skala": 1.0,
            "afvigelse_pct": None, "tolerance_pct": None,
            "inden_tolerance": None, "handling": None,
            "t_vejdim_mm": None, "t_rand_mm": None, "eo_rand": None,
        }
    return _opslag_for_tykkelse(eu, tykkelse, t_basis_table, yder_regler)


def korrelation_fra_koersler(
    koersler: dict, t_basis_table: dict | None = None,
    yder_regler: dict | None = None,
) -> dict:
    """Byg korrelationstabellen (T → Eu → Eo_ækv/'under'/'over') fra de rå
    VejDim-kørsler ved tilbageberegning mod designdiagrammet.

    Celleværdien kan være enten den ubundne total i mm (tal) eller en dict med
    "sg"/"bl" (som VEJDIM_KOERSLER). Kun summen SG+BL indgår i broen —
    fordelingen mellem lagene har ingen betydning for Eo_ækv.

    Cellerne uden for diagrammets område bærer randkurvens Eo, når
    reglerne i yder_regler lader dem regne med, og ellers zonestrengen, jf.
    trafik_opslag(). Detaljerne pr. celle fås af korrelation_opslag().
    """
    korr: dict = {}
    for t_klasse, raekker in koersler.items():
        korr[t_klasse] = {}
        for eu, v in raekker.items():
            if isinstance(v, dict):
                ub = (v.get("sg") or 0) + (v.get("bl") or 0)
            else:
                ub = float(v or 0)
            if ub <= 0:
                # Ingen kørsel endnu — cellen indgår ikke i broen.
                korr[t_klasse][int(eu)] = TRAFIK_MANGLER
                continue
            opslag = _opslag_for_tykkelse(
                float(eu), float(ub), t_basis_table, yder_regler,
            )
            if opslag["eo"] is not None:
                korr[t_klasse][int(eu)] = opslag["eo"]
            else:
                korr[t_klasse][int(eu)] = opslag["zone"]
    return korr


def korrelation_opslag(
    koersler: dict, t_basis_table: dict | None = None,
    yder_regler: dict | None = None,
) -> dict:
    """Som korrelation_fra_koersler(), men med hele opslaget pr. celle, jf.
    trafik_opslag(). Celler uden kørselsdata får zonen »mangler«."""
    ud: dict = {}
    for t_klasse, raekker in koersler.items():
        ud[t_klasse] = {}
        for eu, v in raekker.items():
            if isinstance(v, dict):
                ub = (v.get("sg") or 0) + (v.get("bl") or 0)
            else:
                ub = float(v or 0)
            if ub <= 0:
                ud[t_klasse][int(eu)] = {"eo": None, "zone": TRAFIK_MANGLER}
                continue
            ud[t_klasse][int(eu)] = _opslag_for_tykkelse(
                float(eu), float(ub), t_basis_table, yder_regler,
            )
    return ud


# Standard-korrelationen, tilbageberegnet fra VEJDIM_KOERSLER mod diagrammet.
# Notatets §4 er beregnet mod den hidtidige diagramtabel; efter rettelsen af
# diagramtabellerne 24.09.2026 afviger enkelte celler fra notatet.
KORRELATION_T_EO = korrelation_fra_koersler(VEJDIM_KOERSLER, T_BASIS_TABLE)

# Metadata pr. trafikklasse. naae10_mio_20aar = NÆ10 over 20 års
# dimensioneringsperiode (mio.), som brugt i VejDim-kørslerne (jf. notatets §2).
# Trafikklasser efter håndbogens Figur 4.1. Felterne tunge_koeretoejer,
# naae10_doegn og naae10_aar er gengivet direkte derfra; naae10_mio_20aar er
# naae10_aar × 20 år. Feltet anvendelse er ikke fra håndbogen, men en
# vejledende angivelse af typiske vejtyper i klassen.
TRAFIKKLASSER = {
    "T1": {
        "ikon": "🚲", "naae10_mio_20aar": 0.0015,
        "beskrivelse": "Meget let trafik",
        "tunge_koeretoejer": "≤ 1", "naae10_doegn": "0,5", "naae10_aar": "75",
        "anvendelse": "Fortove, cykelstier, stisystemer og mindre boligveje "
                      "uden bustrafik",
    },
    "T2": {
        "ikon": "🚜", "naae10_mio_20aar": 0.146,
        "beskrivelse": "Let trafik",
        "tunge_koeretoejer": "≤ 65", "naae10_doegn": "20", "naae10_aar": "7.300",
        "anvendelse": "Lokale boligveje og samleveje med begrænset "
                      "servicetrafik",
    },
    "T3": {
        "ikon": "🚗", "naae10_mio_20aar": 0.366,
        "beskrivelse": "Let–middel trafik",
        "tunge_koeretoejer": "65 til 120", "naae10_doegn": "50",
        "naae10_aar": "18.300",
        "anvendelse": "Lokale boligveje og samleveje med begrænset "
                      "servicetrafik",
    },
    "T4": {
        "ikon": "🚛", "naae10_mio_20aar": 1.46,
        "beskrivelse": "Middel trafik",
        "tunge_koeretoejer": "120 til 560", "naae10_doegn": "200",
        "naae10_aar": "73.000",
        "anvendelse": "Bybusruter, erhvervsveje og hovedfordelingsveje",
    },
    "T5": {
        "ikon": "🏗️", "naae10_mio_20aar": 3.6,
        "beskrivelse": "Tung trafik",
        "tunge_koeretoejer": "560 til 1.200", "naae10_doegn": "500",
        "naae10_aar": "180.000",
        "anvendelse": "Bybusruter, erhvervsveje og hovedfordelingsveje",
    },
    "T6": {
        "ikon": "✈️", "naae10_mio_20aar": 6.0,
        "beskrivelse": "Meget tung trafik",
        "tunge_koeretoejer": "1.200 til 1.500", "naae10_doegn": "800",
        "naae10_aar": "300.000",
        "anvendelse": "Hovedveje, motortrafikveje og motorveje",
    },
}

TRAFIKKLASSE_NOTE = (
    "Trafikklasse-grundlaget kobler Vejdirektoratets trafikklasser til "
    "designdiagrammerne via en dokumenteret tilbageberegning: VejDim fastlægger "
    "den krævede ubundne lagtykkelse (SG + BL) for (trafikklasse, Eᵤ), og "
    "geonet-reduktionen aflæses som diagrammets egen feltdokumenterede værdi ved "
    "den ækvivalente Eₒ. Grundlaget er rent bæreevne (frostsikker underbund) — "
    "frost/koblingshøjde skal kontrolleres separat. Se "
    "'Korrelation_trafikklasse_Eo.md' for fuld dokumentation og forbehold."
)


def trafik_ubundet_tykkelse(
    t_klasse: str, eu: float, koersler: dict | None = None
) -> float | None:
    """VejDims krævede ubundne tykkelse (SG+BL, mm) ved vilkårligt Eu.

    Mellem to kørte Eu-punkter interpoleres **lineært i log(Eu)**. Tykkelsen
    aftager tilnærmelsesvis retlinet med log(Eu) i hele datasættet, så det
    rammer markant bedre end lineær interpolation i Eu (målt: middelfejl i
    Eo_ækv 2,9 mod 5,5 MPa i en udeladelsestest).

    Punkter uden kørselsdata (SG+BL = 0) springes over — hverken som endepunkt
    eller som interpolationsgrænse. Returnerer None uden for de kørte punkter.
    """
    kk = koersler if koersler is not None else VEJDIM_KOERSLER
    rk = kk.get(t_klasse)
    if not rk:
        return None

    def _total(v) -> float:
        if isinstance(v, dict):
            return float((v.get("sg") or 0) + (v.get("bl") or 0))
        return float(v or 0)

    kendte = sorted(p for p in rk if _total(rk[p]) > 0)
    if not kendte or eu < kendte[0] or eu > kendte[-1] or eu <= 0:
        return None
    if eu in kendte:
        return _total(rk[eu])

    lav = max(p for p in kendte if p <= eu)
    hoej = min(p for p in kendte if p >= eu)
    t_lav, t_hoej = _total(rk[lav]), _total(rk[hoej])
    frac = (math.log(eu) - math.log(lav)) / (math.log(hoej) - math.log(lav))
    return t_lav + frac * (t_hoej - t_lav)


def trafik_eo_aekv(
    t_klasse: str,
    eu: float,
    koersler: dict | None = None,
    t_basis_table: dict | None = None,
    yder_regler: dict | None = None,
) -> tuple[float | None, str, float]:
    """Ækvivalent Eo (MPa) for en trafikklasse ved given Eu.

    Fremgangsmåde: find VejDims krævede ubundne tykkelse ved netop dette Eu
    (interpoleret i log(Eu), se trafik_ubundet_tykkelse) og tilbageberegn
    Eo_ækv **eksakt** mod designdiagrammets række for samme Eu. Zonen bestemmes
    dermed også ved brugerens eget Eu i stedet for at blive arvet fra et
    nabopunkt.

    Returnerer (eo_aekv, zone, skala):
        "ok"      — eo_aekv er et tal; dimensionér via diagrammet.
        "under"   — VejDim kræver mindre end diagrammets tyndeste kurve.
        "over"    — VejDim kræver mere end diagrammets tykkeste kurve.
        "udenfor" — Eu uden for de kørte punkter, eller ukendt trafikklasse.

    Uden for diagrammets område afgør yder_regler, om der regnes på
    randkurven — skaleret til VejDims tykkelse eller uændret — eller om der
    intet driftspunkt er (eo_aekv None), jf. trafik_opslag(), som også
    returnerer afvigelsen og håndteringen. I zonen ok er skala altid 1,0.
    """
    opslag = trafik_opslag(t_klasse, eu, koersler, t_basis_table, yder_regler)
    return opslag["eo"], opslag["zone"], opslag["skala"]


def trafik_eu_interval(
    t_klasse: str, koersler: dict | None = None
) -> tuple[int, int] | None:
    """Mindste og største Eu med kørselsdata for en trafikklasse (til beskeder)."""
    kk = koersler if koersler is not None else VEJDIM_KOERSLER
    rk = kk.get(t_klasse) or {}
    kendte = sorted(
        p for p, v in rk.items()
        if (float((v.get("sg") or 0) + (v.get("bl") or 0))
            if isinstance(v, dict) else float(v or 0)) > 0
    )
    return (kendte[0], kendte[-1]) if kendte else None


def eo_til_naermeste_klasse(eo: float | None) -> int | None:
    """Belastningsklasse hvis Eo-kolonne ligger tættest på eo.

    Bruges KUN til produkt-anbefalingsbadges i trafikklasse-tilstand, hvor
    Eo_ækv sjældent rammer en præcis kolonne. Det er en indeks-tilnærmelse til
    visning, IKKE en fysisk klasse-lighed.
    """
    if eo is None:
        return None
    bedst, bedst_diff = None, None
    for klasse, data in BELASTNINGSKLASSER.items():
        diff = abs(data["eo"] - eo)
        if bedst_diff is None or diff < bedst_diff:
            bedst, bedst_diff = klasse, diff
    return bedst


def trafikklasser_for_belastningsklasser(
    klasser,
    eu: float,
    koersler: dict | None = None,
    t_basis_table: dict | None = None,
    yder_regler: dict | None = None,
) -> list[str]:
    """Hvilke trafikklasser slår op i en af de angivne belastningsklasser?

    Bruges til at oversætte et geonets anbefalede belastningsklasser til
    trafikklasser i produktlisten. Hver trafikklasse får sin Eo_ækv ved dette
    Eu, og den afrundes til nærmeste Eo-kolonne (se eo_til_naermeste_klasse).

    Oversættelsen gælder KUN det Eu, der sendes ind — den er ikke en egenskab
    ved nettet. Den samme trafikklasse rammer vidt forskellige
    belastningsklasser afhængigt af underbunden (T2 spænder fx klasse 1-6 hen
    over Eu 3-40), fordi Eo_ækv stiger med Eu. Klasser uden gyldig Eo_ækv
    ("under"/"over"/"mangler") udelades.
    """
    ks = {int(k) for k in (klasser or [])}
    if not ks:
        return []
    fundet: list[str] = []
    for t_klasse in TRAFIKKLASSER:
        eo, _zone, _skala = trafik_eo_aekv(
            t_klasse, eu, koersler, t_basis_table, yder_regler
        )
        if eo is not None and eo_til_naermeste_klasse(eo) in ks:
            fundet.append(t_klasse)
    return fundet


def format_trafikklasse_interval(t_klasser) -> str:
    """Komprimér trafikklasser til intervaller: ['T3','T4','T5'] → 'T3-T5',
    ['T2','T4'] → 'T2, T4'. Tom liste → '—'. Modstykke til
    format_klasse_interval, men med T-præfiks på begge ender.
    """
    numre = sorted({
        int(str(t)[1:]) for t in (t_klasser or []) if str(t).startswith("T")
    })
    if not numre:
        return "—"
    grupper: list[str] = []
    start = forrige = numre[0]
    for n in numre[1:]:
        if n == forrige + 1:
            forrige = n
            continue
        grupper.append(f"T{start}" if start == forrige else f"T{start}-T{forrige}")
        start = forrige = n
    grupper.append(f"T{start}" if start == forrige else f"T{start}-T{forrige}")
    return ", ".join(grupper)


def format_trafikklasse(t_klasse: str) -> str:
    """Overskriftslinje for en trafikklasse, fx 'T4 — Middel trafik'."""
    d = TRAFIKKLASSER.get(t_klasse)
    return f"{t_klasse} — {d['beskrivelse']}" if d else t_klasse


def trafikklasse_noegletal(t_klasse: str) -> list[tuple[str, str]]:
    """Nøgletal for en trafikklasse som (betegnelse, værdi)-par.

    De tre første par er gengivet efter håndbogens Figur 4.1. Det fjerde er
    den dimensionsgivende trafikbelastning omregnet til dimensioneringsperioden
    på 20 år, og det femte er en vejledende angivelse af typiske vejtyper, som
    ikke indgår i håndbogen.
    """
    d = TRAFIKKLASSER.get(t_klasse)
    if not d:
        return []
    # Absolutte tal med dansk tusindtalsseparator, som i håndbogens Figur 4.1.
    # "0,0015 mio." for T1 ville være svært at sammenholde med årsværdien.
    over_20_aar = f"{d['naae10_mio_20aar'] * 1e6:,.0f}".replace(",", ".")
    return [
        ("Tunge køretøjer pr. døgn, begge retninger", d["tunge_koeretoejer"]),
        ("NÆ10 pr. døgn pr. vognbane (øvre grænse)", d["naae10_doegn"]),
        ("Dimensionsgivende trafikbelastning",
         f"{d['naae10_aar']} NÆ10 pr. år pr. vognbane"),
        ("Svarende til 20 år", f"{over_20_aar} NÆ10"),
        ("Typisk anvendelse", d["anvendelse"]),
    ]


# ---------------------------------------------------------------------------
# 3. CV_TIL_EU
#    Kilde: Excel fane 7.4 (GS-GRID Designmanual fig. 3)
#    Liste af (cv_min, cv_max, eu) - intervallerne er eksklusive forneden,
#    inklusive foroven (dvs. Cv=30 hører til intervallet 0–30 → Eu=5).
# ---------------------------------------------------------------------------

CV_TIL_EU = [
    (0,   30,  5),
    (30,  60,  10),
    (60,  90,  15),
    (90,  120, 20),
    (120, 150, 25),
    (150, 180, 30),
]


# ---------------------------------------------------------------------------
# 4. MATERIAL_DB
#    Kilde: Excel fane 5 "DB Materialer"
#    phi: friktionsvinkel i grader
#    max_korn: maksimal kornstørrelse i mm
#    lagtype: "Bærelag" | "Bundsikring"
#    krav_maskestoerrelse_mm: minimum kvadratisk maskestørrelse (mm) som
#        materialet kræver af et biaksialt geonet. None = intet krav.
#        Bruges kun til biaksiale net (se valider_input A14).
# ---------------------------------------------------------------------------

MATERIAL_DB = [
    {
        "navn": "Bundsikringssand",
        "phi": 37,
        "max_korn": 8,
        "lagtype": "Bundsikring",
        "anvendelse": "Frostsikring og drænlag",
        "krav_maskestoerrelse_mm": 35,
    },
    {
        "navn": "Bundgrus 0-80",
        "phi": 38,
        "max_korn": 80,
        "lagtype": "Bundsikring",
        "anvendelse": "Frostsikring, dræning, bærelag",
        "krav_maskestoerrelse_mm": 65,
    },
    {
        "navn": "Stabilgrus SGI 0-32",
        "phi": 40,
        "max_korn": 32,
        "lagtype": "Bærelag",
        "anvendelse": "Bærelag",
        "krav_maskestoerrelse_mm": 35,
    },
    {
        "navn": "Stabilgrus SGII 0-32",
        "phi": 40,
        "max_korn": 32,
        "lagtype": "Bærelag",
        "anvendelse": "Bærelag",
        "krav_maskestoerrelse_mm": 35,
    },
    {
        "navn": "Knust beton 0-32",
        "phi": 40,
        "max_korn": 32,
        "lagtype": "Bærelag",
        "anvendelse": "Genbrugsmateriale, bærelag",
        "krav_maskestoerrelse_mm": 35,
    },
    {
        "navn": "Skærver 0-32",
        "phi": 45,
        "max_korn": 32,
        "lagtype": "Bærelag",
        "anvendelse": "Bærelag",
        "krav_maskestoerrelse_mm": 35,
    },
    {
        "navn": "Skærver 0-64",
        "phi": 45,
        "max_korn": 64,
        "lagtype": "Bærelag",
        "anvendelse": "Bærelag",
        "krav_maskestoerrelse_mm": 35,
    },
    {
        "navn": "Skærver 0-90",
        "phi": 45,
        "max_korn": 90,
        "lagtype": "Bærelag",
        "anvendelse": "Bærelag (kan også anvendes som bundsikring)",
        "krav_maskestoerrelse_mm": 65,
    },
    {
        "navn": "Skærver 0-120",
        "phi": 45,
        "max_korn": 120,
        "lagtype": "Bundsikring",
        "anvendelse": "Bundsikring",
        "krav_maskestoerrelse_mm": 65,
    },
    {
        "navn": "Skærver 0-150",
        "phi": 45,
        "max_korn": 150,
        "lagtype": "Bundsikring",
        "anvendelse": "Bundsikring grov",
        "krav_maskestoerrelse_mm": 65,
    },
    {
        "navn": "Skærver 0-200",
        "phi": 45,
        "max_korn": 200,
        "lagtype": "Bundsikring",
        "anvendelse": "Bundsikring meget grov",
        "krav_maskestoerrelse_mm": 100,
    },
    {
        "navn": "Skærver 0-250",
        "phi": 45,
        "max_korn": 250,
        "lagtype": "Bundsikring",
        "anvendelse": "Bundsikring ekstrem",
        "krav_maskestoerrelse_mm": 100,
    },
]

# Hjælpeliste - kun navne, bruges til dropdowns
MATERIAL_NAVNE = [m["navn"] for m in MATERIAL_DB] + ["Manuel indtastning"]


# ---------------------------------------------------------------------------
# 5. GEONET_DB
#    Kilde: Excel fane 6 "DB Geonet"
#    korrektion: multiplikativ faktor ift. reference (TX160/SX160/T6 = 0.00)
#                positiv = mindre effektivt = tykkere bærelag
#                negativ = mere effektivt = tyndere bærelag
#    max_korn: maksimal kornstørrelse i mm (None = ikke specificeret/verificeres)
#    min_daklag: minimum dæklag over geonet i cm
#    klasser: liste af gyldige belastningsklasser (1–6)
#    serie: "Tensar" | "GS-GRID" | "E'GRID" | "Manuel"
# ---------------------------------------------------------------------------

GEONET_DB = [
    # --- Tensar-serien ---
    # Tekniske data (trækstyrke, maskestørrelse, dimensioner, GWP) for SS30, HX5.5
    # og HX165 er ikke tilgængelige i de foreliggende kildedokumenter. For NX750 og
    # NX850 findes Product Identification Data Sheets (PIDS, dec. 2024), som leverer
    # identifikations- og holdbarhedsdata, men ikke designværdier.
    # Korrektionsfaktorer og belastningsklasser er fra Tensar Geonet Designmanual sept. 2024.
    {
        "navn": "Tensar SS30",
        "serie": "Tensar",
        "type": "Biaxialt",
        "effektindeks": "90",
        "korrektion": 0.10,
        "max_korn": None,
        "anbefalet_tilslag": None,
        "rudeaabning": None,
        "min_daklag": 20,
        "klasser": [3, 4, 5],
        "radial_stivhed": None,
        "gwp": None,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "maskestoerrelse_datablad_mm": None,
        "gwp_bredder": None,
        "knudepunkt_effektivitet": None,
        "maskestabilitet_Nmm_grad": None,
        "stivhedsforhold": None,
        "min_traekstyrke": None,
        "traekstyrke_2pct": None,
        "traekstyrke_5pct": None,
        "max_deformation_pct": None,
        "ribbetykkelse": None,
        "resistens_kemisk_pct": None,
        "resistens_uv_pct": None,
        "resistens_oxidation_pct": None,
        "resistens_installationsskader": None,
        "bemærkning": "Effektindeks 90. Tekniske specifikationer ikke tilgængelige i foreliggende kildedokumenter.",
    },
    {
        "navn": "Tensar TriAx TX150",
        "serie": "Tensar",
        "type": "Triaxialt",
        "effektindeks": "90",
        "korrektion": 0.10,
        "max_korn": None,
        "anbefalet_tilslag": None,
        "rudeaabning": None,
        "min_daklag": 20,
        "klasser": [1, 2, 3, 4],
        "radial_stivhed": None,
        "gwp": None,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "maskestoerrelse_datablad_mm": None,
        "gwp_bredder": None,
        "knudepunkt_effektivitet": None,
        "maskestabilitet_Nmm_grad": None,
        "stivhedsforhold": None,
        "min_traekstyrke": None,
        "traekstyrke_2pct": None,
        "traekstyrke_5pct": None,
        "max_deformation_pct": None,
        "ribbetykkelse": None,
        "resistens_kemisk_pct": None,
        "resistens_uv_pct": None,
        "resistens_oxidation_pct": None,
        "resistens_installationsskader": None,
        "bemærkning": "Effektindeks 90. Tekniske specifikationer ikke tilgængelige i foreliggende kildedokumenter.",
    },
    {
        "navn": "Tensar HX5.5",
        "serie": "Tensar",
        "type": "Hexagonalt",
        "effektindeks": "95",
        "korrektion": 0.05,
        "max_korn": None,
        "anbefalet_tilslag": None,
        "rudeaabning": None,
        "min_daklag": 20,
        "klasser": [1, 2, 3, 4, 5],
        "radial_stivhed": None,
        "gwp": None,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "maskestoerrelse_datablad_mm": None,
        "gwp_bredder": None,
        "knudepunkt_effektivitet": None,
        "maskestabilitet_Nmm_grad": None,
        "stivhedsforhold": None,
        "min_traekstyrke": None,
        "traekstyrke_2pct": None,
        "traekstyrke_5pct": None,
        "max_deformation_pct": None,
        "ribbetykkelse": None,
        "resistens_kemisk_pct": None,
        "resistens_uv_pct": None,
        "resistens_oxidation_pct": None,
        "resistens_installationsskader": None,
        "bemærkning": "Effektindeks 95. Tekniske specifikationer ikke tilgængelige i foreliggende kildedokumenter.",
    },
    {
        "navn": "Tensar TriAx TX160",
        "serie": "Tensar",
        "type": "Triaxialt",
        "effektindeks": "100",
        "korrektion": 0.00,
        "max_korn": 80,
        "anbefalet_tilslag": "0–80 mm",
        "rudeaabning": "Triangulær, ribbe 40 mm",
        "min_daklag": 20,
        "klasser": [3, 4, 5, 6],
        "radial_stivhed": 390,
        "gwp": None,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "maskestoerrelse_datablad_mm": None,
        "gwp_bredder": None,
        "knudepunkt_effektivitet": "90%",
        "maskestabilitet_Nmm_grad": 390,
        "stivhedsforhold": ">0,75",
        "min_traekstyrke": None,
        "traekstyrke_2pct": None,
        "traekstyrke_5pct": None,
        "max_deformation_pct": None,
        "ribbetykkelse": None,
        "resistens_kemisk_pct": 96,
        "resistens_uv_pct": 98,
        "resistens_oxidation_pct": 90,
        "resistens_installationsskader": ">87%",
        "bemærkning": "REFERENCE (Tensar-design) - effektindeks 100. Maks. tid uden afdækning: < 2 uger.",
    },
    {
        "navn": "Tensar HX165",
        "serie": "Tensar",
        "type": "Hexagonalt",
        "effektindeks": "105",
        "korrektion": -0.05,
        "max_korn": None,
        "anbefalet_tilslag": None,
        "rudeaabning": None,
        "min_daklag": 20,
        "klasser": [4, 5, 6],
        "radial_stivhed": None,
        "gwp": None,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "maskestoerrelse_datablad_mm": None,
        "gwp_bredder": None,
        "knudepunkt_effektivitet": None,
        "maskestabilitet_Nmm_grad": None,
        "stivhedsforhold": None,
        "min_traekstyrke": None,
        "traekstyrke_2pct": None,
        "traekstyrke_5pct": None,
        "max_deformation_pct": None,
        "ribbetykkelse": None,
        "resistens_kemisk_pct": None,
        "resistens_uv_pct": None,
        "resistens_oxidation_pct": None,
        "resistens_installationsskader": None,
        "bemærkning": "Effektindeks 105. Tekniske specifikationer ikke tilgængelige i foreliggende kildedokumenter.",
    },
    {
        "navn": "Tensar InterAx NX750",
        "serie": "Tensar",
        "type": "Hexagonalt",
        "effektindeks": "110–120",
        "korrektion": -0.10,
        "korrektion_interval": (-0.20, -0.10),
        "max_korn": None,
        "anbefalet_tilslag": None,
        "rudeaabning": "Hexagonal/trapezoidal/triangulær, ribbeafstand 80 mm",
        "min_daklag": 20,
        "klasser": [5, 6],
        "radial_stivhed": None,
        "gwp": None,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "maskestoerrelse_datablad_mm": None,
        "gwp_bredder": None,
        "knudepunkt_effektivitet": None,
        "maskestabilitet_Nmm_grad": None,
        "stivhedsforhold": None,
        "min_traekstyrke": None,
        "traekstyrke_2pct": None,
        "traekstyrke_5pct": None,
        "max_deformation_pct": None,
        "ribbetykkelse": None,
        "resistens_kemisk_pct": None,
        "resistens_uv_pct": None,
        "resistens_oxidation_pct": None,
        "resistens_installationsskader": None,
        "bemærkning": (
            "Effektindeks 110–120 ⇒ korrektion fra −20 % (bedste) til −10 % (konservativ). "
            "Coekstruderet, integralt formet hexagonalt geonet med rektangulære ribber og "
            "knudetykkelse 3,5 mm. EPD-certificeret (EN 15804+A2:2019). 100 % modstand mod "
            "kemisk nedbrydning, 90 % modstand mod UV/forvitring. PIDS angiver ikke "
            "designværdier (trækstyrke, radial stivhed, GWP, maks. korn)."
        ),
    },
    {
        "navn": "Tensar InterAx NX850",
        "serie": "Tensar",
        "type": "Hexagonalt",
        "effektindeks": "115–130",
        "korrektion": -0.15,
        "korrektion_interval": (-0.30, -0.15),
        "max_korn": None,
        "anbefalet_tilslag": None,
        "rudeaabning": "Hexagonal/trapezoidal/triangulær, ribbeafstand 80 mm",
        "min_daklag": 20,
        "klasser": [5, 6],
        "radial_stivhed": None,
        "gwp": None,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "maskestoerrelse_datablad_mm": None,
        "gwp_bredder": None,
        "knudepunkt_effektivitet": None,
        "maskestabilitet_Nmm_grad": None,
        "stivhedsforhold": None,
        "min_traekstyrke": None,
        "traekstyrke_2pct": None,
        "traekstyrke_5pct": None,
        "max_deformation_pct": None,
        "ribbetykkelse": None,
        "resistens_kemisk_pct": None,
        "resistens_uv_pct": None,
        "resistens_oxidation_pct": None,
        "resistens_installationsskader": None,
        "bemærkning": (
            "Effektindeks 115–130 ⇒ korrektion fra −30 % (bedste) til −15 % (konservativ). "
            "Coekstruderet, integralt formet hexagonalt geonet med rektangulære ribber og "
            "knudetykkelse 4,5 mm. EPD-certificeret (EN 15804+A2:2019). 100 % modstand mod "
            "kemisk nedbrydning, 90 % modstand mod UV/forvitring. PIDS angiver ikke "
            "designværdier (trækstyrke, radial stivhed, GWP, maks. korn)."
        ),
    },
    {
        "navn": "Tensar TriAx TX190L",
        "serie": "Tensar",
        "type": "Triaxialt",
        "effektindeks": "100",
        "korrektion": 0.00,
        "max_korn": None,
        "anbefalet_tilslag": None,
        "rudeaabning": "Hexagonalt pitch 120 mm",
        "min_daklag": 20,
        "klasser": [4, 5, 6],
        "radial_stivhed": 540,
        "gwp": None,
        "min_levetid": "100 år (<15°C) / 50 år (<25°C)",
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "maskestoerrelse_datablad_mm": None,
        "gwp_bredder": None,
        "knudepunkt_effektivitet": "100%",
        "maskestabilitet_Nmm_grad": None,
        "stivhedsforhold": 0.75,
        "min_traekstyrke": None,
        "traekstyrke_2pct": None,
        "traekstyrke_5pct": None,
        "max_deformation_pct": None,
        "ribbetykkelse": None,
        "resistens_kemisk_pct": None,
        "resistens_uv_pct": None,
        "resistens_oxidation_pct": None,
        "resistens_installationsskader": None,
        "bemærkning": (
            "Effektindeks og belastningsklasser er vejledende (ikke officielt specificeret). "
            "Radial stivhed 540 kN/m (-90 tol.), hexagonalt pitch 120 mm, vægt 0,300 kg/m². "
            "ETA-certificeret (EAD 080002-00-0102). Min. levetid 100 år (T<15°C) / 50 år (T<25°C)."
        ),
    },
    # --- GS-GRID-serien ---
    # Kilde: GS-GRID/E'GRID Designmanual okt. 2025 + GS-GRID Biaxial datablad jun. 2025
    {
        "navn": "GS-GRID B20/20",
        "serie": "GS-GRID",
        "type": "Biaxialt",
        "effektindeks": "80",
        "korrektion": 0.20,
        "max_korn": 64,
        "anbefalet_tilslag": "0–80 mm",
        "rudeaabning": "37×37 mm",
        "maskestoerrelse_mm": 37,
        "min_daklag": 20,
        "klasser": [1, 2, 3],
        "radial_stivhed": None,
        "gwp": 0.55,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "maskestoerrelse_datablad_mm": 35,
        "gwp_bredder": None,
        "knudepunkt_effektivitet": ">93%",
        "maskestabilitet_Nmm_grad": 500,
        "stivhedsforhold": None,
        "min_traekstyrke": "20/20 kN/m",
        "traekstyrke_2pct": "7/7 kN/m",
        "traekstyrke_5pct": "14/14 kN/m",
        "max_deformation_pct": 10,
        "ribbetykkelse": "1,5/1,1 mm",
        "resistens_kemisk_pct": None,
        "resistens_uv_pct": None,
        "resistens_oxidation_pct": None,
        "resistens_installationsskader": None,
        "bemærkning": "Effektindeks 80.",
    },
    {
        "navn": "GS-GRID B20/20L",
        "serie": "GS-GRID",
        "type": "Biaxialt",
        "effektindeks": "80",
        "korrektion": 0.20,
        "max_korn": 64,
        "anbefalet_tilslag": None,
        "rudeaabning": None,
        "min_daklag": 20,
        "klasser": [1, 2, 3],
        "radial_stivhed": None,
        "gwp": None,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "maskestoerrelse_datablad_mm": None,
        "gwp_bredder": None,
        "knudepunkt_effektivitet": None,
        "maskestabilitet_Nmm_grad": None,
        "stivhedsforhold": None,
        "min_traekstyrke": None,
        "traekstyrke_2pct": None,
        "traekstyrke_5pct": None,
        "max_deformation_pct": None,
        "ribbetykkelse": None,
        "resistens_kemisk_pct": None,
        "resistens_uv_pct": None,
        "resistens_oxidation_pct": None,
        "resistens_installationsskader": None,
        "bemærkning": "Effektindeks 80.",
    },
    {
        "navn": "GS-GRID B30/30",
        "serie": "GS-GRID",
        "type": "Biaxialt",
        "effektindeks": "90",
        "korrektion": 0.10,
        "max_korn": 64,
        "anbefalet_tilslag": "0–80 mm",
        "rudeaabning": "35×35 mm",
        "maskestoerrelse_mm": 35,
        "min_daklag": 20,
        "klasser": [3, 4, 5],
        "radial_stivhed": None,
        "gwp": 0.79,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "maskestoerrelse_datablad_mm": 34,
        "gwp_bredder": {1.975: 0.79, 3.95: 0.79, 5.95: 0.83},
        "knudepunkt_effektivitet": ">93%",
        "maskestabilitet_Nmm_grad": 750,
        "stivhedsforhold": None,
        "min_traekstyrke": "30/30 kN/m",
        "traekstyrke_2pct": "10,5/10,5 kN/m",
        "traekstyrke_5pct": "21/21 kN/m",
        "max_deformation_pct": 10,
        "ribbetykkelse": "2,5/1,5 mm",
        "resistens_kemisk_pct": None,
        "resistens_uv_pct": None,
        "resistens_oxidation_pct": None,
        "resistens_installationsskader": None,
        "bemærkning": "Effektindeks 90.",
    },
    {
        "navn": "GS-GRID B30/30L",
        "serie": "GS-GRID",
        "type": "Biaxialt",
        "effektindeks": "90",
        "korrektion": 0.10,
        "max_korn": 120,
        "anbefalet_tilslag": "0–150 mm",
        "rudeaabning": "65×65 mm",
        "maskestoerrelse_mm": 65,
        "min_daklag": 40,
        "klasser": [3, 4, 5],
        "radial_stivhed": None,
        "gwp": 0.88,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "maskestoerrelse_datablad_mm": 57,
        "gwp_bredder": {3.95: 0.88, 5.95: 0.85},
        "knudepunkt_effektivitet": ">93%",
        "maskestabilitet_Nmm_grad": 750,
        "stivhedsforhold": None,
        "min_traekstyrke": "30/30 kN/m",
        "traekstyrke_2pct": "10,5/10,5 kN/m",
        "traekstyrke_5pct": "21/21 kN/m",
        "max_deformation_pct": 10,
        "ribbetykkelse": "1,9/1,3 mm",
        "resistens_kemisk_pct": None,
        "resistens_uv_pct": None,
        "resistens_oxidation_pct": None,
        "resistens_installationsskader": None,
        "bemærkning": "Effektindeks 90. Stor rudeåbning - egnet til groft tilslag.",
    },
    {
        "navn": "GS-GRID B30/30XL",
        "serie": "GS-GRID",
        "type": "Biaxialt",
        "effektindeks": "90",
        "korrektion": 0.10,
        "max_korn": 200,
        "anbefalet_tilslag": "0–200 mm",
        "rudeaabning": "100×100 mm",
        "maskestoerrelse_mm": 100,
        "min_daklag": 60,
        "klasser": [4, 5, 6],
        "radial_stivhed": None,
        "gwp": 0.83,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "maskestoerrelse_datablad_mm": 95,
        "gwp_bredder": None,
        "knudepunkt_effektivitet": ">93%",
        "maskestabilitet_Nmm_grad": 750,
        "stivhedsforhold": None,
        "min_traekstyrke": "30/30 kN/m",
        "traekstyrke_2pct": "10,5/10,5 kN/m",
        "traekstyrke_5pct": "21/21 kN/m",
        "max_deformation_pct": 10,
        "ribbetykkelse": "2,6/2,1 mm",
        "resistens_kemisk_pct": None,
        "resistens_uv_pct": None,
        "resistens_oxidation_pct": None,
        "resistens_installationsskader": None,
        "bemærkning": "Effektindeks 90. Meget stor rudeåbning - til meget groft tilslag.",
    },
    {
        "navn": "GS-GRID B40/40",
        "serie": "GS-GRID",
        "type": "Biaxialt",
        "effektindeks": "100",
        "korrektion": 0.00,
        "max_korn": 64,
        "anbefalet_tilslag": "0–80 mm",
        "rudeaabning": "35×35 mm",
        "maskestoerrelse_mm": 35,
        "min_daklag": 20,
        "klasser": [4, 5, 6],
        "radial_stivhed": None,
        "gwp": 1.15,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "maskestoerrelse_datablad_mm": 33,
        "gwp_bredder": None,
        "knudepunkt_effektivitet": ">93%",
        "maskestabilitet_Nmm_grad": 980,
        "stivhedsforhold": None,
        "min_traekstyrke": "40/40 kN/m",
        "traekstyrke_2pct": "15/15 kN/m",
        "traekstyrke_5pct": "28/28 kN/m",
        "max_deformation_pct": 10,
        "ribbetykkelse": "3,4/2,1 mm",
        "resistens_kemisk_pct": None,
        "resistens_uv_pct": None,
        "resistens_oxidation_pct": None,
        "resistens_installationsskader": None,
        "bemærkning": "Effektindeks 100. Svarende til E'GRID T6 på GS/E'GRID-skalaen.",
    },
    {
        "navn": "GS-GRID B40/40L",
        "serie": "GS-GRID",
        "type": "Biaxialt",
        "effektindeks": "100",
        "korrektion": 0.00,
        "max_korn": 120,
        "anbefalet_tilslag": "0–150 mm",
        "rudeaabning": "60×60 mm",
        "maskestoerrelse_mm": 60,
        "min_daklag": 40,
        "klasser": [4, 5, 6],
        "radial_stivhed": None,
        "gwp": 1.17,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "maskestoerrelse_datablad_mm": 57,
        "gwp_bredder": None,
        "knudepunkt_effektivitet": ">93%",
        "maskestabilitet_Nmm_grad": 980,
        "stivhedsforhold": None,
        "min_traekstyrke": "40/40 kN/m",
        "traekstyrke_2pct": "15/15 kN/m",
        "traekstyrke_5pct": "28/28 kN/m",
        "max_deformation_pct": 10,
        "ribbetykkelse": "3,0/2,0 mm",
        "resistens_kemisk_pct": None,
        "resistens_uv_pct": None,
        "resistens_oxidation_pct": None,
        "resistens_installationsskader": None,
        "bemærkning": "Effektindeks 100. Stor rudeåbning - egnet til groft tilslag.",
    },
    {
        "navn": "GS-GRID SX160",
        "serie": "GS-GRID",
        "type": "Hexagonalt",
        "effektindeks": "100",
        "korrektion": 0.00,
        "max_korn": 80,
        "anbefalet_tilslag": "0–80 mm",
        "rudeaabning": "Hexagonalt pitch 80 mm",
        "min_daklag": 20,
        "klasser": [3, 4, 5, 6],
        "radial_stivhed": 390,
        "gwp": 0.51,
        "min_levetid": ">25 år",
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "maskestoerrelse_datablad_mm": None,
        "gwp_bredder": None,
        "knudepunkt_effektivitet": "100%",
        "maskestabilitet_Nmm_grad": None,
        "stivhedsforhold": 0.80,
        "min_traekstyrke": None,
        "traekstyrke_2pct": None,
        "traekstyrke_5pct": None,
        "max_deformation_pct": None,
        "ribbetykkelse": None,
        "resistens_kemisk_pct": None,
        "resistens_uv_pct": None,
        "resistens_oxidation_pct": None,
        "resistens_installationsskader": None,
        "bemærkning": "REFERENCE (GS/E'GRID-design) - effektindeks 100. Maks. tid uden afdækning: < 2 uger.",
    },
    {
        "navn": "GS-GRID SX170",
        "serie": "GS-GRID",
        "type": "Hexagonalt",
        "effektindeks": "110",
        "korrektion": -0.10,
        "max_korn": 150,
        "anbefalet_tilslag": "0–80 mm",
        "rudeaabning": "Hexagonalt pitch 80 mm",
        "min_daklag": 20,
        "klasser": [4, 5, 6],
        "radial_stivhed": 480,
        "gwp": 0.62,
        "min_levetid": ">25 år",
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "maskestoerrelse_datablad_mm": None,
        "gwp_bredder": None,
        "knudepunkt_effektivitet": "100%",
        "maskestabilitet_Nmm_grad": None,
        "stivhedsforhold": 0.80,
        "min_traekstyrke": None,
        "traekstyrke_2pct": None,
        "traekstyrke_5pct": None,
        "max_deformation_pct": None,
        "ribbetykkelse": None,
        "resistens_kemisk_pct": None,
        "resistens_uv_pct": None,
        "resistens_oxidation_pct": None,
        "resistens_installationsskader": None,
        "bemærkning": (
            "Effektindeks 110. Maks. kornstørrelse 150 mm (datablad), men designmanualens "
            "anbefalede tilslag er 0–80 mm (samme som SX160, grundet identisk hexagonalt pitch). "
            "Maks. tid uden afdækning: < 2 uger."
        ),
    },
    # --- E'GRID-serien ---
    # Kilde: GS-GRID/E'GRID Designmanual okt. 2025
    {
        "navn": "E'GRID T6",
        "serie": "E'GRID",
        "type": "Hexagonalt",
        "effektindeks": "100",
        "korrektion": 0.00,
        "max_korn": 80,
        "anbefalet_tilslag": "0–80 mm",
        "rudeaabning": "Hexagonalt pitch 80 mm",
        "min_daklag": 20,
        "klasser": [3, 4, 5, 6],
        "radial_stivhed": None,
        "gwp": None,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "maskestoerrelse_datablad_mm": None,
        "gwp_bredder": None,
        "knudepunkt_effektivitet": None,
        "maskestabilitet_Nmm_grad": None,
        "stivhedsforhold": None,
        "min_traekstyrke": None,
        "traekstyrke_2pct": None,
        "traekstyrke_5pct": None,
        "max_deformation_pct": None,
        "ribbetykkelse": None,
        "resistens_kemisk_pct": None,
        "resistens_uv_pct": None,
        "resistens_oxidation_pct": None,
        "resistens_installationsskader": None,
        "bemærkning": "Alternativ til GS-GRID SX160 - REFERENCE (GS/E'GRID-design), effektindeks 100.",
    },
    {
        "navn": "E'GRID T7",
        "serie": "E'GRID",
        "type": "Hexagonalt",
        "effektindeks": "110",
        "korrektion": -0.10,
        "max_korn": 80,
        "anbefalet_tilslag": "0–80 mm",
        "rudeaabning": "Hexagonalt pitch 80 mm",
        "min_daklag": 20,
        "klasser": [4, 5, 6],
        "radial_stivhed": None,
        "gwp": None,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "maskestoerrelse_datablad_mm": None,
        "gwp_bredder": None,
        "knudepunkt_effektivitet": None,
        "maskestabilitet_Nmm_grad": None,
        "stivhedsforhold": None,
        "min_traekstyrke": None,
        "traekstyrke_2pct": None,
        "traekstyrke_5pct": None,
        "max_deformation_pct": None,
        "ribbetykkelse": None,
        "resistens_kemisk_pct": None,
        "resistens_uv_pct": None,
        "resistens_oxidation_pct": None,
        "resistens_installationsskader": None,
        "bemærkning": "Alternativ til GS-GRID SX170 - effektindeks 110.",
    },
    {
        "navn": "E'GRID T9L",
        "serie": "E'GRID",
        "type": "Hexagonalt",
        "effektindeks": "110",
        "korrektion": -0.10,
        "max_korn": 150,
        "anbefalet_tilslag": "0–150 mm",
        "rudeaabning": "Hexagonalt pitch 120 mm",
        "min_daklag": 40,
        "klasser": [4, 5, 6],
        "radial_stivhed": None,
        "gwp": None,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "maskestoerrelse_datablad_mm": None,
        "gwp_bredder": None,
        "knudepunkt_effektivitet": None,
        "maskestabilitet_Nmm_grad": None,
        "stivhedsforhold": None,
        "min_traekstyrke": None,
        "traekstyrke_2pct": None,
        "traekstyrke_5pct": None,
        "max_deformation_pct": None,
        "ribbetykkelse": None,
        "resistens_kemisk_pct": None,
        "resistens_uv_pct": None,
        "resistens_oxidation_pct": None,
        "resistens_installationsskader": None,
        "bemærkning": (
            "Effektindeks rettet til 110 (korrektionsfaktor −0,10). "
            "GS/E'GRID Designmanual fig. 7 angiver eksplicit: "
            "\"E'GRID T9L – Aflæst bærelagstykkelse REDUCERES med 10 %\"."
        ),
    },
    # --- Manuel ---
    {
        "navn": "Anden armering (manuel)",
        "serie": "Manuel",
        "type": "-",
        "effektindeks": "-",
        "korrektion": 0.00,
        "max_korn": None,
        "anbefalet_tilslag": None,
        "rudeaabning": None,
        "min_daklag": 20,
        "klasser": [1, 2, 3, 4, 5, 6],
        "radial_stivhed": None,
        "gwp": None,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "maskestoerrelse_datablad_mm": None,
        "gwp_bredder": None,
        "knudepunkt_effektivitet": None,
        "maskestabilitet_Nmm_grad": None,
        "stivhedsforhold": None,
        "min_traekstyrke": None,
        "traekstyrke_2pct": None,
        "traekstyrke_5pct": None,
        "max_deformation_pct": None,
        "ribbetykkelse": None,
        "resistens_kemisk_pct": None,
        "resistens_uv_pct": None,
        "resistens_oxidation_pct": None,
        "resistens_installationsskader": None,
        "bemærkning": "Korrektionsfaktor indtastes manuelt",
    },
]

# Hjælpeliste - kun navne, bruges til dropdowns
GEONET_NAVNE = [g["navn"] for g in GEONET_DB]

# ---------------------------------------------------------------------------
# 5b. GEONET_NOTER
#     Kilde: geonet_database_komplet.xlsx - "DB Geonet v2"
#     Vigtige noter og kildehenvisninger fra den komplette produktdatabase.
# ---------------------------------------------------------------------------

# Kildedokumenterne bag produktdatabasen, med link til udgiverens egen
# offentliggjorte udgave. URL'erne peger direkte på PDF-filerne. Listen vises
# i Hjælp, kapitel 8, jf. :::kilder-blokken i kapitelfilen.
KILDEDOKUMENTER = [
    {
        "titel": "GS-GRID/E'GRID Designmanual",
        "udgiver": "BG Byggros", "dato": "okt. 2025",
        "url": "https://www.byggros.com/media/dxqbrimw/"
               "dk-brochure-gs-grid-designmanual.pdf",
    },
    {
        "titel": "Tensar Geonet Designmanual",
        "udgiver": "BG Byggros", "dato": "sept. 2024",
        "url": "https://www.byggros.com/media/c2tavgwm/"
               "brochure-tensar-designmanual-sept-2024-1.pdf",
    },
    {
        "titel": "GS-GRID Biaxial teknisk datablad (B-serien)",
        "udgiver": "BG Byggros", "dato": "jun. 2025",
        "url": "https://www.byggros.com/media/tlwdjvk2/"
               "gs-grid-data-dk0625-6-100.pdf",
    },
    {
        "titel": "GS-GRID SX teknisk datablad (SX160/SX170)",
        "udgiver": "BG Byggros", "dato": "okt. 2025",
        "url": "https://www.byggros.com/media/a31jv5rj/"
               "gs-grid-sx-teknisk-datablad-1025.pdf",
    },
    {
        "titel": "Tensar TriAx TX160 teknisk datablad",
        "udgiver": "BG Byggros", "dato": "aug. 2024",
        "url": "https://www.byggros.com/media/2ldmxhf0/"
               "datablad-tensar-triax-tx-160_23-08-24-1.pdf",
    },
    {
        "titel": "Tensar TriAx TX190L teknisk datablad",
        "udgiver": "BG Byggros", "dato": "okt. 2024",
        "url": "https://www.byggros.com/media/vydj5w24/"
               "tensar-geonet-tx190l-10-10-2024.pdf",
    },
    {
        "titel": "Tensar InterAx NX750 Product Identification Data Sheet",
        "udgiver": "Tensar", "dato": "dec. 2024",
        "url": "https://www.tensarcorp.com/getattachment/"
               "a0bac181-91df-463b-b7ab-c5f642ac92b5/NX750_PIDS_DEC_2024.pdf",
    },
    {
        "titel": "Tensar InterAx NX850 Product Identification Data Sheet",
        "udgiver": "Tensar", "dato": "dec. 2024",
        "url": "https://www.tensarcorp.com/getattachment/"
               "63057717-50ff-4ac2-bd31-5bfe261c115c/NX850_PIDS_DEC_2024.pdf",
    },
]

GEONET_NOTER = [
    {
        "titel": "Rettelse: E'GRID T9L effektindeks",
        "tekst": (
            "E'GRID T9L er rettet fra effektindeks 100 (korrektionsfaktor 0,00) til "
            "effektindeks 110 (korrektionsfaktor −0,10). "
            "BEGRUNDELSE: GS-GRID/E'GRID Designmanual fig. 6 angiver indeks 100 for T9L, "
            "men fig. 7 (tekst) angiver eksplicit: "
            "\"E'GRID T9L – Aflæst bærelagstykkelse REDUCERES med 10 %\"."
        ),
    },
    {
        "titel": "Forskel mellem datablad og designmanual: Maskestørrelse vs. rudeåbning",
        "tekst": (
            "For de biaxiale GS-GRID produkter angiver databladet 'maskestørrelse (ca.)' "
            "og designmanualen (figur 9) angiver 'rudeåbning'. Begge er vist i tabellen."
        ),
    },
    {
        "titel": "Forskel mellem datablad og designmanual: Maks. kornstørrelse vs. anbefalet tilslag",
        "tekst": (
            "For enkelte geonet, GS-GRID B20/20, B30/30, B30/30L, B40/40, overstiger den anbefalede tilslagsstørrelse fra designmanualen den maksimale kornstørrelse fra databladet. "
            "For GS-GRID SX170 er det omvendt, hvor den anbefalede tilslagsstørrelse er mindre end den maksimale kornstørrelse. "
        ),
    },
    {
        "titel": "Tensar-serien: Manglende tekniske data",
        "tekst": (
            "Datablade for Tensar SS30, HX5.5 og HX165 indgår ikke i de foreliggende "
            "kildedokumenter. For Tensar InterAx NX750 og NX850 findes kun Product "
            "Identification Data Sheet (PIDS, dec. 2024), som leverer identifikations- "
            "og holdbarhedsdata, men eksplicit ikke designværdier (trækstyrke, radial "
            "stivhed, GWP, maks. kornstørrelse). Korrektionsfaktorer og belastningsklasser "
            "er fra Tensar Geonet Designmanual sept. 2024."
        ),
    },
    {
        "titel": "2-lags opbygning",
        "tekst": (
            "Begge designmanualer anbefaler ved total bærelagstykkelse > 50 cm at anvende "
            "2 eller flere lag geonet. Afstand mellem lag: min. 20 cm og maks. 50 cm "
            "(GS/E'GRID) / maks. 40 cm (Tensar). Øverste lag skal placeres min. 20 cm "
            "under overside af bærelag. I designmanualerne vises eksempler på der kan anvendes "
            "forskellige produkter ved flerlagsopbygninger."
        ),
    },
    # Overlæg i samlinger indgår ikke som note. Kravet afhænger af underbundens
    # E-værdi og vises derfor under "Krav til nettet" i produktlisten, hvor
    # E-værdien er kendt (se placement.overlap_krav_mm). Værdierne pr. produkt
    # står fortsat i kolonnerne "Overlæg Eu ≥ 5" og "Overlæg Eu < 5" ovenfor.
    # Kildedokumenterne indgår heller ikke som note; de står samlet i Hjælp,
    # kapitel 8, dannet af KILDEDOKUMENTER ovenfor.
]


# ---------------------------------------------------------------------------
# 6. KORREKTIONSFAKTORER
#    Kilde: Excel fane 4 "Korrektionsfaktorer"
# ---------------------------------------------------------------------------

# Basis-friktionsvinkel for opslagstabellens referencegrundlag
PHI_BASIS = 37.0

# φᵥ-korrektion pr. grad over 37° (negativ = tyndere bærelag ved højere φᵥ)
K_PHI = -0.02

# Gyldighedsgrænser
EU_MIN = 1.0    # MPa - hård fejl under denne grænse
EU_MAX = 45.0   # MPa - hård fejl over denne grænse
EO_MIN = 30.0   # MPa
EO_MAX = 150.0  # MPa
PHI_MIN = PHI_BASIS  # grader - advarsel under denne (følger basis-friktionsvinklen)
PHI_MAX = 50.0  # grader - advarsel over denne
MIN_DAKLAG_STANDARD = 200  # mm - minimum dæklag over geonet i opbygning


# ---------------------------------------------------------------------------
# 7. Hjælpefunktioner til opslag
# ---------------------------------------------------------------------------

def find_geonet(navn: str) -> dict | None:
    """Returner geonet-dict ud fra produktnavn, eller None."""
    for g in GEONET_DB:
        if g["navn"] == navn:
            return g
    return None


def find_materiale(navn: str) -> dict | None:
    """Returner materiale-dict ud fra navn, eller None."""
    for m in MATERIAL_DB:
        if m["navn"] == navn:
            return m
    return None


def cv_til_eu(cv: float) -> float | None:
    """
    Konverter vingestyrke Cv (kN/m²) til Eu (MPa).
    Returnerer None hvis Cv er uden for tabelområdet (0–180 kN/m²).
    """
    if cv == 0:
        return float(CV_TIL_EU[0][2])
    for cv_min, cv_max, eu in CV_TIL_EU:
        if cv_min < cv <= cv_max:
            return float(eu)
    return None


def klasse_til_eo(klasse: int) -> float | None:
    """Returner Eo (MPa) for belastningsklasse 1–6, eller None."""
    entry = BELASTNINGSKLASSER.get(klasse)
    return float(entry["eo"]) if entry else None


def eo_til_klasse(eo: float) -> int | None:
    """
    Find belastningsklasse ud fra Eo-værdi.
    Returnerer den klasse hvis Eo matcher nøjagtigt, eller None.
    Bruges til produkt-klasse-validering.
    """
    for klasse, data in BELASTNINGSKLASSER.items():
        if data["eo"] == eo:
            return klasse
    return None


def format_klasse_interval(klasser) -> str:
    """Komprimér en klasseliste til intervaller: [3, 4, 5, 6] → '3-6',
    [3, 5, 6] → '3, 5-6', [4] → '4'. Tom liste → '—'.

    Delt formatering brugt af både UI (app.py) og validering (validators.py).
    """
    ks = sorted({int(k) for k in klasser})
    if not ks:
        return "—"
    grupper: list[str] = []
    start = forrige = ks[0]
    for k in ks[1:]:
        if k == forrige + 1:
            forrige = k
            continue
        grupper.append(str(start) if start == forrige else f"{start}-{forrige}")
        start = forrige = k
    grupper.append(str(start) if start == forrige else f"{start}-{forrige}")
    return ", ".join(grupper)
