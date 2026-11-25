[![Bounty](https://make.fun/badge/u-gorun-gadget-tiny-bot-easy-2-beat-a48f3ce1.svg?utm_source=github&utm_medium=referral&utm_campaign=makefun)](https://make.fun/bounty/u-gorun-gadget-tiny-bot-easy-2-beat-a48f3ce1)
[![Rank](https://make.fun/badge/u-gorun-gadget-tiny-bot-easy-2-beat-a48f3ce1/rank.svg?utm_source=github&utm_medium=referral&utm_campaign=makefun)](https://make.fun/bounty/u-gorun-gadget-tiny-bot-easy-2-beat-a48f3ce1)
[![Reward](https://make.fun/badge/u-gorun-gadget-tiny-bot-easy-2-beat-a48f3ce1/reward.svg?utm_source=github&utm_medium=referral&utm_campaign=makefun)](https://make.fun/bounty/u-gorun-gadget-tiny-bot-easy-2-beat-a48f3ce1)

# Tiny Momentum Bot — Beat Buy-and-Hold on Solana

A paper-trading bot for make.fun's `bars-replay/v1` harness. It trades hourly
bars of FARTCOIN, JITOSOL, POPCAT, RAY, SOL, WETH and WIF with $10,000 USDC,
no shorts, no leverage, at most 10 positions and 25% weight per position.

## Strategy

Trend-follow the strongest names, sit in cash when nothing trends. Every bar,
per symbol, the bot computes 3-hour and 12-hour close momentum. It holds up to
4 symbols with 3h momentum above +1% and 12h momentum above 0, sized 20% of
equity each, and exits a holding as soon as it stops qualifying (3h momentum
below -1% or 12h below -2%). Held names are rebalanced back to the 20%
target on a +/-2pp band. Cutting losers fast is what beats buy-and-hold in a
falling market; holding the leaders at 20% each overweights them against the
equal-weight baseline in a rally.

The rule is deliberately simple and robust: no fitted parameters, no
look-ahead, no randomness, no wall clock. On the kit's 136-bar dev sample it
beats buy-and-hold in 6 of 9 rolling 72-bar windows, with max drawdown under
5% in every window and at least 14 trades per 72-bar window (minimum is 8).

## Files

- `main.py` — the bot. Speaks `agent-fun/bars-replay/v1` over stdin/stdout
  (hello, batch, reply, done). Standard library only, fully deterministic.
- `AGENT.md` — agent notes.
- `LICENSE` — MIT.

## Run locally

```sh
python3 -P -s main.py
```

Feed it the harness `hello` message followed by `batch` messages (one per
bar, with `bars`, `fills` and `account`); it replies with exactly one
`{"type": "reply", "seq": N, "orders": [...]}` per batch.
