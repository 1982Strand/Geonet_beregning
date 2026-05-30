"""
Beregningsmotor til Geonet Dimensioneringsværktøj.

Implementerer den 7-trins algoritme beskrevet i Beskrivelse.md § 4.
Ingen imports herfra må være UI-relaterede.

Offentlig API:
    beregn(eu, eo, phi, net_korrektion, lag_mode) -> dict
    beregn_alle_produkter(eu, eo, lag_mode) -> list[dict]  (standard-tilstand)
"""

from .data import (
    T_BASIS_TABLE,
    EU_RAEKKER,
    EO_KOLONNER,
    GEONET_DB,
    K_PHI,
)


# ---------------------------------------------------------------------------
# Interne hjælpefunktioner
# ---------------------------------------------------------------------------

def _aktive_eu_raekker(t_basis_table: dict | None = None) -> list[float]:
    """Returner sorterede Eu-rækker for den valgte opslagstabel."""
    if t_basis_table is None:
        return EU_RAEKKER
    return sorted(t_basis_table.keys())


def _find_eu_naboer(
    eu: float,
    t_basis_table: dict | None = None,
) -> tuple[float, float] | None:
    """
    Find Eu-rækken i tabellen.

    Diagramtabellerne indeholder færdige opslagspunkter for hver Eu-værdi,
    så appen interpolerer ikke længere mellem Eu-rækker.
    """
    eu_raekker = _aktive_eu_raekker(t_basis_table)

    if eu in eu_raekker:
        return (eu, eu)

    return None


def _slaa_op(
    eu_raekke: float,
    eo: float,
    lag_type: str,
    t_basis_table: dict | None = None,
) -> float | None:
    """
    Direkte opslag i T_BASIS_TABLE.
    Returnerer tykkelse i cm, eller None hvis udenfor gyldighed ("—").

    lag_type: "uarmeret" | "1_lag" | "2_lag"
    """
    table = t_basis_table or T_BASIS_TABLE
    eu_data = table.get(eu_raekke)
    if eu_data is None:
        return None
    eo_data = eu_data.get(eo)
    if eo_data is None:
        return None
    # Håndter tastefejl i nøgle ("2_dag" i stedet for "2_lag" for Eu=45, Eo=80)
    val = eo_data.get(lag_type)
    return val


# ---------------------------------------------------------------------------
# Hoved-beregningsfunktion
# ---------------------------------------------------------------------------

def beregn(
    eu: float,
    eo: float,
    phi: float,
    net_korrektion: float,
    lag_mode: str,
    t_basis_table: dict | None = None,
) -> dict:
    """
    Beregn bærelagstykkelse med og uden armering.

    Parametre
    ---------
    eu              Underbundens E-modul i MPa (3–45)
    eo              Krævet E-modul på toppen af bærelaget i MPa (30–150)
    phi             Bærelagets friktionsvinkel i grader (typisk 35–50)
    net_korrektion  Korrektionsfaktor for armeringstype (0.0 = reference TX160/SX160)
    lag_mode        "1_lag" | "2_lag"

    Returnerer
    ----------
    dict med alle mellemresultater og slutresultater.
    Ved fejl indeholder dict'en nøglen "fejl" med en tekstbesked.
    """
    # -- Validér Eo er en af de 6 gyldige kolonner --
    if eo not in EO_KOLONNER:
        return {"fejl": f"Eo={eo} MPa er ikke en gyldig tabelværdi. Gyldige: {EO_KOLONNER}"}

    # -- Trin 1 & 2: Eu og Eo er allerede fastlagt af kalderen --

    # -- Trin 3: Fastlæg φ-korrektion --
    phi_korrektion = K_PHI * (phi - 35.0)

    # -- Trin 4: Opslag i designdiagram --
    eu_raekker = _aktive_eu_raekker(t_basis_table)
    naboer = _find_eu_naboer(eu, t_basis_table=t_basis_table)
    if naboer is None:
        return {"fejl": f"Eu={eu} MPa er uden for tabelområdet ({eu_raekker[0]}–{eu_raekker[-1]} MPa)"}

    eu_lower, eu_upper = naboer

    # Armeret (valgt lag_mode)
    t_low_arm = _slaa_op(eu_lower, eo, lag_mode, t_basis_table=t_basis_table)
    t_high_arm = _slaa_op(eu_upper, eo, lag_mode, t_basis_table=t_basis_table)

    if t_low_arm is None or t_high_arm is None:
        return {
            "fejl": (
                f"Kombinationen Eu={eu} MPa / Eo={eo} MPa / {lag_mode} er "
                f"uden for diagrammets gyldighedsområde (\"—\" i opslagstabellen). "
                f"Prøv et lavere Eu, et lavere Eo, eller færre lag."
            )
        }

    # Uarmeret
    t_low_uarm = _slaa_op(eu_lower, eo, "uarmeret", t_basis_table=t_basis_table)
    t_high_uarm = _slaa_op(eu_upper, eo, "uarmeret", t_basis_table=t_basis_table)

    uarmeret_mangler = t_low_uarm is None or t_high_uarm is None

    # Direkte opslag i diagramtabellen
    t_basis_arm_cm = t_low_arm
    t_basis_uarm_cm = None if uarmeret_mangler else t_low_uarm

    t_basis_arm_mm = t_basis_arm_cm * 10.0
    t_basis_uarm_mm = t_basis_uarm_cm * 10.0 if t_basis_uarm_cm is not None else None

    # -- Trin 5: φ-korrektion --
    # -- Trin 6: Net-korrektion --
    # -- Trin 7: Saml til endelig tykkelse --
    samlet_faktor = 1.0 + phi_korrektion + net_korrektion

    t_armeret_mm = t_basis_arm_mm * samlet_faktor
    # T_uarmeret er altid ren referencetabel — ingen φ/net-korrektion.
    # For meget lave Eu-værdier kan uarmeret være uden for diagrammet,
    # mens armerede resultater stadig er defineret.
    t_uarmeret_mm = t_basis_uarm_mm
    reduktion_mm = (
        t_uarmeret_mm - t_armeret_mm
        if t_uarmeret_mm is not None
        else None
    )
    reduktion_pct = (
        reduktion_mm / t_uarmeret_mm
        if reduktion_mm is not None and t_uarmeret_mm > 0
        else None
    )

    return {
        # Inputs (til forklaringsvisning)
        "eu": eu,
        "eo": eo,
        "phi": phi,
        "lag_mode": lag_mode,
        "net_korrektion": net_korrektion,
        # Mellemresultater — til "Sådan beregnes det"-visning
        "eu_lower": eu_lower,
        "eu_upper": eu_upper,
        "t_low_arm_cm": t_low_arm,
        "t_high_arm_cm": t_high_arm,
        "t_low_uarm_cm": t_low_uarm,
        "t_high_uarm_cm": t_high_uarm,
        "t_basis_arm_cm": round(t_basis_arm_cm, 1),
        "t_basis_arm_mm": round(t_basis_arm_mm, 0),
        "t_basis_uarm_cm": round(t_basis_uarm_cm, 1) if t_basis_uarm_cm is not None else None,
        "t_basis_uarm_mm": round(t_basis_uarm_mm, 0) if t_basis_uarm_mm is not None else None,
        "phi_korrektion": round(phi_korrektion, 4),
        "samlet_faktor": round(samlet_faktor, 4),
        # Slutresultater
        "t_armeret_mm": round(t_armeret_mm, 0),
        "t_uarmeret_mm": round(t_uarmeret_mm, 0) if t_uarmeret_mm is not None else None,
        "reduktion_mm": round(reduktion_mm, 0) if reduktion_mm is not None else None,
        "reduktion_pct": round(reduktion_pct, 4) if reduktion_pct is not None else None,
        "uarmeret_mangler": uarmeret_mangler,
        "uarmeret_fejl": (
            f"Der er ikke defineret nogen uarmeret bærelagstykkelse for Eu={eu} MPa / Eo={eo} MPa."
            if uarmeret_mangler
            else None
        ),
        # Ingen fejl
        "fejl": None,
    }


# ---------------------------------------------------------------------------
# Standard-tilstand: beregn alle produkter på én gang
# ---------------------------------------------------------------------------

def beregn_alle_produkter(
    eu: float,
    eo: float,
    lag_mode: str,
    phi: float = 35.0,
    t_basis_table: dict | None = None,
) -> list[dict]:
    """
    Beregn T_armeret for alle geonet-produkter med en given friktionsvinkel.

    phi defaulter til 35° (Standard-tilstand). Brugerdefineret-tilstand
    kan sende en anden φ-værdi beregnet fra materialelagene.

    Returnerer liste af dicts med:
        navn, serie, korrektion, t_armeret_mm, reduktion_mm, reduktion_pct,
        klasse_ok (bool), klasser, min_daklag, max_korn, fejl

    Sorteret efter t_armeret_mm stigende (tyndeste bærelag øverst).
    """
    # Find belastningsklasse ud fra Eo — til klasse-validering
    from .data import eo_til_klasse
    belastningsklasse = eo_til_klasse(eo)

    resultater = []
    for geonet in GEONET_DB:
        if geonet["navn"] == "Anden armering (manuel)":
            continue  # springer manuel over i oversigten

        resultat = beregn(
            eu=eu,
            eo=eo,
            phi=phi,
            net_korrektion=geonet["korrektion"],
            lag_mode=lag_mode,
            t_basis_table=t_basis_table,
        )

        klasse_ok = (
            belastningsklasse is None
            or belastningsklasse in geonet["klasser"]
        )

        resultater.append({
            "navn": geonet["navn"],
            "serie": geonet["serie"],
            "korrektion": geonet["korrektion"],
            "t_armeret_mm": resultat.get("t_armeret_mm"),
            "t_uarmeret_mm": resultat.get("t_uarmeret_mm"),
            "t_basis_arm_mm": resultat.get("t_basis_arm_mm"),
            "reduktion_mm": resultat.get("reduktion_mm"),
            "reduktion_pct": resultat.get("reduktion_pct"),
            "klasse_ok": klasse_ok,
            "klasser": geonet["klasser"],
            "min_daklag": geonet["min_daklag"],
            "max_korn": geonet["max_korn"],
            "fejl": resultat.get("fejl"),
        })

    # Sorter: produkter med fejl til sidst, ellers stigende tykkelse
    resultater.sort(key=lambda r: (
        r["fejl"] is not None,
        r["t_armeret_mm"] if r["t_armeret_mm"] is not None else 9999,
    ))

    return resultater


def grupper_produkter(produkter: list[dict], tolerance_mm: float = 5.0) -> list[dict]:
    """
    Grupper produkter efter opnåelig tykkelse inden for ±tolerance_mm.
    Produkter med fejl grupperes separat til sidst.

    Returnerer liste af grupper:
    {
        "t_armeret_mm": float,          # repræsentativ tykkelse (afrundet til 10)
        "reduktion_pct": float,
        "produkter": [{"navn", "serie", "klasse_ok", ...}],
        "har_fejl": bool,
        "fejl_besked": str | None,      # kun ved har_fejl=True, 2-lag uden data
    }
    """
    grupper = []
    brugte = set()

    gyldige = [p for p in produkter if p["fejl"] is None]
    fejlede = [p for p in produkter if p["fejl"] is not None]

    for produkt in gyldige:
        if produkt["navn"] in brugte:
            continue

        t = produkt["t_armeret_mm"]
        # Find alle produkter inden for tolerancen
        gruppe_produkter = [
            p for p in gyldige
            if p["navn"] not in brugte
            and abs(p["t_armeret_mm"] - t) <= tolerance_mm
        ]

        # Gennemsnitlig tykkelse for gruppen — eksakt beregnede værdi uden afrunding.
        t_repræsentativ = sum(p["t_armeret_mm"] for p in gruppe_produkter) / len(gruppe_produkter)

        t_uarm = produkt["t_uarmeret_mm"]
        red_pct = (
            (t_uarm - t_repræsentativ) / t_uarm
            if t_uarm is not None and t_uarm > 0
            else None
        )

        # t_basis_arm_mm er identisk for alle produkter i gruppen
        # (afhænger kun af eu/eo/lag_mode, ikke af produktets korrektion)
        t_basis_arm = gruppe_produkter[0].get("t_basis_arm_mm")

        grupper.append({
            "t_armeret_mm": round(t_repræsentativ, 0),
            "t_armeret_eksakt_mm": round(t_repræsentativ, 0),
            "reduktion_pct": round(red_pct, 4) if red_pct is not None else None,
            "reduktion_pct_eksakt": round(red_pct, 4) if red_pct is not None else None,
            "t_basis_arm_mm": t_basis_arm,
            "produkter": gruppe_produkter,
            "har_fejl": False,
            "fejl_besked": None,
        })

        for p in gruppe_produkter:
            brugte.add(p["navn"])

    # Tilføj fejlede produkter som én samlet gruppe med forklaring
    if fejlede:
        # Grupper fejlede efter fejlbesked
        fejl_typer: dict[str, list] = {}
        for p in fejlede:
            fejl_typer.setdefault(p["fejl"], []).append(p)

        for fejl_besked, fejl_gruppe in fejl_typer.items():
            grupper.append({
                "t_armeret_mm": None,
                "t_armeret_eksakt_mm": None,
                "reduktion_pct": None,
                "reduktion_pct_eksakt": None,
                "produkter": fejl_gruppe,
                "har_fejl": True,
                "fejl_besked": fejl_besked,
            })

    return grupper
