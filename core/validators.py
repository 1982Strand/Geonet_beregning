"""
Validering til Geonet Dimensioneringsværktøj.

Implementerer hårde fejl (blokerer beregning), bløde advarsler og anbefalinger.
Ingen imports herfra må være UI-relaterede.

Offentlig API:
    valider_input(eu, eo, phi, lag_mode, geonet, materialer, t_armeret_mm) -> dict

Parametre-format for ``materialer`` (brugerdefineret tilstand):
    Liste af dicts — ét pr. materialelag (øverst til nederst):
    {
        "navn":         str,              # ex. "SG II 0-32" / "Manuel"
        "max_korn":     int | None,       # mm — None hvis ukendt/manuel
        "lagtype":      str,              # "Bærelag" | "Bundsikring"
        "tykkelse_mm":  float | None,     # kun i mm-mode
        "pct":          float | None,     # kun i procent-mode (0–100)
    }
    I standard-tilstand sendes materialer=None (eller []).

Parametre-format for ``geonet``:
    Dict fra GEONET_DB (med nøgler navn, korrektion, max_korn, min_daklag,
    klasser, serie) — eller None i standard-tilstand.
"""

from __future__ import annotations

from .data import (
    EU_MIN,
    EU_MAX,
    EO_MIN,
    EO_MAX,
    PHI_BASIS,
    PHI_MIN,
    PHI_MAX,
    EO_KOLONNER,
    MIN_DAKLAG_STANDARD,
    eo_til_klasse,
    format_klasse_interval,
)
from .calculator import beregn, _slaa_op, _find_eu_naboer


# ---------------------------------------------------------------------------
# Hoved-valideringsfunktion
# ---------------------------------------------------------------------------

def valider_input(
    eu: float,
    eo: float,
    phi: float,
    lag_mode: str,
    geonet: dict | None,
    materialer: list[dict] | None,
    t_armeret_mm: float | None = None,
    t_basis_table: dict | None = None,
) -> dict:
    """
    Valider alle inputs og returner fejl, advarsler og anbefalinger.

    Parametre
    ---------
    eu              Underbundens E-modul i MPa
    eo              Krævet E-modul på toppen af bærelaget i MPa
    phi             Bærelagets friktionsvinkel i grader
    lag_mode        "1_lag" | "2_lag"
    geonet          Dict fra GEONET_DB eller None (standard-tilstand)
    materialer      Liste af materialelag-dicts eller None (standard-tilstand)
    t_armeret_mm    Allerede beregnet T_armeret i mm — sendes ind for at
                    undgå dobbelt beregning. Hvis None, beregnes den internt
                    (kræver at der ikke er hårde fejl i eu/eo/lag_mode).

    Returnerer
    ----------
    {
        "fejl":          list[str],   # hård fejl — blokerer beregning
        "advarsler":     list[str],   # blød advarsel — vises men stopper ikke
        "anbefalinger":  list[str],   # designråd
    }
    """
    fejl: list[str] = []
    advarsler: list[str] = []
    anbefalinger: list[str] = []

    mat = materialer or []

    # -----------------------------------------------------------------------
    # HÅRDE FEJL — stopper beregningen
    # -----------------------------------------------------------------------

    # F1: Eu uden for gyldigt interval
    if eu < EU_MIN:
        fejl.append(
            f"Eu={eu} MPa er for lavt. Minimum er {EU_MIN} MPa. "
        )
    elif eu > EU_MAX:
        fejl.append(
            f"Eu={eu} MPa er for højt. Maximum er {EU_MAX} MPa. "
            f"Ved Eu > {EU_MAX} MPa reduceres effekten af stabilisering med geonet."
        )

    # F2: Eo uden for gyldigt interval
    if eo < EO_MIN:
        fejl.append(
            f"Eo={eo} MPa er for lavt. Minimum er {EO_MIN} MPa."
        )
    elif eo > EO_MAX:
        fejl.append(
            f"Eo={eo} MPa er for højt. Maximum er {EO_MAX} MPa "
            f"(svarer til klasse 6 — meget tung trafik)."
        )

    # F3: Eo er ikke en af de 6 gyldige tabelkolonner
    if EO_MIN <= eo <= EO_MAX and eo not in EO_KOLONNER:
        fejl.append(
            f"Eo={eo} MPa svarer ikke til en belastningsklasse. "
            f"Gyldige Eo-værdier: {EO_KOLONNER} MPa. "
            f"Vælg en gyldig belastningsklasse."
        )

    # F4: lag_mode er ugyldig
    if lag_mode not in ("1_lag", "2_lag"):
        fejl.append(
            f"Ukendt lag-tilstand: '{lag_mode}'. Skal være '1_lag' eller '2_lag'."
        )

    # F5: T_basis-opslag returnerer None (kombination uden for diagrammet)
    # Kun tjekket hvis de foregående input-fejl ikke allerede blokerer
    if not fejl and lag_mode in ("1_lag", "2_lag"):
        naboer = _find_eu_naboer(eu, t_basis_table=t_basis_table)
        if naboer is not None:
            eu_lower, eu_upper = naboer
            t_lower = _slaa_op(eu_lower, eo, lag_mode, t_basis_table=t_basis_table)
            t_upper = _slaa_op(eu_upper, eo, lag_mode, t_basis_table=t_basis_table)
            if t_lower is None or t_upper is None:
                fejl.append(
                    f"Kombinationen Eu={eu} MPa / Eo={eo} MPa / {lag_mode.replace('_', ' ')} "
                    f"er uden for opslagstabellens gyldige område (\"—\"). "
                )
            # Tjek også uarmeret (til resultatvisning), men lad ikke
            # manglende uarmeret blokere armerede resultater.
            t_u_lower = _slaa_op(eu_lower, eo, "uarmeret", t_basis_table=t_basis_table)
            t_u_upper = _slaa_op(eu_upper, eo, "uarmeret", t_basis_table=t_basis_table)
            if t_u_lower is None or t_u_upper is None:
                advarsler.append(
                    f"Der er ikke defineret nogen ustabiliseret bærelagstykkelse "
                    f"for Eu={eu} MPa / Eo={eo} MPa."
                )

    # -----------------------------------------------------------------------
    # Tidlig exit — advarsler giver ingen mening uden gyldige grundlæggende inputs
    # -----------------------------------------------------------------------
    if fejl:
        return {"fejl": fejl, "advarsler": advarsler, "anbefalinger": anbefalinger}

    # -----------------------------------------------------------------------
    # Beregn t_armeret_mm internt hvis ikke sendt med
    # -----------------------------------------------------------------------
    if t_armeret_mm is None:
        net_korrektion = geonet["korrektion"] if geonet else 0.0
        resultat = beregn(eu, eo, phi, net_korrektion, lag_mode, t_basis_table=t_basis_table)
        if resultat.get("fejl"):
            # Beregningsfejl — returner som hård fejl
            fejl.append(resultat["fejl"])
            return {"fejl": fejl, "advarsler": advarsler, "anbefalinger": anbefalinger}
        t_armeret_mm = resultat["t_armeret_mm"]
        t_uarmeret_mm = resultat["t_uarmeret_mm"]
    else:
        # Genberegn uarmeret til brug i anbefalinger
        net_korrektion = geonet["korrektion"] if geonet else 0.0
        _res = beregn(eu, eo, PHI_BASIS, 0.0, lag_mode, t_basis_table=t_basis_table)
        t_uarmeret_mm = _res.get("t_uarmeret_mm", 0)

    # -----------------------------------------------------------------------
    # BLØDE ADVARSLER — stopper ikke beregningen
    # -----------------------------------------------------------------------

    # A1: φ under standard
    if phi < PHI_MIN:
        advarsler.append(
            f"Friktionsvinklen φ={phi}° er under standardværdien på {PHI_MIN:.0f}°. "
            f"φ-korrektionen vil øge den beregnede tykkelse. "
        )

    # A2: φ over realistisk grænse
    if phi > PHI_MAX:
        advarsler.append(
            f"Friktionsvinklen φ={phi}° er over den anbefalede øvre grænse "
            f"på {PHI_MAX:.0f}°."
        )

    # A3: Eu nær tabelgrænsen — uarmeret område indskrænket
    if eu >= 35.0:
        advarsler.append(
            f"Eu={eu} MPa er i den øvre del af opslagstabellen. "
            f"Den ustabiliserede tykkelse er meget lille, og "
            f"den relative besparelse ved stabilisering er begrænset. "
        )

    # A4: Produkt valgt uden for sin belastningsklasse
    if geonet is not None and geonet["navn"] != "Anden armering (manuel)":
        belastningsklasse = eo_til_klasse(eo)
        if belastningsklasse is not None and belastningsklasse not in geonet["klasser"]:
            klasse_str = format_klasse_interval(geonet["klasser"])
            advarsler.append(
                f"Produktet '{geonet['navn']}' er anbefalet til belastningsklasse "
                f"{klasse_str}, men der er valgt belastningsklasse "
                f"{belastningsklasse}."
            )

    # A5: Beregnet tykkelse er mindre end geonettets minimum dæklag
    # (min_daklag er i cm i GEONET_DB)
    if geonet is not None:
        min_daklag_mm = geonet["min_daklag"] * 10  # cm → mm
        if t_armeret_mm < min_daklag_mm:
            advarsler.append(
                f"Den beregnede stabiliserede tykkelse ({t_armeret_mm:.0f} mm) er "
                f"mindre end '{geonet['navn']}' sit minimumsdæklag "
                f"({min_daklag_mm:.0f} mm). "
                f"Geonettets funktion og effektivitet kan ikke garanteres. "
            )

    # A6: Materialelagenes kornstørrelse overstiger geonettets max_korn
    if geonet is not None and geonet["max_korn"] is not None:
        for idx, lag in enumerate(mat, start=1):
            mat_korn = lag.get("max_korn")
            if mat_korn is not None and mat_korn > geonet["max_korn"]:
                advarsler.append(
                    f"Lag {idx} ({lag.get('navn', 'ukendt')}) har en "
                    f"maksimal kornstørrelse på {mat_korn} mm, som overskrider "
                    f"'{geonet['navn']}' sit maximum på {geonet['max_korn']} mm. "
                )

    # A7: Rækkefølge-advarsel — Bundsikring over Bærelag
    # Normalt rækkefølge: Bærelag øverst, Bundsikring nederst
    for idx in range(len(mat) - 1):
        lag_over = mat[idx]
        lag_under = mat[idx + 1]
        if (
            lag_over.get("lagtype") == "Bundsikring"
            and lag_under.get("lagtype") == "Bærelag"
        ):
            advarsler.append(
                f"Rækkefølge-advarsel: Lag {idx + 1} er angivet som "
                f"Bundsikring ({lag_over.get('navn', '?')}), men "
                f"Lag {idx + 2} er Bærelag ({lag_under.get('navn', '?')}). "
                f"Bærelag placeres normalt over bundsikringen."
            )

    # A11: Net-korrektion er stærkt positiv — produktet er relativ ineffektivt
    if geonet is not None and geonet["navn"] != "Anden armering (manuel)":
        if geonet["korrektion"] >= 0.15:
            advarsler.append(
                f"'{geonet['navn']}' har en korrektionsfaktor på "
                f"+{geonet['korrektion']:.0%}, hvilket indikerer lavere "
                f"effektivitet end referenceproduktet. "
                f"Overvej et mere effektivt produkt til belastningsklassen."
            )

    # A12: Geonet med specifikt max_korn og valgt materiale ukendt korn (manuel)
    if geonet is not None and geonet["max_korn"] is not None:
        for idx, lag in enumerate(mat, start=1):
            if lag.get("max_korn") is None and lag.get("navn") not in (None, ""):
                advarsler.append(
                    f"Lag {idx} ({lag.get('navn', 'manuel')}) har ingen "
                    f"specificeret kornstørrelse. Det kan ikke automatisk "
                    f"kontrolleres om den er forenelig med "
                    f"'{geonet['navn']}' (max {geonet['max_korn']} mm). "
                )
                break  # én samlet advarsel er nok

    # A14: Materialets krav til geonet-maskestørrelse vs. biaksialt net
    # Kravet er kun defineret for biaksiale net — triaksiale/hexagonale
    # springes over indtil kravet er afklaret for disse typer.
    if (
        geonet is not None
        and geonet.get("type") == "Biaxialt"
        and geonet.get("maskestoerrelse_mm") is not None
    ):
        net_maske = geonet["maskestoerrelse_mm"]
        for idx, lag in enumerate(mat, start=1):
            krav = lag.get("krav_maskestoerrelse_mm")
            if krav is not None and krav > net_maske:
                advarsler.append(
                    f"Lag {idx} ({lag.get('navn', 'ukendt')}) kræver et "
                    f"biaksialt geonet med maskestørrelse ≥ {krav} mm, men "
                    f"'{geonet['navn']}' har {net_maske} mm. "
                    f"Vælg et net med større maskestørrelse."
                )

    # A13: 2-lag valgt men uarmeret tykkelse er beskeden
    if lag_mode == "2_lag" and t_uarmeret_mm is not None and t_uarmeret_mm < 600:
        advarsler.append(
            f"2 lag geonet er valgt, men den ustabiliserede referenctykkelse er "
            f"kun {t_uarmeret_mm:.0f} mm. "
            f"2 lag giver sjældent ekstra fordel ved relativt tynde opbygninger. "
            f"Overvej om 1 lag er tilstrækkeligt."
        )

    # -----------------------------------------------------------------------
    # ANBEFALINGER — designråd, ikke fejl
    # -----------------------------------------------------------------------

    # R1: T_armeret > 500 mm med 1 lag → foreslå 2 lag
    if lag_mode == "1_lag" and t_armeret_mm > 500:
        anbefalinger.append(
            f"Den stabiliserede tykkelse er {t_armeret_mm:.0f} mm med 1 lag geonet. "
            f"Med 2 lag geonet kan tykkelsen typisk reduceres yderligere. "
            f"Skift til '2 lag' og sammenlign resultatet."
        )

    # R2: T_armeret < 400 mm med 2 lag → 1 lag er sandsynligvis nok
    if lag_mode == "2_lag" and t_armeret_mm < 400:
        anbefalinger.append(
            f"Den stabiliserede tykkelse er {t_armeret_mm:.0f} mm med 2 lag geonet. "
            f"1 lag geonet er sandsynligvis tilstrækkeligt for denne belastning. "
            f"Skift til '1 lag' og sammenlign resultatet."
        )

    return {
        "fejl": fejl,
        "advarsler": advarsler,
        "anbefalinger": anbefalinger,
    }
