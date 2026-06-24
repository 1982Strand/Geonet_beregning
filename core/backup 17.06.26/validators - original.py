"""
Validering til Geonet Dimensioneringsværktøj.

Implementerer hårde fejl (blokerer beregning), bløde advarsler og anbefalinger.
Ingen imports herfra må være UI-relaterede.

Offentlig API:
    valider_input(eu, eo, phi, lag_mode, geonet, materialer, t_armeret_mm) -> dict
    valider_opbygning(lag_liste, geonet, t_armeret_mm) -> dict          (brugerdefineret)

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
    PHI_MIN,
    PHI_MAX,
    EO_KOLONNER,
    MIN_DAKLAG_STANDARD,
    eo_til_klasse,
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
            f"For meget bløde underbunde (Eu < {EU_MIN} MPa) anbefales "
            f"geoteknisk specialrådgivning."
        )
    elif eu > EU_MAX:
        fejl.append(
            f"Eu={eu} MPa er for højt. Maximum er {EU_MAX} MPa. "
            f"Ved Eu > {EU_MAX} MPa er geonetarmering sjældent nødvendig."
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
            f"Vælg den belastningsklasse der passer bedst til projektet."
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
                    f"Prøv et lavere Eo, et lavere Eu, eller skift til 1 lag."
                )
            # Tjek også uarmeret (til resultatvisning), men lad ikke
            # manglende uarmeret blokere armerede resultater.
            t_u_lower = _slaa_op(eu_lower, eo, "uarmeret", t_basis_table=t_basis_table)
            t_u_upper = _slaa_op(eu_upper, eo, "uarmeret", t_basis_table=t_basis_table)
            if t_u_lower is None or t_u_upper is None:
                advarsler.append(
                    f"Der er ikke defineret nogen uarmeret bærelagstykkelse "
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
        _res = beregn(eu, eo, 35.0, 0.0, lag_mode, t_basis_table=t_basis_table)
        t_uarmeret_mm = _res.get("t_uarmeret_mm", 0)

    # -----------------------------------------------------------------------
    # BLØDE ADVARSLER — stopper ikke beregningen
    # -----------------------------------------------------------------------

    # A1: φ under standard
    if phi < PHI_MIN:
        advarsler.append(
            f"Friktionsvinklen φ={phi}° er under standardværdien på {PHI_MIN}°. "
            f"φ-korrektionen vil øge den beregnede tykkelse. "
            f"Kontrollér at materialevalget understøtter denne friktionsvinkel."
        )

    # A2: φ over realistisk grænse
    if phi > PHI_MAX:
        advarsler.append(
            f"Friktionsvinklen φ={phi}° er over den anbefalede øvre grænse "
            f"på {PHI_MAX}°. Granulære materialer opnår sjældent φ > 50°. "
            f"Kontrollér kilden for friktionsvinklen."
        )

    # A3: Eu nær tabelgrænsen — uarmeret område indskrænket
    if eu >= 35.0:
        advarsler.append(
            f"Eu={eu} MPa er i den øvre del af opslagstabellen. "
            f"Den uarmerede tykkelse er meget lille, og "
            f"den relative besparelse ved armering er begrænset. "
            f"Overvej om geonetarmering er rentabel."
        )

    # A4: Produkt valgt uden for sin belastningsklasse
    if geonet is not None and geonet["navn"] != "Anden armering (manuel)":
        belastningsklasse = eo_til_klasse(eo)
        if belastningsklasse is not None and belastningsklasse not in geonet["klasser"]:
            klasse_str = ", ".join(str(k) for k in sorted(geonet["klasser"]))
            advarsler.append(
                f"Produktet '{geonet['navn']}' er godkendt til belastningsklasse "
                f"{klasse_str}, men den valgte belastning svarer til "
                f"klasse {belastningsklasse} (Eo={eo} MPa). "
                f"Vælg et produkt godkendt til den aktuelle klasse."
            )

    # A5: Beregnet tykkelse er mindre end geonettets minimum dæklag
    # (min_daklag er i cm i GEONET_DB)
    if geonet is not None:
        min_daklag_mm = geonet["min_daklag"] * 10  # cm → mm
        if t_armeret_mm < min_daklag_mm:
            advarsler.append(
                f"Den beregnede armerede tykkelse ({t_armeret_mm:.0f} mm) er "
                f"mindre end '{geonet['navn']}' sit minimumsdæklag "
                f"({min_daklag_mm:.0f} mm). "
                f"Geonettets funktion kan ikke garanteres. "
                f"Kontrollér opbygningen eller vælg et andet produkt."
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
                    f"Der er risiko for mekanisk beskadigelse af geonetttet."
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

    # A8: Procent-mode — sum ≠ 100 %
    if mat and all(lag.get("pct") is not None for lag in mat):
        total_pct = sum(lag["pct"] for lag in mat)
        if abs(total_pct - 100.0) > 0.5:
            advarsler.append(
                f"Materialelagsandelene summer til {total_pct:.1f} % — "
                f"de skal summere til 100 %. "
                f"Juster procenterne så de giver mening i opbygningen."
            )

    # A9: Individuelle lag < 100 mm (mm-mode)
    if mat and any(lag.get("tykkelse_mm") is not None for lag in mat):
        for idx, lag in enumerate(mat, start=1):
            t = lag.get("tykkelse_mm")
            if t is not None and 0 < t < 100:
                advarsler.append(
                    f"Lag {idx} ({lag.get('navn', 'ukendt')}) er kun "
                    f"{t:.0f} mm — under minimum på 100 mm. "
                    f"Meget tynde lag er svære at komprimere korrekt og "
                    f"kan forringe bæreevnen."
                )

    # A10: Samlet foreslået opbygning er tynd ift. beregnet T_armeret (mm-mode)
    if mat and any(lag.get("tykkelse_mm") is not None for lag in mat):
        total_opbygning = sum(
            lag["tykkelse_mm"] for lag in mat
            if lag.get("tykkelse_mm") is not None
        )
        if total_opbygning < t_armeret_mm:
            advarsler.append(
                f"Den samlede foreslåede opbygning ({total_opbygning:.0f} mm) "
                f"er mindre end den beregnede minimumtykkelse "
                f"({t_armeret_mm:.0f} mm). "
                f"Øg et eller flere lag for at opnå den nødvendige bæreevne."
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
                    f"Verificér manuelt inden udførelse."
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
            f"2 lag geonet er valgt, men den uarmerede referenctykkelse er "
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
            f"Den armerede tykkelse er {t_armeret_mm:.0f} mm med 1 lag geonet. "
            f"Med 2 lag geonet kan tykkelsen typisk reduceres yderligere. "
            f"Skift til '2 lag' og sammenlign resultatet."
        )

    # R2: T_armeret < 400 mm med 2 lag → 1 lag er sandsynligvis nok
    if lag_mode == "2_lag" and t_armeret_mm < 400:
        anbefalinger.append(
            f"Den armerede tykkelse er {t_armeret_mm:.0f} mm med 2 lag geonet. "
            f"1 lag geonet er sandsynligvis tilstrækkeligt for denne belastning. "
            f"Skift til '1 lag' og sammenlign resultatet."
        )

    return {
        "fejl": fejl,
        "advarsler": advarsler,
        "anbefalinger": anbefalinger,
    }


# ---------------------------------------------------------------------------
# Hjælpefunktion til brugerdefineret opbygnings-validering
# ---------------------------------------------------------------------------

def valider_opbygning(
    lag_liste: list[dict],
    geonet: dict | None,
    t_armeret_mm: float,
) -> dict:
    """
    Validér en konkret lagopbygning (brugerdefineret tilstand, mm-mode).

    Tjekker om den foreslåede opbygning lever op til beregningens krav
    og geonettets udfkrav — uden at gentage de generelle input-tjek.

    Parametre
    ---------
    lag_liste       Liste af lag med 'tykkelse_mm', 'lagtype', 'navn', 'max_korn'.
    geonet          Valgt geonet-dict eller None.
    t_armeret_mm    Beregnet minimum armeret tykkelse.

    Returnerer
    ----------
    { "advarsler": [...], "anbefalinger": [...] }   (ingen "fejl"-liste her)
    """
    advarsler: list[str] = []
    anbefalinger: list[str] = []

    if not lag_liste:
        return {"advarsler": advarsler, "anbefalinger": anbefalinger}

    total_mm = sum(lag.get("tykkelse_mm", 0) or 0 for lag in lag_liste)

    # B1: Total opbygning < T_armeret
    if total_mm < t_armeret_mm:
        advarsler.append(
            f"Samlet opbygning ({total_mm:.0f} mm) er under den beregnede "
            f"minimumtykkelse ({t_armeret_mm:.0f} mm). "
            f"Øg mindst ét lag."
        )

    # B2: Individuelle lag < 100 mm
    for idx, lag in enumerate(lag_liste, start=1):
        t = lag.get("tykkelse_mm") or 0
        if 0 < t < 100:
            advarsler.append(
                f"Lag {idx} ({lag.get('navn', '?')}) er {t:.0f} mm "
                f"— under minimum 100 mm."
            )

    # B3: Kornstørrelse vs. geonet max_korn
    if geonet and geonet["max_korn"] is not None:
        for idx, lag in enumerate(lag_liste, start=1):
            korn = lag.get("max_korn")
            if korn is not None and korn > geonet["max_korn"]:
                advarsler.append(
                    f"Lag {idx} ({lag.get('navn', '?')}) — "
                    f"kornstørrelse {korn} mm > geonet-max {geonet['max_korn']} mm."
                )

    # B4: Rækkefølge Bundsikring/Bærelag
    for idx in range(len(lag_liste) - 1):
        over = lag_liste[idx]
        under = lag_liste[idx + 1]
        if (
            over.get("lagtype") == "Bundsikring"
            and under.get("lagtype") == "Bærelag"
        ):
            advarsler.append(
                f"Lag {idx + 1} (Bundsikring) er placeret over "
                f"Lag {idx + 2} (Bærelag). Kontrollér lagrækken."
            )

    # B5: Dæklags-tjek — første lag over geonet
    if geonet and lag_liste:
        toplag_mm = lag_liste[0].get("tykkelse_mm") or 0
        min_daklag_mm = geonet["min_daklag"] * 10
        if 0 < toplag_mm < min_daklag_mm:
            advarsler.append(
                f"Øverste lag ({toplag_mm:.0f} mm) er under "
                f"'{geonet['navn']}' sit minimumsdæklag "
                f"({min_daklag_mm:.0f} mm)."
            )

    return {"advarsler": advarsler, "anbefalinger": anbefalinger}


# ---------------------------------------------------------------------------
# Hurtig-tjek — bruges til real-time UI-feedback uden fuld validering
# ---------------------------------------------------------------------------

def tjek_eu(eu: float) -> str | None:
    """Returnerer fejlbesked hvis Eu er klart ugyldig, ellers None."""
    if not isinstance(eu, (int, float)):
        return "Eu skal være et tal."
    if eu < EU_MIN:
        return f"Eu skal være mindst {EU_MIN} MPa."
    if eu > EU_MAX:
        return f"Eu må højst være {EU_MAX} MPa."
    return None


def tjek_phi(phi: float) -> str | None:
    """Returnerer advarsel hvis φ er uden for anbefalet interval, ellers None."""
    if not isinstance(phi, (int, float)):
        return "φ skal være et tal."
    if phi < PHI_MIN:
        return f"φ under {PHI_MIN}° — tykkelsen øges med φ-korrektionen."
    if phi > PHI_MAX:
        return f"φ over {PHI_MAX}° er usandsynlig for granulære materialer."
    return None
