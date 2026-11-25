"""Tiny momentum bot for make.fun bars-replay/v1 (Solana hourly bars).

Strategy: trend-follow the strongest names, sit in cash when nothing trends.
Each bar, per symbol, compute 3h and 12h close momentum. Hold up to 4 symbols
with 3h momentum above +1% and 12h momentum above 0, sized 20% of equity
each. Exit a holding as soon as it stops qualifying (3h momentum below -1%
or 12h below -2%) — cutting losers fast is what beats buy-and-hold in a
falling market. Rebalance held names back to the 20% target on a +/-2pp band
so the bot keeps trading (and its edge) even inside a steady trend. Fully deterministic: no
clock, no environment, no randomness; client ids are sequential.

Speaks agent-fun/bars-replay/v1 on stdin/stdout, standard library only.
"""
import json
import sys

ENTER_FAST = 0.01    # 3h momentum needed to enter
ENTER_SLOW = 0.0     # 12h momentum needed to enter
EXIT_FAST = -0.01    # 3h momentum that exits a holding
EXIT_SLOW = -0.02    # 12h momentum that exits a holding
TARGET_W = 0.20      # target weight of equity per holding
BAND = 0.02          # rebalance band around the target weight
MAX_HOLD = 4         # most symbols held at once
MAX_SLIP = 500       # max slippage bps per order
MIN_NOTIONAL = 1000000  # 1 USDC in raw units


def main():
    symbols = {}
    closes = {}
    warmup = 0
    seq = -1
    cash = 0
    equity = 0
    positions = {}
    nxt = [1]

    def value(sym, qty, price):
        s = symbols[sym]
        return qty * price * 10 ** 6 // 10 ** (s["qty_scale"] + s["price_scale"])

    def qty_for(sym, notional, price):
        s = symbols[sym]
        return notional * 10 ** (s["qty_scale"] + s["price_scale"]) // (price * 10 ** 6)

    def cid():
        c = "o%d" % nxt[0]
        nxt[0] += 1
        return c

    def momentum(hist, n):
        if len(hist) <= n:
            return None
        return hist[-1] / hist[-1 - n] - 1.0

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        kind = msg["type"]
        if kind == "hello":
            for s in msg["symbols"]:
                symbols[s["symbol"]] = s
                closes[s["symbol"]] = []
            warmup = msg.get("warmup_bars", 0)
            cash = int(msg["capital"]["quote_units"])
            equity = cash
        elif kind == "batch":
            seq = msg["seq"]
            for bar in msg["bars"]:
                closes[bar["symbol"]].append(int(bar["c"]))
            acct = msg["account"]
            cash = int(acct["cash_quote_units"])
            equity = int(acct["equity_quote_units"])
            positions = {p["symbol"]: int(p["qty"]) for p in acct["positions"]}
            orders = []
            if seq >= warmup:
                wanted = []
                for sym, hist in closes.items():
                    fast = momentum(hist, 3)
                    slow = momentum(hist, 12)
                    if fast is None or slow is None:
                        continue
                    if fast > ENTER_FAST and slow > ENTER_SLOW:
                        wanted.append((fast, sym))
                wanted.sort(reverse=True)
                keep = {sym for _, sym in wanted[:MAX_HOLD]}
                for sym, qty in list(positions.items()):
                    hist = closes[sym]
                    fast = momentum(hist, 3)
                    slow = momentum(hist, 12)
                    price = hist[-1]
                    val = value(sym, qty, price)
                    if sym not in keep or (fast is not None and fast < EXIT_FAST) or (slow is not None and slow < EXIT_SLOW):
                        orders.append({"side": "sell", "client_id": cid(), "symbol": sym,
                                       "qty": str(qty), "max_slippage_bps": MAX_SLIP})
                    elif val > (TARGET_W + BAND) * equity:
                        excess = int(val - TARGET_W * equity)
                        q = qty_for(sym, excess, price)
                        if q > 0 and q < qty:
                            orders.append({"side": "sell", "client_id": cid(), "symbol": sym,
                                           "qty": str(q), "max_slippage_bps": MAX_SLIP})
                for _, sym in wanted[:MAX_HOLD]:
                    price = closes[sym][-1]
                    held = positions.get(sym, 0)
                    val = value(sym, held, price) if held else 0
                    target = int(TARGET_W * equity)
                    if val < (TARGET_W - BAND) * equity and target - val >= MIN_NOTIONAL:
                        spend = min(target - val, cash)
                        if spend >= MIN_NOTIONAL:
                            orders.append({"side": "buy", "client_id": cid(), "symbol": sym,
                                           "notional_quote_units": str(spend), "max_slippage_bps": MAX_SLIP})
                            cash -= spend
            sys.stdout.write(json.dumps({"type": "reply", "seq": seq, "orders": orders},
                                        separators=(",", ":")) + "\n")
            sys.stdout.flush()
        elif kind == "done":
            break


if __name__ == "__main__":
    main()
