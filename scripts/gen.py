import csv, glob, os, random, sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# usage: python3 scripts/gen.py data
# Doplní hodinová měření do data/teploty.csv a přepíše měsíční soubory data/<teploměr>/RRRR-MM.csv.
# Když data/teploty.csv nemá aktuální sloupce, vygeneruje celou historii znovu od START.

TZ = ZoneInfo("Europe/Prague")
START = datetime(2026, 10, 1, 0, 0)
DEVICES = [("mrazak", "Mrazák", "F"), ("auto1", "Auto 1", "A"), ("auto2", "Auto 2", "A"),
           ("auto3", "Auto 3", "A"), ("box", "Chladící box", "C")]
COLS = [d[0] for d in DEVICES]
NAMES = {d[0]: d[1] for d in DEVICES}
KIND = {d[0]: d[2] for d in DEVICES}


def weekday(dt):
    return dt.weekday() < 5


def clamp_reflect(v, lo, hi):
    if v > hi: v = hi - (v - hi) * random.random()
    if v < lo: v = lo + (lo - v) * random.random()
    return min(hi, max(lo, v))


def walk(prev, lo, hi, mode, sig):
    t = random.triangular(lo, hi, mode)
    v = t if prev is None else prev + 0.45 * (t - prev) + random.gauss(0, sig)
    return clamp_reflect(v, lo, hi)


def value(prev, dt, kind):
    h = dt.hour
    if kind == "F":  # stacionární mrazák
        if weekday(dt) and 7 <= h <= 9:
            return walk(prev, -16.0, -13.0, -14.5, 0.7)
        return walk(prev, -19.8, -17.0, -18.4, 0.6)
    if kind == "C":  # chladící box
        if weekday(dt) and 8 <= h < 16:
            return walk(prev, 4.0, 8.0, 6.0, 0.7)
        return walk(prev, 0.0, 4.0, 1.8, 0.6)
    # auta: mražení jen ve všední dny 9:00–17:59, jinak vypnuto a prázdná
    if weekday(dt) and 9 <= h < 18:
        on = h - 9
        if on == 0:
            return clamp_reflect(random.uniform(-7.0, -2.0), -9.0, 8.0)
        if on == 1:
            return clamp_reflect(random.uniform(-15.5, -11.0), -17.0, -9.0)
        return walk(prev if prev is not None and prev < -16.0 else None, -19.8, -17.0, -18.3, 0.6)
    amb = random.triangular(2.0, 10.0, 5.5)
    base = prev if prev is not None else amb
    v = base + 0.45 * (amb - base) + random.gauss(0, 0.6)
    return clamp_reflect(v, -19.8, 12.0)


def nxt(hist, dt, c):
    prev = hist[-1] if hist else None
    v = 0.0
    for _ in range(300):
        v = round(value(prev, dt, KIND[c]), 1)
        if v == -0.0: v = 0.0
        if not (len(hist) >= 2 and hist[-1] == hist[-2] == v):
            return v
    return v


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else "data"
    src = os.path.join(d, "teploty.csv")
    rows = []
    if os.path.exists(src):
        with open(src, newline="", encoding="utf-8") as f:
            rd = csv.DictReader(f)
            if rd.fieldnames == ["cas"] + COLS:
                rows = list(rd)
    if rows:
        t = datetime.strptime(rows[-1]["cas"], "%Y-%m-%d %H:%M") + timedelta(hours=1)
    else:
        t = START
        for old in glob.glob(os.path.join(d, "20[0-9][0-9]-[0-9][0-9].csv")):
            os.remove(old)
    now = datetime.now(TZ).replace(minute=0, second=0, microsecond=0, tzinfo=None)
    hist = {c: [float(r[c]) for r in rows[-2:]] for c in COLS}
    added = 0
    while t <= now:
        r = {"cas": t.strftime("%Y-%m-%d %H:%M")}
        for c in COLS:
            v = nxt(hist[c], t, c)
            hist[c] = (hist[c] + [v])[-2:]
            r[c] = f"{v:.1f}"
        rows.append(r); added += 1; t += timedelta(hours=1)
    with open(src, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["cas"] + COLS); w.writeheader(); w.writerows(rows)
    months = {}
    for r in rows:
        months.setdefault(r["cas"][:7], []).append(r)
    for c in COLS:
        os.makedirs(os.path.join(d, c), exist_ok=True)
        for k, lst in months.items():
            with open(os.path.join(d, c, k + ".csv"), "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f); w.writerow(["Datum a čas", NAMES[c] + " (°C)"])
                for r in lst: w.writerow([r["cas"], r[c]])
    print(f"added {added} rows, total {len(rows)}, last {rows[-1]['cas']}, months {sorted(months)}")


if __name__ == "__main__":
    main()
