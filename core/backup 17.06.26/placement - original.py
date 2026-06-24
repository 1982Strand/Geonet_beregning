"""
Geonet placement checks.

The design diagrams return a required bearing-layer thickness. This module
checks whether the geonet layers can be placed inside that thickness according
to the construction rules from the design manuals.
"""

from __future__ import annotations

MIN_TOP_COVER_MM = 200.0
MIN_GEONET_SPACING_MM = 200.0
MAX_SPACING_TENSAR_MM = 400.0
MAX_SPACING_GS_EGRID_MM = 500.0
MAX_SPACING_CONSERVATIVE_MM = 400.0


def placement_requirements(geonet: dict | None = None) -> dict:
    """Return the active placement requirements for a product or reference net."""
    serie = (geonet or {}).get("serie")
    product_cover = (geonet or {}).get("min_daklag")
    product_cover_mm = (
        float(product_cover) * 10.0
        if isinstance(product_cover, (int, float))
        else MIN_TOP_COVER_MM
    )
    if serie in ("GS-GRID", "E'GRID"):
        max_spacing = MAX_SPACING_GS_EGRID_MM
        source = "GS-GRID/E'GRID"
    elif serie == "Tensar":
        max_spacing = MAX_SPACING_TENSAR_MM
        source = "Tensar"
    else:
        max_spacing = MAX_SPACING_CONSERVATIVE_MM
        source = "reference/ukendt"

    return {
        "min_top_cover_mm": max(MIN_TOP_COVER_MM, product_cover_mm),
        "general_top_cover_mm": MIN_TOP_COVER_MM,
        "product_cover_mm": product_cover_mm,
        "min_spacing_mm": MIN_GEONET_SPACING_MM,
        "max_spacing_mm": max_spacing,
        "source": source,
    }


def _top_cover_requirement_text(krav: dict) -> str:
    return f"Mindste dæklag for dette net er {krav['min_top_cover_mm']:.0f} mm."


def _positive_sub_layers(sub_lag: list[dict] | None) -> list[dict]:
    return [
        {
            "navn": lag.get("navn", "Lag"),
            "tykkelse_mm": float(lag.get("tykkelse_mm") or 0),
        }
        for lag in (sub_lag or [])
        if (lag.get("tykkelse_mm") or 0) > 0
    ]


def _upper_position_from_layers(
    total_mm: float,
    min_top_cover_mm: float,
    sub_lag: list[dict] | None,
) -> tuple[float, str]:
    """Return upper geonet depth from top and the placement basis."""
    layers = _positive_sub_layers(sub_lag)
    if len(layers) >= 2:
        return layers[0]["tykkelse_mm"], "materialeskift"
    return min(min_top_cover_mm, total_mm), "minimumsdæklag"


def check_geonet_placement(
    *,
    lag_mode: str,
    total_mm: float | None,
    geonet: dict | None = None,
    sub_lag: list[dict] | None = None,
) -> dict:
    """Check geonet layer placement for 1- or 2-layer reinforcement.

    Positions are returned as depths in mm from the top of the unbound bearing
    layer. The bottom geonet is therefore placed at ``total_mm``.
    """
    krav = placement_requirements(geonet)
    advarsler: list[str] = []
    total = float(total_mm or 0)

    if total <= 0 or lag_mode not in ("1_lag", "2_lag"):
        return {
            **krav,
            "placering_ok": True,
            "geonet_placeringer_mm_fra_top": [],
            "geonet_y_fracs": [],
            "topdaeklag_mm": None,
            "afstande_mellem_geonet_mm": [],
            "placeringsadvarsler": [],
            "t_min_placering_mm": None,
            "t_dimensionerende_mm": total_mm,
            "placeringsbasis": None,
        }

    min_cover = krav["min_top_cover_mm"]
    min_spacing = krav["min_spacing_mm"]
    max_spacing = krav["max_spacing_mm"]
    t_min = min_cover if lag_mode == "1_lag" else min_cover + min_spacing

    if lag_mode == "1_lag":
        positions = [total]
        top_cover = total
        distances: list[float] = []
        basis = "underbund"
        if top_cover < min_cover:
            advarsler.append(
                f"Geonettet har kun {top_cover:.0f} mm dæklag over sig. "
                f"{_top_cover_requirement_text(krav)}"
            )
    else:
        upper, basis = _upper_position_from_layers(total, min_cover, sub_lag)
        bottom = total
        positions = [upper, bottom]
        top_cover = upper
        spacing = bottom - upper
        distances = [spacing]

        if top_cover < min_cover:
            advarsler.append(
                f"Øverste geonet ligger {top_cover:.0f} mm under oversiden. "
                f"{_top_cover_requirement_text(krav)}"
            )
        if spacing < min_spacing:
            advarsler.append(
                f"Afstanden mellem geonetlagene er {spacing:.0f} mm. "
                f"Kravet er mindst {min_spacing:.0f} mm."
            )
        if spacing > max_spacing:
            advarsler.append(
                f"Afstanden mellem geonetlagene er {spacing:.0f} mm. "
                f"Kravet er højst {max_spacing:.0f} mm for {krav['source']}."
            )

    y_fracs = [
        max(0.0, min(1.0, p / total))
        for p in positions
        if total > 0
    ]

    return {
        **krav,
        "placering_ok": not advarsler,
        "geonet_placeringer_mm_fra_top": positions,
        "geonet_y_fracs": y_fracs,
        "topdaeklag_mm": top_cover,
        "afstande_mellem_geonet_mm": distances,
        "placeringsadvarsler": advarsler,
        "t_min_placering_mm": t_min,
        "t_dimensionerende_mm": max(total, t_min),
        "placeringsbasis": basis,
    }


def enrich_result_with_placement(
    resultat: dict,
    *,
    geonet: dict | None = None,
    sub_lag: list[dict] | None = None,
) -> dict:
    """Return a copy of a calculation/product result with placement fields."""
    if resultat.get("fejl") or resultat.get("t_armeret_mm") is None:
        return dict(resultat)
    placement = check_geonet_placement(
        lag_mode=resultat.get("lag_mode"),
        total_mm=resultat.get("t_armeret_mm"),
        geonet=geonet,
        sub_lag=sub_lag,
    )
    return {**resultat, **placement}
