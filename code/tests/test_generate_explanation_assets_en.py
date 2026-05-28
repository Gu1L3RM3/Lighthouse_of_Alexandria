import sys
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from utils.generate_explanation_assets_en import W, compute_step_boxes_layout


class GenerateExplanationAssetsEnTest(unittest.TestCase):
    def setUp(self):
        self.image = Image.new("RGB", (1280, 720), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.steps = [
            "Read the target and identify the requested quantity.",
            "Collect the known values from the circuit.",
            "Choose the right method for the stage.",
            "Calculate and compare with the panel.",
            "Adjust the circuit and validate again.",
        ]

    def test_compute_step_boxes_layout_centers_boxes_horizontally(self):
        layout = compute_step_boxes_layout(self.draw, self.steps)

        self.assertEqual(layout["x1"], (W - layout["box_width"]) // 2)
        self.assertEqual(layout["x2"], layout["x1"] + layout["box_width"])
        self.assertGreaterEqual(layout["box_width"], 1000)

    def test_compute_step_boxes_layout_centers_stack_in_available_area(self):
        layout = compute_step_boxes_layout(
            self.draw,
            self.steps,
            body_top=170,
            body_bottom=660,
        )

        top_margin = layout["boxes"][0]["y1"] - 170
        bottom_margin = 660 - layout["boxes"][-1]["y2"]

        self.assertGreaterEqual(top_margin, 0)
        self.assertGreaterEqual(bottom_margin, 0)
        self.assertLessEqual(abs(top_margin - bottom_margin), layout["gap"] + 4)


if __name__ == "__main__":
    unittest.main()
