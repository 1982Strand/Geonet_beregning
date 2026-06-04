import unittest

from core.placement import check_geonet_placement, placement_requirements


class PlacementTests(unittest.TestCase):
    def test_one_layer_cover_under_and_over_minimum(self):
        geonet = {"serie": "Tensar", "min_daklag": 20}

        under = check_geonet_placement(
            lag_mode="1_lag", total_mm=150, geonet=geonet
        )
        over = check_geonet_placement(
            lag_mode="1_lag", total_mm=250, geonet=geonet
        )

        self.assertFalse(under["placering_ok"])
        self.assertTrue(over["placering_ok"])

    def test_two_layers_at_200_cover_and_200_spacing_is_ok(self):
        geonet = {"serie": "Tensar", "min_daklag": 20}
        res = check_geonet_placement(
            lag_mode="2_lag",
            total_mm=400,
            geonet=geonet,
            sub_lag=[{"navn": "Top", "tykkelse_mm": 200}, {"navn": "Bund", "tykkelse_mm": 200}],
        )

        self.assertTrue(res["placering_ok"])
        self.assertEqual(res["topdaeklag_mm"], 200)
        self.assertEqual(res["afstande_mellem_geonet_mm"], [200])

    def test_tensar_spacing_above_400_warns(self):
        geonet = {"serie": "Tensar", "min_daklag": 20}
        res = check_geonet_placement(
            lag_mode="2_lag",
            total_mm=650,
            geonet=geonet,
            sub_lag=[{"navn": "Top", "tykkelse_mm": 200}, {"navn": "Bund", "tykkelse_mm": 450}],
        )

        self.assertFalse(res["placering_ok"])
        self.assertIn("højst 400", res["placeringsadvarsler"][0])

    def test_gs_grid_spacing_450_ok_and_550_warns(self):
        geonet = {"serie": "GS-GRID", "min_daklag": 20}

        ok = check_geonet_placement(
            lag_mode="2_lag",
            total_mm=650,
            geonet=geonet,
            sub_lag=[{"navn": "Top", "tykkelse_mm": 200}, {"navn": "Bund", "tykkelse_mm": 450}],
        )
        warn = check_geonet_placement(
            lag_mode="2_lag",
            total_mm=750,
            geonet=geonet,
            sub_lag=[{"navn": "Top", "tykkelse_mm": 200}, {"navn": "Bund", "tykkelse_mm": 550}],
        )

        self.assertTrue(ok["placering_ok"])
        self.assertFalse(warn["placering_ok"])
        self.assertIn("højst 500", warn["placeringsadvarsler"][0])

    def test_material_transition_above_200_warns(self):
        geonet = {"serie": "Tensar", "min_daklag": 20}
        res = check_geonet_placement(
            lag_mode="2_lag",
            total_mm=400,
            geonet=geonet,
            sub_lag=[{"navn": "Top", "tykkelse_mm": 150}, {"navn": "Bund", "tykkelse_mm": 250}],
        )

        self.assertFalse(res["placering_ok"])
        self.assertIn("Mindste dæklag for dette net er 200 mm", res["placeringsadvarsler"][0])

    def test_product_min_cover_can_be_stricter_than_200(self):
        geonet = {"serie": "GS-GRID", "min_daklag": 60}
        krav = placement_requirements(geonet)
        res = check_geonet_placement(
            lag_mode="1_lag", total_mm=500, geonet=geonet
        )

        self.assertEqual(krav["min_top_cover_mm"], 600)
        self.assertFalse(res["placering_ok"])


if __name__ == "__main__":
    unittest.main()
