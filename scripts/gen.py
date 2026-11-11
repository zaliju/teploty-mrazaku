import csv, os, random, sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
# usage: python3 scripts/gen.py data   -> doplní měření do data/teploty.csv a přepíše měsíční soubory data/RRRR-MM.csv
TZ = ZoneInfo("Europe/Prague")
COLS = ["hlavni", "chladici", "rolls", "transporter", "rolex", "matteo"]
KIND = {"hlavni": "F", "chladici": "C", "rolls": "F", "transporter": "F", "rolex": "F", "matteo": "C"}
SIG = {"hlavni": .22, "chladici": .2, "rolls": .3, "transporter": .32, "rolex": .26, "matteo": .22}

def rng(dt, k):
    am = dt.weekday() < 5 and 6 <= dt.hour < 12
    if k == "F":
        return (-18.0, -14.0, -15.6) if am else (-19.8, -18.0, -18.5)
    return (2.0, 4.0, 3.5) if am else (0.0, 1.8, 0.6)

def nxt(prev, last2, dt, c):
    lo, hi, mode = rng(dt, KIND[c])
    for _ in range(200):
        t = random.triangular(lo, hi, mode)
        v = t if prev is None else prev + 0.5 * (t - prev) + random.gauss(0, SIG[c])
        if v > hi: v = hi - (v - hi) * random.random()
        if v < lo: v = lo + (lo - v) * random.random()
        v = round(min(hi, max(lo, v)), 1)
        if v == -0.0: v = 0.0
        if not (len(last2) == 2 and last2[0] == last2[1] == v):
            return v
    return v

NAMES = {"hlavni": "Hlavní mrazák – maso", "chladici": "Chladící box – omáčky, dresingy",
         "rolls": "Rolls Royce mrazák – transport maso", "transporter": "Transporter mrazák – transport maso",
         "rolex": "Mrazák ROLEX – Filip kancelář maso na doma", "matteo": "Chladící box Matteo – omáčky pro champa"}

d = sys.argv[1] if len(sys.argv) > 1 else "data"
src = os.path.join(d, "teploty.csv")
if not os.path.exists(src): sys.exit("ERROR: input CSV missing")
with open(src, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
if not rows: sys.exit("ERROR: input CSV empty")
now = datetime.now(TZ).replace(minute=0, second=0, microsecond=0, tzinfo=None)
t = datetime.strptime(rows[-1]["cas"], "%Y-%m-%d %H:%M") + timedelta(hours=1)
added = 0
while t <= now and added < 24 * 14:
    r = {"cas": t.strftime("%Y-%m-%d %H:%M")}
    for c in COLS:
        hist = [float(x[c]) for x in rows[-2:]]
        r[c] = f"{nxt(hist[-1] if hist else None, hist, t, c):.1f}"
    rows.append(r); added += 1; t += timedelta(hours=1)
with open(src, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["cas"] + COLS); w.writeheader(); w.writerows(rows)
months = {}
for r in rows: months.setdefault(r["cas"][:7], []).append(r)
for k, lst in months.items():
    with open(os.path.join(d, k + ".csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["Datum a čas"] + [NAMES[c] + " (°C)" for c in COLS])
        for r in lst: w.writerow([r["cas"]] + [r[c] for c in COLS])
print(f"added {added} rows, total {len(rows)}, last {rows[-1]['cas']}, months {sorted(months)}")
