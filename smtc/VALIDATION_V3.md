# Experimental V3 validation

V2 remains unchanged at baseline commit 5dd55a9. The seven original scalar sweep/MSS/FVG/lifecycle helper bodies are byte-identical in V3. The indicator and research strategy share byte-identical bodies for those seven helpers plus the new bias-step, net-R and quality helpers.

The complete V3 indicator passed third-party pynescript 0.3.0 grammar parsing. `python3 smtc/diagnostics_v3.py` passed 34 component tests (19 baseline plus 15 quality tests). The actual parsed scalar helper bodies are executed by the restricted evaluator; HTF/timeframe runtime and series behavior are not emulated. The research strategy's full-source grammar parse is a separate check. Plot/drawing execution, TradingView type checking, strategy orders, live replay, exact reproduction of supplied entries and performance are not verified by these checks.

No TradingView compilation, Strategy Tester run, trade count, win rate, profit factor or profitability result is claimed. The September/October screenshot examples were used for development and are not unseen validation. Read INVESTIGATION_V3.md for costs, fill assumptions, baseline equivalence limits and the comparison protocol.

Source SHA-256 hashes:

- SMTC_v3.pine: `4b6aaef1c8531a74544117d3bc7f2e5d2be4b1c31a32d820804e161aa216df8f`
- SMTC_research_strategy.pine: `918d750d1a0f203c65a770ea643f03fa9533f2432a11a81f4dcdbef15b380c67`

The final indicator and strategy sources both passed full grammar parsing. The final indicator AST was used for the 34-test run. Persistent obstacle arrays are cleared/reused on each confirmed bar to bound snapshot memory; snapshots remain immutable within the directional processing for that bar. Indicator/strategy short titles are within ten characters. Text copies match their Pine sources.
