import logging
import unittest
from src.helper import add_spam_log_level
from src.data_analysis import PulseModeAnalysisWrapper, CurrentModeAnalysis
from src.config import PicoscopeConfig, PicoamperemeterConfig

add_spam_log_level()
log = logging.getLogger(__name__)

class TestPulseModeAnalysis(unittest.TestCase):
    def setUp(self):
        cfg = PicoscopeConfig(
            primary_channel="A",
            reference_channel="B",
            sampling_interval=0.8e-9,
            baseline_tmin=0,
            baseline_tmax=30,
            reference_baseline_tmin=0,
            reference_baseline_tmax=30,
            reference_signal_tmin=60,
            reference_signal_tmax=90,
        )
        self.analyser = PulseModeAnalysisWrapper(cfg)

    def test_update_time_axis(self):
        block = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.analyser.update_time_axis(block)
        self.assertEqual(len(self.analyser.time_axis), len(block))

    def test_append_data(self):
        block = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.analyser.append_data(block)
        self.assertEqual(len(self.analyser.data), 1)


class TestCurrentModeAnalysis(unittest.TestCase):
    def setUp(self):
        cfg = PicoamperemeterConfig(COM="COM13", count_per_read=10, primary_channel=0, reference_channel=1)
        self.analyser = CurrentModeAnalysis(cfg)

    def test_append_data(self):
        block = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        self.analyser.append_data(block)
        self.assertEqual(len(self.analyser.data), 1)


if __name__ == "__main__":
    unittest.main()
