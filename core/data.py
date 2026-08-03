"""
Datatabeller til Geonet Dimensioneringsværktøj.

Kilde: geonet_dimensionering_v1_3.xlsx, fane "7. Opslagstabeller"
Alle værdier er aflæst direkte fra Excel-arkets tabel 7.1 (den beregnede
opslagstabel, ikke rådata). None svarer til "-" i Excel (uden for
diagrammets gyldighedsområde).

Ingen imports herfra må være UI-relaterede (Streamlit, Flask, osv.).
"""

import csv
import os

# ---------------------------------------------------------------------------
# 1. T_BASIS_TABLE
#    Struktur: T_BASIS_TABLE[eu_mpa][eo_mpa][lag_type] → tykkelse i cm
#    lag_type: "uarmeret" | "1_lag" | "2_lag"
#    None = "-" = uden for diagrammets gyldighedsområde
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

# Sorteret liste over alle Eu-nøgler.
EU_RAEKKER = sorted(T_BASIS_TABLE.keys())

# Gyldige Eo-værdier (svarer til de 6 belastningsklasser)
EO_KOLONNER = [30, 45, 60, 80, 120, 150]


# ---------------------------------------------------------------------------
# 1b. Diagramdata
#    Kilde: diagrambilleder/geonet_interpolerede_diagrammer.xlsx.
#    Hver række er et færdigt opslagspunkt for Eu. Tykkelserne er i cm og
#    indeholder både aflæste og allerede interpolerede værdier.
# ---------------------------------------------------------------------------

DESIGNDIAGRAM_RAW_TABLES = [{'diagram_nr': 1,
  'eo': 30,
  'klasse': 1,
  'image_name': 'Diagram 1.png',
  'rows': [{'eu': 1, 't_uarmeret_cm': None, 't_1_lag_cm': 87.3, 't_2_lag_cm': None},
           {'eu': 2, 't_uarmeret_cm': None, 't_1_lag_cm': 80, 't_2_lag_cm': None},
           {'eu': 3, 't_uarmeret_cm': 110, 't_1_lag_cm': 70, 't_2_lag_cm': None},
           {'eu': 4, 't_uarmeret_cm': 95.9, 't_1_lag_cm': 64.7, 't_2_lag_cm': None},
           {'eu': 5, 't_uarmeret_cm': 90, 't_1_lag_cm': 60, 't_2_lag_cm': None},
           {'eu': 6, 't_uarmeret_cm': 80, 't_1_lag_cm': 53.1, 't_2_lag_cm': None},
           {'eu': 7, 't_uarmeret_cm': 74.5, 't_1_lag_cm': 47.6, 't_2_lag_cm': None},
           {'eu': 8, 't_uarmeret_cm': 70, 't_1_lag_cm': 43.7, 't_2_lag_cm': None},
           {'eu': 9, 't_uarmeret_cm': 65, 't_1_lag_cm': 40, 't_2_lag_cm': None},
           {'eu': 10, 't_uarmeret_cm': 60, 't_1_lag_cm': 35.8, 't_2_lag_cm': None},
           {'eu': 11, 't_uarmeret_cm': 54.9, 't_1_lag_cm': 31.8, 't_2_lag_cm': None},
           {'eu': 12, 't_uarmeret_cm': 50, 't_1_lag_cm': 28.3, 't_2_lag_cm': None},
           {'eu': 13, 't_uarmeret_cm': 45.7, 't_1_lag_cm': 25.2, 't_2_lag_cm': None},
           {'eu': 14, 't_uarmeret_cm': 41.8, 't_1_lag_cm': 22.4, 't_2_lag_cm': None},
           {'eu': 15, 't_uarmeret_cm': 38.4, 't_1_lag_cm': 20, 't_2_lag_cm': None},
           {'eu': 16, 't_uarmeret_cm': 35.5, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 17, 't_uarmeret_cm': 32.9, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 18, 't_uarmeret_cm': 30, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 19, 't_uarmeret_cm': 26.7, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 20, 't_uarmeret_cm': 23.2, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 21, 't_uarmeret_cm': 20, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 22, 't_uarmeret_cm': 17.2, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 23, 't_uarmeret_cm': 14.7, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 24, 't_uarmeret_cm': 12.3, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 25, 't_uarmeret_cm': 10, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 26, 't_uarmeret_cm': 7.8, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 27, 't_uarmeret_cm': 5.7, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 28, 't_uarmeret_cm': 3.7, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 29, 't_uarmeret_cm': 1.8, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 30, 't_uarmeret_cm': 0, 't_1_lag_cm': None, 't_2_lag_cm': None}]},
 {'diagram_nr': 2,
  'eo': 45,
  'klasse': 2,
  'image_name': 'Diagram 2.png',
  'rows': [{'eu': 1, 't_uarmeret_cm': None, 't_1_lag_cm': 100, 't_2_lag_cm': 90},
           {'eu': 2, 't_uarmeret_cm': None, 't_1_lag_cm': 90, 't_2_lag_cm': 80},
           {'eu': 3, 't_uarmeret_cm': 120, 't_1_lag_cm': 83.5, 't_2_lag_cm': 70},
           {'eu': 4, 't_uarmeret_cm': 105.9, 't_1_lag_cm': 75, 't_2_lag_cm': 63},
           {'eu': 5, 't_uarmeret_cm': 100, 't_1_lag_cm': 66.1, 't_2_lag_cm': 57.2},
           {'eu': 6, 't_uarmeret_cm': 90, 't_1_lag_cm': 60, 't_2_lag_cm': 52.2},
           {'eu': 7, 't_uarmeret_cm': 84.5, 't_1_lag_cm': 56.1, 't_2_lag_cm': None},
           {'eu': 8, 't_uarmeret_cm': 80, 't_1_lag_cm': 53, 't_2_lag_cm': None},
           {'eu': 9, 't_uarmeret_cm': 75, 't_1_lag_cm': 50, 't_2_lag_cm': None},
           {'eu': 10, 't_uarmeret_cm': 70, 't_1_lag_cm': 46.6, 't_2_lag_cm': None},
           {'eu': 11, 't_uarmeret_cm': 64.8, 't_1_lag_cm': 43.2, 't_2_lag_cm': None},
           {'eu': 12, 't_uarmeret_cm': 60, 't_1_lag_cm': 40, 't_2_lag_cm': None},
           {'eu': 13, 't_uarmeret_cm': 56.3, 't_1_lag_cm': 37, 't_2_lag_cm': None},
           {'eu': 14, 't_uarmeret_cm': 53.2, 't_1_lag_cm': 34, 't_2_lag_cm': None},
           {'eu': 15, 't_uarmeret_cm': 50, 't_1_lag_cm': 31.3, 't_2_lag_cm': None},
           {'eu': 16, 't_uarmeret_cm': 46.5, 't_1_lag_cm': 28.8, 't_2_lag_cm': None},
           {'eu': 17, 't_uarmeret_cm': 43, 't_1_lag_cm': 26.4, 't_2_lag_cm': None},
           {'eu': 18, 't_uarmeret_cm': 40, 't_1_lag_cm': 24.1, 't_2_lag_cm': None},
           {'eu': 19, 't_uarmeret_cm': 37.6, 't_1_lag_cm': 22, 't_2_lag_cm': None},
           {'eu': 20, 't_uarmeret_cm': 35.5, 't_1_lag_cm': 20, 't_2_lag_cm': None},
           {'eu': 21, 't_uarmeret_cm': 33.6, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 22, 't_uarmeret_cm': 31.8, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 23, 't_uarmeret_cm': 30, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 24, 't_uarmeret_cm': 28.2, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 25, 't_uarmeret_cm': 26.5, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 26, 't_uarmeret_cm': 24.8, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 27, 't_uarmeret_cm': 23.2, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 28, 't_uarmeret_cm': 21.6, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 29, 't_uarmeret_cm': 20, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 30, 't_uarmeret_cm': 18.5, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 31, 't_uarmeret_cm': 17, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 32, 't_uarmeret_cm': 15.5, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 33, 't_uarmeret_cm': 14, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 34, 't_uarmeret_cm': 12.6, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 35, 't_uarmeret_cm': 11.3, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 36, 't_uarmeret_cm': 10, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 37, 't_uarmeret_cm': 8.8, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 38, 't_uarmeret_cm': 7.5, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 39, 't_uarmeret_cm': 6.4, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 40, 't_uarmeret_cm': 5.2, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 41, 't_uarmeret_cm': 4.1, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 42, 't_uarmeret_cm': 3, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 43, 't_uarmeret_cm': 2, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 44, 't_uarmeret_cm': 1, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 45, 't_uarmeret_cm': 0, 't_1_lag_cm': None, 't_2_lag_cm': None}]},
 {'diagram_nr': 3,
  'eo': 60,
  'klasse': 3,
  'image_name': 'Diagram 3.png',
  'rows': [{'eu': 1, 't_uarmeret_cm': None, 't_1_lag_cm': 110, 't_2_lag_cm': 94.6},
           {'eu': 2, 't_uarmeret_cm': None, 't_1_lag_cm': 95.7, 't_2_lag_cm': 86.3},
           {'eu': 3, 't_uarmeret_cm': 130, 't_1_lag_cm': 90, 't_2_lag_cm': 80},
           {'eu': 4, 't_uarmeret_cm': 115.9, 't_1_lag_cm': 83.1, 't_2_lag_cm': 73.1},
           {'eu': 5, 't_uarmeret_cm': 110, 't_1_lag_cm': 77.2, 't_2_lag_cm': 67.2},
           {'eu': 6, 't_uarmeret_cm': 100, 't_1_lag_cm': 72.3, 't_2_lag_cm': 62.3},
           {'eu': 7, 't_uarmeret_cm': 92.8, 't_1_lag_cm': 67.8, 't_2_lag_cm': 57.8},
           {'eu': 8, 't_uarmeret_cm': 87.7, 't_1_lag_cm': 63.8, 't_2_lag_cm': 53.7},
           {'eu': 9, 't_uarmeret_cm': 83.9, 't_1_lag_cm': 60, 't_2_lag_cm': 50},
           {'eu': 10, 't_uarmeret_cm': 80, 't_1_lag_cm': 56.4, 't_2_lag_cm': None},
           {'eu': 11, 't_uarmeret_cm': 74.9, 't_1_lag_cm': 53.1, 't_2_lag_cm': None},
           {'eu': 12, 't_uarmeret_cm': 70, 't_1_lag_cm': 50, 't_2_lag_cm': None},
           {'eu': 13, 't_uarmeret_cm': 66.3, 't_1_lag_cm': 47.3, 't_2_lag_cm': None},
           {'eu': 14, 't_uarmeret_cm': 63.1, 't_1_lag_cm': 44.8, 't_2_lag_cm': None},
           {'eu': 15, 't_uarmeret_cm': 60, 't_1_lag_cm': 42.4, 't_2_lag_cm': None},
           {'eu': 16, 't_uarmeret_cm': 57, 't_1_lag_cm': 40, 't_2_lag_cm': None},
           {'eu': 17, 't_uarmeret_cm': 54, 't_1_lag_cm': 37.4, 't_2_lag_cm': None},
           {'eu': 18, 't_uarmeret_cm': 51.3, 't_1_lag_cm': 34.7, 't_2_lag_cm': None},
           {'eu': 19, 't_uarmeret_cm': 48.8, 't_1_lag_cm': 32.1, 't_2_lag_cm': None},
           {'eu': 20, 't_uarmeret_cm': 46.4, 't_1_lag_cm': 30, 't_2_lag_cm': None},
           {'eu': 21, 't_uarmeret_cm': 44.1, 't_1_lag_cm': 28.2, 't_2_lag_cm': None},
           {'eu': 22, 't_uarmeret_cm': 42, 't_1_lag_cm': 26.4, 't_2_lag_cm': None},
           {'eu': 23, 't_uarmeret_cm': 40, 't_1_lag_cm': 24.8, 't_2_lag_cm': None},
           {'eu': 24, 't_uarmeret_cm': 38.1, 't_1_lag_cm': 23.3, 't_2_lag_cm': None},
           {'eu': 25, 't_uarmeret_cm': 36.4, 't_1_lag_cm': 22, 't_2_lag_cm': None},
           {'eu': 26, 't_uarmeret_cm': 34.7, 't_1_lag_cm': 20.9, 't_2_lag_cm': None},
           {'eu': 27, 't_uarmeret_cm': 33.1, 't_1_lag_cm': 20, 't_2_lag_cm': None},
           {'eu': 28, 't_uarmeret_cm': 31.5, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 29, 't_uarmeret_cm': 30, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 30, 't_uarmeret_cm': 28.5, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 31, 't_uarmeret_cm': 27, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 32, 't_uarmeret_cm': 25.5, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 33, 't_uarmeret_cm': 24, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 34, 't_uarmeret_cm': 22.6, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 35, 't_uarmeret_cm': 21.3, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 36, 't_uarmeret_cm': 20, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 37, 't_uarmeret_cm': 18.8, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 38, 't_uarmeret_cm': 17.5, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 39, 't_uarmeret_cm': 16.4, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 40, 't_uarmeret_cm': 15.2, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 41, 't_uarmeret_cm': 14.1, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 42, 't_uarmeret_cm': 13, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 43, 't_uarmeret_cm': 12, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 44, 't_uarmeret_cm': 11, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 45, 't_uarmeret_cm': 10, 't_1_lag_cm': None, 't_2_lag_cm': None}]},
 {'diagram_nr': 4,
  'eo': 80,
  'klasse': 4,
  'image_name': 'Diagram 4.png',
  'rows': [{'eu': 1, 't_uarmeret_cm': None, 't_1_lag_cm': 120, 't_2_lag_cm': 110},
           {'eu': 2, 't_uarmeret_cm': None, 't_1_lag_cm': 110, 't_2_lag_cm': 100},
           {'eu': 3, 't_uarmeret_cm': 140, 't_1_lag_cm': 100, 't_2_lag_cm': 90},
           {'eu': 4, 't_uarmeret_cm': 124.5, 't_1_lag_cm': 93.5, 't_2_lag_cm': 80},
           {'eu': 5, 't_uarmeret_cm': 114.5, 't_1_lag_cm': 84.7, 't_2_lag_cm': 74.5},
           {'eu': 6, 't_uarmeret_cm': 107.4, 't_1_lag_cm': 77.3, 't_2_lag_cm': 70},
           {'eu': 7, 't_uarmeret_cm': 103.7, 't_1_lag_cm': 73.5, 't_2_lag_cm': 65},
           {'eu': 8, 't_uarmeret_cm': 100, 't_1_lag_cm': 70, 't_2_lag_cm': 60},
           {'eu': 9, 't_uarmeret_cm': 95.1, 't_1_lag_cm': 65.8, 't_2_lag_cm': None},
           {'eu': 10, 't_uarmeret_cm': 90, 't_1_lag_cm': 61.8, 't_2_lag_cm': None},
           {'eu': 11, 't_uarmeret_cm': 84.8, 't_1_lag_cm': 58.3, 't_2_lag_cm': None},
           {'eu': 12, 't_uarmeret_cm': 80, 't_1_lag_cm': 55.2, 't_2_lag_cm': None},
           {'eu': 13, 't_uarmeret_cm': 76.3, 't_1_lag_cm': 52.4, 't_2_lag_cm': None},
           {'eu': 14, 't_uarmeret_cm': 73.1, 't_1_lag_cm': 50, 't_2_lag_cm': None},
           {'eu': 15, 't_uarmeret_cm': 70, 't_1_lag_cm': 48, 't_2_lag_cm': None},
           {'eu': 16, 't_uarmeret_cm': 67, 't_1_lag_cm': 46.2, 't_2_lag_cm': None},
           {'eu': 17, 't_uarmeret_cm': 64, 't_1_lag_cm': 44.6, 't_2_lag_cm': None},
           {'eu': 18, 't_uarmeret_cm': 61.3, 't_1_lag_cm': 43.1, 't_2_lag_cm': None},
           {'eu': 19, 't_uarmeret_cm': 58.8, 't_1_lag_cm': 41.6, 't_2_lag_cm': None},
           {'eu': 20, 't_uarmeret_cm': 56.4, 't_1_lag_cm': 40, 't_2_lag_cm': None},
           {'eu': 21, 't_uarmeret_cm': 54.1, 't_1_lag_cm': 38.3, 't_2_lag_cm': None},
           {'eu': 22, 't_uarmeret_cm': 52, 't_1_lag_cm': 36.6, 't_2_lag_cm': None},
           {'eu': 23, 't_uarmeret_cm': 50, 't_1_lag_cm': 34.9, 't_2_lag_cm': None},
           {'eu': 24, 't_uarmeret_cm': 48.1, 't_1_lag_cm': 33.2, 't_2_lag_cm': None},
           {'eu': 25, 't_uarmeret_cm': 46.4, 't_1_lag_cm': 31.6, 't_2_lag_cm': None},
           {'eu': 26, 't_uarmeret_cm': 44.7, 't_1_lag_cm': 30, 't_2_lag_cm': None},
           {'eu': 27, 't_uarmeret_cm': 43.1, 't_1_lag_cm': 28.5, 't_2_lag_cm': None},
           {'eu': 28, 't_uarmeret_cm': 41.5, 't_1_lag_cm': 27, 't_2_lag_cm': None},
           {'eu': 29, 't_uarmeret_cm': 40, 't_1_lag_cm': 25.5, 't_2_lag_cm': None},
           {'eu': 30, 't_uarmeret_cm': 38.5, 't_1_lag_cm': 24.1, 't_2_lag_cm': None},
           {'eu': 31, 't_uarmeret_cm': 37, 't_1_lag_cm': 22.7, 't_2_lag_cm': None},
           {'eu': 32, 't_uarmeret_cm': 35.5, 't_1_lag_cm': 21.3, 't_2_lag_cm': None},
           {'eu': 33, 't_uarmeret_cm': 34, 't_1_lag_cm': 20, 't_2_lag_cm': None},
           {'eu': 34, 't_uarmeret_cm': 32.6, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 35, 't_uarmeret_cm': 31.3, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 36, 't_uarmeret_cm': 30, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 37, 't_uarmeret_cm': 28.8, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 38, 't_uarmeret_cm': 27.5, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 39, 't_uarmeret_cm': 26.4, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 40, 't_uarmeret_cm': 25.2, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 41, 't_uarmeret_cm': 24.1, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 42, 't_uarmeret_cm': 23, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 43, 't_uarmeret_cm': 22, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 44, 't_uarmeret_cm': 21, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 45, 't_uarmeret_cm': 20, 't_1_lag_cm': None, 't_2_lag_cm': None}]},
 {'diagram_nr': 5,
  'eo': 120,
  'klasse': 5,
  'image_name': 'Diagram 5.png',
  'rows': [{'eu': 1, 't_uarmeret_cm': None, 't_1_lag_cm': 130, 't_2_lag_cm': 120},
           {'eu': 2, 't_uarmeret_cm': None, 't_1_lag_cm': 120, 't_2_lag_cm': 105.9},
           {'eu': 3, 't_uarmeret_cm': 150, 't_1_lag_cm': 110, 't_2_lag_cm': 100},
           {'eu': 4, 't_uarmeret_cm': 135.9, 't_1_lag_cm': 103.2, 't_2_lag_cm': 90},
           {'eu': 5, 't_uarmeret_cm': 130, 't_1_lag_cm': 96.6, 't_2_lag_cm': 82.8},
           {'eu': 6, 't_uarmeret_cm': 120, 't_1_lag_cm': 90, 't_2_lag_cm': 77.7},
           {'eu': 7, 't_uarmeret_cm': 114.5, 't_1_lag_cm': 84.8, 't_2_lag_cm': 73.9},
           {'eu': 8, 't_uarmeret_cm': 110, 't_1_lag_cm': 80, 't_2_lag_cm': 70},
           {'eu': 9, 't_uarmeret_cm': 105, 't_1_lag_cm': 74.7, 't_2_lag_cm': 64.7},
           {'eu': 10, 't_uarmeret_cm': 100, 't_1_lag_cm': 70, 't_2_lag_cm': 60},
           {'eu': 11, 't_uarmeret_cm': 94.8, 't_1_lag_cm': 66.6, 't_2_lag_cm': 56.6},
           {'eu': 12, 't_uarmeret_cm': 90, 't_1_lag_cm': 63.7, 't_2_lag_cm': 53.7},
           {'eu': 13, 't_uarmeret_cm': 86.3, 't_1_lag_cm': 61.2, 't_2_lag_cm': 51.4},
           {'eu': 14, 't_uarmeret_cm': 83.1, 't_1_lag_cm': 58.9, 't_2_lag_cm': 50},
           {'eu': 15, 't_uarmeret_cm': 80, 't_1_lag_cm': 56.9, 't_2_lag_cm': None},
           {'eu': 16, 't_uarmeret_cm': 77, 't_1_lag_cm': 55.1, 't_2_lag_cm': None},
           {'eu': 17, 't_uarmeret_cm': 74, 't_1_lag_cm': 53.4, 't_2_lag_cm': None},
           {'eu': 18, 't_uarmeret_cm': 71.3, 't_1_lag_cm': 51.7, 't_2_lag_cm': None},
           {'eu': 19, 't_uarmeret_cm': 68.8, 't_1_lag_cm': 50, 't_2_lag_cm': None},
           {'eu': 20, 't_uarmeret_cm': 66.4, 't_1_lag_cm': 48.3, 't_2_lag_cm': None},
           {'eu': 21, 't_uarmeret_cm': 64.1, 't_1_lag_cm': 46.5, 't_2_lag_cm': None},
           {'eu': 22, 't_uarmeret_cm': 62, 't_1_lag_cm': 44.8, 't_2_lag_cm': None},
           {'eu': 23, 't_uarmeret_cm': 60, 't_1_lag_cm': 43.1, 't_2_lag_cm': None},
           {'eu': 24, 't_uarmeret_cm': 58.1, 't_1_lag_cm': 41.5, 't_2_lag_cm': None},
           {'eu': 25, 't_uarmeret_cm': 56.4, 't_1_lag_cm': 40, 't_2_lag_cm': None},
           {'eu': 26, 't_uarmeret_cm': 54.7, 't_1_lag_cm': 38.6, 't_2_lag_cm': None},
           {'eu': 27, 't_uarmeret_cm': 53.1, 't_1_lag_cm': 37.2, 't_2_lag_cm': None},
           {'eu': 28, 't_uarmeret_cm': 51.5, 't_1_lag_cm': 35.9, 't_2_lag_cm': None},
           {'eu': 29, 't_uarmeret_cm': 50, 't_1_lag_cm': 34.6, 't_2_lag_cm': None},
           {'eu': 30, 't_uarmeret_cm': 48.5, 't_1_lag_cm': 33.3, 't_2_lag_cm': None},
           {'eu': 31, 't_uarmeret_cm': 47, 't_1_lag_cm': 32.2, 't_2_lag_cm': None},
           {'eu': 32, 't_uarmeret_cm': 45.5, 't_1_lag_cm': 31, 't_2_lag_cm': None},
           {'eu': 33, 't_uarmeret_cm': 44, 't_1_lag_cm': 30, 't_2_lag_cm': None},
           {'eu': 34, 't_uarmeret_cm': 42.6, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 35, 't_uarmeret_cm': 41.3, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 36, 't_uarmeret_cm': 40, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 37, 't_uarmeret_cm': 38.8, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 38, 't_uarmeret_cm': 37.5, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 39, 't_uarmeret_cm': 36.4, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 40, 't_uarmeret_cm': 35.2, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 41, 't_uarmeret_cm': 34.1, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 42, 't_uarmeret_cm': 33, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 43, 't_uarmeret_cm': 32, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 44, 't_uarmeret_cm': 31, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 45, 't_uarmeret_cm': 30, 't_1_lag_cm': None, 't_2_lag_cm': None}]},
 {'diagram_nr': 6,
  'eo': 150,
  'klasse': 6,
  'image_name': 'Diagram 6.png',
  'rows': [{'eu': 1, 't_uarmeret_cm': None, 't_1_lag_cm': 140, 't_2_lag_cm': 120},
           {'eu': 2, 't_uarmeret_cm': None, 't_1_lag_cm': 124.5, 't_2_lag_cm': 110},
           {'eu': 3, 't_uarmeret_cm': 160, 't_1_lag_cm': 115, 't_2_lag_cm': 100},
           {'eu': 4, 't_uarmeret_cm': 145.9, 't_1_lag_cm': 104.8, 't_2_lag_cm': 93},
           {'eu': 5, 't_uarmeret_cm': 140, 't_1_lag_cm': 96.2, 't_2_lag_cm': 87.2},
           {'eu': 6, 't_uarmeret_cm': 130, 't_1_lag_cm': 90, 't_2_lag_cm': 82.3},
           {'eu': 7, 't_uarmeret_cm': 124.5, 't_1_lag_cm': 85.4, 't_2_lag_cm': 77.8},
           {'eu': 8, 't_uarmeret_cm': 120, 't_1_lag_cm': 81.7, 't_2_lag_cm': 73.8},
           {'eu': 9, 't_uarmeret_cm': 115, 't_1_lag_cm': 78.4, 't_2_lag_cm': 70},
           {'eu': 10, 't_uarmeret_cm': 110, 't_1_lag_cm': 75.3, 't_2_lag_cm': 66.3},
           {'eu': 11, 't_uarmeret_cm': 104.8, 't_1_lag_cm': 72.5, 't_2_lag_cm': 62.8},
           {'eu': 12, 't_uarmeret_cm': 100, 't_1_lag_cm': 70, 't_2_lag_cm': 60},
           {'eu': 13, 't_uarmeret_cm': 96.3, 't_1_lag_cm': 67.7, 't_2_lag_cm': 57.7},
           {'eu': 14, 't_uarmeret_cm': 93.1, 't_1_lag_cm': 65.6, 't_2_lag_cm': 55.6},
           {'eu': 15, 't_uarmeret_cm': 90, 't_1_lag_cm': 63.6, 't_2_lag_cm': 53.7},
           {'eu': 16, 't_uarmeret_cm': 87, 't_1_lag_cm': 61.7, 't_2_lag_cm': 52.1},
           {'eu': 17, 't_uarmeret_cm': 84, 't_1_lag_cm': 60, 't_2_lag_cm': 50.8},
           {'eu': 18, 't_uarmeret_cm': 81.3, 't_1_lag_cm': 58.4, 't_2_lag_cm': 50},
           {'eu': 19, 't_uarmeret_cm': 78.8, 't_1_lag_cm': 56.8, 't_2_lag_cm': None},
           {'eu': 20, 't_uarmeret_cm': 76.4, 't_1_lag_cm': 55.4, 't_2_lag_cm': None},
           {'eu': 21, 't_uarmeret_cm': 74.1, 't_1_lag_cm': 54, 't_2_lag_cm': None},
           {'eu': 22, 't_uarmeret_cm': 72, 't_1_lag_cm': 52.7, 't_2_lag_cm': None},
           {'eu': 23, 't_uarmeret_cm': 70, 't_1_lag_cm': 51.3, 't_2_lag_cm': None},
           {'eu': 24, 't_uarmeret_cm': 68.1, 't_1_lag_cm': 50, 't_2_lag_cm': None},
           {'eu': 25, 't_uarmeret_cm': 66.4, 't_1_lag_cm': 48.7, 't_2_lag_cm': None},
           {'eu': 26, 't_uarmeret_cm': 64.7, 't_1_lag_cm': 47.4, 't_2_lag_cm': None},
           {'eu': 27, 't_uarmeret_cm': 63.1, 't_1_lag_cm': 46.1, 't_2_lag_cm': None},
           {'eu': 28, 't_uarmeret_cm': 61.5, 't_1_lag_cm': 44.8, 't_2_lag_cm': None},
           {'eu': 29, 't_uarmeret_cm': 60, 't_1_lag_cm': 43.6, 't_2_lag_cm': None},
           {'eu': 30, 't_uarmeret_cm': 58.5, 't_1_lag_cm': 42.4, 't_2_lag_cm': None},
           {'eu': 31, 't_uarmeret_cm': 57, 't_1_lag_cm': 41.2, 't_2_lag_cm': None},
           {'eu': 32, 't_uarmeret_cm': 55.5, 't_1_lag_cm': 40, 't_2_lag_cm': None},
           {'eu': 33, 't_uarmeret_cm': 54, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 34, 't_uarmeret_cm': 52.6, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 35, 't_uarmeret_cm': 51.3, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 36, 't_uarmeret_cm': 50, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 37, 't_uarmeret_cm': 48.8, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 38, 't_uarmeret_cm': 47.5, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 39, 't_uarmeret_cm': 46.4, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 40, 't_uarmeret_cm': 45.2, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 41, 't_uarmeret_cm': 44.1, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 42, 't_uarmeret_cm': 43, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 43, 't_uarmeret_cm': 42, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 44, 't_uarmeret_cm': 41, 't_1_lag_cm': None, 't_2_lag_cm': None},
           {'eu': 45, 't_uarmeret_cm': 40, 't_1_lag_cm': None, 't_2_lag_cm': None}]}]


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


T_BASIS_TABLE = _t_basis_table_from_designdiagrammer(DESIGNDIAGRAM_RAW_TABLES)
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
# 2b. TRAFIKKOBLING
#    Vejledende kobling mellem Tensar/GS-GRID belastningsklasse (1–6) og
#    Vejdirektoratets trafikklassificering fra "Dimensionering – befæstelser
#    og forstærkningsbelægninger" (jan. 2022, rev. aug. 2025), figur 4.1.
#
#    Tensar/GS-GRID-designmanualerne knytter ikke klasserne formelt til
#    VD-systemet - denne mapping bygger på anvendelsesbeskrivelsen
#    (cykelsti / villavej / hovedvej / landingsbane) og er en
#    ekspertvurdering, ikke en normfastlagt konvertering.
#
#    naae10_aar: tuple (min, max) for NÆ10/år pr. vognbane.
#                None = ingen tung trafik. max = None = ingen øvre grænse.
#    tunge_doegn: friformuleret string ("≤ 65", "560–1.500", "Ingen ...").
# ---------------------------------------------------------------------------

TRAFIKKOBLING = {
    1: {"t_klasse": "T0",    "naae10_aar": None,                  "tunge_doegn": "Ingen tung trafik"},
    2: {"t_klasse": "T1",    "naae10_aar": (0, 75),               "tunge_doegn": "≤ 1"},
    3: {"t_klasse": "T2",    "naae10_aar": (0, 7_300),            "tunge_doegn": "≤ 65"},
    4: {"t_klasse": "T3–T4", "naae10_aar": (18_300, 73_000),      "tunge_doegn": "65–560"},
    5: {"t_klasse": "T5–T6", "naae10_aar": (180_000, 300_000),    "tunge_doegn": "560–1.500"},
    6: {"t_klasse": "T7",    "naae10_aar": (300_000, None),       "tunge_doegn": "> 1.500"},
}

TRAFIKKOBLING_NOTE = (
    "Med udgangspunkt i designmanualernes belastningsklasser, sammenlignes med "
    "Vejdirektoratets trafikklassificering (T-klasse / Æ10 / ÅDT). "
    "Sammenhængen bygger på anvendelsesbeskrivelsen og er en vurdering."
)


def _format_naae10(naae10: tuple | None) -> str:
    if naae10 is None:
        return "-"
    lo, hi = naae10
    if lo in (None, 0) and hi is not None:
        return f"NÆ10 ≤ {hi:,}/år".replace(",", ".")
    if hi is None and lo is not None:
        return f"NÆ10 > {lo:,}/år".replace(",", ".")
    return f"NÆ10 {lo:,}–{hi:,}/år".replace(",", ".")


def format_trafikkobling(klasse: int) -> str:
    """
    Returnér én-linjes streng med VD-trafikkoblingen for en belastningsklasse,
    fx 'T2 · NÆ10 ≤ 7.300/år · ≤ 65 tunge køretøjer/døgn'.
    """
    data = TRAFIKKOBLING.get(klasse)
    if not data:
        return "-"
    dele = [data["t_klasse"]]
    naae10_str = _format_naae10(data["naae10_aar"])
    if naae10_str != "-":
        dele.append(naae10_str)
    tunge = data["tunge_doegn"]
    if tunge.lower().startswith("ingen"):
        dele.append(tunge)
    else:
        dele.append(f"{tunge} tunge køretøjer/døgn")
    return " · ".join(dele)


# ---------------------------------------------------------------------------
# 2c. TRAFIKKLASSER + KORRELATION_T_EO
#
#     Dokumenteret bro fra Vejdirektoratets trafikklasser (T1–T6) til appens
#     designdiagrammer. I MODSÆTNING til TRAFIKKOBLING ovenfor (en vejledende
#     ekspertvurdering ud fra anvendelse) er dette en beregnet/tilbageberegnet
#     korrelation: for hver (trafikklasse, Eu) er den ækvivalente Eo fundet
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
#              lav klasse)  → dimensionér via belastningsklasse-grundlaget.
#       OVER:  VejDim kræver mere end Eo=150-kurven (stiv bund × høj klasse)
#              → en konkret VejDim-beregning er nødvendig.
# ---------------------------------------------------------------------------

TRAFIK_UNDER = "under"
TRAFIK_OVER = "over"

# De Eu-værdier (MPa) korrelationen er tabuleret ved.
TRAFIK_EU_PUNKTER = [5, 10, 15, 20, 30, 40]

# ---------------------------------------------------------------------------
# VEJDIM_KOERSLER — datagrundlaget (de rå kørsler)
#
#   Indlæses fra "Dokumenter og data/VejDim_kørsler.csv", som er den samlede
#   fil med alle 36 kørsler. Redigeres CSV'en, følger appen med: både de rå
#   lagtykkelser, asfaltpakkerne og den tilbageberegnede Eo_ækv.
#
#   VEJDIM_KOERSLER:      {T: {Eu: {"sg": mm, "bl": mm}}} — kun de ubundne lag.
#                         sg = stabilgrus (SG II), bl = bundsikring (BL II).
#                         Ubundet total = sg + bl → Eo_ækv tilbageberegnes
#                         herfra (se korrelation_fra_koersler).
#   VEJDIM_KOERSLER_RAEKKER: fulde rækker (asfaltlag, E, levetid, koblingshøjde,
#                         kilde, bemærkning) til visning af forudsætningerne.
#
#   Kan CSV'en ikke læses, bruges den indbyggede fallback nedenfor, så appen
#   altid kan køre. Fuld dokumentation: "Korrelation_trafikklasse_Eo.md".
# ---------------------------------------------------------------------------

_REPO_ROD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VEJDIM_KOERSLER_CSV = os.path.join(
    _REPO_ROD, "Dokumenter og data", "VejDim_kørsler.csv"
)

# Indbygget reservekopi — bruges kun hvis CSV-filen mangler eller er defekt.
_VEJDIM_KOERSLER_FALLBACK = {
    "T1": {5: {"sg": 110, "bl": 450}, 10: {"sg": 100, "bl": 356}, 15: {"sg": 100, "bl": 292},
           20: {"sg": 100, "bl": 243}, 30: {"sg": 100, "bl": 200}, 40: {"sg": 100, "bl": 200}},
    "T2": {5: {"sg": 370, "bl": 458}, 10: {"sg": 250, "bl": 458}, 15: {"sg": 190, "bl": 446},
           20: {"sg": 160, "bl": 419}, 30: {"sg": 140, "bl": 346}, 40: {"sg": 140, "bl": 272}},
    "T3": {5: {"sg": 430, "bl": 449}, 10: {"sg": 300, "bl": 449}, 15: {"sg": 210, "bl": 470},
           20: {"sg": 170, "bl": 449}, 30: {"sg": 150, "bl": 364}, 40: {"sg": 150, "bl": 283}},
    "T4": {5: {"sg": 240, "bl": 944}, 10: {"sg": 230, "bl": 740}, 15: {"sg": 220, "bl": 629},
           20: {"sg": 220, "bl": 539}, 30: {"sg": 220, "bl": 409}, 40: {"sg": 220, "bl": 319}},
    "T5": {5: {"sg": 270, "bl": 1042}, 10: {"sg": 260, "bl": 818}, 15: {"sg": 250, "bl": 689},
           20: {"sg": 250, "bl": 590}, 30: {"sg": 240, "bl": 459}, 40: {"sg": 240, "bl": 360}},
    "T6": {5: {"sg": 280, "bl": 1117}, 10: {"sg": 270, "bl": 876}, 15: {"sg": 270, "bl": 723},
           20: {"sg": 260, "bl": 629}, 30: {"sg": 260, "bl": 478}, 40: {"sg": 260, "bl": 370}},
}


def _csv_tal(vaerdi, standard=None):
    """Konverter en CSV-celle til tal (dansk komma tilladt). None ved tom/ugyldig."""
    if vaerdi is None:
        return standard
    tekst = str(vaerdi).strip().replace(",", ".")
    if tekst in ("", "-"):
        return standard
    try:
        return float(tekst)
    except ValueError:
        return standard


def indlaes_vejdim_koersler(
    sti: str | None = None,
) -> tuple[dict, list[dict]]:
    """Indlæs de samlede VejDim-kørsler fra CSV.

    Returnerer (koersler, raekker):
        koersler = {T: {Eu(int): {"sg": float, "bl": float}}}
        raekker  = liste af fulde rækker (tal konverteret) inkl. de afledte
                   totaler "t_ubundet_total_mm" (SG+BL) og
                   "t_befaestelse_total_mm" (alle lag). Totalerne beregnes her
                   og står derfor ikke i CSV'en — den indeholder kun rådata, så
                   der ikke kan opstå uoverensstemmelser.
    Ved manglende/defekt fil returneres (fallback, []).
    """
    sti = sti or VEJDIM_KOERSLER_CSV
    koersler: dict = {}
    raekker: list[dict] = []
    try:
        with open(sti, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f, delimiter=";"):
                t = (r.get("T") or "").strip()
                eu = _csv_tal(r.get("Eu_MPa"))
                sg = _csv_tal(r.get("t_SG_mm"))
                bl = _csv_tal(r.get("t_BL_mm"))
                if not t or eu is None or sg is None or bl is None:
                    continue
                koersler.setdefault(t, {})[int(eu)] = {"sg": sg, "bl": bl}
                t_slid = _csv_tal(r.get("t_slid_mm"), 0.0)
                t_binde = _csv_tal(r.get("t_bindelag_mm"), 0.0)
                t_bundet = _csv_tal(r.get("t_bundet_mm"), 0.0)
                raekker.append({
                    "T": t,
                    "eu": int(eu),
                    "slidlag": (r.get("slidlag") or "").strip(),
                    "t_slid_mm": t_slid,
                    "bindelag": (r.get("bindelag") or "").strip(),
                    "t_bindelag_mm": t_binde,
                    "bundet_baerelag": (r.get("bundet_baerelag") or "").strip(),
                    "t_bundet_mm": t_bundet,
                    "E_asf_vist_MPa": _csv_tal(r.get("E_asf_vist_MPa")),
                    "t_SG_mm": sg,
                    "t_BL_mm": bl,
                    # Afledte totaler — beregnes altid, står ikke i CSV'en.
                    "t_ubundet_total_mm": sg + bl,
                    "t_befaestelse_total_mm": t_slid + t_binde + t_bundet + sg + bl,
                    "levetid_styrende_aar": _csv_tal(r.get("levetid_styrende_aar")),
                    "bemaerkning": (r.get("bemaerkning") or "").strip(),
                })
    except (OSError, csv.Error, ValueError):
        return _VEJDIM_KOERSLER_FALLBACK, []
    if not koersler:
        return _VEJDIM_KOERSLER_FALLBACK, []
    return koersler, raekker


VEJDIM_KOERSLER, VEJDIM_KOERSLER_RAEKKER = indlaes_vejdim_koersler()
# "csv" hvis grundlaget kom fra filen, ellers "indbygget" (fallback).
VEJDIM_KOERSLER_KILDE = "csv" if VEJDIM_KOERSLER_RAEKKER else "indbygget"


def back_beregn_eo_aekv(
    eu: float, ubundet_mm: float, t_basis_table: dict | None = None
) -> tuple[float | None, str]:
    """Tilbageberegn den ækvivalente Eo for en ubundet tykkelse ved given Eu.

    Finder den Eo, hvis ustabiliserede diagram-tykkelse (uarmeret) ved eu netop
    svarer til ``ubundet_mm``, ved lineær interpolation mellem Eo-kolonnerne.
    Returnerer (eo_aekv, zone):
        "ok":   eo_aekv er et tal.
        "under": ubundet < diagrammets Eo=30-kurve (blød bund × lav klasse).
        "over":  ubundet > Eo=150-kurven (stiv bund × høj klasse).
        "udenfor": Eu-rækken findes ikke / ingen uarmeret-data.
    """
    table = t_basis_table or T_BASIS_TABLE
    row = table.get(eu)
    if not row:
        return None, "udenfor"
    pts = sorted(
        [(eo, row[eo]["uarmeret"] * 10.0)
         for eo in EO_KOLONNER
         if row.get(eo, {}).get("uarmeret") is not None],
        key=lambda p: p[1],
    )
    if not pts:
        return None, "udenfor"
    if ubundet_mm < pts[0][1]:
        return None, TRAFIK_UNDER
    if ubundet_mm > pts[-1][1]:
        return None, TRAFIK_OVER
    for (e1, t1), (e2, t2) in zip(pts, pts[1:]):
        if t1 <= ubundet_mm <= t2:
            return (e1 + (ubundet_mm - t1) / (t2 - t1) * (e2 - e1)) if t2 > t1 else float(e1), "ok"
    return None, "udenfor"


def korrelation_fra_koersler(
    koersler: dict, t_basis_table: dict | None = None
) -> dict:
    """Byg korrelationstabellen (T → Eu → Eo_ækv/'under'/'over') fra de rå
    VejDim-kørsler ved tilbageberegning mod designdiagrammet.

    Celleværdien kan være enten den ubundne total i mm (tal) eller en dict med
    "sg"/"bl" (som VEJDIM_KOERSLER). Kun summen SG+BL indgår i broen —
    fordelingen mellem lagene har ingen betydning for Eo_ækv.
    """
    korr: dict = {}
    for t_klasse, raekker in koersler.items():
        korr[t_klasse] = {}
        for eu, v in raekker.items():
            if isinstance(v, dict):
                ub = (v.get("sg") or 0) + (v.get("bl") or 0)
            else:
                ub = float(v or 0)
            eo, zone = back_beregn_eo_aekv(float(eu), float(ub), t_basis_table)
            korr[t_klasse][int(eu)] = eo if zone == "ok" else zone
    return korr


# Standard-korrelationen, tilbageberegnet fra VEJDIM_KOERSLER mod diagrammet.
# (Reproducerer de dokumenterede Eo_ækv-værdier i notatets §4.)
KORRELATION_T_EO = korrelation_fra_koersler(VEJDIM_KOERSLER, T_BASIS_TABLE)

# Metadata pr. trafikklasse. naae10_mio_20aar = NÆ10 over 20 års
# dimensioneringsperiode (mio.), som brugt i VejDim-kørslerne (jf. notatets §2).
TRAFIKKLASSER = {
    "T1": {"ikon": "🚲", "naae10_mio_20aar": 0.002, "beskrivelse": "Meget let trafik (stier, boligveje med minimal tung trafik)"},
    "T2": {"ikon": "🚜", "naae10_mio_20aar": 0.15,  "beskrivelse": "Let trafik"},
    "T3": {"ikon": "🚗", "naae10_mio_20aar": 0.37,  "beskrivelse": "Let–middel trafik"},
    "T4": {"ikon": "🚛", "naae10_mio_20aar": 1.46,  "beskrivelse": "Middel trafik"},
    "T5": {"ikon": "🏗️", "naae10_mio_20aar": 3.6,   "beskrivelse": "Tung trafik"},
    "T6": {"ikon": "✈️", "naae10_mio_20aar": 6.0,   "beskrivelse": "Meget tung trafik"},
}

TRAFIKKLASSE_NOTE = (
    "Trafikklasse-grundlaget kobler Vejdirektoratets trafikklasser til "
    "designdiagrammerne via en dokumenteret tilbageberegning: VejDim fastlægger "
    "den krævede ubundne lagtykkelse (SG + BL) for (trafikklasse, Eu), og "
    "geonet-reduktionen aflæses som diagrammets egen feltdokumenterede værdi ved "
    "den ækvivalente Eo. Grundlaget er rent bæreevne (frostsikker underbund) — "
    "frost/koblingshøjde skal kontrolleres separat. Se "
    "'Korrelation_trafikklasse_Eo.md' for fuld dokumentation og forbehold."
)


def trafik_eo_aekv(
    t_klasse: str, eu: float, korrelation: dict | None = None
) -> tuple[float | None, str]:
    """Ækvivalent Eo (MPa) for en trafikklasse ved given Eu, med Eu-interpolation.

    korrelation overstyrer korrelationstabellen (fx en brugerredigeret tabel fra
    session-state). None = standardtabellen KORRELATION_T_EO.

    Returnerer (eo_aekv, zone):
        zone == "ok":      eo_aekv er et tal — dimensionér via diagrammet.
        zone == "under":   VejDim under diagrammets område (blød bund × lav klasse).
        zone == "over":    VejDim over diagrammets område (stiv bund × høj klasse).
        zone == "udenfor": Eu uden for korrelationens interval (5–40 MPa) eller
                           ukendt trafikklasse.
    Ved zone != "ok" er eo_aekv None.

    Eo_ækv interpoleres lineært mellem de tabulerede Eu-punkter
    {5,10,15,20,30,40}. Falder et af de omkringliggende punkter i en
    UNDER/OVER-zone, arver mellemliggende Eu samme zone (konservativt — der
    interpoleres ikke hen over en zonegrænse).
    """
    tabel = korrelation if korrelation is not None else KORRELATION_T_EO
    rk = tabel.get(t_klasse)
    if rk is None:
        return None, "udenfor"
    punkter = TRAFIK_EU_PUNKTER
    if eu < punkter[0] or eu > punkter[-1]:
        return None, "udenfor"

    if eu in rk:  # præcist tabelpunkt (5,10,15,20,30,40)
        v = rk[eu]
        return (None, v) if isinstance(v, str) else (float(v), "ok")

    lav = max(p for p in punkter if p <= eu)
    hoej = min(p for p in punkter if p >= eu)
    v_lav, v_hoej = rk[lav], rk[hoej]
    if isinstance(v_lav, str):
        return None, v_lav
    if isinstance(v_hoej, str):
        return None, v_hoej
    frac = (eu - lav) / (hoej - lav)
    return v_lav + frac * (v_hoej - v_lav), "ok"


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


def format_trafikklasse(t_klasse: str) -> str:
    """Én-linjes streng for en trafikklasse, fx
    'T4 · NÆ10 ≈ 1,46 mio. (20 år) · Middel trafik'."""
    d = TRAFIKKLASSER.get(t_klasse)
    if not d:
        return t_klasse
    naae10 = f"{d['naae10_mio_20aar']:g}".replace(".", ",")
    return f"{t_klasse} · NÆ10 ≈ {naae10} mio. (20 år) · {d['beskrivelse']}"


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
            "5) Tensar TriAx TX160 teknisk specifikation, Tensar International, aug. 2024  |  "
            "6) Tensar InterAx NX750 Product Identification Data Sheet (PIDS), Tensar, dec. 2024  |  "
            "7) Tensar InterAx NX850 Product Identification Data Sheet (PIDS), Tensar, dec. 2024"
        ),
    },
]


# ---------------------------------------------------------------------------
# 6. KORREKTIONSFAKTORER
#    Kilde: Excel fane 4 "Korrektionsfaktorer"
# ---------------------------------------------------------------------------

# Basis-friktionsvinkel for opslagstabellens referencegrundlag
PHI_BASIS = 37.0

# φ-korrektion pr. grad over 37° (negativ = tyndere bærelag ved højere φ)
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
