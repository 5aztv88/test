# Smart Money Triple Confirmation V2

Read [AUDIT_V2.md](AUDIT_V2.md) first for the five requested findings. [SMTC_v2.pine](SMTC_v2.pine) is the complete Pine Script v6 source; `SMTC.pine` and the `.txt` copies contain the same current release.

Copy the entire source into a new TradingView Pine Editor tab, save, and add to a standard OHLC chart. Remove the previous chart instance before adding V2 so its scale assignment refreshes. V2 uses `scale.none`; all event labels explicitly use bar-index and price coordinates. If an existing instance still floats, use **Pin to scale** and choose the symbol's scale. No standalone FVG, unconfirmed sweep, or same-bar FVG retest can create an entry.

**Validation:** full-source grammar parsing and local scalar-helper diagnostics are available. They are not TradingView compilation, chart execution, replay or backtesting. The full acceptance checklist below remains necessary. No TradingView compile or profitability claim is made.

## Default strategy and exact confirmation times

The default numeric preset is **Custom**, so the visible individual parameters take effect. Balanced uses the same V2 defaults. Default signal mode is Conservative, with confirmed H1 swing-structure bias enabled.

| Parameter | V2 default |
|---|---:|
| External pivot left/right | 10 / 10 |
| Internal pivot left/right | 3 / 3 |
| Minimum sweep penetration | 0.10 ATR |
| Inclusive reclaim window | 2 candles |
| Sweep → MSS | 10 bars |
| Displacement body / ATR | 0.60 |
| Displacement body / range | 0.60 |
| Directional closing position | 0.75 |
| Minimum FVG / middle ATR | 0.20 |
| MSS → FVG confirmation window | 2 bars |
| FVG → retest expiry | 15 bars |
| HTF bias / pivots | H1 / 5 bars per side |
| Rejection wick/body | 0.25 |
| Rejection wick/ATR | 0.03 |
| Total sweep → entry age | 40 bars |
| Stop buffer | 0.10 entry ATR |
| TP1 / fixed TP2 / minimum TP2 | 1R / 2R / 2R |
| Recent completed entries retained | 10 |
| Incomplete/debug groups retained | 3 |

Previous-day pools and equal-external-level recognition default on; completed-session and internal liquidity default off. Additional chart EMA, volatility and session-entry filters default off to avoid silently combining them with the required structural HTF filter. Rejection, MSS displacement, and FVG middle displacement are required in Conservative mode. ATR length is 14. Equal-level tolerance is 0.10 ATR; eligible level age is at most 500 chart bars; internal reference age is at most 100 bars.

1. **IDLE → SWEEP_PENDING:** price wick-breaches a previously eligible confirmed pool, after approaching from its unswept side on the previous close. Select a single crossed pool per direction. Priority is previous day (4), completed session (3), external pivot (2), optional internal pivot (1). Tie-break: highest crossed low for BUY, lowest crossed high for SELL. Reserve the chosen object. Retire other crossed objects as ignored/unconfirmed breaches. A new setup gets a globally unique monotonically increasing ID. A candidate created on a closed bar can reclaim on that same bar.
2. **SWEEP_CONFIRMED:** within the inclusive reclaim window, require a strict close back on the original side and sufficient maximum penetration measured with ATR frozen at penetration. Two candles means penetration candle plus one following candle. Reclaim at age 2 is too late. An unreclaimed or insufficiently penetrated breach never emits a confirmed-sweep pulse. Confirmed objects are permanently consumed; expired reservations are retired. Neither returns to eligible via a timer.
3. At reclaim, freeze the most recent confirmed opposing INTERNAL swing high/low, including one confirmed during the sweep. It must satisfy the reference-age setting and not already be behind that reclaim close. A valid liquidity sweep without an eligible reference remains an internally recorded sweep but is invalidated for trading. No future pivot can replace its frozen reference. Sweep low/high freezes at reclaim; a later strict break of that extreme invalidates the setup before entry.
4. **MSS_CONFIRMED:** on a strictly later closed bar, require the first closing cross of that reference within 10 bars. Require direction, body/ATR, body/range and close-position thresholds. A wick-only break does nothing. A first close cross that fails displacement invalidates the setup instead of promoting a later continuation. MSS is the qualifying post-sweep internal reversal shift. CHoCH additionally requires an opposing established external HH+HL or LH+LL trend frozen at sweep confirmation and a same-candle first closing cross of its frozen external opposing swing. Mixed/equal external structures are neutral. Later breaks do not retroactively relabel MSS.
5. **FVG_CONFIRMED:** bullish candle-3 low > candle-1 high; bearish candle-3 high < candle-1 low. Size must exceed BOTH the ATR threshold and the additional tick minimum. The middle candle must independently pass the displacement filter in the correct direction. Candle 1 must not precede sweep confirmation. Its middle candle must be the MSS candle or be within the immediate association window, overlap the frozen MSS range and reach beyond the frozen structural reference. For a later middle candle, every intervening candle must remain directional, make directional closing progress beyond structure and overlap its predecessor's range. Once that sequence breaks, it cannot rearm within this MSS event. FVG confirmation itself must be no later than MSS + the window.
6. Same-MSS-bar FVG confirmation is allowed by default. Its middle candle is the immediately prior displaced candle, and it still must pass every association check. Disabling this mode requires FVG confirmation on a later bar. A pattern confirming one bar after MSS has MSS as its middle candle. These timing rules are explicit mechanical associations, not proof of institutional activity.
7. **WAITING_RETEST:** FVG_CONFIRMED is an atomic logged event followed by WAITING_RETEST on the same close. A birth-candle touch never counts. On a strictly later closed candle, require zone overlap. Conservative BUY requires bullish body, close strictly above the gap midpoint, positive lower wick ≥ 0.25 body and ≥ 0.03 ATR. SELL uses bearish body, close below midpoint, and upper rejection wick. Wick thresholds are adjustable. Aggressive signal mode still requires a later retest, directional body and midpoint close; it relaxes only the wick minimum. This intentionally replaces V1's birth-bar aggressive entry so V2 never skips the requested retest stage.
8. **ENTRY_CONFIRMED:** require entry filters and risk validation at the rejection close. Entry is suggested at that close, not a hypothetical gap limit fill. A failed filtered entry attempt consumes the setup. Earlier partial touches without qualifying rejection can wait for a later actual touch/rejection within the same expiry window. Only one completed entry is possible per ID.

All of these events are confirmed at chart-bar close. A pivot is known after its right-hand bars close; its pool becomes eligible on the next chart candle. Previous-day data is already closed at the new day's open, and completed sessions contain only previous closed chart bars, so those sources can be eligible on the first following candle. The accumulating current session is never a pool. Day boundaries follow the TradingView feed's daily bars, not a user-defined Forex rollover.

Each pivot pool stores price, original pivot bar and known/confirmation bar separately. Session origins are the chart bars making their extremes. Previous-day line origins represent the final preceding chart bar when that daily range became confirmed, not an inferred intraday extremum time. Equal recognition combines adjacent still-eligible external levels at their outermost price. It never merges into a consumed level. A newly confirmed later pivot/range can legitimately establish new liquidity at an old price; that is a new structural event, not a cooldown reset.

## Cancellation and overlaps

Cancel for reclaim expiry, missing reference, first weak closing break, sweep-extreme breach, missed MSS/FVG/retest window, total age, full gap mitigation or failed entry filters. Endpoints are inclusive: MSS at sweep + 10, FVG at MSS + 2 and retest at FVG + 15 are allowed; the following candle expires. Expiry/invalidation is checked before any entry proposal.

A bullish low at/below gap bottom or bearish high at/above gap top fully mitigates it, including a jump across the entire gap. That candle cannot produce an entry even if it later closes with rejection. Full fill always invalidates waiting entries regardless of box-removal settings. The first touch is partial mitigation only while the far boundary remains intact. Boxes fade on partial/full mitigation, expire after the retest window, and cannot independently initiate trades.

There is one active setup per direction. New same-direction candidates are ignored while active, and their wick-breached pools retire. Bullish and bearish setups can coexist. If both propose valid entries on the same close, consume both and signal neither. Their stage/price facts are never retrospectively rewritten on historical candles. Arbitration occurs before entry events/labels/alerts are committed.

## Filters and risk

HTF bias uses the latest TWO confirmed pivot highs and lows: HH+HL = Bullish, LH+LL = Bearish, mixed/equal/missing = Neutral. BUY requires Bullish and SELL Bearish when enabled; Neutral rejects either. This is not a candle-color or EMA-only bias. Outputs are offset by one completed HTF candle before `lookahead_on` distributes them. The forming HTF candle cannot affect entries. The filter deliberately lags emerging trends by pivot confirmation plus the completed-HTF sampling interval.

Use H1 for M5/M15; choose H4 for H1. Enabled bias must strictly exceed the chart timeframe or the script reports an error. Previous-day pools require intraday charts; disable them on daily and higher charts. These explicit restrictions prevent accidental lower-timeframe sampling. Standard time-based charts are intended; tick and synthetic chart behavior is unverified.

Optional chart EMA 50/200 requires close above/below it. Optional volatility requires ATR / its 50-bar SMA between 0.70 and 2.00 by default. Optional entry sessions use London OR New York, weekdays, default local 08:00–12:00 windows. IANA zones Europe/London and America/New_York handle DST independently. Session membership uses the candle OPEN time; coarse/misaligned chart bars can include prices outside the intended window. Session range extrema are built from those chart bars; they are not lower-timeframe precise session extrema. Gaps with no out-of-session bars are separated by session keys. Validate customized/overnight sessions in TradingView.

BUY stop = frozen sweep low − entry ATR × buffer; SELL stop = frozen sweep high + buffer. Fixed TP2 uses 2R by default, TP1 1R. The alternative TP2 is the nearest eligible primary opposing liquidity beyond the entire entry candle's high/low. No target is taken from a future pivot or an already breached pool. Missing targets, negative risk/reward and insufficient minimum RR reject the entry; there is no silent fallback to a farther target or fixed RR. TP1 is omitted when at/above TP2's RR. Raising minimum RR above fixed target RR filters every fixed-target entry until those settings are reconciled.

Entry, SL and TP lines are independently switchable and frozen at entry. They extend for the configured drawing length; they do not represent orders, broker fills or actual positions. Spreads, fees, slippage, financing and gap execution are excluded.

## Numeric presets

Presets override ONLY the following numeric controls. Other inputs and toggles remain independent. Select Custom to edit the corresponding individual values. Every preset still requires sweep → displaced MSS → associated displaced FVG → later retest → directional confirmation; none enables internal liquidity automatically.

| Setting | Aggressive | Balanced | Conservative |
|---|---:|---:|---:|
| External / internal pivots | 6 / 2 | 10 / 3 | 14 / 4 |
| Penetration / ATR | 0.10 | 0.10 | 0.15 |
| Inclusive reclaim | 2 | 2 | 2 |
| Sweep → MSS | 12 | 10 | 8 |
| Body / ATR | 0.60 | 0.60 | 0.80 |
| Body / range | 0.60 | 0.60 | 0.65 |
| Directional close position | 0.75 | 0.75 | 0.80 |
| Gap / middle ATR | 0.20 | 0.20 | 0.25 |
| MSS → FVG window | 3 | 2 | 1 |
| FVG → retest window | 15 | 15 | 10 |

These are sensitivity presets, not measured frequency or profitability guarantees. They do not switch the independently selected signal mode, HTF settings or risk targets.

## Visuals and dashboard

Default sweeps show only primary confirmed sweeps that reach MSS. Their small SSL → MSS / BSL → MSS marker is created on the MSS detection bar, not backdated to the sweep. Debug creates a gray Pending marker at penetration; it is removed on confirmation/expiry, and a distinct confirmed marker appears at the actual reclaim close. It never relabels an old penetration candle as a confirmed sweep. Each ID gets at most one confirmed sweep marker and one large BUY/SELL entry label. MSS and triple markers are separate event types. A blue bullish / orange bearish FVG box spans the pattern's three candles only after candle 3 closes; its left edge is not an earlier signal.

Retain the ten most recently COMPLETED entry groups by entry completion time, plus at most three incomplete/debug terminal groups and the two active directions by default. Incomplete attempts never displace completed entries from their budget. Eviction removes a whole group's drawings to respect limits; historical alert facts remain unchanged. The diagnostic ledger retains the latest 200 events in memory, including hidden sweeps, IDs and actual detection bars; it is not a permanent exported backtest log. Chart recalculation rebuilds it.

The dashboard shows HTF bias; current Bullish/Bearish/Both/None; stage and age; latest confirmed sweep/MSS levels; active FVG; last entry direction/price/time; entry status/outcome; and latest rejection with ID. When both directions are active it explicitly says Both and details the newest ID. Latest-level rows are historical facts, not active pending levels. The entry timestamp uses the configured timezone (UTC default).

Historical/replay entries start Historical, not Active. Only a confirmed realtime entry starts Active. Subsequent closed bars mark stop touches Invalidated, target touches Historical, or monitoring expiry Historical after 100 bars by default. SL and TP2 touched in the same candle are order-unknown and conservatively Invalidated. This is advisory candle-based status, not a position ledger or P&L backtest. Reloaded historical entries do not magically become live positions. The screen-fixed dashboard itself intentionally does not follow a candle.

## Alerts

Add V2 and set the intended symbol, timeframe and inputs. In Create alert select one of the eight named V2 conditions and choose **Once Per Bar Close**. Early sweep alerts include internally valid sweeps even when default drawings hide them pending MSS; disable those conditions if you want fewer notifications. MSS alerts are post-sweep displacement shifts. Triple alerts indicate setup completion only, before retest/risk filtering. Use Bullish FVG retest entry / BUY and Bearish FVG retest entry / SELL for complete entries. Their messages include setup ID, Entry, SL and TP2 using hidden plot placeholders.

Every event condition pulses once at its detection close. Recreate TradingView alerts after code/input changes because existing alerts run a saved snapshot. Multiple separately created alerts for the same condition can still yield multiple notifications.

## Local diagnostics

From `/workspace/test` run:

```sh
python3 smtc/diagnostics_v2.py
```

It parses the full source through `/workspace/smtc-tools/bin/pynescript` and safely interprets the scalar helper AST bodies for synthetic scenarios. Parsing can take around a minute or longer. For a just-generated AST of this exact unchanged file, `--ast /tmp/smtc-v2-diagnostics-ast.txt` reuses that dump; do not reuse it for changed source. The standard command always reparses.

Checks cover A–F at the scalar-component level, bullish/bearish displacement and rejection, ATR penetration, FVG timing/range association, same-bar prohibitions, endpoint expiry, missing references, full-fill/extreme invalidation, filter consumption and terminal-state duplication. This harness deliberately does not emulate Pine series/NA semantics in general or execute UDT orchestration, real pivots, `request.security`, drawing queues, session boundaries, live rollback or alert delivery. A passing result does not prove the complete indicator compiles or behaves correctly in TradingView.

## TradingView acceptance and Bar Replay

Use at least several hundred standard-candle chart bars with enough preceding H1 history to confirm two HTF highs and lows. Start with Custom V2 defaults, Conservative mode, H1 bias and fixed 2R targets on EUR/USD M5/M15. GBP/USD can start with the same settings and 0.15 ATR stop buffer. Those are unoptimized hypotheses. Enable debug while inspecting detection, then compare the default uncluttered view.

1. Compile the COMPLETE file in Pine Editor and inspect all errors/warnings. Remove V1, add V2 fresh and verify markers remain attached when panning/scaling. Local grammar acceptance is not this compile check.
2. **A — Strong downtrend:** replay from before confirmed external lows. Repeated lower lows without valid reclaim must produce no confirmed SSL alerts/labels. Debug may show pending/expired breaches, never confirmed sweeps without reclaim. If a genuine reclaim does happen, check the actual rule rather than assuming every trend candle must be excluded.
3. **B — False sweep:** replay a breach with no qualifying reclaim on the penetration candle or following candle. It must expire; a later reclaim cannot revive that object.
4. **C — Sweep without MSS:** verify one internal sweep event and its frozen reference, then no closing break within ten bars. Expect expiry, no triple and no BUY/SELL. Default view hides its isolated sweep; debug and early alerts distinguish it from a trade.
5. **D — MSS without FVG:** verify a qualified later closing cross, but no correctly directed 0.20 ATR displaced/associated gap. Expect no triple/entry and expiry. Confirm a nearby unrelated later gap does not rescue the setup.
6. **E — Complete BUY:** replay sweep → displaced MSS → associated FVG → later partial retest → bullish midpoint/wick rejection. Expect exactly one BUY at that rejection CLOSE and matching frozen risk levels. Repeat symmetrically for SELL. For deterministic component inspection you can temporarily disable HTF/optional filters; with default enabled HTF, E also needs bullish confirmed H1 bias and sufficient RR. A Neutral bias rejection is not a missing entry bug.
7. **F — Same level repeatedly crossed:** after confirmed consumption, repeated crossings of that same object must never emit another sweep. If another sweep occurs at the same price, inspect whether a genuinely later confirmed pivot/day/session range established a new eligible object and ID.
8. Check same-bar MSS/FVG acceptance, disabling that mode, no birth-bar retest, exact expiry endpoints, missing-reference invalidation, first weak close cross, an interrupted impulse, midpoint versus wick tests, full mitigation, sweep-extreme break and failed target/RR filters. Test day/session boundary first bars and gaps, especially customized overnight windows. Confirm partial touches without rejection do not create an entry by themselves.
9. Check H1 bias against the last TWO confirmed H1 highs/lows, not the forming H1 candle. It must not change inside a forming H1 interval. H1 charts require H4 or another higher bias; daily charts must disable previous-day pools and choose a larger HTF or disable it.
10. **G — Live versus historical:** record symbol/feed, chart type, inputs, timestamps, detection bars and IDs for closed-bar events during replay/live. Reload with the same available history and compare event bar/price facts. Confirmed signals should match on unchanged OHLC. IDs depend on the history start and are not globally stable across different loaded windows. Live-only Active status is intentionally different from Historical/replay status; compare signals, not that status tag.

## Unverified assumptions and limitations

The audited source is the available workspace version, not a separately modified chart script. TradingView compilation, chart-level acceptance A–F and replay/live G remain unverified until performed there. Third-party grammar parsing cannot resolve Pine-specific type/compiler limitations. Diagnostic helper execution covers a restricted scalar subset and does not establish chart-level behavior.

Confirmed HTF pivots lag trends; strict displacement and full-fill rejection skip some discretionary trades. Equal recognition is adjacent-level matching, not an exhaustive cluster algorithm. Previous-day boundaries and OHLC differ by Forex feed; session precision depends on chart-bar alignment and available data. A bounded impulse association is a mechanical proxy for MSS-linked FVGs, not proof of causality. Neutral HTF filtering can suppress all entries during ranges and early warmup. News, spread widening, weekend gaps, trend continuation after a true reclaim and low liquidity can still produce losing setups. There is no news/spread filter, position sizing, execution engine or validated strategy backtest.

Signals use only confirmed chart/HTF data and frozen references; they are not retroactively backdated. Changing inputs, symbol, timeframe, chart type or available history recalculates results. Feed corrections can alter old signals. Pending debug markers and bounded/mitigated drawings can disappear by design; that does not mean a confirmed entry event was revised. Synthetic/tick charts are not validated. No indicator can promise profitability or eliminate false signals.

Development uses the existing `/workspace/test` checkout. Cloud tasks are already isolated; do not create a worktree unless explicitly requested. The optional parser lives outside the checkout at `/workspace/smtc-tools`; no application server or secrets are needed. Validate Pine execution in TradingView before treating V2 as production-ready.
