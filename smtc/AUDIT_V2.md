# SMTC V1 audit and V2 corrections

This audit uses the latest available workspace SMTC source, including its chart-scale fix. A separately edited TradingView copy was not supplied. The V1 source was preserved at `/workspace/smtc-backup/SMTC_v1.pine`; V2 is a source revision, not a claimed TradingView-verified release.

## 1. Why V1 produced many sweep labels

Balanced used external pivots of 5 bars per side, minimum penetration 0.05 ATR, and a three-candle reclaim window. It did not restrict liquidity to internal pivots, but these external pivots were still more frequent and less significant than the requested 10-bar pivots. Every qualifying reclaim was labeled immediately, even when no later MSS or entry followed. Equal-level recognition did not require a major structural reversal. There were no previous-day/session priorities or unique setup IDs in the visible labels.

V2 changes the default underlying detection to external 10/internal 3, 0.10 ATR penetration, and a two-candle inclusive reclaim window. Previous-day and completed-session levels can take priority; internal liquidity requires BOTH Aggressive signal mode and its explicit toggle. Visibility is a separate later rule: default sweep markers are revealed only at MSS detection for primary liquidity. Hidden confirmed sweep events remain in a bounded event ledger and can issue early-stage alerts.

## 2. Did V1 classify ordinary continuation as sweeps?

It did not classify every lower low or higher high as a sweep. It required a pre-existing confirmed pool, a wick breach approached from the unswept side, minimum penetration, and a closing reclaim. An unreclaimed continuation break could not pass those rules. However, brief pullbacks through frequent small pivots inside a continuing trend could qualify as mathematically valid sweeps and clutter the chart even though they never produced a meaningful reversal. A sweep is not evidence of a profitable reversal.

V1 removed any wick-breached level immediately, including a failed sweep. This already discouraged duplicate crossings; it did not use a cooldown to rearm levels. V2 makes eligible, reserved, confirmed-swept, and retired-breakout states explicit. Confirmed sweeps permanently consume their level object; failed reservations are permanently retired. Only a genuinely new confirmed structural/day/session event can establish a fresh pool. Exact-price aliases do not duplicate an existing eligible object.

## 3. Were MSS and FVG correctly connected?

V1 used separate directional state machines, so a standalone FVG could not create a trade. It froze an internal reference at penetration, required a later closing cross, and bounded the post-MSS FVG window. This part was fundamentally connected, not three unrelated booleans.

Two weaknesses remained relative to V2's specification. First, freezing at penetration omitted a relevant pivot confirmed during the reclaim window; V2 freezes the latest confirmed internal opposing swing at sweep confirmation. Second, time plus overlap with the MSS range was a relatively loose FVG association. V2 additionally requires the pattern to start no earlier than the sweep confirmation bar, displacement in its middle candle, the requested 0.20 ATR minimum, a short association window, and an uninterrupted directional/progressing overlap sequence for later middle candles. MSS itself always requires displacement. A first closing cross that fails displacement invalidates its setup.

CHoCH in the latest V1 already required an opposing established external trend and a same-candle first closing cross of its frozen external swing. V2 retains that stronger definition; an internal MSS alone is not relabeled CHoCH.

## 4. Repainting or future information

The reviewed V1 used confirmed chart-bar processing, confirmed pivots, fixed references and offset HTF data. No future-data leak was found in that design. Floating markers are a scale/coordinate issue, not evidence of signal repainting. This was a source audit, not a TradingView replay comparison.

V2 keeps closed-bar processing and explicit bar-index/price anchoring. HTF bias now comes from confirmed HH+HL/LH+LL pivot sequences instead of EMA slope. Every output in that HTF request is offset one completed HTF bar before `lookahead_on` distributes it; `lookahead_on` is not used with current HTF data. Previous-day values are also offset. Pivot-origin coordinates and actual detection-bar coordinates remain separate. Default delayed sweep labels are placed at the later MSS detection bar, never retroactively on the sweep candle.

## 5. Stale dashboard information

V1 displayed persistent last-trade direction/price and persistent setup status strings. It lacked entry timestamp, entry outcome, and a distinction between historical and live advisory entries, so an old entry could look current.

V2 shows HTF structural bias, current direction(s), active stage/age, latest sweep/MSS levels, active gap, last entry/time, status and latest rejection. An entry calculated on historical bars or replay is Historical; only an entry produced on a realtime confirmed bar starts Active. Later closed bars mark SL touches Invalidated, TP2 touches Historical, and monitor expiry Historical. A bar hitting SL and TP2 is reported as order-unknown with conservative invalidation, not a fabricated trade result. Reloading the indicator cannot reconstruct whether a historical trade was actually placed.

## Validation boundary

The complete V2 source is parsed by the third-party `pynescript` grammar parser. Synthetic diagnostics execute the actual parsed scalar helper bodies for reclaim, displacement, FVG geometry/association, rejection, lifecycle transitions, and pool consumption. They do not execute TradingView's compiler, pivot engine, HTF requests, UDT orchestration, drawing system, alert delivery or realtime rollback. Compilation, chart-level tests A–F and live-versus-historical test G must still be run in TradingView. No backtest or profitability evidence exists.
