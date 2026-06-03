---
name: import-faturas
description: Import Itaú credit-card PDF statements into SpendTrack — parse the PDFs, populate the database (expenses + invoices) for a user, and verify each month's total matches the statement. Use when the user wants to import bank statements/invoices ("faturas"), populate spending data from PDFs, or refresh the dashboard data from new Itaú statements.
---

# Import Itaú statements into SpendTrack

Imports Itaú credit-card statement PDFs into the database so the dashboard and
analytics show real spending. The importer lives in the repo at
`backend/scripts/import_itau.py` and runs inside the backend container.

## How it works

For each PDF it parses the **"Lançamentos: compras e saques"** (domestic
purchases) section using positional text extraction (pymupdf), reconstructing the
two-column layout into `date · merchant · amount · category`. It then:

- Maps each Itaú category (ALIMENTAÇÃO, SAÚDE, VESTUÁRIO, DIVERSOS, HOBBY,
  EDUCAÇÃO, TURISMO E ENTRETENIM, VEÍCULOS, MORADIA…) to a SpendTrack category
  (food, health, shopping, other, entertainment, education, transport, utilities).
- Dates every expense inside the invoice's **reference month** (from
  `Vencimento: dd/mm/aaaa`), so monthly analytics match the statement. Days in the
  current month are capped at "today" so nothing is dropped as future-dated.
- Adds **one reconciliation expense** per invoice (category `other`) equal to
  `Total desta fatura − sum(domestic items)`. This absorbs international charges,
  annual fees and finance charges (encargos), guaranteeing the imported monthly
  total equals the statement's "Total desta fatura" exactly.
- Creates an `Invoice` row per PDF (status `processed`, metadata with totals).

International transactions, annuity and finance charges are **not** itemised
line-by-line — they are summed into the reconciliation line.

Each expense is attributed to a **cardholder** (person) by tracking the per-card
section headers ("NOME (final XXXX)") in reading order. The mapping of names to
people lives in `_cardholder_from_line` in the importer (currently Diego /
Beatriz); adjust it for other statements. The reconciliation line is attributed
to the account titular. The `cardholder` is stored on each expense and powers
the global "person" filter in the UI.

## Steps

1. Make sure the services are up: `docker compose ps` (backend must be running).
2. Put the statement PDFs where the backend can read them. The backend mounts
   `./invoices` at `/app/invoices`, so copy them in:
   ```bash
   mkdir -p invoices/itau
   cp /path/to/statements/*.pdf invoices/itau/
   ```
   (`invoices/` is gitignored, so personal statements are never committed.)
3. Ensure the target user exists (default `diego`). Create one via
   `POST /api/auth/register` or directly in the DB if needed.
4. Run the importer. Use `--reset` to wipe the user's existing expenses/invoices
   first (recommended for a clean re-import):
   ```bash
   make import-itau RESET=1                 # DIR=/app/invoices/itau USER=diego
   # or directly:
   docker compose exec backend python scripts/import_itau.py /app/invoices/itau --user diego --reset
   ```
5. Verify the per-invoice report: every line should start with ✅ and show
   `total == fatura`. If the user provided expected monthly totals, confirm each
   matches.
6. Confirm via the API (login as the user, then):
   ```bash
   curl -s http://localhost:8000/api/analytics/trends/monthly?months=6 -H "Authorization: Bearer $TOKEN"
   curl -s http://localhost:8000/api/analytics/summary -H "Authorization: Bearer $TOKEN"
   ```
   The dashboard summary is all-time; the monthly trends chart shows one bar per
   reference month.

## Notes / extending

- `pymupdf` is a backend dependency (Dockerfile + pyproject.toml). After a clean
  `docker compose build` it is already present.
- The parser is specific to the Itaú statement layout (two columns, section
  headers in Portuguese). For a different bank, adapt `SECTION_START`,
  `SECTION_STOP`, the column x-bands, and `_map_category` in
  `backend/scripts/import_itau.py`.
- All amounts are treated as BRL.
