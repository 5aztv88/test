# V2 validation record

The final full source passed `pynescript 0.3.0` grammar parsing. `python3 smtc/diagnostics_v2.py` completed **19 tests, all passed**. It invoked the parser itself before executing the actual source helper ASTs; it did not test a separately copied transition model.

Covered scalar components: downtrend/unreclaimed attempts; inclusive reclaim deadlines; sweep without MSS; MSS without a gap; complete one-entry bullish sequence; bearish geometry; consumed and failed pools; same-bar sweep/MSS and FVG-entry prohibitions; wick-only/weak structure breaks; displacement body/range/close-position; penetration/reclaim geometry; FVG timing, range association and interrupted-sequence input; retest direction/midpoint/wick; full-fill/extreme invalidation; endpoint expiry; failed filter consumption; missing reference and terminal-state duplication.

Not executed: TradingView compiler/type checker, full Pine series semantics, real pivot confirmation, HTF/session integration, UDT orchestration, drawing queue runtime, chart-level scenarios A–F, live/replay comparison G, or backtesting. The source review and restricted helper evaluator do not replace those checks. Use the README acceptance checklist before relying on chart behavior.

No unintended tracked-file modifications occurred; this initially empty repository has new deliverables under `smtc/`. V1 is preserved outside the checkout at `/workspace/smtc-backup/SMTC_v1.pine`.

Final SMTC_v2.pine SHA-256: `1b674ec5a8451b0e6500ee2fd509629e27a8c9a1d3fe92d9544a982081508c88`.

SMTC.pine, SMTC.txt, SMTC_v2.txt and the workspace text copies are byte-identical to that source.

TradingView reported CE10150 for the reserved `text` parameter in `f_label`. Renamed that parameter and its reference to `caption` in every Pine/text copy. Local grammar/helper checks cannot establish TradingView compiler acceptance; further compiler errors remain possible.

Full-history update: full-source grammar parsing and all 19 existing scalar diagnostics passed again. A source comparison confirmed all seven detection/lifecycle helper bodies are unchanged. Entry markers now use historical plots in both modes; default full-history mode also plots sweep/MSS/CHoCH/triple events and retains expired/mitigated rectangles. Object queues are bounded at TradingView's 500-per-type capacity. Compact group eviction is disabled by default. Releasing finished processing metadata does not delete its drawings. There are 19 plot calls and 8 alert conditions; the nominal plot count is below Pine's 64-count limit. Chart rendering, capacity turnover, full-history replay behavior, and TradingView compilation of this update remain unverified.
