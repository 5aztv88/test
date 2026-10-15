# Signal-quality investigation and experimental V3

## Conclusion

The screenshots motivate testing trend-context and reward-clearance checks. They do not establish an improved win rate, profitability, or an optimal parameter set. The user confirmed the examples are actual BUY/SELL entries using default settings; this report treats them as reported losing entries, not merely misread stage markers.

V2 remains unchanged as the baseline. `SMTC_v3.pine` / `SMTC_v3.txt` contain a separate experimental indicator, and `SMTC_research_strategy.pine` / `.txt` provide a TradingView Strategy Tester comparison. Do not interpret these files as a validated upgrade or a recommendation to trade live.

## Screenshot observations

| Example | Observable context | What it suggests testing | What the image cannot prove |
|---|---|---|---|
| EUR/USD H1 decline and bullish setup | Broad visible sequence of declining prices, followed by a relatively small bullish bounce | Reject countertrend entries; invalidate stale higher-timeframe bias; check entry distance from the FVG | H4 structure at the exact entry, actual SL/TP prices, which filter version ran, or stop/target execution order |
| EUR/USD M15 bearish setup before an upward expansion | Local bearish reversal inside a wider upward move; price initially moves down before rallying | Avoid fading an aligned bullish regime; require realistic target room | Whether the initial decline reached TP1/TP2 before the subsequent rally. A later rally alone does not prove a losing short |
| EUR/USD M15 with several bullish setups | Choppy/ranging sections, abrupt volatility, and repeated local reversals | Neutralize mixed structure; separate candidate events from actual entries; reject trades near tracked opposing levels | The performance of every entry, exact filter settings at each entry, or whether a news release caused the volatility |

Crosshair timestamps are not automatically the marked entry timestamps. The screenshots' displayed last quote is also not necessarily the historical entry price. No exact trade price or timestamp was reconstructed from pixels. The displayed feed is ICE; a different Forex feed can have different pivots/FVGs.

## Findings in the actual V2 source

1. **HTF bias can remain stale.** `f_htfStructure()` compares the last two confirmed highs/lows, without invalidating an existing bullish bias when a completed HTF candle closes below its protected low. Pivot confirmation can lag that break. The same applies to bearish bias.
2. **Fixed-R filtering is largely arithmetic.** Fixed mode sets TP2 at entry ± stop distance × target R, then checks that calculated R. It does not establish enough room before opposing structure and ignores spread/fees/slippage in that planning calculation.
3. **MSS is deliberately internal.** A displaced break of a small internal pivot after a sweep is not proof that a larger downtrend/uptrend has reversed. V2's optional chart EMA filter defaults off and has no slope requirement. This is a strategy-context weakness, not proof of a future-data bug.
4. **Late rejection closes can degrade entry location.** V2 requires a zone touch and directional midpoint/wick rejection but does not limit how far the final close has moved past the entry-side FVG edge.
5. **Stage markers are not entry signals.** Colored SSL/BSL/MSS/Triple markers are intentionally produced before final entry filters pass. They remain useful diagnostics, but cannot be used as a count of executed trades. This distinction does not dismiss the user's confirmed examples of actual entries.
6. **The H1 default configuration does not match a running current V2 instance.** Current V2 defaults to enabled H1 bias, with an explicit runtime guard requiring bias TF > chart TF. It should therefore stop on an H1 chart under all current defaults. The screenshots cannot establish which saved source/inputs ran. V3 displays a distinct version name and its effective HTF to make configuration auditable.

## Implemented V3 candidate solution

### A. Invalidate broken/mixed HTF structure

Track a protected confirmed HTF low for bullish structure, or high for bearish structure. A completed HTF close strictly through that level makes bias Neutral immediately. Mixed confirmed pivot structure also neutralizes an active bias.

After neutralization, both high and low pivot CONFIRMATION timestamps must be newer than the reset bar before a qualifying HH+HL / LH+LL pair can restore direction. A price rebound alone cannot rearm the old pair. This is a conservative hypothesis and can delay valid reversals. It does not require both pivot ORIGINS to be after the reset.

All outputs are offset one closed HTF bar before `lookahead_on` distributes them. No forming HTF candle affects confirmed entries. The scalar state-transition helper is testable, but actual `request.security` integration still needs TradingView validation.

Auto HTF defaults on: at least H1, otherwise approximately 4× chart timeframe using TradingView's supported conversion. For the target charts it gives M5/M15 → H1 and H1 → H4. Manual override remains available. Unsupported/non-time-based or extremely high chart intervals require explicit validation and a strictly higher available manual TF or disabled HTF filter.

### B. Require chart-trend alignment

Default BUY requires the chart close above the selected EMA and that EMA above its value three bars earlier. SELL requires the inverse. EMA length defaults to 50, with 200 still selectable. This is an additional filter, independent of the legacy chart EMA toggle, and is enabled by the V3 quality control.

The purpose is to stop buying a small bounce below a declining chart EMA or selling a dip above a rising one. It can reject profitable early reversals and is not guaranteed to improve expectancy. It is a regime constraint, not a change to the original sweep/MSS/FVG ordering.

### C. Check actual tracked target clearance in BOTH target modes

Before either directional sweep loop modifies liquidity status, snapshot the previously available eligible primary levels, latest previously known internal opposing swing, and closed-HTF high/low. These are candidate obstacles; select the closest one ahead of the entry close. Include obstacles that an entry candle wick crosses but closes back behind. The immutable snapshot avoids direction-loop ordering effects.

This is the nearest **tracked** obstacle, not an exhaustive map of resistance/support, order flow or all historical internal pivots. Some price levels may be untracked, aged out, previously consumed, or absent from loaded data. A missing obstacle rejects headroom validation by default rather than inventing room.

Place a 0.05 ATR target buffer before that obstacle. Require enough estimated reward after costs and reject a Fixed-R TP2 beyond the buffered obstacle. Do not skip the nearest obstacle to choose a convenient farther one. Opposing-liquidity mode also uses the buffered nearest obstacle.

V3 defaults to Fixed RR to avoid automatically replacing a 2R baseline target with a much farther liquidity target. Its fixed target R and minimum R are explicitly **estimated net R**, unlike V2's gross R. For stop distance D, target distance P and an estimated round-trip price cost C:

`net R = (P - C) / (D + C)`

A desired fixed net R requires `P = desired R × (D + C) + C`. This makes the planned target farther than 2 gross R when costs are positive, and can reduce target hit rate. The headroom gate prevents that farther target from being placed through a nearer tracked obstacle. It is not a promise of attainable or realized R.

Default planning cost is 10 ticks total round trip: approximately 1 pip ONLY on a 5-digit EUR/USD feed. Check `syminfo.mintick`, broker spread, commissions and slippage; adjust the input. This is a fixed cost estimate, not observed bid/ask execution. Actual next-bar fills and gaps can change realized risk/reward.

### D. Reject chased entries

Reject BUY closes more than 0.25 ATR above the FVG top, and SELL closes more than 0.25 ATR below its bottom. A close inside the gap's expected half has zero chase distance. Keep the original later-bar retest, directional rejection and wick checks. The 0.25 threshold is an initial research value, not optimized.

An optional maximum stop-distance filter is provided at 2 ATR, OFF by default so it can be tested separately. Structural stops are not pulled inward to manufacture a better ratio.

### E. Make diagnostics explicit and keep history

Full loaded signal history and maximum drawing capacities are inherited from V2. V2 files are not replaced. V3 marks actual entries `BUY ENTRY` / `SELL ENTRY`; default stage captions explicitly say `Watch: ...` and `Setup: Triple`. Candidate events remain visible even if entry is filtered; the solution does not conceal failed setups.

The expanded dashboard includes effective HTF, protected HTF level, latest attempted-entry net R / obstacle room R, and the check result with setup ID. These fields describe the latest ATTEMPT, which may be filtered, not necessarily the last executed entry. The existing last-entry advisory status is not a broker position record.

## How to compare performance instead of fitting screenshots

1. Add `SMTC_research_strategy.pine` in a NEW Pine Editor strategy tab. Compile before use. Keep the same ICE EUR/USD feed, chart timeframe, loaded history, sessions, pivots and risk parameters in both runs.
2. Its Variant input selects **V2-equivalent fixed-R baseline** or **V3 quality**. The baseline turns off protected-bias invalidation and new quality gates, uses legacy closed-HTF pivot pair bias, and plans gross fixed R with zero costs in the SIGNAL filter, as V2 did. Simulator costs still apply to BOTH variants. Both use the same automatic/manual HTF selection; matching V2 on H1 requires manually setting V2 to H4. This comparison is fixed-R only, not a reproduction of V2's opposing-liquidity target mode. Exact full-runtime parity remains unverified.
3. The strategy uses next-bar-open market orders, one open position, no pyramiding, and full SL/TP2 exits. TP1 remains advisory; there are no partial exits, breakeven or trailing stops. Signals while a position is open are untraded. The indicator continues to show all qualifying candidates, so candidate count and executed trade count can differ. The benchmark hides extra candidate-entry plots by default: use native Long/Short strategy arrows for actual simulated fills. Its optional candidate plots explicitly say BUY CAND / SELL CAND.
4. Fixed quantity defaults to 10,000 base units and initial USD capital 100,000; this is a comparison sizing convention, not a risk-percent recommendation. Default commission is USD 0.00005 per unit each side: about 1 pip round trip for 10,000-unit EUR/USD, PLUS one tick simulator slippage. Adjust Properties and the V3 planning-cost input together; the default 10-tick planning proxy does not exactly include the additional simulator slippage. Actual symbol contract specifications must be checked.
5. Stop and TP2 are frozen signal-time prices. Orders fill at the next bar's opening price under the tester model, not a guaranteed signal-close fill. Gaps can change actual entry risk/RR or cross brackets. The strategy does not revise a trade retroactively using the next opening price. Bars touching both SL and TP need intrabar inspection / Bar Magnifier where available. Commission-as-spread is a proxy; it does not model bid/ask trigger prices.
6. Compare the baseline against one change at a time. In V3 mode, first turn off the new quality switches and set planning cost to zero to assess approximate baseline parity. Then test protected HTF invalidation; then chart EMA alignment; then headroom/net-cost planning; then anti-chase; finally the optional stop cap. Save each run and its exact settings. Do not enable every stricter option and assume fewer trades means better performance.
7. Report closed trade count, gross and net expectancy, profit factor, average winner/loser, drawdown, costs and timeframe. Normalize per-trade results to their ACTUAL filled-entry-to-stop risk when studying expectancy in R; the tester's cash P&L with fixed quantity is not itself an R metric. Win rate alone is insufficient.
8. Use enough closed trades to assess uncertainty; around 100 or more is a useful initial goal, not statistical proof or a reason to change thresholds until that count appears. The supplied September/October examples are development data and cannot honestly serve as unseen validation. Freeze settings before testing a separate unseen period, then forward paper-test. Keep H1 and M15 results separate.

## Checks and remaining uncertainty

`python3 smtc/diagnostics_v3.py` parses the complete V3 indicator and runs the existing 19 lifecycle/geometry tests plus 15 new scalar checks: stale bias breaking, neutral restoration rules, mixed structure, cost-adjusted R, missing/near targets, Fixed-R target clearance, symmetric valid trades, chase distance, oversized stops and invalid risk. The helper AST evaluator does not execute chart pivots, HTF requests, EMA series, UDT orchestration, strategy fills or plots. Strategy grammar parsing is separate.

TradingView compilation, chart-level integration, screenshot reproduction, Strategy Tester execution, live/replay agreement and performance improvement are UNVERIFIED. A local passing suite establishes component behavior only. No backtest statistics were fabricated or inferred from chart images. Losing trades remain possible and some good V2 entries will be filtered by V3.
