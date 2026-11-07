"""Regression protection for the 15-outcome infographic's generated canvas.

The original mobile source allocated 5,200 pixels but cropped to 7,111 pixels,
silently filling missing canvas pixels with black. This test covers both variants.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from generate_ai_business_changes_15 import GROUPS, render, required_height

class AiBusinessChangesCanvasTests(unittest.TestCase):
    def test_fifteen_selected_outcomes(self):
        self.assertEqual(sum(len(group[5]) for group in GROUPS),15)
        self.assertEqual([int(item[0]) for group in GROUPS for item in group[5]],list(range(1,16)))

    def test_mobile_and_desktop_are_not_black_padded(self):
        for mobile in (True,False):
            with self.subTest(mobile=mobile):
                im=render(mobile)
                self.assertEqual(im.height,required_height(mobile))
                self.assertGreater(im.height,7000 if mobile else 3300)
                # The entire left/right canvas edges are intentional cream/navy,
                # never the pure black introduced by PIL cropping out of bounds.
                for y in range(im.height):
                    self.assertNotEqual(im.getpixel((0,y)),(0,0,0),f"Left black row {y}")
                    self.assertNotEqual(im.getpixel((im.width-1,y)),(0,0,0),f"Right black row {y}")
                self.assertNotEqual(im.getpixel((im.width//2,im.height-60)),(0,0,0))
if __name__=="__main__":
    unittest.main()
