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

    HOVER = "%{x:.0f} cm · Eu %{y:.1f} MN/m²<extra>%{fullData.name}</extra>"

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

    _armeret("1_lag", FARVE_1LAG, f"1 lag · {geonet_navn}")
    _armeret("2_lag", FARVE_2LAG, f"2 lag · {geonet_navn}")

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
        margin=dict(l=60, r=220, t=10, b=60),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=SKRIFT, size=11,
                  color=FARVE_INK),
        hovermode="closest",
        legend=dict(orientation="v", yanchor="top", y=1.0,
                    xanchor="left", x=1.02, font=dict(size=10),
                    bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(title="Bærelagstykkelse [cm]", range=[0, max(x_maks, 80)], **akse),
        yaxis=dict(
            title="Bundmodul Eu [MN/m²]",
            range=[0, max(max(eu_vals) * 1.05, eu * 1.2, 50)],
            **akse,
        ),
    )
    return fig
