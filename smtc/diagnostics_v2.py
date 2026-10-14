"""Execute SMTC V2's parsed scalar Pine helpers for synthetic diagnostics.

This is a restricted AST evaluator, NOT TradingView/Pine runtime emulation.
It tests the actual helper bodies, not a separately copied state machine.
It does not execute request.security, pivots, UDT orchestration, drawings,
alerts, realtime rollback, or broker feeds. Those require TradingView.
"""
from __future__ import annotations
import argparse
import ast
import math
import operator
from pathlib import Path
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).with_name("SMTC_v2.pine")


def decode(node):
    """Read the grammar parser's AST dump as data, without eval/exec."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple)):
        return [decode(value) for value in node.elts]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -decode(node.operand)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return {"kind": node.func.id, **{key.arg: decode(key.value) for key in node.keywords}}
    raise ValueError(f"Unsupported dump data: {ast.dump(node)}")


class Helpers:
    def __init__(self, tree):
        self.functions = {item["name"]: item for item in tree["body"] if item["kind"] == "FunctionDef"}
        self.globals = {"math": {"abs": abs, "min": min, "max": max},
                        "syminfo": {"mintick": 0.00001}, "na": lambda value: value is None or (isinstance(value, float) and math.isnan(value))}
        # Load constants and input defaults from the actual source AST.
        for item in tree["body"]:
            if item["kind"] != "Assign" or item["target"]["kind"] != "Name":
                continue
            value = item.get("value", {})
            name = item["target"]["id"]
            if value.get("kind") == "Constant":
                self.globals[name] = value["value"]
            elif value.get("kind") == "Conditional":
                self.globals[name] = self.value(value, self.globals)
            elif value.get("kind") == "Call":
                function = value["func"]
                if function["kind"] == "Attribute" and function["value"].get("id") == "input":
                    first = value["args"][0]["value"]
                    if first["kind"] == "Constant":
                        self.globals[name] = first["value"]

    def call(self, name, *args, **overrides):
        function = self.functions[name]
        if len(args) != len(function["args"]):
            raise ValueError(f"{name}: argument count mismatch")
        env = {**self.globals, **overrides}
        env.update({param["name"]: value for param, value in zip(function["args"], args)})
        return self.block(function["body"], env)

    def block(self, statements, env):
        result = None
        for statement in statements:
            result = self.value(statement, env)
        return result

    def value(self, node, env):
        kind = node["kind"]
        if kind == "Constant":
            return node["value"]
        if kind == "Name":
            return env[node["id"]]
        if kind == "Attribute":
            return self.value(node["value"], env)[node["attr"]]
        if kind in ("Tuple", "List"):
            return tuple(self.value(item, env) for item in node["elts"])
        if kind == "Expr":
            return self.value(node["value"], env)
        if kind in ("Assign", "ReAssign"):
            assert node["target"]["kind"] == "Name"
            result = self.value(node["value"], env)
            env[node["target"]["id"]] = result
            return result
        if kind == "Conditional":
            branch = "body" if self.value(node["test"], env) else "orelse"
            return self.value(node[branch], env)
        if kind == "If":
            branch = "body" if self.value(node["test"], env) else "orelse"
            return self.block(node.get(branch) or [], env)
        if kind == "BoolOp":
            if node["op"]["kind"] == "And":
                return all(self.value(item, env) for item in node["values"])
            if node["op"]["kind"] == "Or":
                return any(self.value(item, env) for item in node["values"])
            raise ValueError(kind)
        if kind == "UnaryOp":
            op = {"Not": operator.not_, "USub": operator.neg, "UAdd": operator.pos}[node["op"]["kind"]]
            return op(self.value(node["operand"], env))
        if kind == "BinOp":
            op = {"Add": operator.add, "Sub": operator.sub, "Mult": operator.mul, "Div": operator.truediv}[node["op"]["kind"]]
            return op(self.value(node["left"], env), self.value(node["right"], env))
        if kind == "Compare":
            left = self.value(node["left"], env)
            for op_node, right_node in zip(node["ops"], node["comparators"]):
                right = self.value(right_node, env)
                op = {"Eq": operator.eq, "NotEq": operator.ne, "Gt": operator.gt,
                      "GtE": operator.ge, "Lt": operator.lt, "LtE": operator.le}[op_node["kind"]]
                if not op(left, right):
                    return False
                left = right
            return True
        if kind == "Call":
            function = self.value(node["func"], env)
            args = [self.value(arg["value"], env) for arg in node["args"]]
            return function(*args)
        raise ValueError(f"Unsupported helper node {kind}")


class Diagnostics(unittest.TestCase):
    helpers: Helpers

    def step(self, stage, **values):
        inputs = dict(pendingAge=0, sweepAge=1, mssAge=0, gapAge=1,
                      reclaim=False, referenceOk=True, invalid=False, fullFill=False,
                      cross=False, displaced=False, gap=False, touch=False,
                      rejection=False, filters=True)
        inputs.update(values)
        return self.helpers.call("f_transition", stage, *inputs.values())

    def test_A_downtrend_without_reclaims(self):
        # Many newly confirmed levels can break in a trend; no reclaim means
        # zero confirmed sweeps and zero entries across all attempts.
        sweeps = entries = 0
        for _ in range(20):
            state = 1
            for age in range(3):
                result = self.step(state, pendingAge=age, reclaim=False)
                state = result[0]
                sweeps += result[1]
                entries += result[4]
            self.assertEqual(state, 7)
        self.assertEqual((sweeps, entries), (0, 0))

    def test_B_false_sweep_and_window_endpoints(self):
        result = self.step(1, pendingAge=2, reclaim=True)
        self.assertEqual(result[0], 7)
        self.assertFalse(result[1])
        last_allowed = self.step(1, pendingAge=1, reclaim=True)
        self.assertEqual(last_allowed[:3], (2, True, False))

    def test_C_sweep_without_MSS(self):
        result = self.step(1, reclaim=True)
        self.assertTrue(result[1])
        self.assertEqual(result[0], 2)
        for age in range(1, 11):
            result = self.step(2, sweepAge=age, gap=True, touch=True, rejection=True)
            self.assertEqual(result[0], 2)
            self.assertFalse(result[3] or result[4])
        self.assertEqual(self.step(2, sweepAge=11)[0], 7)

    def test_D_MSS_without_qualifying_FVG(self):
        result = self.step(2, cross=True, displaced=True, gap=False)
        self.assertEqual(result[:5], (3, False, True, False, False))
        self.assertEqual(self.step(3, mssAge=3)[0], 7)
        self.assertFalse(self.helpers.call("f_gap", 1, 100, 99, 101, 100.1, 1))
        self.assertFalse(self.helpers.call("f_gap", -1, 100, 99, 99.1, 98, 1))

    def test_E_complete_bullish_setup_one_entry(self):
        self.assertTrue(self.helpers.call("f_displaced", 1, 100.6, 101.8, 100.5, 101.7, 1))
        self.assertTrue(self.helpers.call("f_gap", 1, 100.9, 100.0, 102.1, 101.2, 1))
        rejection = self.helpers.call("f_rejection", 1, 101.3, 101.55, 101.05, 101.5, 1, 101.2, 100.9)
        self.assertTrue(rejection)
        state = self.step(1, reclaim=True)[0]
        state = self.step(state, cross=True, displaced=True)[0]
        formed = self.step(state, mssAge=1, gap=True, touch=True, rejection=True)
        self.assertEqual(formed[0], 5)
        self.assertTrue(formed[3])
        self.assertFalse(formed[4])
        birth = self.step(5, gapAge=0, touch=True, rejection=True)
        self.assertFalse(birth[4])
        entry = self.step(5, gapAge=1, touch=True, rejection=rejection)
        self.assertEqual(entry[0], 6)
        self.assertTrue(entry[4])
        for _ in range(5):
            self.assertFalse(self.step(6, touch=True, rejection=True, gap=True)[4])

    def test_F_consumed_and_failed_pools_never_rearm(self):
        call = self.helpers.call
        pending = call("f_poolState", 0, True, False, False)
        self.assertEqual(pending, 1)
        swept = call("f_poolState", pending, False, True, False)
        retired = call("f_poolState", pending, False, False, True)
        self.assertEqual((swept, retired), (2, 3))
        for _ in range(20):
            swept = call("f_poolState", swept, True, True, False)
            retired = call("f_poolState", retired, True, False, False)
        self.assertEqual((swept, retired), (2, 3))

    def test_reclaim_geometry_penetration_and_direction(self):
        call = self.helpers.call
        self.assertTrue(call("f_reclaimed", 1, 100, 99.875, 100.1, 1.25))
        self.assertTrue(call("f_reclaimed", -1, 100, 100.125, 99.9, 1.25))
        self.assertFalse(call("f_reclaimed", 1, 100, 99.99, 100.1, 1.25))
        self.assertFalse(call("f_reclaimed", 1, 100, 99.8, 99.9, 1.25))
        self.assertFalse(call("f_reclaimed", 1, 100, 99.8, 100, 1.25))
        self.assertFalse(call("f_reclaimed", -1, 100, 100.01, 99.9, 1.25))

    def test_FVG_association_timing_and_connected_range(self):
        call = self.helpers.call
        args = (1, 13, 10, 12, 102, 100.5, 102, 100.5, 101, True)
        self.assertTrue(call("f_associated", *args))  # MSS middle candle
        self.assertTrue(call("f_associated", 1, 12, 10, 12, 102, 100.5, 102, 100.5, 101, True))
        self.assertFalse(call("f_associated", 1, 12, 10, 12, 102, 100.5, 102, 100.5, 101, True, sameBarFvg=False))
        self.assertFalse(call("f_associated", 1, 10, 11, 10, 102, 100.5, 102, 100.5, 101, True))
        self.assertFalse(call("f_associated", 1, 15, 10, 12, 102, 100.5, 102, 100.5, 101, True))
        self.assertFalse(call("f_associated", 1, 13, 10, 12, 105, 104, 102, 100.5, 101, True))
        self.assertFalse(call("f_associated", 1, 13, 10, 12, 100.8, 100.5, 102, 100.5, 101, True))
        self.assertFalse(call("f_associated", *args[:-1], False))
        self.assertTrue(call("f_associated", -1, 13, 10, 12, 99.5, 98.2, 99.5, 98.2, 99, True))

    def test_same_bar_MSS_FVG_cannot_enter(self):
        result = self.step(2, cross=True, displaced=True, gap=True, touch=True, rejection=True)
        self.assertEqual(result[:5], (5, False, True, True, False))

    def test_same_bar_sweep_MSS_is_blocked(self):
        result = self.step(1, reclaim=True, cross=True, displaced=True, gap=True)
        self.assertEqual(result[:5], (2, True, False, False, False))
        self.assertFalse(self.step(2, sweepAge=0, cross=True, displaced=True)[2])

    def test_wick_only_or_weak_close_break(self):
        self.assertFalse(self.step(2, cross=False, displaced=True)[2])
        weak = self.step(2, cross=True, displaced=False, gap=True)
        self.assertEqual(weak[0], 8)
        self.assertFalse(weak[2] or weak[3] or weak[4])

    def test_displacement_rejects_doji_small_body_and_weak_close(self):
        call = self.helpers.call
        self.assertFalse(call("f_displaced", 1, 100, 100, 100, 100, 1))
        self.assertFalse(call("f_displaced", 1, 100, 100.4, 99.9, 100.3, 1))
        self.assertFalse(call("f_displaced", 1, 100, 101.8, 99.9, 100.7, 1))
        self.assertFalse(call("f_displaced", 1, 101, 101.1, 99.9, 100, 1))
        self.assertFalse(call("f_displaced", 1, 100, 101.2, 99.9, 101, None))

    def test_bearish_geometry_is_symmetric(self):
        self.assertTrue(self.helpers.call("f_displaced", -1, 99.4, 99.5, 98.2, 98.3, 1))
        self.assertTrue(self.helpers.call("f_gap", -1, 100, 99.1, 98.8, 97.9, 1))
        self.assertTrue(self.helpers.call("f_rejection", -1, 98.7, 98.95, 98.45, 98.5, 1, 99.1, 98.8))

    def test_retest_requires_midpoint_direction_and_wick(self):
        call = self.helpers.call
        self.assertFalse(call("f_rejection", 1, 101.3, 101.55, 101.3, 101.5, 1, 101.4, 100.9))
        self.assertFalse(call("f_rejection", 1, 101.2, 101.4, 101.0, 101.1, 1, 101.3, 100.9))
        self.assertFalse(call("f_rejection", 1, 100.91, 101.2, 100.90, 100.99, 1, 101.2, 100.9))
        self.assertFalse(call("f_rejection", 1, 102, 102.5, 101.9, 102.3, 1, 101.2, 100.9))

    def test_full_fill_and_extreme_break_override_entry(self):
        for condition in ("invalid", "fullFill"):
            result = self.step(5, touch=True, rejection=True, **{condition: True})
            self.assertEqual(result[0], 8)
            self.assertFalse(result[4])

    def test_entry_retest_and_MSS_expiry_boundaries(self):
        self.assertTrue(self.step(5, gapAge=15, touch=True, rejection=True)[4])
        self.assertFalse(self.step(5, gapAge=16, touch=True, rejection=True)[4])
        self.assertTrue(self.step(2, sweepAge=10, cross=True, displaced=True)[2])
        self.assertFalse(self.step(2, sweepAge=11, cross=True, displaced=True)[2])
        self.assertTrue(self.step(3, mssAge=2, gap=True)[3])
        self.assertFalse(self.step(3, mssAge=3, gap=True)[3])

    def test_failed_filters_consume_entry(self):
        rejected = self.step(5, touch=True, rejection=True, filters=False)
        self.assertEqual(rejected[0], 8)
        self.assertFalse(rejected[4])
        self.assertFalse(self.step(rejected[0], touch=True, rejection=True, filters=True)[4])

    def test_missing_structure_reference_preserves_sweep_fact(self):
        result = self.step(1, reclaim=True, referenceOk=False)
        self.assertEqual(result[0], 8)
        self.assertTrue(result[1])
        self.assertFalse(result[2] or result[4])

    def test_idle_and_terminal_states_cannot_skip_sequence(self):
        for state in (0, 6, 7, 8):
            result = self.step(state, reclaim=True, cross=True, displaced=True, gap=True, touch=True, rejection=True)
            self.assertEqual(result[0], state)
            self.assertFalse(any(result[1:5]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ast", type=Path, help="Reuse a freshly generated full-source pynescript AST dump")
    args = parser.parse_args()
    if args.ast:
        dump = args.ast
        if dump.stat().st_mtime < SOURCE.stat().st_mtime:
            raise SystemExit("AST is older than source. Reparse before testing.")
    else:
        dump = Path(tempfile.gettempdir()) / "smtc-v2-diagnostics-ast.txt"
        subprocess.run(["/workspace/smtc-tools/bin/pynescript", "parse-and-dump", str(SOURCE), "--output-file", str(dump)], check=True)
    tree = decode(ast.parse(dump.read_text(), mode="eval").body)
    assert tree["kind"] == "Script"
    Diagnostics.helpers = Helpers(tree)
    print("Testing actual parsed scalar helpers only; TradingView runtime and replay remain UNVERIFIED.", flush=True)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Diagnostics)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
