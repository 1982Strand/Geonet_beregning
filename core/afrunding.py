"""Oprunding af dimensionerede lagtykkelser til indbygningstrin.

De beregnede lagtykkelser er mindstetykkelser. Ved indbygning anvendes
lagtykkelser i hele trin — typisk 50 mm — og resultatet oprundes derfor til
nærmeste hele trin. Der rundes aldrig ned.

Modulet er frit for Streamlit, så oprundingen kan anvendes af både
beregningsmotoren, rapporten og en eventuel afprøvning uden at køre appen.

Indstillingen er en dict med fire felter:

    trin_mm            oprundingstrin i mm, jf. TRIN_VALG
    reduktion_eksakt   False: reduktionen i mm og % opgøres af de oprundede
                       tykkelser, så regnestykket i resultatet går op.
                       True: reduktionen opgøres af de beregnede tykkelser.
    vis_eksakt         True: den beregnede tykkelse anføres i parentes
                       efter den oprundede.
    phi_afrunding      afrundingen af den vægtede friktionsvinkel φᵥ, før
                       korrektionen k_φ bestemmes, jf. PHI_AFRUNDING_VALG og
                       afrund_phi().

Til beregningen kan dict'en desuden bære to felter, der ikke hører til de
gemte indstillinger, men dannes pr. beregning, jf. core.lagfordeling:

    t_min_mm       den mindste samlede bærelagstykkelse for klassen. Den
                   oprundede tykkelse sættes mindst hertil, selv oprundet
                   til trinnet.
    lagopbygning   materialelagene og fordelingen, når underliggende lag
                   skal have lagtypens mindste tykkelse:
                   {"lag": [{"navn", "andel", "lagtype"}], "fordeling",
                   "min_mm", "vd_minimum_mm", "oeverst_ref_mm"}. Tykkelsen
                   øges da til den mindste, hvor lagene kan indbygges.
                   oeverst_ref_mm er det indtastede øverste lag ved
                   fordelingen »fastholdt«, eller None.

Rækkefølgen er: oprunding, minimumstykkelse, mindste lagtykkelse. Hvert
tillæg kan opgøres for sig, jf. tillaeg().
"""

from __future__ import annotations

import math

TRIN_VALG: tuple[int, ...] = (1, 10, 50, 100)
TRIN_STANDARD = 50

# Afrundingen af φᵥ: ingen, nedrunding til hel grad eller afrunding til
# nærmeste hele grad. Nedrundingen er på den sikre side, idet en lavere φᵥ
# giver en tykkere opbygning.
PHI_AFRUNDING_INGEN = "ingen"
PHI_AFRUNDING_NED = "ned"
PHI_AFRUNDING_NAERMESTE = "naermeste"
PHI_AFRUNDING_VALG: tuple[str, ...] = (
    PHI_AFRUNDING_INGEN, PHI_AFRUNDING_NED, PHI_AFRUNDING_NAERMESTE,
)

STANDARD_INDSTILLING: dict = {
    "trin_mm": TRIN_STANDARD,
    "reduktion_eksakt": False,
    "vis_eksakt": False,
    "phi_afrunding": PHI_AFRUNDING_INGEN,
}

# Tykkelsesfelter i beregn()-resultatet, der oprundes. Den beregnede værdi
# bevares under samme navn med »_eksakt« indskudt før enheden.
_T_FELTER: tuple[str, ...] = (
    "t_armeret_mm",
    "t_uarmeret_mm",
    "t_uarmeret_phi_kor_mm",
)

# Tolerance ved oprunding, så flydende-kommastøj (fx 550,0000000001) ikke
# løfter en værdi, der allerede ligger på et trin, til det næste.
_TOLERANCE = 1e-6


def normaliser(indstilling: dict | None) -> dict:
    """Udfyld manglende felter og afvis ugyldige værdier."""
    ud = dict(STANDARD_INDSTILLING)
    if isinstance(indstilling, dict):
        trin = indstilling.get("trin_mm")
        if isinstance(trin, (int, float)) and int(trin) in TRIN_VALG:
            ud["trin_mm"] = int(trin)
        for felt in ("reduktion_eksakt", "vis_eksakt"):
            if isinstance(indstilling.get(felt), bool):
                ud[felt] = indstilling[felt]
        if indstilling.get("phi_afrunding") in PHI_AFRUNDING_VALG:
            ud["phi_afrunding"] = indstilling["phi_afrunding"]
        t_min = indstilling.get("t_min_mm")
        if (
            isinstance(t_min, (int, float)) and not isinstance(t_min, bool)
            and t_min > 0
        ):
            ud["t_min_mm"] = float(t_min)
        lagopbygning = indstilling.get("lagopbygning")
        if isinstance(lagopbygning, dict) and lagopbygning.get("lag"):
            ud["lagopbygning"] = lagopbygning
    return ud


def afrund_phi(phi: float | None, metode: str | None) -> float | None:
    """φᵥ afrundet efter metode, jf. PHI_AFRUNDING_VALG.

    »ned« runder ned til hel grad, »naermeste« til nærmeste hele grad med
    halve grader rundet op. Ved »ingen« eller en ukendt metode returneres
    φᵥ uændret. None → None.
    """
    if phi is None:
        return None
    if metode == PHI_AFRUNDING_NED:
        return float(math.floor(phi + _TOLERANCE))
    if metode == PHI_AFRUNDING_NAERMESTE:
        return float(math.floor(phi + 0.5 + _TOLERANCE))
    return float(phi)


def eksakt_navn(felt: str) -> str:
    """'t_armeret_mm' → 't_armeret_eksakt_mm'."""
    if felt.endswith("_mm"):
        return felt[:-3] + "_eksakt_mm"
    return felt + "_eksakt"


def minimum_navn(felt: str) -> str:
    """'t_armeret_mm' → 't_armeret_til_minimum': flaget for, at den
    oprundede tykkelse er sat op til minimumstykkelsen."""
    if felt.endswith("_mm"):
        return felt[:-3] + "_til_minimum"
    return felt + "_til_minimum"


def rund_op(vaerdi: float | None, trin: int) -> float | None:
    """Oprund vaerdi til nærmeste hele multiplum af trin. None → None."""
    if vaerdi is None:
        return None
    trin = int(trin) if trin else 1
    if trin <= 1:
        return float(math.ceil(vaerdi - _TOLERANCE))
    return float(math.ceil(vaerdi / trin - _TOLERANCE) * trin)


def er_oprundet(afrundet: float | None, eksakt: float | None) -> bool:
    """Sandt, når oprundingen har flyttet værdien mindst 1 mm."""
    if afrundet is None or eksakt is None:
        return False
    return abs(afrundet - eksakt) >= 0.5


def anvend_paa_resultat(res: dict, indstilling: dict | None) -> dict:
    """Oprund tykkelserne i et beregn()-resultat.

    Returnerer en kopi, hvor t_armeret_mm, t_uarmeret_mm og
    t_uarmeret_phi_kor_mm er oprundet til indstillingens trin, mens de
    beregnede værdier er bevaret i t_armeret_eksakt_mm m.fl. Reduktionen i mm
    og % opgøres af de oprundede tykkelser, medmindre reduktion_eksakt er
    sat; de beregnede reduktioner bevares altid i reduktion_mm_eksakt og
    reduktion_pct_eksakt. Feltet afrunding_trin_mm angiver det anvendte trin.

    Bærer indstillingen t_min_mm, sættes de oprundede tykkelser mindst til
    denne værdi, oprundet til trinnet. En tykkelse, der er sat op, mærkes
    med flaget t_armeret_til_minimum m.fl., jf. minimum_navn(), og feltet
    t_min_mm angiver den anvendte minimumstykkelse. De beregnede værdier i
    *_eksakt_mm er fortsat diagrammets.

    Bærer indstillingen lagopbygning, øges t_uarmeret_phi_kor_mm og
    t_armeret_mm derefter til den mindste tykkelse, hvor de underliggende lag
    har lagtypens mindste tykkelse, jf. lagfordeling.byggelig_total(). Den
    ustabiliserede tykkelse behandles først, idet dens øverste lag er
    referencen ved fordelingen »fastholdt«, når lagene er angivet i procent.

    Resultater med fejl returneres uændret.
    """
    if not isinstance(res, dict) or res.get("fejl") is not None:
        return res
    ind = normaliser(indstilling)
    trin = ind["trin_mm"]
    t_min = rund_op(ind["t_min_mm"], trin) if "t_min_mm" in ind else None
    ud = dict(res)
    for felt in _T_FELTER:
        if felt not in res:
            continue
        v = res.get(felt)
        ud[eksakt_navn(felt)] = v
        oprundet = rund_op(v, trin)
        if t_min is not None and oprundet is not None and oprundet < t_min:
            oprundet = t_min
            ud[minimum_navn(felt)] = True
        ud[felt] = oprundet
    ud["t_min_mm"] = t_min
    if "lagopbygning" in ind:
        _anvend_lagminimum(ud, ind["lagopbygning"], trin)

    ud["reduktion_mm_eksakt"] = res.get("reduktion_mm")
    ud["reduktion_pct_eksakt"] = res.get("reduktion_pct")
    if not ind["reduktion_eksakt"]:
        # Samme reference som beregn(): den φᵥ-korrigerede ustabiliserede
        # tykkelse, når den findes.
        t_ref = ud.get("t_uarmeret_phi_kor_mm")
        if t_ref is None:
            t_ref = ud.get("t_uarmeret_mm")
        t_arm = ud.get("t_armeret_mm")
        if t_ref is not None and t_arm is not None:
            ud["reduktion_mm"] = t_ref - t_arm
            ud["reduktion_pct"] = (
                round((t_ref - t_arm) / t_ref, 4) if t_ref > 0 else None
            )
    ud["afrunding_trin_mm"] = trin
    return ud


def _anvend_lagminimum(ud: dict, lagopbygning: dict, trin: int) -> None:
    """Øg de oprundede tykkelser i ud, så de underliggende lag kan indbygges.

    Modulet importeres her, idet core.lagfordeling selv bygger på dette
    modul.
    """
    from .lagfordeling import (
        FORDELING_FASTHOLDT, byggelig_total, fordel_opbygning, oeverste_lag_mm,
    )
    lag = lagopbygning.get("lag") or []
    fordeling = lagopbygning.get("fordeling")
    min_mm = lagopbygning.get("min_mm")
    vd = lagopbygning.get("vd_minimum_mm")
    if not vd:
        # Lagopbygningen bæres alene for friktionsvinklens skyld.
        return
    kw = {
        "fordeling": fordeling, "min_mm": min_mm, "vd_minimum_mm": vd,
        "kraev_alle_lag": bool(lagopbygning.get("kraev_bundsikring")),
    }

    # Ved »fastholdt« er referencen det indtastede øverste lag, som gælder
    # alle søjler. Er lagene angivet i procent, findes den ikke, og det
    # øverste lag i den ustabiliserede opbygning anvendes i stedet.
    ref = lagopbygning.get("oeverst_ref_mm") if fordeling == FORDELING_FASTHOLDT else None
    t_uarm = ud.get("t_uarmeret_phi_kor_mm")
    if t_uarm is not None:
        ny = byggelig_total(lag, t_uarm, trin, **kw, oeverst_ref_mm=ref)
        if ny is not None and ny > t_uarm:
            ud["t_uarmeret_phi_kor_mm"] = ny
            ud[lagminimum_navn("t_uarmeret_phi_kor_mm")] = True
        if fordeling == FORDELING_FASTHOLDT and ref is None:
            ref = oeverste_lag_mm(
                lag, ud["t_uarmeret_phi_kor_mm"], trin,
                fordeling=fordeling, min_mm=min_mm,
            )
    t_arm = ud.get("t_armeret_mm")
    if t_arm is not None:
        ny = byggelig_total(lag, t_arm, trin, **kw, oeverst_ref_mm=ref)
        if ny is not None and ny > t_arm:
            ud["t_armeret_mm"] = ny
            ud[lagminimum_navn("t_armeret_mm")] = True
            # Lagene før og efter tillægget, så mellemregningen kan vise,
            # hvilket lag der er øget, jf. app._lagtillaeg_tekst().
            def _lag(t: float) -> list[dict]:
                return [
                    {"navn": l["navn"], "tykkelse_mm": l["tykkelse_mm"]}
                    for l in fordel_opbygning(
                        lag, t, trin, fordeling=fordeling, min_mm=min_mm,
                        oeverst_ref_mm=ref,
                    )
                ]
            ud["t_armeret_lagtillaeg_lag"] = {"foer": _lag(t_arm), "efter": _lag(ny)}


def lagminimum_navn(felt: str) -> str:
    """'t_armeret_mm' → 't_armeret_til_lagminimum': flaget for, at
    tykkelsen er øget, så de underliggende lag kan indbygges."""
    if felt.endswith("_mm"):
        return felt[:-3] + "_til_lagminimum"
    return felt + "_til_lagminimum"


def tillaeg(
    angivet: float | None,
    eksakt: float | None,
    trin: int,
    t_min: float | None = None,
) -> tuple[float, float, float]:
    """(oprunding_mm, minimum_mm, lag_mm) mellem den beregnede og den angivne
    tykkelse.

    Oprundingen er forskellen op til nærmeste hele trin. Minimumstillægget
    er det, der derudover er lagt til for at nå minimumstykkelsen t_min
    (resultatets t_min_mm). Lagtillægget er resten: det, der er lagt til,
    for at de underliggende lag kan indbygges, jf. anvend_paa_resultat().
    Alle tre er 0, når der intet er lagt til.
    """
    if angivet is None or eksakt is None:
        return 0.0, 0.0, 0.0
    oprundet = rund_op(eksakt, trin)
    oprunding = oprundet - eksakt if er_oprundet(oprundet, eksakt) else 0.0
    efter_minimum = max(oprundet, t_min) if t_min else oprundet
    minimum = efter_minimum - oprundet if efter_minimum - oprundet >= 0.5 else 0.0
    lag = angivet - efter_minimum if angivet - efter_minimum >= 0.5 else 0.0
    return oprunding, minimum, lag


def reduktion_for(
    t_ref: float | None,
    t_arm: float | None,
    t_ref_eksakt: float | None = None,
    t_arm_eksakt: float | None = None,
    indstilling: dict | None = None,
) -> tuple[float | None, float | None]:
    """(reduktion_mm, reduktion_pct) mellem en reference og en armeret tykkelse.

    Med reduktion_eksakt sat opgøres reduktionen af de beregnede tykkelser,
    når de er angivet; ellers af de (oprundede) tykkelser t_ref og t_arm.
    """
    ind = normaliser(indstilling)
    if ind["reduktion_eksakt"] and t_ref_eksakt is not None and t_arm_eksakt is not None:
        t_ref, t_arm = t_ref_eksakt, t_arm_eksakt
    if t_ref is None or t_arm is None:
        return None, None
    red = t_ref - t_arm
    return red, (red / t_ref if t_ref > 0 else None)


def fordel_lag(
    lag: list[dict], total_mm: float | None, trin: int,
) -> list[dict]:
    """Fordel total_mm på lagene i hele trin efter lagenes indbyrdes andele.

    lag er en liste af {"navn": str, "andel": float}, hvor andelen er lagets
    vægt — en tykkelse i mm eller en procent. Summen af de returnerede
    tykkelser er total_mm, forudsat total_mm selv er et multiplum af trin;
    ellers oprundes den. Hvert lag tildeles mindst ét trin, når der er trin
    nok til det, så et tyndt lag ikke bortfalder. Resten fordeles efter
    største rest.
    """
    lag = [l for l in lag if (l.get("andel") or 0) > 0]
    if not lag or not total_mm or total_mm <= 0:
        return []
    trin = int(trin) if trin else 1
    total = rund_op(total_mm, trin)
    n = int(round(total / trin))
    sum_andel = sum(float(l["andel"]) for l in lag)
    andele = [float(l["andel"]) / sum_andel * n for l in lag]
    basis = [math.floor(a + _TOLERANCE) for a in andele]
    if n >= len(lag):
        basis = [max(b, 1) for b in basis]
    rest = n - sum(basis)
    # Rækkefølge efter faldende rest; ved lige rest tælles det tykkeste lag
    # først, så resten samles i bærelaget.
    orden = sorted(
        range(len(lag)),
        key=lambda i: (andele[i] - math.floor(andele[i] + _TOLERANCE), andele[i]),
        reverse=True,
    )
    i = 0
    while rest > 0 and orden:
        basis[orden[i % len(orden)]] += 1
        rest -= 1
        i += 1
    i = 0
    while rest < 0 and orden:
        j = orden[-1 - (i % len(orden))]
        if basis[j] > 1 or n < len(lag):
            basis[j] -= 1
            rest += 1
        i += 1
        if i > 10 * len(orden):
            break
    # Øvrige felter på lagene — fx lagtype og friktionsvinkel — føres med,
    # så fordelingen kan vurderes lag for lag, jf. core.lagfordeling.
    return [
        {
            **{k: v for k, v in l.items() if k != "andel"},
            "navn": l.get("navn", "Lag"),
            "tykkelse_mm": float(b * trin),
        }
        for l, b in zip(lag, basis)
    ]


def trin_tekst(trin: int) -> str:
    """'50 mm' — trinnet som tekst til noter og rapport."""
    return f"{int(trin)} mm"
