# Agent Notes — Tiny Momentum Bot

## What this is

A make.fun `bars-replay/v1` entry for "Tiny Bot, Easy $2: Beat Buy-and-Hold
on Solana" (`u-gorun-gadget-tiny-bot-easy-2-beat-a48f3ce1`). Single-file
Python bot, standard library only, no network, no randomness, no wall clock.

## How it works

- Reads `hello` (symbols with price/qty scales, capital, caps, fees, warmup),
  then one `batch` per hourly bar.
- Tracks closes per symbol. Signals: 3h momentum (`close / close[-3] - 1`)
  and 12h momentum (`close / close[-12] - 1`).
- Entry: 3h momentum > +1% and 12h momentum > 0. Holds the top 4 by 3h
  momentum, 20% of equity each (max weight cap is 25%).
- Exit: a holding is sold in full as soon as 3h momentum < -1% or 12h
  momentum < -2% — it no longer qualifies.
- Rebalance: held names drifting outside the 20% +/- 2pp band are topped up
  or trimmed back to target, which also keeps trade count healthy in steady
  trends.
- Buys use `notional_quote_units`, sells use `qty`; every order carries
  `max_slippage_bps` 500 and a sequential client id (`o1`, `o2`, ...).
- Never trades during warmup bars. Replies exactly once per batch.

## Verification

Replayed locally against the kit's 136-bar dev dataset with a harness that
mimics the wire protocol and the market model (fills at next bar's open, 10
bps fee, 5 bps slippage, constant-product impact vs pool depth, flatten at
the end):

- Full 136 bars: Net PnL -$401.84 vs buy-and-hold -$876.93, 54 bot fills,
  max drawdown 4.95%.
- Rolling 72-bar windows (the final window is 72 bars): beats buy-and-hold
  in 6 of 9 windows, max drawdown under 5% everywhere, 14-36 fills per
  window (minimum is 8).
- Two identical runs produce byte-identical replies (fully deterministic).

## Known limits

- A broad, evenly-spread rally favours buy-and-hold (the bot holds at most
  80% invested); the edge is in falling and choppy markets, where it sits
  mostly in cash and cuts losers fast.
- Flat windows cost a little in fees; the bot still trades 14+ times there,
  so the 8-trade minimum is met with margin.
