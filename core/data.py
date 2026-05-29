"""
Datatabeller til Geonet Dimensioneringsværktøj.

Kilde: geonet_dimensionering_v1_3.xlsx, fane "7. Opslagstabeller"
Alle værdier er aflæst direkte fra Excel-arkets tabel 7.1 (den beregnede
opslagstabel, ikke rådata). None svarer til "—" i Excel (uden for
diagrammets gyldighedsområde).

Ingen imports herfra må være UI-relaterede (Streamlit, Flask, osv.).
"""

# ---------------------------------------------------------------------------
# 1. T_BASIS_TABLE
#    Struktur: T_BASIS_TABLE[eu_mpa][eo_mpa][lag_type] → tykkelse i cm
#    lag_type: "uarmeret" | "1_lag" | "2_lag"
#    None = "—" = uden for diagrammets gyldighedsområde
#
#    Eu-rækker (MPa): 2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 18, 20, 25, 30,
#                    35, 40, 45, 50
#    Eo-kolonner (MPa): 30, 45, 60, 80, 120, 150
# ---------------------------------------------------------------------------

T_BASIS_TABLE = {
    2: {
        30:  {"uarmeret": None,  "1_lag": 80.0,  "2_lag": None },
        45:  {"uarmeret": None,  "1_lag": 90.0,  "2_lag": 80.0 },
        60:  {"uarmeret": None,  "1_lag": 96.7,  "2_lag": 86.7 },
        80:  {"uarmeret": None,  "1_lag": 110.0, "2_lag": 100.0},
        120: {"uarmeret": None,  "1_lag": 120.0, "2_lag": 106.7},
        150: {"uarmeret": None,  "1_lag": 125.0, "2_lag": 110.0},
    },
    3: {
        30:  {"uarmeret": 110.0, "1_lag": 70.0,  "2_lag": None },
        45:  {"uarmeret": 120.0, "1_lag": 83.3,  "2_lag": 70.0 },
        60:  {"uarmeret": 130.0, "1_lag": 90.0,  "2_lag": 80.0 },
        80:  {"uarmeret": 140.0, "1_lag": 100.0, "2_lag": 90.0 },
        120: {"uarmeret": 150.0, "1_lag": 110.0, "2_lag": 100.0},
        150: {"uarmeret": 160.0, "1_lag": 115.0, "2_lag": 100.0},
    },
    4: {
        30:  {"uarmeret": 96.7,  "1_lag": 65.0,  "2_lag": None },
        45:  {"uarmeret": 106.7, "1_lag": 75.0,  "2_lag": 63.3 },
        60:  {"uarmeret": 116.7, "1_lag": 83.3,  "2_lag": 73.3 },
        80:  {"uarmeret": 125.0, "1_lag": 93.3,  "2_lag": 80.0 },
        120: {"uarmeret": 136.7, "1_lag": 103.3, "2_lag": 90.0 },
        150: {"uarmeret": 146.7, "1_lag": 106.7, "2_lag": 93.3 },
    },
    5: {
        30:  {"uarmeret": 90.0,  "1_lag": 60.0,  "2_lag": None },
        45:  {"uarmeret": 100.0, "1_lag": 66.7,  "2_lag": 57.5 },
        60:  {"uarmeret": 110.0, "1_lag": 77.5,  "2_lag": 67.5 },
        80:  {"uarmeret": 115.0, "1_lag": 85.0,  "2_lag": 75.0 },
        120: {"uarmeret": 130.0, "1_lag": 96.7,  "2_lag": 83.3 },
        150: {"uarmeret": 140.0, "1_lag": 100.0, "2_lag": 87.5 },
    },
    6: {
        30:  {"uarmeret": 80.0,  "1_lag": 53.3,  "2_lag": None },
        45:  {"uarmeret": 90.0,  "1_lag": 60.0,  "2_lag": 52.5 },
        60:  {"uarmeret": 100.0, "1_lag": 72.5,  "2_lag": 62.5 },
        80:  {"uarmeret": 108.0, "1_lag": 78.0,  "2_lag": 70.0 },
        120: {"uarmeret": 120.0, "1_lag": 90.0,  "2_lag": 78.0 },
        150: {"uarmeret": 130.0, "1_lag": 90.0,  "2_lag": 82.5 },
    },
    7: {
        30:  {"uarmeret": 75.0,  "1_lag": 48.0,  "2_lag": None },
        45:  {"uarmeret": 85.0,  "1_lag": 56.7,  "2_lag": None },
        60:  {"uarmeret": 93.3,  "1_lag": 68.0,  "2_lag": 58.0 },
        80:  {"uarmeret": 104.0, "1_lag": 74.0,  "2_lag": 65.0 },
        120: {"uarmeret": 115.0, "1_lag": 85.0,  "2_lag": 74.0 },
        150: {"uarmeret": 125.0, "1_lag": 86.0,  "2_lag": 78.0 },
    },
    8: {
        30:  {"uarmeret": 70.0,  "1_lag": 44.0,  "2_lag": None },
        45:  {"uarmeret": 80.0,  "1_lag": 53.3,  "2_lag": None },
        60:  {"uarmeret": 88.0,  "1_lag": 64.0,  "2_lag": 54.0 },
        80:  {"uarmeret": 100.0, "1_lag": 70.0,  "2_lag": 60.0 },
        120: {"uarmeret": 110.0, "1_lag": 80.0,  "2_lag": 70.0 },
        150: {"uarmeret": 120.0, "1_lag": 82.0,  "2_lag": 74.0 },
    },
    10: {
        30:  {"uarmeret": 60.0,  "1_lag": 36.0,  "2_lag": None },
        45:  {"uarmeret": 70.0,  "1_lag": 46.7,  "2_lag": None },
        60:  {"uarmeret": 80.0,  "1_lag": 56.7,  "2_lag": None },
        80:  {"uarmeret": 90.0,  "1_lag": 62.0,  "2_lag": None },
        120: {"uarmeret": 100.0, "1_lag": 70.0,  "2_lag": 60.0 },
        150: {"uarmeret": 110.0, "1_lag": 75.7,  "2_lag": 66.7 },
    },
    12: {
        30:  {"uarmeret": 50.0,  "1_lag": 28.6,  "2_lag": None },
        45:  {"uarmeret": 60.0,  "1_lag": 40.0,  "2_lag": None },
        60:  {"uarmeret": 70.0,  "1_lag": 50.0,  "2_lag": None },
        80:  {"uarmeret": 80.0,  "1_lag": 55.7,  "2_lag": None },
        120: {"uarmeret": 90.0,  "1_lag": 64.3,  "2_lag": 55.0 },
        150: {"uarmeret": 100.0, "1_lag": 70.0,  "2_lag": 60.0 },
    },
    15: {
        30:  {"uarmeret": 38.6,  "1_lag": 20.0,  "2_lag": None },
        45:  {"uarmeret": 50.0,  "1_lag": 31.4,  "2_lag": None },
        60:  {"uarmeret": 60.0,  "1_lag": 42.5,  "2_lag": None },
        80:  {"uarmeret": 70.0,  "1_lag": 48.3,  "2_lag": None },
        120: {"uarmeret": 80.0,  "1_lag": 57.3,  "2_lag": None },
        150: {"uarmeret": 90.0,  "1_lag": 64.0,  "2_lag": 55.0 },
    },
    18: {
        30:  {"uarmeret": 30.0,  "1_lag": None,  "2_lag": None },
        45:  {"uarmeret": 40.0,  "1_lag": 24.4,  "2_lag": None },
        60:  {"uarmeret": 51.4,  "1_lag": 35.0,  "2_lag": None },
        80:  {"uarmeret": 61.4,  "1_lag": 43.3,  "2_lag": None },
        120: {"uarmeret": 71.4,  "1_lag": 51.8,  "2_lag": None },
        150: {"uarmeret": 81.4,  "1_lag": 58.6,  "2_lag": 50.0 },
    },
    20: {
        30:  {"uarmeret": 23.3,  "1_lag": None,  "2_lag": None },
        45:  {"uarmeret": 36.0,  "1_lag": 20.0,  "2_lag": None },
        60:  {"uarmeret": 46.7,  "1_lag": 30.0,  "2_lag": None },
        80:  {"uarmeret": 56.7,  "1_lag": 40.0,  "2_lag": None },
        120: {"uarmeret": 66.7,  "1_lag": 48.3,  "2_lag": None },
        150: {"uarmeret": 76.7,  "1_lag": 55.7,  "2_lag": None },
    },
    25: {
        30:  {"uarmeret": 10.0,  "1_lag": None,  "2_lag": None },
        45:  {"uarmeret": 26.7,  "1_lag": None,  "2_lag": None },
        60:  {"uarmeret": 36.7,  "1_lag": 22.9,  "2_lag": None },
        80:  {"uarmeret": 46.7,  "1_lag": 31.7,  "2_lag": None },
        120: {"uarmeret": 56.7,  "1_lag": 40.0,  "2_lag": None },
        150: {"uarmeret": 66.7,  "1_lag": 48.8,  "2_lag": None },
    },
    30: {
        30:  {"uarmeret": 0.0,   "1_lag": None,  "2_lag": None },
        45:  {"uarmeret": 18.6,  "1_lag": None,  "2_lag": None },
        60:  {"uarmeret": 28.6,  "1_lag": None,  "2_lag": None },
        80:  {"uarmeret": 38.6,  "1_lag": 24.3,  "2_lag": None },
        120: {"uarmeret": 48.6,  "1_lag": 33.8,  "2_lag": None },
        150: {"uarmeret": 58.6,  "1_lag": 42.5,  "2_lag": None },
    },
    35: {
        30:  {"uarmeret": None,  "1_lag": None,  "2_lag": None },
        45:  {"uarmeret": 11.4,  "1_lag": None,  "2_lag": None },
        60:  {"uarmeret": 21.4,  "1_lag": None,  "2_lag": None },
        80:  {"uarmeret": 31.4,  "1_lag": None,  "2_lag": None },
        120: {"uarmeret": 41.4,  "1_lag": None,  "2_lag": None },
        150: {"uarmeret": 51.4,  "1_lag": None,  "2_lag": None },
    },
    40: {
        30:  {"uarmeret": None,  "1_lag": None,  "2_lag": None },
        45:  {"uarmeret": 5.6,   "1_lag": None,  "2_lag": None },
        60:  {"uarmeret": 15.6,  "1_lag": None,  "2_lag": None },
        80:  {"uarmeret": 25.6,  "1_lag": None,  "2_lag": None },
        120: {"uarmeret": 35.6,  "1_lag": None,  "2_lag": None },
        150: {"uarmeret": 45.6,  "1_lag": None,  "2_lag": None },
    },
    45: {
        30:  {"uarmeret": None,  "1_lag": None,  "2_lag": None },
        45:  {"uarmeret": 0.0,   "1_lag": None,  "2_lag": None },
        60:  {"uarmeret": 10.0,  "1_lag": None,  "2_lag": None },
        80:  {"uarmeret": 20.0,  "1_lag": None,  "2_dag": None },
        120: {"uarmeret": 30.0,  "1_lag": None,  "2_lag": None },
        150: {"uarmeret": 40.0,  "1_lag": None,  "2_lag": None },
    },
    50: {
        30:  {"uarmeret": None,  "1_lag": None,  "2_lag": None },
        45:  {"uarmeret": None,  "1_lag": None,  "2_lag": None },
        60:  {"uarmeret": None,  "1_lag": None,  "2_lag": None },
        80:  {"uarmeret": None,  "1_lag": None,  "2_lag": None },
        120: {"uarmeret": None,  "1_lag": None,  "2_lag": None },
        150: {"uarmeret": None,  "1_lag": None,  "2_lag": None },
    },
}

# Sorteret liste over alle Eu-nøgler — bruges til interpolation
EU_RAEKKER = sorted(T_BASIS_TABLE.keys())

# Gyldige Eo-værdier (svarer til de 6 belastningsklasser)
EO_KOLONNER = [30, 45, 60, 80, 120, 150]


# ---------------------------------------------------------------------------
# 1b. Rådata fra designdiagrammer
#    Kilde: Excel fane "7. Opslagstabeller", tabel 7.2.
#    Hver tabel er aflæste punkter fra designmanualernes diagrammer.
# ---------------------------------------------------------------------------

DESIGNDIAGRAM_RAW_TABLES = [
    {
        "diagram_nr": 1,
        "eo": 30,
        "klasse": 1,
        "image_name": "Diagram 1.png",
        "rows": [
            {"tykkelse_cm": 0, "eu_uarmeret": 30, "eu_1_lag": None, "eu_2_lag": None},
            {"tykkelse_cm": 10, "eu_uarmeret": 25, "eu_1_lag": None, "eu_2_lag": None},
            {"tykkelse_cm": 20, "eu_uarmeret": 21, "eu_1_lag": 15, "eu_2_lag": None},
            {"tykkelse_cm": 30, "eu_uarmeret": 18, "eu_1_lag": 11.5, "eu_2_lag": None},
            {"tykkelse_cm": 40, "eu_uarmeret": 14.5, "eu_1_lag": 9, "eu_2_lag": None},
            {"tykkelse_cm": 50, "eu_uarmeret": 12, "eu_1_lag": 6.5, "eu_2_lag": None},
            {"tykkelse_cm": 60, "eu_uarmeret": 10, "eu_1_lag": 5, "eu_2_lag": None},
            {"tykkelse_cm": 70, "eu_uarmeret": 8, "eu_1_lag": 3, "eu_2_lag": None},
            {"tykkelse_cm": 80, "eu_uarmeret": 6, "eu_1_lag": 2, "eu_2_lag": None},
            {"tykkelse_cm": 90, "eu_uarmeret": 5, "eu_1_lag": 0, "eu_2_lag": None},
            {"tykkelse_cm": 100, "eu_uarmeret": 3.5, "eu_1_lag": None, "eu_2_lag": None},
            {"tykkelse_cm": 110, "eu_uarmeret": 3, "eu_1_lag": None, "eu_2_lag": None},
        ],
    },
    {
        "diagram_nr": 2,
        "eo": 45,
        "klasse": 2,
        "image_name": "Diagram 2.png",
        "rows": [
            {"tykkelse_cm": 0, "eu_uarmeret": 45, "eu_1_lag": None, "eu_2_lag": None},
            {"tykkelse_cm": 10, "eu_uarmeret": 36, "eu_1_lag": None, "eu_2_lag": None},
            {"tykkelse_cm": 20, "eu_uarmeret": 29, "eu_1_lag": 20, "eu_2_lag": None},
            {"tykkelse_cm": 30, "eu_uarmeret": 22, "eu_1_lag": 15.5, "eu_2_lag": None},
            {"tykkelse_cm": 40, "eu_uarmeret": 18, "eu_1_lag": 12, "eu_2_lag": None},
            {"tykkelse_cm": 50, "eu_uarmeret": 15, "eu_1_lag": 9, "eu_2_lag": 6.5},
            {"tykkelse_cm": 60, "eu_uarmeret": 12, "eu_1_lag": 6, "eu_2_lag": 4.5},
            {"tykkelse_cm": 70, "eu_uarmeret": 10, "eu_1_lag": 4.5, "eu_2_lag": 3},
            {"tykkelse_cm": 80, "eu_uarmeret": 8, "eu_1_lag": 3.5, "eu_2_lag": 2},
            {"tykkelse_cm": 90, "eu_uarmeret": 6, "eu_1_lag": 2, "eu_2_lag": 1},
            {"tykkelse_cm": 100, "eu_uarmeret": 5, "eu_1_lag": 1, "eu_2_lag": None},
            {"tykkelse_cm": 110, "eu_uarmeret": 3.5, "eu_1_lag": None, "eu_2_lag": None},
            {"tykkelse_cm": 120, "eu_uarmeret": 3, "eu_1_lag": None, "eu_2_lag": None},
            {"tykkelse_cm": 130, "eu_uarmeret": 2.5, "eu_1_lag": None, "eu_2_lag": None},
        ],
    },
    {
        "diagram_nr": 3,
        "eo": 60,
        "klasse": 3,
        "image_name": "Diagram 3.png",
        "rows": [
            {"tykkelse_cm": 10, "eu_uarmeret": 45, "eu_1_lag": None, "eu_2_lag": None},
            {"tykkelse_cm": 20, "eu_uarmeret": 36, "eu_1_lag": 27, "eu_2_lag": None},
            {"tykkelse_cm": 30, "eu_uarmeret": 29, "eu_1_lag": 20, "eu_2_lag": None},
            {"tykkelse_cm": 40, "eu_uarmeret": 23, "eu_1_lag": 16, "eu_2_lag": None},
            {"tykkelse_cm": 50, "eu_uarmeret": 18.5, "eu_1_lag": 12, "eu_2_lag": 9},
            {"tykkelse_cm": 60, "eu_uarmeret": 15, "eu_1_lag": 9, "eu_2_lag": 6.5},
            {"tykkelse_cm": 70, "eu_uarmeret": 12, "eu_1_lag": 6.5, "eu_2_lag": 4.5},
            {"tykkelse_cm": 80, "eu_uarmeret": 10, "eu_1_lag": 4.5, "eu_2_lag": 3},
            {"tykkelse_cm": 90, "eu_uarmeret": 7.5, "eu_1_lag": 3, "eu_2_lag": 1.5},
            {"tykkelse_cm": 100, "eu_uarmeret": 6, "eu_1_lag": 1.5, "eu_2_lag": 0.5},
            {"tykkelse_cm": 110, "eu_uarmeret": 5, "eu_1_lag": 1, "eu_2_lag": None},
            {"tykkelse_cm": 120, "eu_uarmeret": 3.5, "eu_1_lag": None, "eu_2_lag": None},
            {"tykkelse_cm": 130, "eu_uarmeret": 3, "eu_1_lag": None, "eu_2_lag": None},
            {"tykkelse_cm": 140, "eu_uarmeret": 2.5, "eu_1_lag": None, "eu_2_lag": None},
        ],
    },
    {
        "diagram_nr": 4,
        "eo": 80,
        "klasse": 4,
        "image_name": "Diagram 4.png",
        "rows": [
            {"tykkelse_cm": 20, "eu_uarmeret": 45, "eu_1_lag": 33, "eu_2_lag": None},
            {"tykkelse_cm": 30, "eu_uarmeret": 36, "eu_1_lag": 26, "eu_2_lag": None},
            {"tykkelse_cm": 40, "eu_uarmeret": 29, "eu_1_lag": 20, "eu_2_lag": None},
            {"tykkelse_cm": 50, "eu_uarmeret": 23, "eu_1_lag": 14, "eu_2_lag": None},
            {"tykkelse_cm": 60, "eu_uarmeret": 18.5, "eu_1_lag": 10.5, "eu_2_lag": 8},
            {"tykkelse_cm": 70, "eu_uarmeret": 15, "eu_1_lag": 8, "eu_2_lag": 6},
            {"tykkelse_cm": 80, "eu_uarmeret": 12, "eu_1_lag": 5.5, "eu_2_lag": 4},
            {"tykkelse_cm": 90, "eu_uarmeret": 10, "eu_1_lag": 4.5, "eu_2_lag": 3},
            {"tykkelse_cm": 100, "eu_uarmeret": 8, "eu_1_lag": 3, "eu_2_lag": 2},
            {"tykkelse_cm": 110, "eu_uarmeret": 5.5, "eu_1_lag": 2, "eu_2_lag": 1},
            {"tykkelse_cm": 120, "eu_uarmeret": 4.5, "eu_1_lag": 1, "eu_2_lag": None},
            {"tykkelse_cm": 130, "eu_uarmeret": 3.5, "eu_1_lag": None, "eu_2_lag": None},
            {"tykkelse_cm": 140, "eu_uarmeret": 3, "eu_1_lag": None, "eu_2_lag": None},
            {"tykkelse_cm": 150, "eu_uarmeret": 2.5, "eu_1_lag": None, "eu_2_lag": None},
        ],
    },
    {
        "diagram_nr": 5,
        "eo": 120,
        "klasse": 5,
        "image_name": "Diagram 5.png",
        "rows": [
            {"tykkelse_cm": 30, "eu_uarmeret": 45, "eu_1_lag": 33, "eu_2_lag": None},
            {"tykkelse_cm": 40, "eu_uarmeret": 36, "eu_1_lag": 25, "eu_2_lag": None},
            {"tykkelse_cm": 50, "eu_uarmeret": 29, "eu_1_lag": 19, "eu_2_lag": 14},
            {"tykkelse_cm": 60, "eu_uarmeret": 23, "eu_1_lag": 13.5, "eu_2_lag": 10},
            {"tykkelse_cm": 70, "eu_uarmeret": 18.5, "eu_1_lag": 10, "eu_2_lag": 8},
            {"tykkelse_cm": 80, "eu_uarmeret": 15, "eu_1_lag": 8, "eu_2_lag": 5.5},
            {"tykkelse_cm": 90, "eu_uarmeret": 12, "eu_1_lag": 6, "eu_2_lag": 4},
            {"tykkelse_cm": 100, "eu_uarmeret": 10, "eu_1_lag": 4.5, "eu_2_lag": 3},
            {"tykkelse_cm": 110, "eu_uarmeret": 8, "eu_1_lag": 3, "eu_2_lag": 1.5},
            {"tykkelse_cm": 120, "eu_uarmeret": 6, "eu_1_lag": 2, "eu_2_lag": 1},
            {"tykkelse_cm": 130, "eu_uarmeret": 5, "eu_1_lag": 1, "eu_2_lag": None},
            {"tykkelse_cm": 140, "eu_uarmeret": 3.5, "eu_1_lag": None, "eu_2_lag": None},
            {"tykkelse_cm": 150, "eu_uarmeret": 3, "eu_1_lag": None, "eu_2_lag": None},
            {"tykkelse_cm": 160, "eu_uarmeret": 2.5, "eu_1_lag": None, "eu_2_lag": None},
        ],
    },
    {
        "diagram_nr": 6,
        "eo": 150,
        "klasse": 6,
        "image_name": "Diagram 6.png",
        "rows": [
            {"tykkelse_cm": 40, "eu_uarmeret": 45, "eu_1_lag": 32, "eu_2_lag": None},
            {"tykkelse_cm": 50, "eu_uarmeret": 36, "eu_1_lag": 24, "eu_2_lag": 18},
            {"tykkelse_cm": 60, "eu_uarmeret": 29, "eu_1_lag": 17, "eu_2_lag": 12},
            {"tykkelse_cm": 70, "eu_uarmeret": 23, "eu_1_lag": 12, "eu_2_lag": 9},
            {"tykkelse_cm": 80, "eu_uarmeret": 18.5, "eu_1_lag": 8.5, "eu_2_lag": 6.5},
            {"tykkelse_cm": 90, "eu_uarmeret": 15, "eu_1_lag": 6, "eu_2_lag": 4.5},
            {"tykkelse_cm": 100, "eu_uarmeret": 12, "eu_1_lag": 5, "eu_2_lag": 3},
            {"tykkelse_cm": 110, "eu_uarmeret": 10, "eu_1_lag": 3.5, "eu_2_lag": 2},
            {"tykkelse_cm": 120, "eu_uarmeret": 8, "eu_1_lag": 2.5, "eu_2_lag": 1},
            {"tykkelse_cm": 130, "eu_uarmeret": 6, "eu_1_lag": 1.5, "eu_2_lag": None},
            {"tykkelse_cm": 140, "eu_uarmeret": 5, "eu_1_lag": 1, "eu_2_lag": None},
            {"tykkelse_cm": 150, "eu_uarmeret": 3.5, "eu_1_lag": None, "eu_2_lag": None},
            {"tykkelse_cm": 160, "eu_uarmeret": 3, "eu_1_lag": None, "eu_2_lag": None},
            {"tykkelse_cm": 170, "eu_uarmeret": 2.5, "eu_1_lag": None, "eu_2_lag": None},
        ],
    },
]


# ---------------------------------------------------------------------------
# 2. BELASTNINGSKLASSER
#    Kilde: Excel fane 7.5
# ---------------------------------------------------------------------------

BELASTNINGSKLASSER = {
    1: {
        "eo": 30,
        "navn": "Klasse 1 — Begrænset belastning",
        "belastning": "Begrænset belastning",
        "anvendelse": "Cykelstier, midlertidige byggeveje",
    },
    2: {
        "eo": 45,
        "navn": "Klasse 2 — Større belastning",
        "belastning": "Større belastning",
        "anvendelse": "Markveje, midlertidige byggeveje med større belastning",
    },
    3: {
        "eo": 60,
        "navn": "Klasse 3 — Let trafik",
        "belastning": "Let trafik (akseltryk ≤ 6 t)",
        "anvendelse": "Villaveje, p-pladser for personbiler",
    },
    4: {
        "eo": 80,
        "navn": "Klasse 4 — Middel trafik",
        "belastning": "Middel trafik (akseltryk ≤ 8 t)",
        "anvendelse": "Middel trafikerede veje, p-arealer, flydende gulve i lagerhaller",
    },
    5: {
        "eo": 120,
        "navn": "Klasse 5 — Tung trafik",
        "belastning": "Tung trafik (akseltryk ≤ 12 t)",
        "anvendelse": "Hovedveje, amtsveje, containerpladser",
    },
    6: {
        "eo": 150,
        "navn": "Klasse 6 — Meget tung trafik",
        "belastning": "Meget tung trafik (akseltryk ≤ 15 t)",
        "anvendelse": "Landingsbaner, p-arealer for meget tunge køretøjer",
    },
}


# ---------------------------------------------------------------------------
# 3. CV_TIL_EU
#    Kilde: Excel fane 7.4 (GS-GRID Designmanual fig. 3)
#    Liste af (cv_min, cv_max, eu) — begge grænser er inklusive øvre,
#    eksklusive nedre (dvs. Cv=30 hører til intervallet 30–60 → Eu=10).
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
# ---------------------------------------------------------------------------

MATERIAL_DB = [
    {
        "navn": "Bundsand",
        "phi": 35,
        "max_korn": 8,
        "lagtype": "Bundsikring",
        "anvendelse": "Bundlag, friktionsmateriale",
    },
    {
        "navn": "Bundgrus 0-80",
        "phi": 38,
        "max_korn": 80,
        "lagtype": "Bundsikring",
        "anvendelse": "Bundsikring",
    },
    {
        "navn": "SG I 0-32",
        "phi": 40,
        "max_korn": 32,
        "lagtype": "Bærelag",
        "anvendelse": "Stabilgrus, øvre bærelag",
    },
    {
        "navn": "SG II 0-32",
        "phi": 40,
        "max_korn": 32,
        "lagtype": "Bærelag",
        "anvendelse": "Stabilgrus",
    },
    {
        "navn": "Knust beton 0-32",
        "phi": 40,
        "max_korn": 32,
        "lagtype": "Bærelag",
        "anvendelse": "Genbrugsmateriale, øvre bærelag",
    },
    {
        "navn": "Skærver 0-32",
        "phi": 45,
        "max_korn": 32,
        "lagtype": "Bærelag",
        "anvendelse": "Topbærelag, høj kvalitet",
    },
    {
        "navn": "Skærver 0-64",
        "phi": 45,
        "max_korn": 64,
        "lagtype": "Bærelag",
        "anvendelse": "Bærelag",
    },
    {
        "navn": "Skærver 0-90",
        "phi": 45,
        "max_korn": 90,
        "lagtype": "Bærelag",
        "anvendelse": "Bærelag (kan også anvendes som bundsikring)",
    },
    {
        "navn": "Skærver 0-120",
        "phi": 45,
        "max_korn": 120,
        "lagtype": "Bundsikring",
        "anvendelse": "Bundsikring",
    },
    {
        "navn": "Skærver 0-150",
        "phi": 45,
        "max_korn": 150,
        "lagtype": "Bundsikring",
        "anvendelse": "Bundsikring grov",
    },
    {
        "navn": "Skærver 0-200",
        "phi": 45,
        "max_korn": 200,
        "lagtype": "Bundsikring",
        "anvendelse": "Bundsikring meget grov",
    },
    {
        "navn": "Skærver 0-250",
        "phi": 45,
        "max_korn": 250,
        "lagtype": "Bundsikring",
        "anvendelse": "Bundsikring ekstrem",
    },
]

# Hjælpeliste — kun navne, bruges til dropdowns
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
    # Tekniske data (trækstyrke, maskestørrelse, dimensioner, GWP) for SS30, HX5.5,
    # HX165, NX750 og NX850 er ikke tilgængelige i de foreliggende kildedokumenter.
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
        "bemærkning": "REFERENCE (Tensar-design) — effektindeks 100. Maks. tid uden afdækning: < 2 uger.",
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
        "bemærkning": "Effektindeks 105. Tekniske specifikationer ikke tilgængelige i foreliggende kildedokumenter.",
    },
    {
        "navn": "Tensar InterAx NX750",
        "serie": "Tensar",
        "type": "Hexagonalt",
        "effektindeks": "110–120",
        "korrektion": -0.10,
        "max_korn": None,
        "anbefalet_tilslag": None,
        "rudeaabning": None,
        "min_daklag": 20,
        "klasser": [5, 6],
        "radial_stivhed": None,
        "gwp": None,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "bemærkning": "Effektindeks 110–120. Tekniske specifikationer ikke tilgængelige i foreliggende kildedokumenter.",
    },
    {
        "navn": "Tensar InterAx NX850",
        "serie": "Tensar",
        "type": "Hexagonalt",
        "effektindeks": "115–130",
        "korrektion": -0.15,
        "max_korn": None,
        "anbefalet_tilslag": None,
        "rudeaabning": None,
        "min_daklag": 20,
        "klasser": [5, 6],
        "radial_stivhed": None,
        "gwp": None,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "bemærkning": "Effektindeks 115–130. Tekniske specifikationer ikke tilgængelige i foreliggende kildedokumenter.",
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
        "min_daklag": 20,
        "klasser": [1, 2, 3],
        "radial_stivhed": None,
        "gwp": 0.55,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
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
        "min_daklag": 20,
        "klasser": [3, 4, 5],
        "radial_stivhed": None,
        "gwp": 0.81,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
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
        "min_daklag": 40,
        "klasser": [3, 4, 5],
        "radial_stivhed": None,
        "gwp": 0.87,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "bemærkning": "Effektindeks 90. Stor rudeåbning — egnet til groft tilslag.",
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
        "min_daklag": 60,
        "klasser": [4, 5, 6],
        "radial_stivhed": None,
        "gwp": 0.83,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "bemærkning": "Effektindeks 90. Meget stor rudeåbning — til meget groft tilslag.",
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
        "min_daklag": 20,
        "klasser": [4, 5, 6],
        "radial_stivhed": None,
        "gwp": 1.15,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
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
        "min_daklag": 40,
        "klasser": [4, 5, 6],
        "radial_stivhed": None,
        "gwp": 1.17,
        "min_levetid": None,
        "overlap_eu_ge5_cm": 30,
        "overlap_eu_lt5_cm": 40,
        "bemærkning": "Effektindeks 100. Stor rudeåbning — egnet til groft tilslag.",
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
        "bemærkning": "REFERENCE (GS/E'GRID-design) — effektindeks 100. Maks. tid uden afdækning: < 2 uger.",
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
        "bemærkning": "Alternativ til GS-GRID SX160 — REFERENCE (GS/E'GRID-design), effektindeks 100.",
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
        "bemærkning": "Alternativ til GS-GRID SX170 — effektindeks 110.",
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
        "type": "—",
        "effektindeks": "—",
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
        "bemærkning": "Korrektionsfaktor indtastes manuelt",
    },
]

# Hjælpeliste — kun navne, bruges til dropdowns
GEONET_NAVNE = [g["navn"] for g in GEONET_DB]

# ---------------------------------------------------------------------------
# 5b. GEONET_NOTER
#     Kilde: geonet_database_komplet.xlsx — "DB Geonet v2"
#     Vigtige noter og kildehenvisninger fra den komplette produktdatabase.
# ---------------------------------------------------------------------------

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
        "titel": "GS-GRID SX170: Maks. kornstørrelse vs. anbefalet tilslag",
        "tekst": (
            "GS-GRID SX170 har maks. kornstørrelse < 150 mm (datablad), men designmanualens "
            "figur 9 angiver anbefalet tilslag 0–80 mm — samme som SX160. "
            "Dette skyldes at SX170 har samme hexagonale pitch (80 mm) som SX160. "
            "Den højere max-korn på SX170 er en databladsgrænse, ikke en designanbefaling. "
            "I praksis anvendes 0–80 mm tilslag ved SX170."
        ),
    },
    {
        "titel": "Tensar-serien: Manglende tekniske data",
        "tekst": (
            "Datablade for Tensar SS30, HX5.5, HX165, InterAx NX750 og NX850 indgår ikke "
            "i de foreliggende kildedokumenter. Tekniske data (trækstyrke, maskestørrelse, "
            "dimensioner, GWP m.v.) for disse produkter kan ikke verificeres. "
            "Korrektionsfaktorer og belastningsklasser er fra Tensar Geonet Designmanual sept. 2024."
        ),
    },
    {
        "titel": "2-lags opbygning",
        "tekst": (
            "Begge designmanualer anbefaler ved total bærelagstykkelse > 50 cm at anvende "
            "2 eller flere lag geonet. Afstand mellem lag: min. 20 cm og maks. 50 cm "
            "(GS/E'GRID) / maks. 40 cm (Tensar). Øverste lag skal placeres min. 20 cm "
            "under overside af bærelag. I 2-lags Tensar-konstruktioner kan øverste lag "
            "udføres i TriAx TX150 med TX160 i bunden."
        ),
    },
    {
        "titel": "Overlæg i samlinger",
        "tekst": (
            "For alle produkter (begge serier): min. 30 cm overlæg ved Eu ≥ 5 MPa. "
            "Min. 40 cm overlæg ved Eu < 5 MPa."
        ),
    },
    {
        "titel": "Kildedokumenter",
        "tekst": (
            "1) GS-GRID/E'GRID Designmanual, BG Byggros, okt. 2025  |  "
            "2) Tensar Geonet Designmanual, BG Byggros, sept. 2024  |  "
            "3) GS-GRID Biaxial teknisk datablad (B-serien), BG Byggros, jun. 2025  |  "
            "4) GS-GRID SX teknisk datablad (SX160/SX170), BG Byggros, okt. 2025  |  "
            "5) Tensar TriAx TX160 teknisk specifikation, Tensar International, aug. 2024"
        ),
    },
]


# ---------------------------------------------------------------------------
# 6. KORREKTIONSFAKTORER
#    Kilde: Excel fane 4 "Korrektionsfaktorer"
# ---------------------------------------------------------------------------

# φ-korrektion pr. grad over 35° (negativ = tyndere bærelag ved højere φ)
K_PHI = -0.02

# Gyldighedsgrænser
EU_MIN = 3.0    # MPa — hård fejl under denne grænse
EU_MAX = 45.0   # MPa — hård fejl over denne grænse
EO_MIN = 30.0   # MPa
EO_MAX = 150.0  # MPa
PHI_MIN = 35.0  # grader — advarsel under denne
PHI_MAX = 50.0  # grader — advarsel over denne
MIN_DAKLAG_STANDARD = 200  # mm — minimum dæklag over geonet i opbygning


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
    for cv_min, cv_max, eu in CV_TIL_EU:
        if cv_min <= cv < cv_max:
            return float(eu)
    # Øvre grænse er inklusiv
    if cv == 180:
        return 30.0
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
