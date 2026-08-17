"""Designdiagrammet — én tegning til både skærm og rapport.

Modulet er frit for Streamlit, så det kan bruges både af app.py (som viser
figuren interaktivt) og af core/rapport.py (som eksporterer den til PNG til
Word- og PDF-rapporten). Dermed kan de to visninger ikke divergere.

Farverne er de samme som i assets/byggros_theme.css og ui.FARVE; de skrives
her direkte, da core ikke må afhænge af præsentationslaget.
"""

from __future__ import annotations

from .data import K_PHI, PHI_BASIS
from .calculator import _slaa_op_interp

# Paletten, jf. :root i assets/byggros_theme.css
FARVE_INK = "#15211A"
FARVE_LINJE = "#DCE1DD"
FARVE_KRITISK = "#B42318"
FARVE_UARM = "#15211A"      # ustabiliseret
FARVE_1LAG = "#1F4E9C"      # 1 lag geonet
FARVE_2LAG = "#7B1FA2"      # 2 lag geonet

SKRIFT = "IBM Plex Sans, Segoe UI, system-ui, sans-serif"


def byg_designdiagram(
    *,
    eu: float,
    eo: float,
    phi: float,
    geonet: dict | None,
    t_indtastet_mm: float | None,
    t_basis_table: dict,
    t_1_lag_mm: float | None = None,
    t_2_lag_mm: float | None = None,
    t_1_lag_best_mm: float | None = None,
    t_2_lag_best_mm: float | None = None,
):
    """Designdiagrammet som Plotly-figur.

    Kurverne dannes af designdiagram-tabellen ved det viste Eo og korrigeres
    med φ og nettets korrektion, jf. afsnittet "Sådan dannes diagrammet".
    Produkter med korrektionsinterval tegnes med et tonet bånd mellem den
    optimale og den konservative kurve.

    Figuren bruges både af skærmen og af rapporten: app.py viser den med
    st.plotly_chart, og rapport.designdiagram_png() eksporterer den samme
    figur til PNG. De to visninger kan derfor ikke divergere.
    """

    import plotly.graph_objects as go

    phi_kor = K_PHI * (phi - PHI_BASIS)
    net_kor_kons = float(geonet.get("korrektion", 0.0)) if geonet else 0.0
    interval = geonet.get("korrektion_interval") if geonet else None
    net_kor_best = float(interval[0]) if interval else None
    geonet_navn = (geonet or {}).get("navn", "Referencenet")

    eu_vals = sorted(t_basis_table.keys())

    def _kurve(lag_mode: str, faktor: float) -> tuple[list[float], list[float]]:
        xs: list[float] = []
        ys: list[float] = []
        for eu_v in eu_vals:
            v = _slaa_op_interp(eu_v, eo, lag_mode, t_basis_table=t_basis_table)
            if v is not None:
                xs.append(v * faktor)      # cm
                ys.append(eu_v)
        return xs, ys

    HOVER = "%{x:.0f} cm · Eᵤ %{y:.1f} MN/m²<extra>%{fullData.name}</extra>"

    fig = go.Figure()

    xs_u, ys_u = _kurve("uarmeret", 1.0 + phi_kor)
    if xs_u:
        fig.add_trace(go.Scatter(
            x=xs_u, y=ys_u, mode="lines", name="Ustabiliseret",
            line=dict(color=FARVE_UARM, width=2),
            hovertemplate=HOVER,
        ))

    def _armeret(lag_mode: str, farve: str, navn: str) -> None:
        xs_k, ys_k = _kurve(lag_mode, 1.0 + phi_kor + net_kor_kons)
        if not xs_k:
            return
        if net_kor_best is not None:
            xs_b, ys_b = _kurve(lag_mode, 1.0 + phi_kor + net_kor_best)
            if xs_b and ys_b == ys_k:
                # Båndet mellem den optimale og den konservative kurve.
                fig.add_trace(go.Scatter(
                    x=xs_b + xs_k[::-1], y=ys_b + ys_k[::-1],
                    fill="toself", fillcolor=farve, opacity=0.10,
                    line=dict(width=0), hoverinfo="skip",
                    showlegend=False,
                ))
                fig.add_trace(go.Scatter(
                    x=xs_b, y=ys_b, mode="lines",
                    name=f"{navn} (optimal)",
                    line=dict(color=farve, width=1.2, dash="dot"),
                    hovertemplate=HOVER,
                ))
        fig.add_trace(go.Scatter(
            x=xs_k, y=ys_k, mode="lines", name=navn,
            line=dict(color=farve, width=2),
            hovertemplate=HOVER,
        ))

    # Geonettets navn staar i kortets sidehoved; signaturen benævner alene
    # kurverne, saa navnet ikke gentages fire gange lige efter hinanden.
    _armeret("1_lag", FARVE_1LAG, "1 lag geonet")
    _armeret("2_lag", FARVE_2LAG, "2 lag geonet")

    for t_mm, farve, navn in (
        (t_1_lag_mm, FARVE_1LAG, "1 lag geonet"),
        (t_2_lag_mm, FARVE_2LAG, "2 lag geonet"),
    ):
        if t_mm:
            fig.add_trace(go.Scatter(
                x=[t_mm / 10.0], y=[eu], mode="markers",
                name=navn, showlegend=False,
                marker=dict(color=farve, size=9,
                            line=dict(color="#FFFFFF", width=1.5)),
                hovertemplate=HOVER,
            ))
    for t_mm, farve, navn in (
        (t_1_lag_best_mm, FARVE_1LAG, "1 lag geonet (optimal)"),
        (t_2_lag_best_mm, FARVE_2LAG, "2 lag geonet (optimal)"),
    ):
        if t_mm:
            fig.add_trace(go.Scatter(
                x=[t_mm / 10.0], y=[eu], mode="markers",
                name=navn, showlegend=False,
                marker=dict(color="rgba(0,0,0,0)", size=10,
                            line=dict(color=farve, width=2)),
                hovertemplate=HOVER,
            ))

    # Den indtastede opbygning med lodret hjælpelinje, så aflæsningen på
    # x-aksen kan foretages direkte. Tykkelsen står i signaturen frem for som
    # etiket ved punktet, så diagrammet ikke får påskrift i kurveområdet.
    if t_indtastet_mm and t_indtastet_mm > 0:
        t_cm = t_indtastet_mm / 10.0
        fig.add_shape(
            type="line", x0=t_cm, x1=t_cm, y0=0, y1=eu,
            line=dict(color=FARVE_KRITISK, width=1, dash="dash"),
        )
        fig.add_trace(go.Scatter(
            x=[t_cm], y=[eu], mode="markers",
            name=f"Indtastet opbygning ({t_cm:.0f} cm)", showlegend=True,
            marker=dict(color=FARVE_KRITISK, size=11,
                        line=dict(color="#FFFFFF", width=1.5)),
            hovertemplate=HOVER,
        ))

    alle_x = list(xs_u)
    for t in (t_indtastet_mm, t_1_lag_mm, t_2_lag_mm,
              t_1_lag_best_mm, t_2_lag_best_mm):
        if t:
            alle_x.append(t / 10.0)
    x_maks = max(alle_x) * 1.08 if alle_x else 160

    akse = dict(
        gridcolor="#EDEFED", zeroline=False,
        linecolor=FARVE_LINJE, ticks="outside",
        tickcolor=FARVE_LINJE, tickfont=dict(size=10),
    )
    fig.update_layout(
        height=380,
        margin=dict(l=60, r=20, t=10, b=60),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=SKRIFT, size=11,
                  color=FARVE_INK),
        hovermode="closest",
        legend=dict(
            orientation="v", yanchor="top", y=0.98,
            xanchor="right", x=0.99, font=dict(size=10),
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor=FARVE_LINJE, borderwidth=1,
        ),
        xaxis=dict(title="Bærelagstykkelse [cm]", range=[0, max(x_maks, 80)], **akse),
        yaxis=dict(
            title="Bundmodul Eᵤ [MN/m²]",
            range=[0, max(max(eu_vals) * 1.05, eu * 1.2, 50)],
            **akse,
        ),
    )
    return fig


# ---------------------------------------------------------------------------
# Designmanualernes diagrammer optegnet af de aflæste værdier
# ---------------------------------------------------------------------------

# Kurvernes benævnelse og farve, i den rækkefølge de optegnes. Nøglerne er
# felterne i diagramdataens rækker.
_RAA_KURVER = (
    ("t_uarmeret_cm", "Ustabiliseret", FARVE_UARM),
    ("t_1_lag_cm", "1 lag armering", FARVE_1LAG),
    ("t_2_lag_cm", "2 lag armering", FARVE_2LAG),
)


def byg_raadiagram(diagram: dict, hoejde_px: int = 400):
    """Designmanualens diagram optegnet af de aflæste værdier.

    Diagrammet gengiver den tabel, beregningerne slår op i, med bundmodulet
    Eu på den lodrette akse og bærelagstykkelsen på den vandrette — samme
    orientering som designmanualernes egne diagrammer. Kurverne dannes af
    tabellens rækker og optegnes alene, hvor der er aflæste værdier; en
    kurve uden værdier udelades.

    Optegningen er en gengivelse af tabellen og ikke en selvstændig kilde;
    den originale scanning af manualens diagram vises ved siden af.

    Returnerer None, når ingen af kurverne har værdier.
    """
    import plotly.graph_objects as go

    raekker = sorted(diagram.get("rows") or [], key=lambda r: r["eu"])
    if not raekker:
        return None

    fig = go.Figure()
    x_maks = 0.0
    for felt, navn, farve in _RAA_KURVER:
        punkter = [
            (r[felt], r["eu"]) for r in raekker if r.get(felt) is not None
        ]
        if not punkter:
            continue
        xs = [p[0] for p in punkter]
        x_maks = max(x_maks, max(xs))
        fig.add_trace(go.Scatter(
            x=xs, y=[p[1] for p in punkter],
            mode="lines+markers", name=navn,
            line=dict(color=farve, width=2),
            marker=dict(color=farve, size=3.5),
            hovertemplate=(
                "%{x:.1f} cm · Eᵤ %{y:.0f} MN/m²<extra>%{fullData.name}</extra>"
            ),
        ))
    if not fig.data:
        return None

    eu_vals = [r["eu"] for r in raekker]
    akse = dict(
        gridcolor="#EDEFED", zeroline=False,
        linecolor=FARVE_LINJE, ticks="outside",
        tickcolor=FARVE_LINJE, tickfont=dict(size=10),
    )
    fig.update_layout(
        height=hoejde_px,
        margin=dict(l=60, r=20, t=10, b=55),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=SKRIFT, size=11, color=FARVE_INK),
        hovermode="closest",
        legend=dict(
            orientation="v", yanchor="top", y=0.98,
            xanchor="right", x=0.99, font=dict(size=10),
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor=FARVE_LINJE, borderwidth=1,
        ),
        xaxis=dict(
            title="Bærelagstykkelse [cm]", range=[0, x_maks * 1.08], **akse,
        ),
        yaxis=dict(
            title="Bundmodul Eᵤ [MN/m²]",
            range=[0, max(eu_vals) * 1.05], **akse,
        ),
    )
    return fig


# ---------------------------------------------------------------------------
# Opbygningssnit — én tegning til både skærm og rapport
# ---------------------------------------------------------------------------

# Lagfarver, jf. ui.FARVE og :root i stylesheetet
FARVE_BAERELAG = "#D9DDD9"
FARVE_BAERELAG_KANT = "#B9C0BA"
FARVE_BUNDSIKRING = "#EDEFED"
FARVE_BUNDSIKRING_KANT = "#C4CAC5"
FARVE_JORD = "#8B7355"
FARVE_INK_45 = "#7A857D"
FARVE_INK_25 = "#9AA39C"
FARVE_GRON = "#1B6B34"
FARVE_ADVARSEL = "#A8600B"

# Jordbåndets højde angives i samme enhed som søjlerne, så det skalerer med.
_JORD_ANDEL = 0.11

# Signaturen lægges under tegningen. Højden lægges til den ønskede tegnehøjde,
# så søjlerne bevarer deres plads, uanset hvilken højde kalderen angiver.
_SIGNATUR_PX = 46

# Figurens margener. Overkanten rummer søjletitlerne, bunden statusteksten og
# signaturen. Værdierne indgår i beregningen af, hvor mange tekstlinjer der er
# plads til i det enkelte materialelag.
_MARGIN_TOP = 34
_MARGIN_BUND = 96

# Linjehøjde for materialeteksten inde i lagene, ved skriftstørrelse 10.
_LINJE_PX = 13.5

# Forklaringen i en søjle uden opbygning. Annotationens bredde er fast, og
# tekstlinjer, der er bredere, klippes; teksten ombrydes derfor til
# _TOM_TEKST_TEGN pr. linje, jf. ombryd_tekst().
_TOM_TEKST_PX = 110
_TOM_TEKST_TEGN = 18


def byg_snit(
    kolonner: list[dict],
    reference_mm: float | None = None,
    geonet_navn: str | None = None,
    hoejde_px: int = 340,
):
    """Opbygningssnittene som Plotly-figur.

    kolonner: liste af
        {"titel",
         "lag": [(navn, mm, "baerelag"|"bundsikring")],
         "geonet_mm": [kote målt fra underbundens overkant],
         "total_mm": float | None,
         "status": (tekst, "gron"|"advarsel"|"kritisk"|"neutral"),
         "tom_tekst": str,
         "best_case_mm": float,
         "advarsler": [str]}

    Alle søjler deler lodret skala, så de kan sammenlignes direkte.
    reference_mm tegnes som en fælles stiplet linje ved den indtastede
    tykkelse; None i standardtilstanden, hvor der ikke indtastes lag.

    Figuren bruges både af skærmen (ui.snit) og af rapporten
    (rapport.render_opbygning_png), så de to visninger ikke kan divergere.
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    hoejder = [k["total_mm"] for k in kolonner if k.get("total_mm")]
    hoejder += [k["best_case_mm"] for k in kolonner if k.get("best_case_mm")]
    if reference_mm:
        hoejder.append(reference_mm)
    if not hoejder:
        return None
    maks = max(hoejder)
    jord = maks * _JORD_ANDEL

    # Lagteksten sættes efter, hvor mange linjer der er plads til i laget.
    # Omregningen fra mm til billedpunkter følger y-området og plotfladens
    # højde, jf. update_yaxes og update_layout nedenfor.
    plot_px = max(hoejde_px + _SIGNATUR_PX - _MARGIN_TOP - _MARGIN_BUND, 60)
    px_pr_mm = plot_px / (maks * 1.08 + jord * 1.15)

    antal = len(kolonner)
    fig = make_subplots(
        rows=1, cols=antal, shared_yaxes=True,
        subplot_titles=[k["titel"] for k in kolonner],
        horizontal_spacing=0.04,
    )

    for i, k in enumerate(kolonner, start=1):
        # Underbunden som skraveret bånd under nulniveauet, i samme bredde som
        # opbygningen ovenover. Baggrunden er den fulde jordfarve, så den hvide
        # angivelse af underbundens E-modul kan læses; skraveringen tegnes
        # ovenpå i en mørkere tone.
        fig.add_trace(
            go.Bar(
                x=[""], y=[jord], base=[-jord],
                marker=dict(
                    color=FARVE_JORD,
                    pattern=dict(
                        shape="/", bgcolor=FARVE_JORD,
                        fgcolor="#6E5A42", size=5, solidity=0.22,
                    ),
                    line=dict(width=0),
                ),
                width=0.62, hoverinfo="skip", showlegend=False,
            ),
            row=1, col=i,
        )
        if k.get("underbund_tekst"):
            fig.add_annotation(
                xref=f"x{i}" if i > 1 else "x", yref="y",
                x=0, y=-jord / 2,
                text=k["underbund_tekst"], showarrow=False,
                font=dict(size=8, color="#FFFFFF"),
            )

        total = k.get("total_mm")
        if not total:
            fig.add_annotation(
                text=ombryd_tekst(
                    k.get("tom_tekst", "Ikke defineret"), _TOM_TEKST_TEGN,
                ),
                xref=f"x{i}" if i > 1 else "x", yref="y",
                x=0, y=maks / 2, showarrow=False,
                font=dict(size=10, color=FARVE_INK_45),
                align="center", width=_TOM_TEKST_PX,
            )
        else:
            # Lagene stables nedefra, så rækkefølgen i "lag" læses oppefra.
            bund = 0.0
            for navn, tykkelse, slags in reversed(k.get("lag", [])):
                baere = slags == "baerelag"
                fig.add_trace(
                    go.Bar(
                        x=[""], y=[tykkelse], base=[bund],
                        marker=dict(
                            color=FARVE_BAERELAG if baere else FARVE_BUNDSIKRING,
                            line=dict(
                                color=(FARVE_BAERELAG_KANT if baere
                                       else FARVE_BUNDSIKRING_KANT),
                                width=1,
                            ),
                        ),
                        width=0.62,
                        text=_lagtekst(navn, tykkelse, px_pr_mm),
                        textposition="inside", insidetextanchor="middle",
                        textfont=dict(size=10, color=FARVE_INK),
                        hovertemplate=f"{navn} · %{{y:.0f}} mm<extra></extra>",
                        showlegend=False,
                    ),
                    row=1, col=i,
                )
                bund += tykkelse

            # Målsætningen står til højre for søjlen.
            fig.add_annotation(
                xref=f"x{i}" if i > 1 else "x", yref="y",
                x=0.4, y=total / 2,
                text=f"{total:,.0f} mm".replace(",", "."),
                showarrow=False, xanchor="left",
                font=dict(size=10.5, color=FARVE_INK),
            )

            for kote in k.get("geonet_mm", []):
                fig.add_shape(
                    type="line", xref=f"x{i}" if i > 1 else "x", yref="y",
                    x0=-0.36, x1=0.36, y0=kote, y1=kote,
                    line=dict(color=FARVE_KRITISK, width=2),
                )

            best = k.get("best_case_mm")
            if best and best < total:
                fig.add_shape(
                    type="line", xref=f"x{i}" if i > 1 else "x", yref="y",
                    x0=-0.33, x1=0.33, y0=best, y1=best,
                    line=dict(color=FARVE_GRON, width=1, dash="dot"),
                )
                # Mellemregningen bag den optimale tykkelse aflæses ved at
                # hvile på linjen. Formen selv bærer ingen hover, og der
                # lægges derfor en gennemsigtig markørrække oven på den.
                note = k.get("best_case_note") or (
                    f"Optimal korrektion · {best:,.0f} mm".replace(",", ".")
                )
                fig.add_trace(
                    go.Scatter(
                        x=[-0.24, 0.0, 0.24], y=[best] * 3,
                        mode="markers",
                        marker=dict(size=18, color="rgba(0,0,0,0)"),
                        hovertemplate=(
                            note.replace("\n", "<br>") + "<extra></extra>"
                        ),
                        showlegend=False,
                    ),
                    row=1, col=i,
                )

        if reference_mm:
            fig.add_shape(
                type="line", xref=f"x{i}" if i > 1 else "x", yref="y",
                x0=-0.62, x1=0.92, y0=reference_mm, y1=reference_mm,
                line=dict(color=FARVE_INK_25, width=1.5, dash="dash"),
            )

        # Statusteksten står under jordbåndet.
        status_tekst, status_slags = k.get("status", ("", "neutral"))
        farve = {
            "gron": FARVE_GRON,
            "advarsel": FARVE_ADVARSEL,
            "kritisk": FARVE_KRITISK,
        }.get(status_slags, FARVE_INK_45)
        linjer = [t for t in (status_tekst or "").split("\n") if t]
        linjer += list(k.get("advarsler", []))
        if linjer:
            fig.add_annotation(
                xref=f"x{i}" if i > 1 else "x", yref="paper",
                x=-0.05, y=-0.02, yanchor="top",
                text="<br>".join(linjer), showarrow=False,
                font=dict(size=10.5, color=farve), align="center",
            )

    # Signaturen tegnes som en del af figuren, så den følger med til rapportens
    # PNG. Posterne føjes som tomme kurver alene for signaturens skyld; deres
    # udseende er det samme, som fladerne og linjerne har i tegningen.
    _tilfoej_signatur(fig, go, kolonner, geonet_navn, reference_mm)

    fig.update_yaxes(
        range=[-jord * 1.15, maks * 1.08],
        showgrid=False, zeroline=False, showticklabels=False,
        showline=False,
    )
    # X-området rækker ud over søjlen, så målsætningen til højre får plads.
    fig.update_xaxes(
        showgrid=False, zeroline=False, showticklabels=False, showline=False,
        range=[-0.62, 0.92],
    )
    # Søjletitlerne sættes af make_subplots midt over subplot-fladen. Fladen
    # rækker ud til højre for at give plads til målsætningen, og titlen ville
    # derfor stå forskudt i forhold til opbygningen. Den bindes i stedet til
    # søjlens egen akse, så den står centreret over opbygningen.
    for i, ann in enumerate(fig.layout.annotations[:antal], start=1):
        ann.font = dict(size=11.5, color=FARVE_INK, family=SKRIFT)
        ann.xref = f"x{i}" if i > 1 else "x"
        ann.x = 0
        ann.xanchor = "center"

    fig.update_layout(
        height=hoejde_px + _SIGNATUR_PX,
        barmode="overlay", bargap=0,
        # Bundmarginen rummer statusteksten under søjlerne og signaturen
        # nederst; overkanten rummer søjletitlerne.
        margin=dict(l=10, r=10, t=_MARGIN_TOP, b=_MARGIN_BUND),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=SKRIFT, size=11, color=FARVE_INK),
        showlegend=True,
        legend=dict(
            orientation="h",
            x=0, xanchor="left", y=-0.19, yanchor="top",
            font=dict(size=10.5, color=FARVE_INK_45, family=SKRIFT),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            itemclick=False, itemdoubleclick=False,
            tracegroupgap=0,
        ),
        hovermode="closest",
    )
    return fig


def _tilfoej_signatur(fig, go, kolonner, geonet_navn, reference_mm) -> None:
    """Signaturen for opbygningssnittene.

    Posterne dannes af figurens indhold: lagfladerne angives altid, mens
    geonettet, den optimale korrektion og det indtastede niveau alene angives,
    når de forekommer i tegningen. Symbolerne gengives, som de fremtræder i
    figuren, så de kan skelnes fra hinanden.
    """
    poster: list[tuple[str, str, str, str]] = [
        (FARVE_BAERELAG, FARVE_BAERELAG_KANT, "Bærelag", "flade"),
        (FARVE_BUNDSIKRING, FARVE_BUNDSIKRING_KANT, "Bundsikring", "flade"),
    ]
    if any(k.get("geonet_mm") for k in kolonner):
        poster.append(
            (FARVE_KRITISK, FARVE_KRITISK, geonet_navn or "Geonet", "linje")
        )
    if any(
        k.get("best_case_mm") and k.get("total_mm")
        and k["best_case_mm"] < k["total_mm"]
        for k in kolonner
    ):
        poster.append((FARVE_GRON, FARVE_GRON, "Optimal korrektion", "prikket"))
    if reference_mm:
        poster.append(
            (FARVE_INK_25, FARVE_INK_25, "Indtastet niveau", "stiplet")
        )

    for flade, kant, tekst, slags in poster:
        if slags == "flade":
            spor = go.Bar(
                x=[None], y=[None], name=tekst,
                marker=dict(color=flade, line=dict(color=kant, width=1)),
                showlegend=True, hoverinfo="skip",
            )
        else:
            spor = go.Scatter(
                x=[None], y=[None], mode="lines", name=tekst,
                line=dict(
                    color=flade, width=2,
                    dash={"linje": "solid", "prikket": "dot"}.get(
                        slags, "dash"
                    ),
                ),
                showlegend=True, hoverinfo="skip",
            )
        fig.add_trace(spor, row=1, col=1)


def kort_lagnavn(navn: str) -> str:
    """Materialenavnet afkortet til materialets hovedord.

    Anvendes alene, hvor laget er for tyndt til, at det fulde navn kan stå,
    jf. _lagtekst().
    """
    ord = navn.split()
    return ord[0] if ord else navn


def ombryd_tekst(tekst: str, maks_tegn: int) -> str:
    """Teksten ombrudt ved mellemrum i linjer af højst maks_tegn.

    Et enkelt ord brydes ikke; er ordet længere end maks_tegn, står det
    alene på sin linje.
    """
    linjer: list[str] = []
    for ord in tekst.split():
        if linjer and len(linjer[-1]) + 1 + len(ord) <= maks_tegn:
            linjer[-1] = f"{linjer[-1]} {ord}"
        else:
            linjer.append(ord)
    return "<br>".join(linjer) if linjer else tekst


def ombryd_lagnavn(navn: str, maks_tegn: int = 13) -> str:
    """Materialenavnet ombrudt til søjlebredden.

    Søjlerne er smallere end det længste materialenavn, og navnet brydes
    derfor ved mellemrum i linjer af højst maks_tegn. Et enkelt ord brydes
    ikke; "Bundsikringssand" står på én linje, mens "Stabilgrus SGII 0-32"
    sættes over to.
    """
    return ombryd_tekst(navn, maks_tegn)


def _lagtekst(navn: str, tykkelse: float, px_pr_mm: float) -> str:
    """Materialebetegnelse og tykkelse, som de kan stå i laget.

    Teksten sættes efter lagets højde: er der plads til det fulde navn,
    anvendes dette; ellers materialets hovedord; er laget for tyndt til
    andet, angives tykkelsen alene. Rummer laget ikke en enkelt linje,
    udelades teksten, og lagets tykkelse aflæses af målsætningen.
    """
    lag_px = tykkelse * px_pr_mm
    for betegnelse in (ombryd_lagnavn(navn), kort_lagnavn(navn), ""):
        if not betegnelse:
            break
        linjer = betegnelse.count("<br>") + 2  # betegnelse + tykkelse
        if lag_px >= linjer * _LINJE_PX + 4:
            return f"{betegnelse}<br>{tykkelse:.0f}"
    return f"{tykkelse:.0f}" if lag_px >= _LINJE_PX + 4 else ""


def lagtype_for_navn(navn: str, materialer: list[dict] | None) -> str:
    """Fladefarve for et lag: bærelag eller bundsikring.

    Lagtypen slås op i de indtastede materialer. Findes navnet ikke — søjlen
    kan være dannet af en skaleret fordeling — afgøres den ud fra navnet.
    """
    for m in materialer or []:
        if m.get("navn") == navn:
            return (
                "bundsikring"
                if str(m.get("lagtype", "")).lower().startswith("bunds")
                else "baerelag"
            )
    return "bundsikring" if "bundsikring" in navn.lower() else "baerelag"


def snit_til_kolonner(
    snit_liste: list, materialer: list[dict] | None, eu: float,
) -> list[dict]:
    """Oversætter snit-listen til ui.snit()'s kolonner.

    Snit-objekterne er den fælles beskrivelse, som både skærm og rapport
    tegner af. Her omsættes de til byg_snit()'s format:

    - geonet_y_fracs er brøkdele målt fra bærelagets overkant; ui.snit()
      forventer koter over underbunden, altså total × (1 − frac).
    - En søjle uden materialefordeling tegnes som ét ubundet lag.
    - Statusfarverne følger stylesheetets tre statusfarver.
    """
    farve = {"danger": "kritisk", "warning": "advarsel", "success": "gron"}
    kolonner: list[dict] = []
    for s in snit_liste:
        total = s.t_baerelag_mm
        if s.sub_lag:
            # Det fulde materialenavn føres videre; tegningen afgør, hvor
            # meget af det der er plads til i laget, jf. _lagtekst().
            lag = [
                (
                    l["navn"],
                    l["tykkelse_mm"],
                    lagtype_for_navn(l["navn"], materialer),
                )
                for l in s.sub_lag
            ]
        elif total:
            lag = [("Ubunden opbygning", total, "baerelag")]
        else:
            lag = []

        advarsler = list((s.placement or {}).get("placeringsadvarsler") or [])

        kolonner.append({
            "titel": s.titel,
            "lag": lag,
            "geonet_mm": [
                total * (1 - frac) for frac in (s.geonet_y_fracs or []) if total
            ],
            "total_mm": total,
            "tom_tekst": s.ikke_defineret_tekst or "Ikke defineret",
            "best_case_mm": s.best_case_mm,
            "best_case_note": s.best_case_note,
            "advarsler": advarsler,
            "status": (
                s.status_tekst or "",
                farve.get(s.status_farve or "", "neutral"),
            ),
        })

    if kolonner:
        kolonner[0]["underbund_tekst"] = f"UNDERBUND\n{eu:.0f} MPa"
    return kolonner
