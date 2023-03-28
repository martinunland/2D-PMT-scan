import unittest
from src.grids import Grid, CircularConstantDensity
from src.config import CircularConstantDensity_config

class TestCircularConstantDensity(unittest.TestCase):
    def setUp(self):
        cfg = CircularConstantDensity_config(r_max=41, r_step=1.25)
        self.grid = CircularConstantDensity(cfg)

    def test_make_grid(self):
        self.grid.make_grid()
        self.assertTrue(len(self.grid.grid_positions) > 0)

    def test_validate_grid(self):
        # Assuming you have a valid motors object
        motors = ...
        self.grid.make_grid()
        self.grid.validate_grid(motors)
        self.assertTrue(len(self.grid.valid_grid_positions) > 0)

if __name__ == "__main__":
    unittest.main()