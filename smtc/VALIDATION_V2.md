# V2 validation record

The final full source passed `pynescript 0.3.0` grammar parsing. `python3 smtc/diagnostics_v2.py` completed **19 tests, all passed**. It invoked the parser itself before executing the actual source helper ASTs; it did not test a separately copied transition model.

Covered scalar components: downtrend/unreclaimed attempts; inclusive reclaim deadlines; sweep without MSS; MSS without a gap; complete one-entry bullish sequence; bearish geometry; consumed and failed pools; same-bar sweep/MSS and FVG-entry prohibitions; wick-only/weak structure breaks; displacement body/range/close-position; penetration/reclaim geometry; FVG timing, range association and interrupted-sequence input; retest direction/midpoint/wick; full-fill/extreme invalidation; endpoint expiry; failed filter consumption; missing reference and terminal-state duplication.

Not executed: TradingView compiler/type checker, full Pine series semantics, real pivot confirmation, HTF/session integration, UDT orchestration, drawing queue runtime, chart-level scenarios A–F, live/replay comparison G, or backtesting. The source review and restricted helper evaluator do not replace those checks. Use the README acceptance checklist before relying on chart behavior.

No unintended tracked-file modifications occurred; this initially empty repository has new deliverables under `smtc/`. V1 is preserved outside the checkout at `/workspace/smtc-backup/SMTC_v1.pine`.

Final SMTC_v2.pine SHA-256: `b84765cf99b066554e0e349e1d4a468521063f5e2cf00e526acc4daef29ae5cd`.

SMTC.pine, SMTC.txt, SMTC_v2.txt and the workspace text copies are byte-identical to that source.
