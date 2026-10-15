"""SMTC V3 component checks: NOT a Pine compiler, replay or backtest.

Reuse the V2 AST evaluator and its 19 baseline lifecycle tests. Extend only
scalar helper support for literal na and calls between scalar helpers.
The runtime-dependent global biasTf expression is deliberately excluded;
no timeframe, series, pivot or request.security behavior is simulated.
"""
from pathlib import Path
import argparse
import ast
import subprocess
import tempfile
import unittest
from diagnostics_v2 import Helpers, Diagnostics, decode

SOURCE = Path(__file__).with_name("SMTC_v3.pine")


class QualityHelpers(Helpers):
    def __init__(self, tree):
        filtered = dict(tree)
        filtered["body"] = [node for node in tree["body"] if not (
            node["kind"] == "Assign" and node["target"].get("id") == "biasTf")]
        super().__init__(filtered)

    def value(self, node, env):
        if node["kind"] == "Name" and node["id"] == "na":
            return None
        if node["kind"] == "Call" and node["func"]["kind"] == "Name":
            name = node["func"]["id"]
            values = [self.value(arg["value"], env) for arg in node["args"]]
            if name == "na":
                return self.globals["na"](*values)
            if name in self.functions:
                return self.call(name, *values)
        return super().value(node, env)


class QualityDiagnostics(unittest.TestCase):
    helpers: QualityHelpers

    def test_broken_bullish_bias_neutralizes_without_waiting_for_new_pivot(self):
        self.assertEqual(self.helpers.call("f_biasStep", 1, -1, 100, 99, 1, 90, 95, 100, 110, 100), (0, 100, None))

    def test_broken_bearish_bias_neutralizes(self):
        self.assertEqual(self.helpers.call("f_biasStep", -1, -1, 110, 111, -1, 90, 95, 100, 110, 100), (0, 100, None))

    def test_price_rebound_does_not_rearm_stale_structure(self):
        self.assertEqual(self.helpers.call("f_biasStep", 0, 100, None, 105, 1, 90, 95, 101, 110, 100)[0], 0)

    def test_only_one_new_pivot_is_insufficient_to_rearm(self):
        self.assertEqual(self.helpers.call("f_biasStep", 0, 100, None, 105, 1, 110, 95, 120, 110, 100)[0], 0)

    def test_fresh_pair_restores_valid_bias_and_protected_level(self):
        self.assertEqual(self.helpers.call("f_biasStep", 0, 100, None, 105, 1, 110, 115, 120, 110, 100), (1, 100, 100))
        self.assertEqual(self.helpers.call("f_biasStep", 0, 100, None, 105, -1, 110, 115, 120, 110, 100), (-1, 100, 110))

    def test_new_pair_already_broken_cannot_activate(self):
        self.assertEqual(self.helpers.call("f_biasStep", 0, 100, None, 99, 1, 110, 115, 120, 110, 100)[0], 0)

    def test_mixed_structure_neutralizes_active_bias(self):
        self.assertEqual(self.helpers.call("f_biasStep", 1, -1, 100, 105, 0, 110, 115, 120, 110, 100), (0, 120, None))

    def test_costs_reduce_the_actual_reward_to_risk(self):
        self.assertEqual(self.helpers.call("f_netR", 1, 100, 99, 102, 0), 2)
        self.assertAlmostEqual(self.helpers.call("f_netR", 1, 100, 99, 102, 0.1), 1.9 / 1.1)
        self.assertAlmostEqual(self.helpers.call("f_netR", -1, 100, 101, 98, 0.1), 1.9 / 1.1)

    def test_nearby_obstacle_blocks_insufficient_reward(self):
        target, net, room, chase, stop, valid, clear = self.helpers.call("f_quality", 1, 100, 99, 101.5, 100.1, 99.8, 1, 0.1, targetMode="Opposing liquidity")
        self.assertAlmostEqual(target, 101.45)
        self.assertLess(net, 2)
        self.assertFalse(valid)
        self.assertFalse(clear)

    def test_fixed_R_cannot_bypass_a_nearer_obstacle(self):
        target, net, room, chase, stop, valid, clear = self.helpers.call("f_quality", 1, 100, 99, 101.5, 100.1, 99.8, 1, 0.1, targetMode="Fixed RR")
        self.assertAlmostEqual(target, 102.3)
        self.assertAlmostEqual(net, 2)
        self.assertTrue(valid)
        self.assertFalse(clear)

    def test_valid_bullish_and_bearish_geometry(self):
        bull = self.helpers.call("f_quality", 1, 100.95, 100, 104, 101, 100.8, 1, 0.05)
        bear = self.helpers.call("f_quality", -1, 99.05, 100, 96, 99.2, 99, 1, 0.05)
        self.assertTrue(all(bull[3:]))
        self.assertTrue(all(bear[3:]))
        self.assertAlmostEqual(bull[1], bear[1])

    def test_chased_entry_fails_even_with_room_for_target(self):
        result = self.helpers.call("f_quality", 1, 102, 101, 106, 101, 100.8, 1, 0.05)
        self.assertFalse(result[3])
        self.assertTrue(result[5] and result[6])

    def test_oversized_stop_is_reported(self):
        result = self.helpers.call("f_quality", 1, 100, 97, 110, 100.1, 99.8, 1, 0.05)
        self.assertFalse(result[4])
        self.assertTrue(result[5])

    def test_missing_obstacle_has_no_fabricated_target(self):
        result = self.helpers.call("f_quality", 1, 100, 99, None, 100.1, 99.8, 1, 0.05, targetMode="Opposing liquidity")
        self.assertIsNone(result[0])
        self.assertFalse(result[5] or result[6])

    def test_zero_or_negative_risk_is_rejected(self):
        for stop in (100, 101):
            result = self.helpers.call("f_quality", 1, 100, stop, 105, 100.1, 99.8, 1, 0.05)
            self.assertFalse(result[5])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ast", type=Path)
    args = parser.parse_args()
    dump = args.ast or Path(tempfile.gettempdir()) / "smtc-v3-diagnostics-ast.txt"
    if args.ast:
        if dump.stat().st_mtime < SOURCE.stat().st_mtime:
            raise SystemExit("AST is older than source; reparse.")
    else:
        subprocess.run(["/workspace/smtc-tools/bin/pynescript", "parse-and-dump", str(SOURCE), "--output-file", str(dump)], check=True)
    tree = decode(ast.parse(dump.read_text(), mode="eval").body)
    helper = QualityHelpers(tree)
    Diagnostics.helpers = helper
    QualityDiagnostics.helpers = helper
    suite = unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromTestCase(Diagnostics),
        unittest.defaultTestLoader.loadTestsFromTestCase(QualityDiagnostics)])
    print("V3 component checks only. TradingView compilation, integration and performance are UNVERIFIED.", flush=True)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
