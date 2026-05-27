"""
Geonet Dimensioneringsværktøj — Streamlit entrypoint.

Start med: streamlit run app.py
"""

# ---------------------------------------------------------------------------
# set_page_config SKAL stå som allerførste Streamlit-kald
# ---------------------------------------------------------------------------
import streamlit as st

st.set_page_config(
    page_title="Geonet Dimensionering",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Imports — efter set_page_config
# ---------------------------------------------------------------------------
from core.data import (
    BELASTNINGSKLASSER,
    GEONET_NAVNE,
    MATERIAL_NAVNE,
    EU_MIN, EU_MAX,
    find_geonet,
    find_materiale,
    cv_til_eu,
    eo_til_klasse,
)
from core.calculator import (
    beregn,
    beregn_alle_produkter,
    grupper_produkter,
)
from core.validators import valider_input

# ---------------------------------------------------------------------------
# Farvepalette
# ---------------------------------------------------------------------------
GRØN   = "#2E7D32"
GUL    = "#F9A825"
RØD    = "#C62828"
GRÅ    = "#9E9E9E"
LYS_GR = "#E8F5E9"

# ---------------------------------------------------------------------------
# Serie-sortering til standard-oversigten
# ---------------------------------------------------------------------------
SERIE_ORDER = {"Tensar": 0, "GS-GRID": 1, "E'GRID": 2, "Manuel": 3}

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown(f"""
<style>
  .block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; }}

  .res-kort {{
    background: {LYS_GR};
    border-left: 5px solid {GRØN};
    border-radius: 6px;
    padding: 1rem 1.25rem 0.75rem;
    margin-bottom: 0.5rem;
  }}
  .res-tal   {{ font-size: 2.2rem; font-weight: 700; color: {GRØN}; line-height: 1.1; }}
  .res-label {{ font-size: 0.78rem; color: #555; text-transform: uppercase;
                letter-spacing: 0.06em; margin-bottom: 0.15rem; }}
  .uarm-tal  {{ font-size: 1.5rem; font-weight: 600; color: {GRÅ}; }}

  .boks-fejl  {{ background:#FFEBEE; border-left:4px solid {RØD};
                 border-radius:4px; padding:0.6rem 1rem;
                 margin:0.25rem 0; font-size:0.88rem; }}
  .boks-adv   {{ background:#FFF8E1; border-left:4px solid {GUL};
                 border-radius:4px; padding:0.6rem 1rem;
                 margin:0.25rem 0; font-size:0.88rem; }}
  .boks-tip   {{ background:#E3F2FD; border-left:4px solid #1565C0;
                 border-radius:4px; padding:0.6rem 1rem;
                 margin:0.25rem 0; font-size:0.88rem; }}

  .uarm-banner {{
    background:#F5F5F5; border-left:5px solid {GRÅ};
    border-radius:6px; padding:0.75rem 1.25rem; margin-bottom:1rem;
  }}
  .uarm-banner-label {{ font-size:0.78rem; color:#555; text-transform:uppercase;
                        letter-spacing:0.06em; }}
  .uarm-banner-tal   {{ font-size:1.8rem; font-weight:700; color:{GRÅ};
                        line-height:1.1; }}

  .gruppe-kort {{
    background:{LYS_GR}; border-left:5px solid {GRØN};
    border-radius:6px; padding:0.75rem 1rem; margin:0.4rem 0 0.6rem 0;
  }}
  .gruppe-kort-rest {{
    background:#FAFAFA; border-left:4px solid {GRÅ};
    border-radius:6px; padding:0.6rem 0.9rem; margin:0.3rem 0;
  }}
  .gruppe-tal {{ font-size:1.6rem; font-weight:700; color:{GRØN}; line-height:1.1; }}
  .gruppe-tal-rest {{ font-size:1.15rem; font-weight:600; color:#444; line-height:1.1; }}
  .gruppe-red {{ font-size:0.9rem; color:#555; margin-left:0.5rem; }}
  .gruppe-red-linje {{ font-size:0.95rem; font-weight:600; color:{GRØN};
                       margin-top:0.05rem; margin-bottom:0.1rem; }}
  .gruppe-serie {{ font-size:0.88rem; margin-top:0.35rem; }}
  .gruppe-serie b {{ color:#333; }}

  /* Net-korrektionslinjer i gruppe-kort */
  .net-kor-spar {{
    font-size:0.82rem; font-weight:500; color:#1565C0;
    margin:0.1rem 0 0.05rem;
  }}
  .net-kor-pen {{
    font-size:0.82rem; font-weight:500; color:#BF360C;
    margin:0.1rem 0 0.05rem;
  }}
  .net-kor-ref {{
    font-size:0.80rem; color:{GRÅ}; font-style:italic;
    margin:0.1rem 0 0.05rem;
  }}
  .bedste-label {{
    font-size:0.7rem; color:{GRØN}; text-transform:uppercase;
    letter-spacing:0.08em; font-weight:600; margin:0.1rem 0 0.1rem 0;
  }}
  .kol-titel {{
    font-size:0.95rem; font-weight:700; color:#333;
    border-bottom:2px solid {GRØN}; padding-bottom:0.25rem;
    margin-bottom:0.4rem;
  }}

  hr {{ margin: 0.75rem 0; }}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Hjælpefunktioner til bokse
# ---------------------------------------------------------------------------

def _boks(css_klasse: str, ikon: str, tekst: str):
    st.markdown(
        f'<div class="{css_klasse}">{ikon} {tekst}</div>',
        unsafe_allow_html=True,
    )

def vis_fejl(tekst: str):        _boks("boks-fejl", "⛔", tekst)
def vis_advarsel(tekst: str):    _boks("boks-adv",  "⚠️", tekst)
def vis_anbefaling(tekst: str):  _boks("boks-tip",  "💡", tekst)

# ---------------------------------------------------------------------------
# Belastningsklasse-ikoner
# ---------------------------------------------------------------------------
KLASSE_IKON = {1: "🚲", 2: "🚜", 3: "🚗", 4: "🚛", 5: "🏗️", 6: "✈️"}


# ===========================================================================
# Fælles input-widgets (genbruges på tværs af tilstande)
# ===========================================================================

def input_underbund(key_prefix: str) -> float:
    """Render A. Underbund (Eu eller Cv → Eu). Returnerer Eu i MPa."""
    st.subheader("A. Underbund")

    eu_mode = st.radio(
        "Input-form",
        ["Eu — E-modul (MPa)", "Cv — vingestyrke (kN/m²)"],
        horizontal=True,
        key=f"{key_prefix}_eu_mode",
        label_visibility="collapsed",
    )

    if eu_mode.startswith("Eu"):
        eu = float(st.slider(
            "Eu (MPa)", min_value=int(EU_MIN), max_value=int(EU_MAX),
            value=10, step=1, key=f"{key_prefix}_eu_slider",
            help="Underbundens E-modul. Lavere Eu = blødere bund = tykkere bærelag.",
        ))
        st.caption(f"Valgt **Eu = {eu:.0f} MPa**")
        return eu

    cv = st.slider(
        "Cv (kN/m²)", min_value=0, max_value=180,
        value=60, step=5, key=f"{key_prefix}_cv_slider",
        help="Ukorrigeret vingerstyrke fra feltmåling (tabel 7.4).",
    )
    eu_opslag = cv_til_eu(float(cv))
    if eu_opslag is None:
        st.error("Cv er uden for tabelområdet (0–180 kN/m²).")
        return 10.0
    st.caption(f"Cv = {cv} kN/m²  →  **Eu = {eu_opslag:.0f} MPa**")
    return eu_opslag


def input_belastning(key_prefix: str) -> tuple[int, dict, float]:
    """Render B. Belastning som 6 klasse-knapper. Returnerer (klasse, info, eo)."""
    st.subheader("B. Belastning")

    state_key = f"{key_prefix}_valgt_klasse"
    if state_key not in st.session_state:
        st.session_state[state_key] = 4

    kl_cols = st.columns(6)
    for kl_nr, kl_data in BELASTNINGSKLASSER.items():
        with kl_cols[kl_nr - 1]:
            aktiv = st.session_state[state_key] == kl_nr
            if st.button(
                f"{KLASSE_IKON[kl_nr]}\n**{kl_nr}**",
                key=f"{key_prefix}_kl_{kl_nr}",
                type="primary" if aktiv else "secondary",
                use_container_width=True,
                help=f"Klasse {kl_nr}: {kl_data['anvendelse']}",
            ):
                st.session_state[state_key] = kl_nr
                st.rerun()

    valgt = st.session_state[state_key]
    info  = BELASTNINGSKLASSER[valgt]
    eo    = float(info["eo"])
    st.caption(
        f"**Klasse {valgt}** · {info['belastning']} · "
        f"Eo = {eo:.0f} MPa · _{info['anvendelse']}_"
    )
    return valgt, info, eo


# ===========================================================================
# STANDARD-TILSTAND — produktoversigt
# ===========================================================================

def _sort_produkter(produkter: list[dict]) -> list[dict]:
    """Sortér produkter inden for en gruppe: serie først, derefter navn."""
    return sorted(
        produkter,
        key=lambda p: (SERIE_ORDER.get(p["serie"], 99), p["navn"]),
    )


def _filter_klasse_anbefalede(grupper: list[dict]) -> list[dict]:
    """
    Returnér kun gyldige grupper (har_fejl=False) hvor klasse-anbefalede
    produkter er beholdt. Manuel-produktet og produkter uden for valgt
    klasse fjernes helt. Grupper der ender tomme droppes.
    """
    resultat: list[dict] = []
    for g in grupper:
        if g["har_fejl"]:
            continue
        beholdt = [
            p for p in g["produkter"]
            if p["klasse_ok"] and p["navn"] != "Anden armering (manuel)"
        ]
        if beholdt:
            resultat.append({**g, "produkter": beholdt})
    return resultat


def _render_gruppe_kort(gruppe: dict, primaer: bool, phi: float = 35.0) -> None:
    """
    Render én tykkelses-gruppe som kort.
    primaer=True ⇒ fremhævet grønt kort (bedste). False ⇒ dæmpet grå variant.
    """
    t_vis   = gruppe["t_armeret_mm"]
    red_pct = gruppe["reduktion_pct"]

    # Hent t_uarmeret fra første produkt (alle i gruppen har samme uarmerede tykkelse)
    t_uarm_prod = (
        gruppe["produkter"][0].get("t_uarmeret_mm")
        if gruppe.get("produkter") else None
    )

    # ↓ mm-reduktionslinje
    if t_uarm_prod is not None and red_pct is not None:
        red_mm = round(t_uarm_prod - t_vis)
        red_pct_str = f"{red_pct:.0%}"
        red_linje = (
            f'<div class="gruppe-red-linje">↓ {red_mm} mm ({red_pct_str})</div>'
        )
    else:
        red_linje = ""

    # φ-korrektionslinje — vises kun hvis phi ≠ 35°
    phi_kor_html = ""
    t_basis = gruppe.get("t_basis_arm_mm")
    if t_basis and t_basis > 0 and abs(phi - 35.0) > 0.05:
        phi_kor = -0.02 * (phi - 35.0)
        phi_kor_mm = round(t_basis * phi_kor)
        abs_mm = abs(phi_kor_mm)
        pct = abs(round(phi_kor * 100))
        phi_str = f"{phi:.1f}".replace(".", ",")
        if phi_kor < 0:
            phi_kor_html = (
                f'<div class="net-kor-spar">'
                f'φ-kor: \u2212{abs_mm} mm (\u2212{pct}\u00a0%) · φ = {phi_str}°'
                f'</div>'
            )
        else:
            phi_kor_html = (
                f'<div class="net-kor-pen">'
                f'φ-kor: +{abs_mm} mm (+{pct}\u00a0%) · φ = {phi_str}°'
                f'</div>'
            )

    # ↕ net-korrektionslinje — viser delta ift. referenceprodukt (kor=0)
    # t_basis er fælles for alle produkter i gruppen (samme eu/eo/lag_mode)
    net_kor_html = ""
    t_basis = gruppe.get("t_basis_arm_mm")
    if t_basis and t_basis > 0 and gruppe.get("produkter"):
        korrektioner = sorted({p["korrektion"] for p in gruppe["produkter"]})
        kor_min = korrektioner[0]
        kor_max = korrektioner[-1]
        delta_min = round(t_basis * kor_min)  # mm; negativ = sparer, positiv = koster mere
        delta_max = round(t_basis * kor_max)

        if abs(kor_min) < 0.005 and abs(kor_max) < 0.005:
            # Referenceprodukt(er)
            net_kor_html = '<div class="net-kor-ref">referenceprodukt (0 % korrektion)</div>'
        elif abs(kor_min - kor_max) < 0.005:
            # Alle produkter i gruppen har samme korrektion
            delta = delta_min
            pct = int(round(abs(kor_min) * 100))
            abs_delta = abs(delta)
            if kor_min < 0:
                net_kor_html = (
                    f'<div class="net-kor-spar">'
                    f'net-kor: −{abs_delta} mm (−{pct} %) ift. reference'
                    f'</div>'
                )
            else:
                net_kor_html = (
                    f'<div class="net-kor-pen">'
                    f'net-kor: +{abs_delta} mm (+{pct} %) ift. reference'
                    f'</div>'
                )
        else:
            # Blandet gruppe — vis interval
            d_lo, d_hi = delta_min, delta_max
            if d_hi <= 0:
                # Alt er besparelser (kor < 0)
                net_kor_html = (
                    f'<div class="net-kor-spar">'
                    f'net-kor: {d_lo:+d} til {d_hi:+d} mm ift. reference'
                    f'</div>'
                )
            elif d_lo >= 0:
                # Alt er tillæg (kor > 0)
                net_kor_html = (
                    f'<div class="net-kor-pen">'
                    f'net-kor: +{d_lo} til +{d_hi} mm ift. reference'
                    f'</div>'
                )
            else:
                # Blandet fortegn — neutral
                net_kor_html = (
                    f'<div class="net-kor-ref">'
                    f'net-kor: {d_lo:+d} til {d_hi:+d} mm ift. reference'
                    f'</div>'
                )

    pr_serie: dict[str, list[dict]] = {}
    for p in _sort_produkter(gruppe["produkter"]):
        pr_serie.setdefault(p["serie"], []).append(p)

    serie_linjer: list[str] = []
    for serie in sorted(pr_serie.keys(), key=lambda s: SERIE_ORDER.get(s, 99)):
        navne = [p["navn"].replace(f"{serie} ", "", 1) for p in pr_serie[serie]]
        serie_linjer.append(
            f'<div class="gruppe-serie"><b>{serie}:</b> {", ".join(navne)}</div>'
        )

    kort_css = "gruppe-kort" if primaer else "gruppe-kort-rest"
    tal_css  = "gruppe-tal"  if primaer else "gruppe-tal-rest"

    st.markdown(
        f'<div class="{kort_css}">'
        f'<span class="{tal_css}">{t_vis:.0f} mm</span>'
        f'{red_linje}'
        f'{phi_kor_html}'
        f'{net_kor_html}'
        f'{"".join(serie_linjer)}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _resultat_til_gruppe(
    res: dict, geonet: dict, valgt_klasse: int
) -> dict | None:
    """
    Pak et enkelt beregn()-resultat ind i samme dict-struktur som
    grupper_produkter()-output, så det kan vises med _render_gruppe_kort.

    Returnerer None hvis beregningen fejlede.
    """
    if res.get("fejl") or res.get("t_armeret_mm") is None:
        return None

    t_eks = res["t_armeret_mm"]
    t_uarm = res["t_uarmeret_mm"]
    red_eks = (t_uarm - t_eks) / t_uarm if t_uarm else 0

    produkt = {
        "navn":           geonet["navn"],
        "serie":          geonet["serie"],
        "korrektion":     geonet["korrektion"],
        "t_armeret_mm":   t_eks,
        "t_uarmeret_mm":  t_uarm,
        "t_basis_arm_mm": res.get("t_basis_arm_mm"),
        "reduktion_mm":   t_uarm - t_eks,
        "reduktion_pct":  red_eks,
        "klasse_ok":      valgt_klasse in geonet["klasser"],
        "klasser":        geonet["klasser"],
        "min_daklag":     geonet["min_daklag"],
        "max_korn":       geonet["max_korn"],
        "fejl":           None,
    }
    return {
        "t_armeret_mm":         round(t_eks, 0),
        "t_armeret_eksakt_mm":  round(t_eks, 0),
        "reduktion_pct":        round(red_eks, 4),
        "reduktion_pct_eksakt": round(red_eks, 4),
        "t_basis_arm_mm":       res.get("t_basis_arm_mm"),
        "produkter":            [produkt],
        "har_fejl":             False,
        "fejl_besked":          None,
    }


def _render_lag_kolonne(
    titel: str,
    grupper: list[dict],
    valgt_klasse: int,
    lag_mode: str,
    tom_besked: str | None = None,
    phi: float = 35.0,
) -> None:
    """
    Render én kolonne (1-lag eller 2-lag): bedste gruppe øverst,
    øvrige skjult i en expander nedenunder.

    tom_besked: tilpasset besked når grupper er tomme (overstyrer default).
    """
    st.markdown(f'<div class="kol-titel">{titel}</div>', unsafe_allow_html=True)

    if not grupper:
        if tom_besked is not None:
            st.info(tom_besked)
        elif lag_mode == "2_lag":
            st.info(
                f"Designdiagrammet definerer ikke 2-lag-værdier for "
                f"kombinationen af det valgte Eu og klasse {valgt_klasse}. "
                f"\n\n"
                f"2 lag geonet anvendes primært ved **svag underbund** "
                f"(lave Eu-værdier) eller **høj belastning**, hvor 1 lag "
                f"ikke giver tilstrækkelig reduktion. Når underbunden er "
                f"tilstrækkelig stiv — eller belastningen relativt lav — "
                f"er 1 lag geonet typisk tilstrækkeligt, og designmanualen "
                f"angiver derfor ingen 2-lag-værdier."
            )
        else:
            st.info(
                f"Ingen produkter anbefalet til klasse {valgt_klasse} "
                f"giver et gyldigt 1-lag-resultat for denne kombination. "
                f"Prøv en anden belastningsklasse eller justér Eu."
            )
        return

    grupper_sorteret = sorted(grupper, key=lambda g: g["t_armeret_eksakt_mm"])
    bedste = grupper_sorteret[0]
    rest   = grupper_sorteret[1:]

    st.markdown('<div class="bedste-label">Armeret bærelagstykkelse</div>',
                unsafe_allow_html=True)
    _render_gruppe_kort(bedste, primaer=True, phi=phi)

    if rest:
        label = (
            f"Vis {len(rest)} flere mulighed"
            f"{'er' if len(rest) > 1 else ''}"
        )
        with st.expander(label, expanded=False):
            for g in rest:
                _render_gruppe_kort(g, primaer=False, phi=phi)


def _navne_kort(gruppe: dict) -> str:
    """Format produktnavne i en bedste-gruppe: '<navn>' eller '<navn> m.fl.'"""
    navne = [p["navn"] for p in gruppe["produkter"]]
    if len(navne) == 1:
        return navne[0]
    return f"{navne[0]} m.fl."


def _samme_produkter(g1: dict | None, g2: dict | None) -> bool:
    """True hvis to grupper indeholder præcis det samme sæt produktnavne."""
    if g1 is None or g2 is None:
        return False
    n1 = {p["navn"] for p in g1["produkter"]}
    n2 = {p["navn"] for p in g2["produkter"]}
    return n1 == n2


def _krav_for_gruppe(gruppe: dict) -> tuple[str, str, str]:
    """
    Returner (navne, min_dæklag_str, max_korn_str) for visning af
    udførelseskrav for produkterne i en bedste-gruppe.

    Hvis alle produkter har samme værdi vises kun det ene tal.
    Hvis de varierer vises et interval med en lille forklaring.
    """
    produkter = gruppe["produkter"]
    navne = ", ".join(p["navn"] for p in produkter)

    # min_daklag er i cm i GEONET_DB → konvertér til mm
    dk_unik = sorted({p["min_daklag"] * 10 for p in produkter})
    if len(dk_unik) == 1:
        dk_str = f"{dk_unik[0]} mm"
    else:
        dk_str = f"{dk_unik[0]}–{dk_unik[-1]} mm (varierer pr. produkt)"

    korn_alle = [p["max_korn"] for p in produkter]
    korn_unik = sorted({k for k in korn_alle if k is not None})
    har_none = any(k is None for k in korn_alle)

    if not korn_unik:
        korn_str = "ikke specificeret (kontakt leverandør)"
    elif len(korn_unik) == 1 and not har_none:
        korn_str = f"{korn_unik[0]} mm"
    else:
        rng = (
            f"{korn_unik[0]}–{korn_unik[-1]}"
            if len(korn_unik) > 1 else f"{korn_unik[0]}"
        )
        if har_none:
            korn_str = f"{rng} mm (visse produkter ikke specificeret)"
        else:
            korn_str = f"{rng} mm (varierer pr. produkt)"

    return navne, dk_str, korn_str


def _render_oversigt_expanders(
    eu: float,
    eo: float,
    valgt_klasse: int,
    bedste_1: dict | None,
    bedste_2: dict | None,
    *,
    phi: float = 35.0,
    geonet: dict | None = None,
    geonet_navn: str | None = None,
    materialer: list[dict] | None = None,
) -> None:
    """De 3 informations-expandere under resultaterne.

    Bruges af både Standard (phi=35, geonet=None, materialer=None)
    og Brugerdefineret (egne phi/geonet/materialer-værdier).

    bedste_1 / bedste_2: bedste (mindste t_armeret) gruppe i hver lag-mode,
    eller None hvis ingen er gyldige. I "Vælg specifikt produkt"-mode er
    bedste-gruppen den enkelte produkts resultat pakket via
    _resultat_til_gruppe().
    """
    materialer = materialer or []

    # --- Advarsler -------------------------------------------------------
    # Validator-kørslen bruger den valgte phi/geonet/materialer-kontekst.
    # I "alle produkter"-mode er geonet=None, så produktspecifikke checks
    # springes over. Validator-anbefalinger (R1/R2) ignoreres altid — de
    # erstattes længere nede af tilpassede anbefalinger baseret på det
    # bedst reducerende net (gælder også specifikt produkt, da begge
    # lag-modes vises samtidig i den nye UI).
    advarsler_unik: list[str] = []
    seen_a: set[str] = set()
    for lm in ("1_lag", "2_lag"):
        val = valider_input(
            eu=eu, eo=eo, phi=phi, lag_mode=lm,
            geonet=geonet, materialer=materialer,
        )
        for a in val.get("advarsler", []):
            if a not in seen_a:
                seen_a.add(a)
                advarsler_unik.append(a)

    # --- Tilpassede anbefalinger baseret på bedste produkt --------------
    anbefalinger: list[str] = []

    # Anbefalinger bruger den afrundede (praktisk indbyggelige) tykkelse —
    # det er den værdi der konkret skal bygges, og som matcher kortenes
    # headline-tal.
    if bedste_1 is not None and bedste_1["t_armeret_mm"] > 500:
        msg = (
            f"Bedste opnåelige bærelagstykkelse med 1 lag geonet er "
            f"<b>{bedste_1['t_armeret_mm']:.0f} mm</b> "
            f"({_navne_kort(bedste_1)}). "
            f"Ved opbygninger over 500 mm kan der med fordel anvendes "
            f"2 lag net for yderligere reduktion"
        )
        if bedste_2 is not None:
            msg += (
                f" — her: <b>{bedste_2['t_armeret_mm']:.0f} mm</b> "
                f"({_navne_kort(bedste_2)})."
            )
        else:
            msg += " (ikke gyldigt for denne kombination)."
        anbefalinger.append(msg)

    if bedste_2 is not None and bedste_2["t_armeret_mm"] < 400:
        msg = (
            f"Bedste opnåelige tykkelse med 2 lag geonet er kun "
            f"<b>{bedste_2['t_armeret_mm']:.0f} mm</b>. "
            f"1 lag geonet er sandsynligvis tilstrækkeligt for denne belastning"
        )
        if bedste_1 is not None:
            msg += f" (1 lag giver <b>{bedste_1['t_armeret_mm']:.0f} mm</b>)."
        else:
            msg += "."
        anbefalinger.append(msg)

    antal = len(advarsler_unik) + len(anbefalinger)
    titel_adv = (
        f"⚠️ Advarsler og anbefalinger ({antal})"
        if antal else "⚠️ Advarsler og anbefalinger"
    )
    with st.expander(titel_adv, expanded=bool(advarsler_unik or anbefalinger)):
        if antal == 0:
            st.caption(
                "Ingen generelle advarsler for den valgte Eu og belastning."
            )
        for a in advarsler_unik:
            vis_advarsel(a)
        for r in anbefalinger:
            vis_anbefaling(r)

    # --- Udførelseskrav ---------------------------------------------------
    with st.expander("📋 Udførelseskrav"):
        st.markdown("**Generelle krav ved udførelse med geonet:**")
        st.markdown("""
- Underbund jævnes og planeres — ingen skarpe fremspring eller huller
- Komprimering i lag på maksimalt 200–300 mm
- Direkte kørsel på udlagt geonet er **ikke tilladt**
- Overlap ved skød: minimum **300 mm** (eller leverandørens anvisning)
- Geonettet udlægges stramt uden folder eller bølger
        """)

        if geonet is not None:
            # Specifikt produkt: vis konkrete værdier
            navn_vis = geonet_navn or geonet["navn"]
            min_dk_mm = geonet["min_daklag"] * 10
            if geonet["max_korn"] is not None:
                korn_str = f"**{geonet['max_korn']} mm**"
            else:
                korn_str = "**ikke specificeret** — kontakt leverandør"
            st.markdown(
                f"**Krav for {navn_vis}:**\n"
                f"- Minimum dæklag over geonet: **{min_dk_mm} mm**\n"
                f"- Max kornstørrelse i kontakt med geonet: {korn_str}"
            )
        else:
            # Oversigt: produkt-specifikke krav for bedste 1-lag og 2-lag.
            # Hvis samme sæt produkter er bedste i begge lag-modes,
            # vises kravene kun én gang.
            def _vis_krav_blok(overskrift: str, gruppe: dict) -> None:
                navne, dk_str, korn_str = _krav_for_gruppe(gruppe)
                st.markdown(
                    f"**{overskrift}** ({navne})\n"
                    f"- Minimum dæklag over geonet: **{dk_str}**\n"
                    f"- Max kornstørrelse i kontakt med geonet: **{korn_str}**"
                )

            samme = _samme_produkter(bedste_1, bedste_2)

            if samme and bedste_1 is not None:
                _vis_krav_blok("Krav for produkt", bedste_1)
            else:
                if bedste_1 is not None:
                    _vis_krav_blok("Krav for bedste 1-lag-produkt", bedste_1)
                if bedste_2 is not None:
                    _vis_krav_blok("Krav for bedste 2-lag-produkt", bedste_2)

            if bedste_1 is None and bedste_2 is None:
                st.caption(
                    "Ingen produkt-specifikke krav at vise — ingen gyldige "
                    "beregninger for den valgte kombination."
                )
            else:
                st.caption(
                    "Bemærk: kravene ovenfor gælder det bedst reducerende net. "
                    "Andre produkter kan have andre krav til dæklag og "
                    "kornstørrelse — se datablad eller skift til "
                    "'Vælg specifikt produkt' for individuelle værdier."
                )

    # --- Sådan beregnes det -----------------------------------------------
    with st.expander("🔢 Sådan beregnes det"):
        st.markdown("""
Trinvis beregning, baseret på designmanualer og intern forsøgsdata fra Byggros:

Der beregnes en bærelagstykkelse ud fra 1 eller 2 lag armering med udgangspunkt i et referencenet.
Den beregnede bærelagstykkelse korrigeres for friktionsvinkler forskellig fra φ = 35° samt effektindeks af forskellige geonet.

1. **Bundmodulet Eu** vælges eller beregnes via sammenhæng med Cv
2. **Krav til overflademodulet Eo** vælges alt efter belastningsklasse
3. **Opslag i designdiagrammerne** i forhold til valg af bund- og overflademodul, til fastlæggelse af bærelagstykkelse — uarmeret og armeret med 1–2 lag geonet.
   Der laves lineær interpolation hvis det valgte/beregnede Eu ikke er en direkte tabelværdi.
4. **På baggrund af opslaget/interpolationen bestemmes basistykkelsen T_basis:**
   - Uarmeret: *xx mm*
   - 1 lag armering (referencenet): *xx mm*
   - 2 lag armering (referencenet): *xx mm*
5. **Korrektionsfaktorer for friktionsvinkel og effektivitet af geonet**

   **Friktionsvinkel:**
   Friktionsvinkel-korrektionen justerer basistykkelsen fra opslagstabellen, som er baseret på et standardmateriale med φ ≈ 35°. For hver grad over 35° reduceres tykkelsen med 2 %, og for φ under 35° øges tykkelsen tilsvarende.

   I standardberegningen sættes bærelagets friktionsvinkel φ = 35°.

   I den brugerdefinerede beregning beregnes en vægtet friktionsvinkel ud fra den angivne procentvægtning eller lagtykkelser af lagene, som er prædefinerede materialer med forskellige friktionsvinkler.

   *Eksempel på beregning i brugerdefineret tilstand, ud fra lagtykkelser:*

   | Lag | Materiale | Tykkelse | φ (°) | Vægtet bidrag |
   |-----|-----------|----------|------:|-------------:|
   | 1   | SG I 0-32 | 300 mm   | 40,0  | 12 000        |
   | 2   | Bundsand  | 450 mm   | 35,0  | 15 750        |

   Vægtet φ = Σ(tᵢ × φᵢ) / Σ(tᵢ) = 27 750 / 750 = **37,00°**

   φ-korrektion = −0,02 × (φ − 35°) = −0,02 × (37,00 − 35) = **−0,0400**
   *(dvs. tykkelsen reduceres med −4,00 % af T_basis)*

   **Net-korrektion:**
   Designdiagrammerne bruger GS-GRID SX160, E'GRID T6 eller Tensar TriAx TX160 som referencenet (effektindeks 100). Hvis der er valgt en anden armering, skaleres tykkelsen op eller ned med op til 20 % alt efter produkt.
   En positiv korrektionsfaktor = tykkere bærelag (mindre effektiv armering), negativ = tyndere bærelag (mere effektiv armering).

6. **Den endelige bærelagstykkelse beregnes som:**

   **T_armeret = T_basis × (1 + φ-kor + net-kor)**

_Kilde: GS-GRID Designmanual og Tensar Designmanual, samt interne forsøgsdata fra Byggros_
        """)


def _render_breakdown_tabel(
    rows: list[tuple[str, str, str]],
    t_final: float | None,
    t_uarm: float | None = None,
    red_mm: float | None = None,
    red_pct: float | None = None,
) -> None:
    """
    Render en tabel-lignende breakdown med linjer og et slutresultat.
    rows: liste af (label, værditekst, notetekst). Hvis værditekst er tom
    vises kun label-teksten som en note-linje.
    """
    lines: list[str] = []
    for label, val, note in rows:
        if val:
            note_html = (
                f' <span style="color:#888;font-size:0.82em">{note}</span>'
                if note else ""
            )
            lines.append(
                f'<div style="display:flex;justify-content:space-between;'
                f'padding:2px 0;font-size:0.9rem">'
                f'<span style="color:#444">{label}{note_html}</span>'
                f'<span style="font-weight:600;font-variant-numeric:tabular-nums">'
                f'{val}</span>'
                f'</div>'
            )
        else:
            lines.append(
                f'<div style="font-size:0.83rem;color:#888;padding:2px 0">'
                f'{label}'
                f'</div>'
            )

    result_lines = "".join(lines)

    if t_final is not None:
        red_html = ""
        if red_mm is not None and red_pct is not None:
            pct_str = f"{red_pct:.0%}"
            red_html = (
                f'<span style="color:{GRØN};font-size:0.85em;margin-left:10px">'
                f'↓ {red_mm:.0f} mm fra uarmeret ({pct_str})'
                f'</span>'
            )
        result_html = (
            f'<div style="border-top:1px solid #C8E6C9;margin-top:6px;'
            f'padding-top:6px;display:flex;align-items:baseline;gap:6px">'
            f'<span style="font-size:1.25rem;font-weight:700;color:{GRØN}">'
            f'= {t_final:.0f} mm</span>'
            f'{red_html}'
            f'</div>'
        )
    else:
        result_html = ""

    st.markdown(
        f'<div style="background:#F8FFF8;border-radius:6px;'
        f'padding:0.75rem 1rem;border:1px solid #C8E6C9;margin-bottom:0.5rem">'
        f'{result_lines}'
        f'{result_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _vis_beregnings_breakdown(
    eu: float,
    eo: float,
    phi: float,
    valgt_klasse: int,
    bedste_1: dict | None,
    bedste_2: dict | None,
    *,
    geonet: dict | None = None,
    geonet_navn: str | None = None,
) -> None:
    """
    Beregnings-breakdown boks under resultat (kun i Brugerdefineret).
    Viser trin-for-trin: uarmeret, 1 lag og 2 lag med korrektioner i mm.
    """
    phi_kor = -0.02 * (phi - 35.0)

    # Net-korrektioner og produktnavne per lag-mode
    if geonet is not None:
        # Specifikt-mode: samme korrektion begge lag-modes
        net_kor_1 = geonet["korrektion"]
        net_kor_2 = geonet["korrektion"]
        net_navn_1 = geonet_navn or geonet["navn"]
        net_navn_2 = net_navn_1
        note = None
    else:
        # Oversigt-mode: brug bedste produkt per lag-mode
        if bedste_1 is not None and bedste_1.get("produkter"):
            net_kor_1 = bedste_1["produkter"][0]["korrektion"]
            net_navn_1 = bedste_1["produkter"][0]["navn"]
        else:
            net_kor_1 = 0.0
            net_navn_1 = "reference"
        if bedste_2 is not None and bedste_2.get("produkter"):
            net_kor_2 = bedste_2["produkter"][0]["korrektion"]
            net_navn_2 = bedste_2["produkter"][0]["navn"]
        else:
            net_kor_2 = 0.0
            net_navn_2 = "reference"
        note = (
            "Net-korrektionen vist her gælder det bedst reducerende produkt. "
            "Andre produkter har andre korrektioner — se kolonnerne ovenfor."
        )

    # Kald beregn() med de relevante net-korrektioner
    ref_uarm = beregn(eu=eu, eo=eo, phi=phi, net_korrektion=0.0,    lag_mode="1_lag")
    ref_1    = beregn(eu=eu, eo=eo, phi=phi, net_korrektion=net_kor_1, lag_mode="1_lag")
    ref_2    = beregn(eu=eu, eo=eo, phi=phi, net_korrektion=net_kor_2, lag_mode="2_lag")

    t_uarm_final = ref_uarm.get("t_uarmeret_mm") if not ref_uarm.get("fejl") else None

    with st.container(border=True):
        st.markdown("**📊 Beregnings-breakdown**")

        # ── Uarmeret ──────────────────────────────────────────────────
        st.markdown("**Uarmeret bærelagstykkelse**")
        if not ref_uarm.get("fejl") and ref_uarm.get("t_basis_uarm_mm") is not None:
            t_b_u = ref_uarm["t_basis_uarm_mm"]
            phi_kor_mm_u = t_b_u * phi_kor
            rows_u: list[tuple[str, str, str]] = [
                ("T_basis (opslag/interpoleret)", f"{t_b_u:.0f} mm", ""),
            ]
            if abs(phi_kor_mm_u) > 0.5:
                rows_u.append((
                    "φ-korrektion",
                    f"{_dk_num(phi_kor_mm_u, '+.0f')} mm",
                    f"φ = {_dk_num(phi, '.1f')}°  ({_dk_num(phi_kor, '+.4f')})",
                ))
            else:
                rows_u.append(("(ingen φ- eller net-korrektion)", "", ""))
            _render_breakdown_tabel(rows_u, t_uarm_final)
        else:
            st.caption("Kan ikke beregnes for denne Eu/Eo-kombination.")

        st.markdown("---")

        # ── 1 lag ─────────────────────────────────────────────────────
        if bedste_1 is not None:
            st.markdown(f"**Med 1 lag geonet** ({net_navn_1})")
            if not ref_1.get("fejl") and ref_1.get("t_basis_arm_mm") is not None:
                t_b_1     = ref_1["t_basis_arm_mm"]
                t_1_final = ref_1.get("t_armeret_mm")
                phi_kor_mm_1 = t_b_1 * phi_kor
                net_kor_mm_1 = t_b_1 * net_kor_1
                rows_1: list[tuple[str, str, str]] = [
                    ("T_basis_armeret (opslag)", f"{t_b_1:.0f} mm", ""),
                    (
                        "φ-korrektion",
                        f"{_dk_num(phi_kor_mm_1, '+.0f')} mm",
                        f"φ = {_dk_num(phi, '.1f')}°  ({_dk_num(phi_kor, '+.4f')})",
                    ),
                    (
                        "Net-korrektion",
                        f"{_dk_num(net_kor_mm_1, '+.0f')} mm",
                        f"({_dk_num(net_kor_1, '+.2f')})",
                    ),
                ]
                red_mm_1  = (t_uarm_final - t_1_final) if (t_uarm_final and t_1_final) else None
                red_pct_1 = (red_mm_1 / t_uarm_final)  if (red_mm_1 and t_uarm_final)  else None
                _render_breakdown_tabel(rows_1, t_1_final, t_uarm_final, red_mm_1, red_pct_1)
            else:
                st.caption("Ingen gyldigt 1-lag resultat for denne kombination.")

        # ── 2 lag ─────────────────────────────────────────────────────
        if bedste_2 is not None:
            st.markdown("---")
            st.markdown(f"**Med 2 lag geonet** ({net_navn_2})")
            if not ref_2.get("fejl") and ref_2.get("t_basis_arm_mm") is not None:
                t_b_2     = ref_2["t_basis_arm_mm"]
                t_2_final = ref_2.get("t_armeret_mm")
                phi_kor_mm_2 = t_b_2 * phi_kor
                net_kor_mm_2 = t_b_2 * net_kor_2
                rows_2: list[tuple[str, str, str]] = [
                    ("T_basis_armeret (opslag)", f"{t_b_2:.0f} mm", ""),
                    (
                        "φ-korrektion",
                        f"{_dk_num(phi_kor_mm_2, '+.0f')} mm",
                        f"φ = {_dk_num(phi, '.1f')}°  ({_dk_num(phi_kor, '+.4f')})",
                    ),
                    (
                        "Net-korrektion",
                        f"{_dk_num(net_kor_mm_2, '+.0f')} mm",
                        f"({_dk_num(net_kor_2, '+.2f')})",
                    ),
                ]
                red_mm_2  = (t_uarm_final - t_2_final) if (t_uarm_final and t_2_final) else None
                red_pct_2 = (red_mm_2 / t_uarm_final)  if (red_mm_2 and t_uarm_final)  else None
                _render_breakdown_tabel(rows_2, t_2_final, t_uarm_final, red_mm_2, red_pct_2)
            else:
                st.caption("Ingen gyldigt 2-lag resultat for denne kombination.")

        if note:
            st.caption(f"ℹ️ {note}")


def render_standard() -> None:
    """Standard-tilstand: produktoversigt for alle geonet på én gang.

    Lodret stablet layout: A. Underbund → B. Belastning →
    Produktoversigt (uarmeret + 1/2-lag-kolonner) → informations-expandere.
    """

    # --- A. Underbund + B. Belastning -----------------------------------
    eu = input_underbund(key_prefix="std")
    valgt_klasse, _kl_info, eo = input_belastning(key_prefix="std")
    st.caption(
        "ℹ️ Standard-tilstanden bruger φ = 35° og viser kun geonet-"
        "produkter, der er anbefalet til den valgte belastningsklasse."
    )

    # --- Beregn alt -----------------------------------------------------
    prod_1lag = beregn_alle_produkter(eu, eo, "1_lag")
    prod_2lag = beregn_alle_produkter(eu, eo, "2_lag")

    alle_fejler_1 = all(p["fejl"] for p in prod_1lag)
    alle_fejler_2 = all(p["fejl"] for p in prod_2lag)
    haard_fejl: str | None = None
    if alle_fejler_1 and alle_fejler_2:
        for p in prod_1lag:
            if p["fejl"]:
                haard_fejl = p["fejl"]
                break

    t_uarm = None
    for p in prod_1lag + prod_2lag:
        if p["t_uarmeret_mm"] is not None:
            t_uarm = p["t_uarmeret_mm"]
            break

    grupper_1 = _filter_klasse_anbefalede(
        grupper_produkter(prod_1lag, tolerance_mm=5.0)
    )
    grupper_2 = _filter_klasse_anbefalede(
        grupper_produkter(prod_2lag, tolerance_mm=5.0)
    )

    bedste_1 = (
        sorted(grupper_1, key=lambda g: g["t_armeret_eksakt_mm"])[0]
        if grupper_1 else None
    )
    bedste_2 = (
        sorted(grupper_2, key=lambda g: g["t_armeret_eksakt_mm"])[0]
        if grupper_2 else None
    )

    # --- Produktoversigt -----------------------------------------------
    st.divider()
    st.subheader("Produktoversigt")

    if haard_fejl:
        vis_fejl(haard_fejl)
    else:
        if t_uarm is not None:
            st.markdown(
                f'<div class="uarm-banner">'
                f'<div class="uarm-banner-label">Uarmeret bærelagstykkelse</div>'
                f'<div class="uarm-banner-tal">{t_uarm:.0f} mm</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        kol_1, kol_2 = st.columns(2, gap="large")
        with kol_1:
            _render_lag_kolonne("1 LAG GEONET", grupper_1, valgt_klasse, "1_lag")
        with kol_2:
            _render_lag_kolonne("2 LAG GEONET", grupper_2, valgt_klasse, "2_lag")

    # --- Informations-expandere ----------------------------------------
    st.divider()
    _render_oversigt_expanders(eu, eo, valgt_klasse, bedste_1, bedste_2)


# ===========================================================================
# BRUGERDEFINERET-TILSTAND — målrettet beregning (uændret logik)
# ===========================================================================

def _dk_num(v: float, fmt: str) -> str:
    """Formattér tal med dansk decimal-komma og rigtigt minus-tegn."""
    s = format(v, fmt).replace(".", ",")
    if s.startswith("-"):
        s = "−" + s[1:]
    return s


def _phi_tabel_data(materialer: list[dict]) -> dict:
    """Byg data til φ-beregningstabel — genbruges af opsummeringsboks og trin 3.

    Returnerer dict med:
        tabel_md       — markdown-tabel (header + adskiller + rækker)
        total_v        — sum af tykkelser (mm) eller andele (%)
        total_bidrag   — Σ(vᵢ × φᵢ)
        phi_weighted   — total_bidrag / total_v (eller 35.0 ved tom input)
        lag_mode_pct   — True hvis andele i %, ellers tykkelser i mm
        symbol         — 'p' eller 't' (til formelvisning)
        enhed          — '%' eller 'mm'
    """
    if not materialer:
        return {
            "tabel_md": "", "total_v": 0.0, "total_bidrag": 0.0,
            "phi_weighted": 35.0, "lag_mode_pct": False,
            "symbol": "t", "enhed": "mm",
        }

    lag_mode_pct = any(m.get("pct") is not None for m in materialer)
    enhed = "%" if lag_mode_pct else "mm"
    symbol = "p" if lag_mode_pct else "t"
    feltnavn = "Andel" if lag_mode_pct else "Tykkelse"

    header = f"| Lag | Materiale | {feltnavn} | φ (°) | Vægtet bidrag |"
    sep = "|---|---|---:|---:|---:|"

    rows: list[str] = []
    total_v = 0.0
    total_bidrag = 0.0
    for i, m in enumerate(materialer):
        v = (m.get("pct") if lag_mode_pct else m.get("tykkelse_mm")) or 0.0
        bidrag = v * m["phi"]
        total_v += v
        total_bidrag += bidrag
        v_str = f"{v:.0f} {enhed}"
        phi_i_str = _dk_num(m["phi"], ".1f")
        bidrag_str = _dk_num(bidrag, ".0f")
        rows.append(
            f"| {i + 1} | {m['navn']} | {v_str} | {phi_i_str} | {bidrag_str} |"
        )

    tabel_md = "\n".join([header, sep] + rows)
    phi_weighted = total_bidrag / total_v if total_v > 0 else 35.0

    return {
        "tabel_md": tabel_md,
        "total_v": total_v,
        "total_bidrag": total_bidrag,
        "phi_weighted": phi_weighted,
        "lag_mode_pct": lag_mode_pct,
        "symbol": symbol,
        "enhed": enhed,
    }


def _vis_phi_opsummeringsboks(
    materialer: list[dict],
    phi_final: float,
    eu: float,
    eo: float,
) -> None:
    """Opsummeringsboks under lag-inputs: tabel, formel, φ-korrektion, mm-ækvivalent."""
    data = _phi_tabel_data(materialer)
    phi_weighted = data["phi_weighted"]
    overskrevet = abs(phi_final - phi_weighted) > 0.005

    phi_w_str = _dk_num(phi_weighted, ".2f")
    phi_f_str = _dk_num(phi_final, ".2f")
    bidrag_str = _dk_num(data["total_bidrag"], ".0f")
    v_str = _dk_num(data["total_v"], ".0f")

    phi_kor = -0.02 * (phi_final - 35.0)
    phi_kor_str = _dk_num(phi_kor, "+.4f")
    phi_kor_pct_str = _dk_num(phi_kor * 100, "+.2f")

    with st.container(border=True):
        st.markdown("**📐 φ-beregning fra materialelagene**")
        st.markdown(data["tabel_md"])
        st.markdown(
            f"φ = Σ({data['symbol']}ᵢ × φᵢ) / Σ({data['symbol']}ᵢ) = "
            f"{bidrag_str} / {v_str} = **{phi_w_str}°**"
        )

        if overskrevet:
            st.markdown(
                f"⚠️ φ overskrevet manuelt → bruger **{phi_f_str}°** "
                f"i resten af beregningen (vægtet værdi {phi_w_str}° ignoreres)."
            )

        st.markdown(
            f"**φ-korrektion** = −0,02 × (φ − 35°) = "
            f"−0,02 × ({phi_f_str} − 35) = **{phi_kor_str}** "
            f"({phi_kor_pct_str} % af T_basis)"
        )

        ref_1 = beregn(eu=eu, eo=eo, phi=phi_final,
                       net_korrektion=0.0, lag_mode="1_lag")
        ref_2 = beregn(eu=eu, eo=eo, phi=phi_final,
                       net_korrektion=0.0, lag_mode="2_lag")




def _input_materialelag(eu: float, eo: float) -> tuple[list[dict], float]:
    """
    C. Materialelag — render input-sektionen og returnér
    (materialer-liste, beregnet/overskrevet φ).
    """
    st.subheader("C. Materialelag")

    antal_lag = st.number_input(
        "Antal lag", min_value=1, max_value=3, value=2, step=1,
        key="bd_antal_lag",
    )
    lag_mode_mat = st.radio(
        "Angiv tykkelse som",
        ["mm (absolut)", "% (andele)"],
        horizontal=True,
        key="bd_lag_mode_mat",
    )

    materialer: list[dict] = []
    phi_vaerdier: list[float] = []
    total_pct = 0.0

    for i in range(int(antal_lag)):
        with st.expander(f"Lag {i + 1}", expanded=True):
            mat_navn = st.selectbox(
                "Materiale", MATERIAL_NAVNE, key=f"bd_mat_{i}",
            )
            if mat_navn == "Manuel indtastning":
                phi_i = st.number_input(
                    "φ (°)", 20.0, 60.0, 35.0, 0.5, key=f"bd_phi_m_{i}"
                )
                korn_i = st.number_input(
                    "Max kornstørrelse (mm)", 0, 500, 32, key=f"bd_korn_m_{i}"
                )
                ltype_i = st.selectbox(
                    "Lagtype", ["Bærelag", "Bundsikring"], key=f"bd_lt_m_{i}"
                )
            else:
                md = find_materiale(mat_navn)
                phi_i = float(md["phi"])
                korn_i = md["max_korn"]
                ltype_i = md["lagtype"]
                st.caption(
                    f"φ = {phi_i}° · max korn = {korn_i} mm · {ltype_i}"
                )

            phi_vaerdier.append(phi_i)

            if lag_mode_mat == "mm (absolut)":
                t_i = st.number_input(
                    "Tykkelse (mm)", 0, 2000, 300, 50, key=f"bd_t_{i}",
                )
                materialer.append({
                    "navn": mat_navn, "phi": phi_i, "max_korn": korn_i,
                    "lagtype": ltype_i, "tykkelse_mm": float(t_i),
                    "pct": None,
                })
            else:
                pct_default = round(100.0 / antal_lag, 1)
                p_i = st.number_input(
                    "Andel (%)", 0.0, 100.0, pct_default, 5.0,
                    key=f"bd_p_{i}",
                )
                total_pct += p_i
                materialer.append({
                    "navn": mat_navn, "phi": phi_i, "max_korn": korn_i,
                    "lagtype": ltype_i, "tykkelse_mm": None,
                    "pct": float(p_i),
                })

    if lag_mode_mat.startswith("%"):
        st.metric("Sum af andele", f"{total_pct:.1f} %")

    if lag_mode_mat == "mm (absolut)":
        total_t = sum(m["tykkelse_mm"] for m in materialer)
        phi_weighted = (
            sum(m["phi"] * m["tykkelse_mm"] for m in materialer) / total_t
            if total_t > 0
            else (sum(phi_vaerdier) / len(phi_vaerdier) if phi_vaerdier else 35.0)
        )
    else:
        total_p = sum(m["pct"] for m in materialer if m["pct"] is not None)
        phi_weighted = (
            sum(m["phi"] * m["pct"] for m in materialer) / total_p
            if total_p > 0
            else (sum(phi_vaerdier) / len(phi_vaerdier) if phi_vaerdier else 35.0)
        )

    if st.checkbox("Overskriv φ manuelt", key="bd_phi_override"):
        phi = st.number_input(
            "φ (°)", 20.0, 60.0, round(phi_weighted, 1), 0.5, key="bd_phi_man",
        )
    else:
        phi = phi_weighted

    _vis_phi_opsummeringsboks(materialer, phi, eu, eo)

    return materialer, phi


def render_brugerdefineret() -> None:
    """Brugerdefineret-tilstand: A–D input + resultater + expandere.

    Lodret stablet layout som i Standard-tilstand. Sektion D lader brugeren
    vælge mellem 'Vis alle produkter' (oversigt med custom φ) og 'Vælg
    specifikt produkt' (detaljeret resultat for ét produkt). Begge modes
    viser 1-lag og 2-lag side om side — ingen separat lag-mode-radio.
    """

    # --- A + B + C --------------------------------------------------------
    eu = input_underbund(key_prefix="bd")
    valgt_klasse, _kl_info, eo = input_belastning(key_prefix="bd")
    materialer, phi = _input_materialelag(eu, eo)

    # --- D. Geonet --------------------------------------------------------
    st.subheader("D. Geonet")

    visning = st.radio(
        "Visning",
        ["Vis alle produkter (oversigt)", "Vælg specifikt produkt"],
        horizontal=True,
        key="bd_visning",
        help=(
            "**Vis alle produkter:** samme oversigt som Standard, men med "
            "din custom φ fra materialelagene.  \n"
            "**Vælg specifikt produkt:** detaljeret resultat for ét valgt "
            "produkt, herunder dets specifikke udførelseskrav."
        ),
    )
    specifikt_mode = visning == "Vælg specifikt produkt"

    geonet: dict | None = None
    geonet_navn: str | None = None
    if specifikt_mode:
        geonet_navn = st.selectbox(
            "Produkt",
            GEONET_NAVNE,
            index=GEONET_NAVNE.index("GS-GRID SX160"),
            key="bd_geonet",
        )
        geonet = find_geonet(geonet_navn)

        if geonet:
            korn_txt = f"{geonet['max_korn']} mm" if geonet["max_korn"] else "—"
            kl_txt = ", ".join(str(k) for k in geonet["klasser"])
            kor_txt = f"{geonet['korrektion']:+.0%}"
            st.caption(
                f"Serie: **{geonet['serie']}** · Korrektion: {kor_txt} · "
                f"Max korn: {korn_txt} · Klasser: {kl_txt} · "
                f"Min dæklag: {geonet['min_daklag']} cm"
            )
            if geonet["navn"] == "Anden armering (manuel)":
                kor_man = st.number_input(
                    "Korrektionsfaktor (−0.20 til +0.20)",
                    min_value=-0.20, max_value=0.20,
                    value=0.0, step=0.01, format="%.2f",
                    key="bd_kor_man",
                    help="0.00 = samme effektivitet som reference (TX160/SX160/T6).",
                )
                geonet = {**geonet, "korrektion": kor_man}

    # --- Resultat ---------------------------------------------------------
    st.divider()
    st.subheader("Resultat")

    bedste_1: dict | None = None
    bedste_2: dict | None = None

    if not specifikt_mode:
        # OVERSIGT-MODE — som Standard, men med custom phi
        prod_1lag = beregn_alle_produkter(eu, eo, "1_lag", phi=phi)
        prod_2lag = beregn_alle_produkter(eu, eo, "2_lag", phi=phi)

        alle_fejler_1 = all(p["fejl"] for p in prod_1lag)
        alle_fejler_2 = all(p["fejl"] for p in prod_2lag)
        haard_fejl: str | None = None
        if alle_fejler_1 and alle_fejler_2:
            for p in prod_1lag:
                if p["fejl"]:
                    haard_fejl = p["fejl"]
                    break

        t_uarm = None
        for p in prod_1lag + prod_2lag:
            if p["t_uarmeret_mm"] is not None:
                t_uarm = p["t_uarmeret_mm"]
                break

        grupper_1 = _filter_klasse_anbefalede(
            grupper_produkter(prod_1lag, tolerance_mm=5.0)
        )
        grupper_2 = _filter_klasse_anbefalede(
            grupper_produkter(prod_2lag, tolerance_mm=5.0)
        )
        bedste_1 = (
            sorted(grupper_1, key=lambda g: g["t_armeret_eksakt_mm"])[0]
            if grupper_1 else None
        )
        bedste_2 = (
            sorted(grupper_2, key=lambda g: g["t_armeret_eksakt_mm"])[0]
            if grupper_2 else None
        )

        if haard_fejl:
            vis_fejl(haard_fejl)
        else:
            if t_uarm is not None:
                st.markdown(
                    f'<div class="uarm-banner">'
                    f'<div class="uarm-banner-label">Uarmeret bærelagstykkelse</div>'
                    f'<div class="uarm-banner-tal">{t_uarm:.0f} mm</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            kol_1, kol_2 = st.columns(2, gap="large")
            with kol_1:
                _render_lag_kolonne("1 LAG GEONET", grupper_1, valgt_klasse, "1_lag", phi=phi)
            with kol_2:
                _render_lag_kolonne("2 LAG GEONET", grupper_2, valgt_klasse, "2_lag", phi=phi)

    else:
        # SPECIFIKT PRODUKT-MODE
        net_kor = geonet["korrektion"] if geonet else 0.0
        res_1 = beregn(
            eu=eu, eo=eo, phi=phi, net_korrektion=net_kor, lag_mode="1_lag"
        )
        res_2 = beregn(
            eu=eu, eo=eo, phi=phi, net_korrektion=net_kor, lag_mode="2_lag"
        )

        bedste_1 = _resultat_til_gruppe(res_1, geonet, valgt_klasse)
        bedste_2 = _resultat_til_gruppe(res_2, geonet, valgt_klasse)

        t_uarm = None
        for r in (res_1, res_2):
            if not r.get("fejl") and r.get("t_uarmeret_mm") is not None:
                t_uarm = r["t_uarmeret_mm"]
                break

        haard_fejl_specifikt: str | None = None
        if bedste_1 is None and bedste_2 is None:
            haard_fejl_specifikt = res_1.get("fejl") or res_2.get("fejl")

        if haard_fejl_specifikt:
            vis_fejl(haard_fejl_specifikt)
        else:
            if t_uarm is not None:
                st.markdown(
                    f'<div class="uarm-banner">'
                    f'<div class="uarm-banner-label">Uarmeret bærelagstykkelse</div>'
                    f'<div class="uarm-banner-tal">{t_uarm:.0f} mm</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            grupper_1 = [bedste_1] if bedste_1 else []
            grupper_2 = [bedste_2] if bedste_2 else []

            tom_1 = (
                f"**{geonet_navn}** har ingen gyldigt 1-lag-resultat for "
                f"denne kombination.\n\n_{res_1.get('fejl', '')}_"
                if bedste_1 is None else None
            )
            tom_2 = (
                f"**{geonet_navn}** har ingen gyldigt 2-lag-resultat for "
                f"denne kombination.\n\n_{res_2.get('fejl', '')}_"
                if bedste_2 is None else None
            )

            kol_1, kol_2 = st.columns(2, gap="large")
            with kol_1:
                _render_lag_kolonne(
                    "1 LAG GEONET", grupper_1, valgt_klasse, "1_lag",
                    tom_besked=tom_1, phi=phi,
                )
            with kol_2:
                _render_lag_kolonne(
                    "2 LAG GEONET", grupper_2, valgt_klasse, "2_lag",
                    tom_besked=tom_2, phi=phi,
                )

    # --- Informations-expandere ------------------------------------------
    st.divider()
    _render_oversigt_expanders(
        eu, eo, valgt_klasse, bedste_1, bedste_2,
        phi=phi,
        geonet=geonet,
        geonet_navn=geonet_navn,
        materialer=materialer,
    )


# ===========================================================================
# Top-level layout — titel + tilstandsvælger + dispatch
# ===========================================================================

st.title("🏗️ Geonet Dimensioneringsværktøj")
st.caption(
    "Beregning af bærelagstykkelse med og uden geonetarmering "
    "· Baseret på BG Byggros designmanualer for Tensar og GS-GRID, samt interne forsøgsdata"
)

tilstand = st.radio(
    "Tilstand",
    ["Standard", "Brugerdefineret"],
    horizontal=True,
    key="tilstand",
    help=(
        "**Standard:** Vælg Eu/Cv og belastningsklasse — få en oversigt over "
        "alle geonet-produkter med deres opnåelige bærelagstykkelse (φ = 35°).  \n"
        "**Brugerdefineret:** Vælg ét produkt med op til 3 materialelag, "
        "vægtet φ og manuel overstyring."
    ),
)

st.caption(
    "I standardberegningen forudsættes 1 homogent bærelag med en forudsat "
    "friktionsvinkel på φ = 35°."
)

st.divider()

if tilstand == "Standard":
    render_standard()
else:
    render_brugerdefineret()