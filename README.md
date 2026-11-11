# Teploty mrazáků – výrobna kebabů

Veřejná stránka: https://zaliju.github.io/teploty-mrazaku/

- `data/teploty.csv` – všechna měření (simulovaná, každou hodinu doplňuje GitHub Actions).
- `data/RRRR-MM.csv` – měsíční soubory, odkud čte Google Sheets (`IMPORTDATA`).
- `scripts/gen.py` – generátor měření podle zadaných rozsahů.
- `.github/workflows/update.yml` – každou hodinu doplní měření a zveřejní stránku.
