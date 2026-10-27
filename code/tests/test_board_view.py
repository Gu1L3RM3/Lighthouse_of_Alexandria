import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pygame import Rect

from core.ui.board_view import BoardView

CELL = 64
ORIGIN = (0, 128)
# The circuits use 20 columns and reach y = 768, so the board needs 20 x 10 cells.
COLS, MIN_ROWS = 20, 10
WEB_FREE_AREA = Rect(0, 128, 1142, 592)       # 1280x720 left of the sidebar, below the top bar
DESKTOP_FREE_AREA = Rect(0, 128, 1768, 952)   # 1920x1080


def board(area):
    return BoardView(ORIGIN, CELL, COLS, MIN_ROWS, area)


class BoardViewTest(unittest.TestCase):
    def test_board_shrinks_to_whole_pixel_cells_when_the_screen_is_small(self):
        view = board(WEB_FREE_AREA)
        self.assertEqual(view.cell_on_screen, 57)
        self.assertEqual(view.screen_rect, Rect(0, 128, 57 * COLS, 57 * MIN_ROWS))

    def test_whole_board_fits_left_of_the_sidebar(self):
        self.assertLessEqual(board(WEB_FREE_AREA).screen_rect.right, WEB_FREE_AREA.right)

    def test_large_screens_keep_the_original_size_and_extra_rows(self):
        view = board(DESKTOP_FREE_AREA)
        self.assertEqual(view.scale, 1.0)
        self.assertEqual(view.rows, 14)

    def test_screen_point_maps_back_to_its_board_cell(self):
        view = board(WEB_FREE_AREA)
        far_cell = Rect(1152, 384, CELL, CELL)
        on_screen = view.to_screen_rect(far_cell)
        self.assertTrue(far_cell.collidepoint(view.to_world(on_screen.center)))

    def test_board_cells_cover_every_column_and_row(self):
        cells = board(WEB_FREE_AREA).world_cells()
        self.assertEqual(len(cells), COLS * MIN_ROWS)
        self.assertIn(Rect(1152, 704, CELL, CELL), cells)

    def test_camera_offset_puts_the_board_origin_at_the_free_area(self):
        view = board(WEB_FREE_AREA)
        offset_x, offset_y = view.camera_offset
        self.assertEqual((round(ORIGIN[0] * view.scale + offset_x), round(ORIGIN[1] * view.scale + offset_y)), (0, 128))


if __name__ == "__main__":
    unittest.main()
