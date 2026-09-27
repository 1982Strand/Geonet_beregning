"""Fordeling af den dimensionerede bærelagstykkelse på materialelagene.

Designdiagrammerne giver én samlet ubunden lagtykkelse. I Brugerdefineret
fordeles den på de indtastede materialelag. Fordelingen indgår ikke i
diagramopslaget; den fastlægger, hvor stor en del af tykkelsen hvert lag
udgør.

Tre fordelinger af det øverste lag:

    proportional   alle lag reduceres i samme forhold som den samlede
                   tykkelse, jf. core.afrunding.fordel_lag.
    minimum        som proportional, men det øverste lag gøres ikke tyndere
                   end minimumstykkelsen for belastningsklassen. Resten
                   fordeles proportionalt på de underliggende lag.
    fastholdt      det øverste lag fastholdes på den indtastede tykkelse,
                   dog mindst minimumstykkelsen, i alle søjler. De
                   underliggende lag optager både forøgelsen til den
                   ustabiliserede tykkelse og reduktionen for geonet. Er
                   lagene angivet i procent, er der ingen indtastet
                   tykkelse, og det øverste lag fastholdes da på sin
                   tykkelse i den ustabiliserede opbygning.

Tre regler for de underliggende lag (restlag), der bliver tynde:

    vis            lagene vises, som fordelingen giver dem.
    flet           et underliggende lag, der er tyndere end grænsen
                   restlag_graense_mm, lægges til laget ovenover — ved to
                   lag således til det øverste lag. Den samlede tykkelse er
                   uændret.
    vd             et underliggende lag gøres ikke tyndere end den mindste
                   lagtykkelse for lagtypen, jf. Vejdirektoratets håndbog,
                   Figur 6.5. Den samlede tykkelse øges derved til den
                   mindste tykkelse, hvor alle lag kan indbygges, jf.
                   byggelig_total(). Det sker i core.afrunding, så
                   resultatkort, produkttabel, søjler og rapport viser samme
                   tykkelse.

Desuden kan den samlede bærelagstykkelse sættes mindst til
minimumstykkelsen (samlet_minimum). Det sker ligeledes i
core.afrunding.anvend_paa_resultat, hvortil minimumet føres som t_min_mm
sammen med oprundingsindstillingen.

Indstillingen er en dict med felterne:

    fordeling           "proportional" | "minimum" | "fastholdt"
    samlet_minimum      True: den samlede bærelagstykkelse sættes mindst til
                        minimumstykkelsen, også i Standard-tilstanden.
    minimum_mm          {belastningsklasse: mm}. 0 betyder intet minimum.
    restlag             "vis" | "flet" | "vd"
    restlag_graense_mm  grænsen for sammenlægning ved »flet«
    vd_minimum_mm       {"Bærelag": mm, "Bundsikring": mm}
    phi_regel           "indtastet" | "laveste" | "soejle"

Tre regler for friktionsvinklen i søjlerne:

    indtastet      φᵥ for den indtastede opbygning anvendes i alle søjler.
    laveste        hver søjle regnes med den laveste af φᵥ for den
                   indtastede opbygning og φᵥ for søjlens egne lag.
    soejle         hver søjle regnes med φᵥ for sine egne lag.

Ved de to sidste afhænger φᵥ af søjlens lagfordeling, som igen afhænger af
søjlens tykkelse. Beregningen gentages derfor, til φᵥ er stabil, jf.
core.calculator.beregn(). Søjlens lag er de viste, efter oprunding til hele
trin og efter reglen for underliggende lag, jf. fordel_soejle().

Ved dimensionering efter trafikklasse anvendes minimumstykkelsen for den
højeste af de to belastningsklasser, som opslagspunktet ligger imellem, jf.
klasse_for_eo().

Modulet er frit for Streamlit.
"""

from __future__ import annotations

import math

from .afrunding import fordel_lag, rund_op
from .data import BELASTNINGSKLASSER
from .placement import PLACERING_LAGGRAENSE, PLACERING_VALG

FORDELING_PROPORTIONAL = "proportional"
FORDELING_MINIMUM = "minimum"
FORDELING_FASTHOLDT = "fastholdt"
FORDELING_VALG: tuple[str, ...] = (
    FORDELING_PROPORTIONAL,
    FORDELING_MINIMUM,
    FORDELING_FASTHOLDT,
)

PHI_INDTASTET = "indtastet"
PHI_LAVESTE = "laveste"
PHI_SOEJLE = "soejle"
PHI_VALG: tuple[str, ...] = (PHI_INDTASTET, PHI_LAVESTE, PHI_SOEJLE)

RESTLAG_VIS = "vis"
RESTLAG_FLET = "flet"
RESTLAG_VD = "vd"
RESTLAG_VALG: tuple[str, ...] = (RESTLAG_VIS, RESTLAG_FLET, RESTLAG_VD)

# Standard-tilstandens opførsel, når fluebenet for samlet minimum er
# fjernet, og opbygningen er tyndere end stabilgrusminimum.
UNDER_MIN_STABILGRUS = "stabilgrus"   # hele tykkelsen vises som stabilgrus
UNDER_MIN_LOEFT = "loeft"             # tykkelsen løftes til stabilgrusminimum
UNDER_MIN_UBUNDET = "ubundet"         # opbygningen vises som ét ubundet lag
UNDER_MIN_VALG: tuple[str, ...] = (
    UNDER_MIN_STABILGRUS, UNDER_MIN_LOEFT, UNDER_MIN_UBUNDET,
)

# Navne på lagene i Standard-tilstandens opdeling.
STANDARD_LAG_OEVERST = "Stabilgrus"
STANDARD_LAG_NEDERST = "Bundsikring"

# Minimumstykkelserne drøftet på det interne møde om dimensioneringsappen,
# 25. september 2026. Værdierne er ikke endeligt fastlagt og kan redigeres
# under Indstillinger.
STANDARD_MINIMUM_MM: dict[int, float] = {
    1: 200.0,
    2: 200.0,
    3: 200.0,
    4: 250.0,
    5: 275.0,
    6: 300.0,
}
MAKS_MINIMUM_MM = 1000.0
# Mindste tilladte værdi i minimumstabellen: VD's mindste lagtykkelse for
# stabilgrus, Figur 6.5.
MIN_MINIMUM_MM = 100.0

STANDARD_RESTLAG_GRAENSE_MM = 100.0

# Mindste lagtykkelse pr. lagtype efter Vejdirektoratets håndbog,
# Dimensionering af befæstelser og forstærkningsbelægninger, Figur 6.5:
# 100 mm for bærelagsmaterialerne SG, KB, KBT, KAS, KBA og FS; 200 mm for
# bundsikringssand og -grus BL I og BL II.
LAGTYPER: tuple[str, ...] = ("Bærelag", "Bundsikring")
STANDARD_VD_MINIMUM_MM: dict[str, float] = {
    "Bærelag": 100.0,
    "Bundsikring": 200.0,
}

STANDARD_INDSTILLING: dict = {
    "fordeling": FORDELING_MINIMUM,
    "samlet_minimum": True,
    "minimum_mm": dict(STANDARD_MINIMUM_MM),
    "restlag": RESTLAG_VIS,
    "restlag_graense_mm": STANDARD_RESTLAG_GRAENSE_MM,
    "vd_minimum_mm": dict(STANDARD_VD_MINIMUM_MM),
    "phi_regel": PHI_LAVESTE,
    "kraev_bundsikring": False,
    "netplacering": PLACERING_LAGGRAENSE,
    "standard_klassisk": False,
    "standard_opdeling": True,
    "standard_under_minimum": UNDER_MIN_STABILGRUS,
}

# Øvre grænse for søgningen i byggelig_total(), så en uopfyldelig
# kombination ikke giver en uendelig løkke.
_MAKS_TILLAEG_MM = 3000.0


def _gyldig_mm(v) -> bool:
    return (
        isinstance(v, (int, float)) and not isinstance(v, bool)
        and not math.isnan(v)
    )


def _normaliser_minimum(vaerdier) -> dict[int, float]:
    """Minimumstabellen med heltalsnøgler; ugyldige felter får standardværdien.

    JSON gemmer nøglerne som tekst, så både »4« og 4 accepteres.
    """
    ud = dict(STANDARD_MINIMUM_MM)
    if not isinstance(vaerdier, dict):
        return ud
    for noegle, mm in vaerdier.items():
        try:
            klasse = int(noegle)
        except (TypeError, ValueError):
            continue
        if klasse not in ud or not _gyldig_mm(mm):
            continue
        ud[klasse] = float(min(max(mm, MIN_MINIMUM_MM), MAKS_MINIMUM_MM))
    return ud


def _normaliser_vd(vaerdier) -> dict[str, float]:
    """Den mindste lagtykkelse pr. lagtype; ugyldige felter får standarden."""
    ud = dict(STANDARD_VD_MINIMUM_MM)
    if not isinstance(vaerdier, dict):
        return ud
    for lagtype in LAGTYPER:
        mm = vaerdier.get(lagtype)
        if _gyldig_mm(mm):
            ud[lagtype] = float(min(max(mm, 0.0), MAKS_MINIMUM_MM))
    return ud


def normaliser(indstilling: dict | None) -> dict:
    """Udfyld manglende felter og afvis ugyldige værdier."""
    ud = {
        "fordeling": STANDARD_INDSTILLING["fordeling"],
        "samlet_minimum": STANDARD_INDSTILLING["samlet_minimum"],
        "minimum_mm": dict(STANDARD_MINIMUM_MM),
        "restlag": STANDARD_INDSTILLING["restlag"],
        "restlag_graense_mm": STANDARD_RESTLAG_GRAENSE_MM,
        "vd_minimum_mm": dict(STANDARD_VD_MINIMUM_MM),
        "phi_regel": STANDARD_INDSTILLING["phi_regel"],
        "kraev_bundsikring": STANDARD_INDSTILLING["kraev_bundsikring"],
        "netplacering": STANDARD_INDSTILLING["netplacering"],
        "standard_klassisk": STANDARD_INDSTILLING["standard_klassisk"],
        "standard_opdeling": STANDARD_INDSTILLING["standard_opdeling"],
        "standard_under_minimum": STANDARD_INDSTILLING["standard_under_minimum"],
    }
    if not isinstance(indstilling, dict):
        return ud
    if indstilling.get("fordeling") in FORDELING_VALG:
        ud["fordeling"] = indstilling["fordeling"]
    if isinstance(indstilling.get("samlet_minimum"), bool):
        ud["samlet_minimum"] = indstilling["samlet_minimum"]
    ud["minimum_mm"] = _normaliser_minimum(indstilling.get("minimum_mm"))
    if indstilling.get("restlag") in RESTLAG_VALG:
        ud["restlag"] = indstilling["restlag"]
    graense = indstilling.get("restlag_graense_mm")
    if _gyldig_mm(graense):
        ud["restlag_graense_mm"] = float(min(max(graense, 0.0), MAKS_MINIMUM_MM))
    ud["vd_minimum_mm"] = _normaliser_vd(indstilling.get("vd_minimum_mm"))
    if indstilling.get("phi_regel") in PHI_VALG:
        ud["phi_regel"] = indstilling["phi_regel"]
    for felt in ("kraev_bundsikring", "standard_klassisk", "standard_opdeling"):
        if isinstance(indstilling.get(felt), bool):
            ud[felt] = indstilling[felt]
    if indstilling.get("netplacering") in PLACERING_VALG:
        ud["netplacering"] = indstilling["netplacering"]
    if indstilling.get("standard_under_minimum") in UNDER_MIN_VALG:
        ud["standard_under_minimum"] = indstilling["standard_under_minimum"]
    return ud


def lagtype_noegle(lagtype: str | None) -> str:
    """Materialets lagtype som nøgle i vd_minimum_mm: »Bundsikring« eller
    »Bærelag«. Ukendte lagtyper regnes som bærelag."""
    if str(lagtype or "").strip().lower().startswith("bunds"):
        return "Bundsikring"
    return "Bærelag"


def klasse_for_eo(eo: float | None) -> int | None:
    """Belastningsklassen, hvis minimumstykkelse gælder ved opslagspunktet eo.

    Det er den laveste klasse, hvis Eₒ er mindst eo — ved et opslagspunkt
    mellem to kurver således den højeste af de to. Et punkt over den øverste
    kurve henføres til den øverste klasse.
    """
    if eo is None:
        return None
    klasser = sorted(BELASTNINGSKLASSER.items(), key=lambda kv: kv[1]["eo"])
    for klasse, data in klasser:
        if data["eo"] >= eo - 1e-6:
            return klasse
    return klasser[-1][0]


def minimum_for_klasse(indstilling: dict | None, klasse: int | None) -> float | None:
    """Minimumstykkelsen for klassen i mm, eller None når der intet er."""
    if klasse is None:
        return None
    mm = normaliser(indstilling)["minimum_mm"].get(int(klasse))
    return mm if mm and mm > 0 else None


def min_oeverste_lag(indstilling: dict | None, klasse: int | None) -> float | None:
    """Minimumstykkelsen for det øverste lag ved fordelingen, eller None."""
    ind = normaliser(indstilling)
    if ind["fordeling"] == FORDELING_PROPORTIONAL:
        return None
    return minimum_for_klasse(ind, klasse)


def min_samlet(indstilling: dict | None, klasse: int | None) -> float | None:
    """Minimumet for den samlede bærelagstykkelse, eller None."""
    ind = normaliser(indstilling)
    if not ind["samlet_minimum"]:
        return None
    return minimum_for_klasse(ind, klasse)


def _flet_restlag(fordelt: list[dict], graense_mm: float) -> list[dict]:
    """Læg underliggende lag, der er tyndere end grænsen, til laget ovenover.

    Lagene gennemgås nedefra, så et tyndt nederste lag først lægges til
    mellemlaget, som derefter selv vurderes mod grænsen. Det øverste lag
    flyttes aldrig.
    """
    lag = [dict(l) for l in fordelt]
    for i in range(len(lag) - 1, 0, -1):
        t = lag[i]["tykkelse_mm"]
        if 0 < t < graense_mm - 1e-6:
            lag[i - 1]["tykkelse_mm"] += t
            lag[i]["tykkelse_mm"] = 0.0
    return [l for l in lag if l["tykkelse_mm"] > 0]


def fordel_opbygning(
    lag: list[dict],
    total_mm: float | None,
    trin: int,
    *,
    fordeling: str = FORDELING_PROPORTIONAL,
    min_mm: float | None = None,
    oeverst_ref_mm: float | None = None,
    restlag: str = RESTLAG_VIS,
    restlag_graense_mm: float | None = None,
) -> list[dict]:
    """Fordel total_mm på lagene efter den valgte fordeling.

    lag er en liste af {"navn": str, "andel": float} ovenfra og ned, som i
    core.afrunding.fordel_lag. Udgangspunktet er den proportionale
    fordeling.

    Ved fordelingen »minimum« løftes det øverste lag til min_mm. Ved
    »fastholdt« sættes det øverste lag til oeverst_ref_mm — det indtastede
    øverste lags tykkelse — dog mindst min_mm, uanset hvad den proportionale
    fordeling giver; de underliggende lag optager da både en forøgelse og en
    reduktion af den samlede tykkelse. Uden oeverst_ref_mm behandles
    »fastholdt« som »minimum«. Tykkelserne oprundes til trinnet. Det øverste
    lag kan ikke blive tykkere end den samlede tykkelse; resten fordeles
    proportionalt på de underliggende lag. Er der ingen rest, udgør det
    øverste lag hele opbygningen.

    Ved restlag »flet« lægges underliggende lag, der er tyndere end
    restlag_graense_mm, til laget ovenover. Reglen »vd« ændrer ikke
    fordelingen her; den samlede tykkelse er da på forhånd sat, så lagene
    kan indbygges, jf. byggelig_total().

    Summen af lagene er den samme som ved den proportionale fordeling. Lag
    uden tykkelse udelades.
    """
    prop = fordel_lag(lag, total_mm, trin)
    fordelt = prop
    if fordeling != FORDELING_PROPORTIONAL and len(prop) >= 2:
        # Samme filtrering som fordel_lag, så lagene svarer til prop.
        lag = [l for l in lag if (l.get("andel") or 0) > 0]
        total = sum(l["tykkelse_mm"] for l in prop)
        oeverst = prop[0]["tykkelse_mm"]
        mindst = rund_op(min_mm, trin) if min_mm else 0.0
        if fordeling == FORDELING_FASTHOLDT and oeverst_ref_mm:
            nyt_oeverst = max(rund_op(oeverst_ref_mm, trin), mindst)
        else:
            nyt_oeverst = max(oeverst, mindst)
        nyt_oeverst = min(nyt_oeverst, total)
        if abs(nyt_oeverst - oeverst) >= 0.5:
            rest = total - nyt_oeverst
            under = fordel_lag(lag[1:], rest, trin) if rest > 0 else []
            fordelt = [{**prop[0], "tykkelse_mm": nyt_oeverst}] + under
    fordelt = [l for l in fordelt if l["tykkelse_mm"] > 0]
    if restlag == RESTLAG_FLET and restlag_graense_mm:
        fordelt = _flet_restlag(fordelt, restlag_graense_mm)
    return fordelt


def _lag_kan_indbygges(
    fordelt: list[dict], lagtyper: dict[str, str], vd_minimum_mm: dict[str, float],
) -> bool:
    """Sandt, når hvert underliggende lag mindst har lagtypens mindste
    tykkelse. Det øverste lag er omfattet af minimumstykkelsen for klassen
    og vurderes ikke her."""
    for l in fordelt[1:]:
        lagtype = l.get("lagtype") or lagtyper.get(l["navn"])
        mindst = vd_minimum_mm.get(lagtype_noegle(lagtype), 0.0)
        if l["tykkelse_mm"] < mindst - 1e-6:
            return False
    return True


def byggelig_total(
    lag: list[dict],
    total_mm: float | None,
    trin: int,
    *,
    fordeling: str = FORDELING_PROPORTIONAL,
    min_mm: float | None = None,
    oeverst_ref_mm: float | None = None,
    vd_minimum_mm: dict[str, float] | None = None,
    kraev_alle_lag: bool = False,
) -> float | None:
    """Den mindste samlede tykkelse fra total_mm og op, hvor fordelingen
    giver underliggende lag med mindst lagtypens mindste tykkelse.

    Uden kraev_alle_lag godtages en opbygning, hvor det øverste lag udgør
    hele tykkelsen, idet der da ikke er noget underliggende lag at vurdere.
    Med kraev_alle_lag skal alle lag være til stede, så tykkelsen øges, til
    også det underliggende lag har sin mindste tykkelse.

    lag er som i fordel_opbygning(), men bærer desuden »lagtype«. Tykkelsen
    øges i hele trin. Da fordelingen er bestemt af den samlede tykkelse,
    giver en ny fordeling af resultatet de samme lag — søjlerne kan derfor
    fordele den returnerede tykkelse på ny og få lag, der kan indbygges.
    Findes ingen sådan tykkelse inden for 3.000 mm, returneres total_mm.
    """
    if total_mm is None or total_mm <= 0 or not vd_minimum_mm:
        return total_mm
    trin = int(trin) if trin else 1
    lagtyper = {l.get("navn", "Lag"): l.get("lagtype") for l in lag}
    antal_lag = sum(1 for l in lag if (l.get("andel") or 0) > 0)
    start = rund_op(total_mm, trin)
    t = start
    while t <= start + _MAKS_TILLAEG_MM:
        fordelt = fordel_opbygning(
            lag, t, trin,
            fordeling=fordeling, min_mm=min_mm, oeverst_ref_mm=oeverst_ref_mm,
        )
        alle_til_stede = len(fordelt) >= antal_lag
        if kraev_alle_lag and not alle_til_stede:
            t += trin
            continue
        if len(fordelt) < 2 or _lag_kan_indbygges(fordelt, lagtyper, vd_minimum_mm):
            return t if t > start else total_mm
        t += trin
    return total_mm


def oeverste_lag_mm(
    lag: list[dict],
    total_mm: float | None,
    trin: int,
    *,
    fordeling: str = FORDELING_PROPORTIONAL,
    min_mm: float | None = None,
) -> float | None:
    """Det øverste lags tykkelse i en opbygning på total_mm — referencen for
    fordelingen »fastholdt«, når lagene er angivet i procent og total_mm er
    den ustabiliserede tykkelse."""
    fordelt = fordel_opbygning(lag, total_mm, trin, fordeling=fordeling, min_mm=min_mm)
    return fordelt[0]["tykkelse_mm"] if fordelt else None


def fordel_soejle(
    spec: dict,
    total_mm: float | None,
    trin: int,
    *,
    t_uarm_mm: float | None = None,
) -> list[dict]:
    """Lagene i en søjle efter lagopbygningen spec.

    spec er lagopbygningen fra appen, jf. core.afrunding: {"lag",
    "fordeling", "min_mm", "oeverst_ref_mm", "restlag",
    "restlag_graense_mm"}. oeverst_ref_mm er det indtastede øverste lag ved
    fordelingen »fastholdt«. Mangler det — lagene er angivet i procent — og
    er t_uarm_mm angivet, anvendes det øverste lag i den ustabiliserede
    opbygning på t_uarm_mm; for den ustabiliserede søjle selv udelades
    t_uarm_mm. Samme funktion danner søjlerne på skærmen og i rapporten og
    lagene bag φᵥ i beregningen, så de tre stemmer overens.
    """
    if not total_mm:
        return []
    lag = spec.get("lag") or []
    fordeling = spec.get("fordeling") or FORDELING_PROPORTIONAL
    min_mm = spec.get("min_mm")
    ref = spec.get("oeverst_ref_mm") if fordeling == FORDELING_FASTHOLDT else None
    if fordeling == FORDELING_FASTHOLDT and ref is None and t_uarm_mm:
        ref = oeverste_lag_mm(lag, t_uarm_mm, trin, fordeling=fordeling, min_mm=min_mm)
    return fordel_opbygning(
        lag, total_mm, trin,
        fordeling=fordeling, min_mm=min_mm, oeverst_ref_mm=ref,
        restlag=spec.get("restlag") or RESTLAG_VIS,
        restlag_graense_mm=spec.get("restlag_graense_mm"),
    )


def standard_spec(
    indstilling: dict | None, stabilgrus_min_mm: float | None,
) -> dict | None:
    """Lagopbygningen bag Standard-tilstandens opdeling, jf. fordel_soejle().

    Stabilgruset fastholdes på stabilgrus_min_mm — minimumstykkelsen for
    klassen — og bundsikringen udgør resten. Tynde bundsikringslag
    behandles efter reglen for underliggende lag. Der regnes ikke med en
    vægtet friktionsvinkel; Standard føres med referencematerialet.

    Returnerer None, når der ikke er noget stabilgrusminimum at dele efter.
    """
    if not stabilgrus_min_mm:
        return None
    ind = normaliser(indstilling)
    return {
        "lag": [
            {"navn": STANDARD_LAG_OEVERST, "andel": 1.0, "lagtype": "Bærelag"},
            {"navn": STANDARD_LAG_NEDERST, "andel": 1.0, "lagtype": "Bundsikring"},
        ],
        "fordeling": FORDELING_FASTHOLDT,
        "min_mm": None,
        "oeverst_ref_mm": float(stabilgrus_min_mm),
        "restlag": ind["restlag"],
        "restlag_graense_mm": ind["restlag_graense_mm"],
        "vd_minimum_mm": (
            dict(ind["vd_minimum_mm"]) if ind["restlag"] == RESTLAG_VD else None
        ),
        "kraev_bundsikring": ind["kraev_bundsikring"],
        "phi_regel": PHI_INDTASTET,
    }


def vaegtet_phi(fordelt: list[dict] | None) -> float | None:
    """Tykkelsesvægtet friktionsvinkel φᵥ = Σ(tᵢ × φᵢ) / Σ(tᵢ) for lagene.

    Lagene skal bære »phi«, som fordel_opbygning() fører med fra
    materialelagene. Mangler en friktionsvinkel, returneres None.
    """
    if not fordelt:
        return None
    total = sum(l["tykkelse_mm"] for l in fordelt)
    if total <= 0:
        return None
    bidrag = 0.0
    for l in fordelt:
        phi = l.get("phi")
        if not isinstance(phi, (int, float)) or isinstance(phi, bool):
            return None
        bidrag += l["tykkelse_mm"] * float(phi)
    return bidrag / total
