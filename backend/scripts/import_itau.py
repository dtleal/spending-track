"""Import Itaú credit-card PDF statements into SpendTrack.

Parses the "Lançamentos: compras e saques" (domestic purchases) section of each
Itaú invoice PDF, maps Itaú's categories to SpendTrack categories, and stores the
transactions as expenses linked to an Invoice record. International charges,
annual fees and finance charges are not itemised line-by-line; instead a single
reconciliation expense is added per invoice so that the imported monthly total
matches the invoice's "Total desta fatura" exactly.

Each invoice's expenses are dated within the invoice's reference month (derived
from "Vencimento: dd/mm/aaaa"), so the monthly analytics match the statement.

Usage (inside the backend container, WORKDIR /app):
    python scripts/import_itau.py /app/invoices/itau --user diego --reset
"""
import argparse
import glob
import os
import re
import sys
from calendar import monthrange
from collections import defaultdict
from datetime import datetime
from typing import Optional

import fitz  # pymupdf

# Allow running as `python scripts/import_itau.py` from /app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal  # noqa: E402
from app.models.expense import Expense, ExpenseCategory  # noqa: E402
from app.models.invoice import Invoice, InvoiceStatus  # noqa: E402
from app.models.user import User  # noqa: E402

DATE = re.compile(r"^\d{2}/\d{2}$")
VAL = re.compile(r"^\d{1,3}(\.\d{3})*,\d{2}$")
SECTION_START = "lançamentos: compras e saques"
SECTION_STOP = (
    "compras parceladas",
    "lançamentos internacionais",
    "lançamentos: produtos e serviços",
    "total dos lançamentos atuais",
    "simulação",
    "encargos cobrados",
    "limites de crédito",
    "demais taxas",
)


def _money(s: str) -> float:
    return float(s.replace(".", "").replace(",", "."))


def _map_category(raw_cat: str) -> ExpenseCategory:
    """Map an Itaú category label (e.g. 'ALIMENTAÇÃO .SOROCABA') to a SpendTrack category."""
    c = raw_cat.split(".")[0].strip().upper()
    if "ALIMENT" in c:
        return ExpenseCategory.FOOD
    if "SAÚDE" in c or "SAUDE" in c:
        return ExpenseCategory.HEALTH
    if "VESTU" in c:
        return ExpenseCategory.SHOPPING
    if "VEÍCUL" in c or "VEICUL" in c or "TRANSPORT" in c or "COMBUST" in c:
        return ExpenseCategory.TRANSPORT
    if "EDUCA" in c:
        return ExpenseCategory.EDUCATION
    if "TURISMO" in c or "ENTRETEN" in c or "LAZER" in c or "HOBBY" in c:
        return ExpenseCategory.ENTERTAINMENT
    if "MORADIA" in c or "SERVIÇO" in c or "SERVICO" in c or "UTILID" in c or "CASA" in c:
        return ExpenseCategory.UTILITIES
    return ExpenseCategory.OTHER


# Merchant-name keywords used to refine Itaú's "DIVERSOS" / uncategorised entries.
# Checked in order; the first matching group wins.
_MERCHANT_RULES = [
    (ExpenseCategory.ENTERTAINMENT, (
        "CLAUDE", "OPENAI", "CHATGPT", "ANTHROPIC", "NETFLIX", "SPOTIFY", "PARAMOUNT",
        "DISNEY", "HBO", "MAX ", "YOUTUBE", "PRIME CANAIS", "PRIME VIDEO", "AMAZON PRIME",
        "SESC", "CINEMA", "INGRESSO", "TICKETMASTER", "MELIMAIS", "DEEZER", "TWITCH",
        "STEAM", "PLAYSTATION", "XBOX", "NINTENDO",
    )),
    (ExpenseCategory.HEALTH, (
        "DROGA", "FARMA", "CLINICA", "HOSPITAL", "ODONTO", "PSICO", "LABORAT",
        "PILATES", "ACADEMIA", "SMARTFIT", "SMART FIT", "BIORITMO", "TOTALPASS",
        "TOTAL PASS", "GYMPASS", "SUPPLEMENT", "SUPLEMENT", "GROWTH", "BARBEAR",
        "CAMERINO", "SALAO", "SALÃO", "ESTETICA", "DERMA", "VACINA", "AZOS",
    )),
    (ExpenseCategory.TRANSPORT, (
        "AZUL", "LATAM", "GOL ", "DECOLAR", "UBER", "99POP", "99 *", "99POP", "CABIFY",
        "POSTO", "COMBUST", "IPIRANGA", "SHELL", "ESTACIONA", "RENTCAR", "RENT A CAR",
        "LOCALIZA", "MOVIDA", "UNIDAS", "PEDAGIO", "SEM PARAR", "CONECTCAR", "AEREA",
    )),
    (ExpenseCategory.FOOD, (
        "IFOOD", "IFD", "99FOOD", "SORVETE", "GELATERIA", "RESTAUR", "PIZZA", "LANCHE",
        "SUPERMERCADO", "PADARIA", "COMIDA", "BURGER", "MC DONALD", "CHURRAS", " BAR ",
        "CAFE", "ACAI", "URLA", "NUTRISAVOUR", "GASTRONOMIA", "COXINHA", "DOCE",
        "HORTIFRUTI", "ATACADAO", "EMPORIO", "DELI",
    )),
    (ExpenseCategory.EDUCATION, (
        "ESCOLA", "COLEGIO", "FACULDADE", "UNIVERS", "CURSO", "UDEMY", "ALURA",
        "EDUCA", "ENSINO",
    )),
    (ExpenseCategory.UTILITIES, (
        "VIVO", "CLARO", "TIM ", "OI ", "ENERGIA", "ENEL", "CPFL", "SABESP", "COMGAS",
        "INTERNET", "SEGURO", "VERISURE", "ALARME", "CONSORCIO", "CONTABILIZEI",
        "LAVAFORT", "LIMPEZA", "CONTA ",
    )),
    (ExpenseCategory.SHOPPING, (
        "AMAZON", "MERCADOLIVRE", "MERCADO LIVRE", "MELI", "SHOPEE", "ALIEXPRESS",
        "MAGAZINE", "MAGALU", "AMERICANAS", "CASAS BAHIA", "VIVARA", "RI HAPPY",
        "PBKIDS", "DECATHLON", "RENNER", "RIACHUELO", "C&A", "ZARA", "LOJA", "LOJAO",
        "SHOPPING", "MOBLY", "COBASI", "PETZ", "LEROY", "TELHANORTE", "PRESENTE",
        "GRAFICA", "PERNAMBUCANA", "MARISA", "CENTER PANOS", "CASA E CIA", "BRINQUEDO",
        "PANOS", "TECID", "ACESS", "FESTA", "SANTA FINA",
    )),
]


def _classify_merchant(merchant: str) -> ExpenseCategory | None:
    """Best-effort category from the merchant name; None if nothing matches."""
    m = (merchant or "").upper()
    for category, keywords in _MERCHANT_RULES:
        if any(kw in m for kw in keywords):
            return category
    return None


# Merchants whose category is always overridden regardless of Itaú's label.
_FORCE_MERCHANT = [
    (ExpenseCategory.HEALTH, ("TOTALPASS", "TOTAL PASS", "GYMPASS")),  # gym
    (ExpenseCategory.UTILITIES, ("APPLE.COM/BILL", "APPLE.COM BILL", "APPLECOMBILL")),
]


def _forced_category(merchant: str) -> ExpenseCategory | None:
    m = (merchant or "").upper()
    for category, keywords in _FORCE_MERCHANT:
        if any(kw in m for kw in keywords):
            return category
    return None


def _resolve_category(raw_cat: str, merchant: str) -> ExpenseCategory:
    """Resolve a category: forced merchant overrides win, then Itaú's label,
    then a merchant-name fallback for Itaú's uncategorised ('DIVERSOS') entries."""
    forced = _forced_category(merchant)
    if forced is not None:
        return forced
    cat = _map_category(raw_cat)
    if cat == ExpenseCategory.OTHER:
        guessed = _classify_merchant(merchant)
        if guessed is not None:
            return guessed
    return cat


def _cardholder_from_line(line: str) -> Optional[str]:
    """Detect an Itaú per-card section header and map it to a person."""
    up = line.upper()
    if "BEATRIZ" in up:
        return "Beatriz"
    if "DIEGO LEAL" in up:
        return "Diego"
    return None


def parse_invoice(path: str):
    """Return (transactions, invoice_total, reference_year, reference_month).

    transactions: list of dicts {date(dd/mm), merchant, amount, raw_cat, cardholder}
    Each transaction is attributed to a cardholder by tracking the per-card
    section headers ("NOME (final XXXX)") in reading order (page → column → y).
    """
    doc = fitz.open(path)

    # Build the row stream in reading order: each page, left column then right
    # column, top to bottom. Cardholder/section state carries across the stream.
    ordered_rows = []
    for pi in range(doc.page_count):
        words = doc[pi].get_text("words")  # x0,y0,x1,y1,word,...
        for col_min, col_max in [(0, 360), (360, 600)]:
            rows = defaultdict(list)
            for w in words:
                if col_min <= w[0] < col_max:
                    rows[round(w[1])].append(w)
            ys = sorted(rows)
            for k, y in enumerate(ys):
                row = [t[4] for t in sorted(rows[y], key=lambda t: t[0])]
                nxt = None
                if k + 1 < len(ys) and 0 < ys[k + 1] - y < 13:
                    nxt = [t[4] for t in sorted(rows[ys[k + 1]], key=lambda t: t[0])]
                ordered_rows.append((row, nxt))

    txns = []
    in_buy = False
    holder = "Diego"  # titular until a card header switches it
    for toks, nxt in ordered_rows:
        line = " ".join(toks)
        low = line.lower()
        if SECTION_START in low:
            in_buy = True
            continue
        if any(s in low for s in SECTION_STOP):
            in_buy = False
            continue
        ch = _cardholder_from_line(line)
        if ch:
            holder = ch
        if not in_buy:
            continue
        dates = [t for t in toks if DATE.match(t)]
        vals = [t for t in toks if VAL.match(t)]
        if not dates or not vals:
            continue
        date, val = dates[0], vals[-1]
        di = toks.index(date)
        vi = len(toks) - 1 - toks[::-1].index(val)
        merchant = " ".join(toks[di + 1:vi]).strip()
        amount = _money(val)
        if "-" in toks[max(0, vi - 1):vi] or merchant.endswith("-"):
            amount = -amount  # estorno / crédito
            merchant = merchant.rstrip(" -")
        raw_cat = ""
        if nxt and not any(DATE.match(t) for t in nxt) and not any(VAL.match(t) for t in nxt):
            raw_cat = " ".join(nxt)
        txns.append({
            "date": date,
            "merchant": merchant or (raw_cat.split(".")[0].strip() or "—"),
            "amount": amount,
            "raw_cat": raw_cat,
            "cardholder": holder,
        })

    page0 = doc[0].get_text()
    m_total = re.search(r"Total desta fatura\s*\n\s*-?\s*([\d\.]+,\d{2})", page0)
    total = _money(m_total.group(1)) if m_total else None
    m_venc = re.search(r"Vencimento:\s*(\d{2})/(\d{2})/(\d{4})", page0)
    if m_venc:
        ref_year, ref_month = int(m_venc.group(3)), int(m_venc.group(2))
    else:
        ref_year, ref_month = datetime.now().year, datetime.now().month

    # Card fees from the statement subtotals: interest/penalty (encargos) and
    # annuity/service charges (produtos e serviços).
    full = "\n".join(doc[p].get_text() for p in range(doc.page_count))

    def _grab(label):
        m = re.search(re.escape(label) + r"\s*\n\s*-?\s*([\d\.]+,\d{2})", full)
        return _money(m.group(1)) if m else 0.0

    def _charge(label):
        # Encargo line layout: "<label>\n<rate> %...\n<value>". Take the value.
        m = re.search(re.escape(label) + r"\s*\n\s*[\d.,]+\s*%[^\n]*\n\s*([\d\.]+,\d{2})", full)
        return _money(m.group(1)) if m else 0.0

    iof_m = re.search(r"IOF de financiamento\s*\n\s*\([^)]*\)\s*\n\s*([\d\.]+,\d{2})", full)
    fees = {
        "juros_rotativo": _charge("Juros do rotativo"),
        "juros_mora": _charge("Juros de mora"),
        "multa_atraso": _charge("Multa por atraso"),
        "iof_financiamento": _money(iof_m.group(1)) if iof_m else 0.0,
        "produtos_servicos": _grab("Lançamentos produtos e serviços"),  # anuidade + tarifas + atraso
        "encargos_total": _grab("Total de encargos em R$"),  # for validation
    }
    return txns, total, ref_year, ref_month, fees


def _clamp_day(day: int, ref_year: int, ref_month: int) -> int:
    """Clamp a day into the valid range of the reference month.

    The purchase day-of-month is preserved so transactions spread realistically
    across their statement month. For the current (incomplete) month nothing may
    fall in the future, so days past today are folded back across the elapsed
    days of the month — this avoids future dates without piling everything on a
    single day.
    """
    last = monthrange(ref_year, ref_month)[1]
    day = min(max(day, 1), last)
    today = datetime.now()
    if (ref_year, ref_month) == (today.year, today.month) and day > today.day:
        day = ((day - 1) % today.day) + 1
    return day


def _expense_date(dd_mm: str, ref_year: int, ref_month: int) -> datetime:
    """Place a transaction within the invoice's reference month, keeping its day-of-month.

    Uses midday so the displayed calendar day stays correct across timezone
    offsets (a midnight UTC value would render as the previous day in BRT).
    """
    try:
        day = int(dd_mm.split("/")[0])
    except (ValueError, IndexError):
        day = 1
    return datetime(ref_year, ref_month, _clamp_day(day, ref_year, ref_month), 12, 0)


def import_dir(directory: str, username: str, reset: bool) -> int:
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        if not user:
            print(f"❌ user '{username}' not found. Create it first.")
            return 1

        if reset:
            n_exp = db.query(Expense).filter(Expense.user_id == user.id).delete()
            n_inv = db.query(Invoice).filter(Invoice.user_id == user.id).delete()
            db.commit()
            print(f"🧹 reset: removed {n_exp} expenses and {n_inv} invoices for '{username}'")

        pdfs = sorted(glob.glob(os.path.join(directory, "*.pdf")))
        if not pdfs:
            print(f"❌ no PDF files found in {directory}")
            return 1

        grand_total = 0.0
        for path in pdfs:
            txns, total, ref_year, ref_month, fees = parse_invoice(path)
            domestic = round(sum(t["amount"] for t in txns), 2)
            reconciliation = round((total or domestic) - domestic, 2)
            # Split the reconciliation into itemised card fees (straight from the
            # statement) + remainder (international purchases).
            fee_lines = [
                ("Juros do rotativo (Itaú)", fees.get("juros_rotativo", 0.0),
                 "Juros do crédito rotativo"),
                ("Juros de mora (Itaú)", fees.get("juros_mora", 0.0),
                 "Juros de mora por atraso de pagamento"),
                ("Multa por atraso (Itaú)", fees.get("multa_atraso", 0.0),
                 "Multa de 2% sobre o saldo por atraso de pagamento"),
                ("IOF de financiamento (Itaú)", fees.get("iof_financiamento", 0.0),
                 "IOF sobre financiamento/parcelamento"),
                ("Anuidade e tarifas do cartão (Itaú)", fees.get("produtos_servicos", 0.0),
                 "Anuidade + tarifas + encargos de atraso (produtos e serviços)"),
            ]
            fees_total = round(sum(v for _, v, _ in fee_lines), 2)
            international = round(reconciliation - fees_total, 2)

            invoice = Invoice(
                user_id=user.id,
                filename=os.path.basename(path),
                file_path=path,
                status=InvoiceStatus.PROCESSED,
                processed_at=datetime.utcnow(),
                invoice_metadata={
                    "bank": "Itau",
                    "reference": f"{ref_year}-{ref_month:02d}",
                    "invoice_total": total,
                    "itemized_domestic": domestic,
                    "reconciliation": reconciliation,
                    "item_count": len(txns),
                },
            )
            db.add(invoice)
            db.flush()  # get invoice.id

            for t in txns:
                cat = _resolve_category(t["raw_cat"], t["merchant"])
                db.add(Expense(
                    user_id=user.id,
                    invoice_id=invoice.id,
                    cardholder=t.get("cardholder"),
                    date=_expense_date(t["date"], ref_year, ref_month),
                    merchant=t["merchant"][:255],
                    amount=t["amount"],
                    category=cat,
                    ai_category=cat,
                    description=t["raw_cat"] or None,
                    tags=["itau", f"{ref_year}-{ref_month:02d}"],
                    expense_metadata={
                        "purchase_date": t["date"],
                        "itau_category": t["raw_cat"],
                        "cardholder": t.get("cardholder"),
                    },
                ))

            last_day = _clamp_day(monthrange(ref_year, ref_month)[1], ref_year, ref_month)
            charge_date = datetime(ref_year, ref_month, last_day, 12, 0)

            def _add_charge(merchant, amount, category, desc, kind):
                if abs(round(amount, 2)) < 0.01:
                    return
                db.add(Expense(
                    user_id=user.id,
                    invoice_id=invoice.id,
                    cardholder="Diego",  # account titular bears fees / int'l on titular card
                    date=charge_date,
                    merchant=merchant,
                    amount=round(amount, 2),
                    category=category,
                    ai_category=category,
                    description=desc,
                    tags=["itau", kind, f"{ref_year}-{ref_month:02d}"],
                    expense_metadata={"kind": kind},
                ))

            for merchant, amount, desc in fee_lines:
                _add_charge(merchant, amount, ExpenseCategory.FEES, desc, "fee")
            _add_charge(
                "Lançamentos internacionais (Itaú)", international, ExpenseCategory.OTHER,
                "Compras internacionais + IOF (não itemizadas)", "international",
            )

            db.commit()
            imported_total = domestic + (reconciliation if abs(reconciliation) >= 0.01 else 0)
            grand_total += imported_total
            ok = "✅" if total is None or abs(imported_total - total) < 0.01 else "⚠️"
            print(
                f"{ok} {os.path.basename(path)}  ref={ref_year}-{ref_month:02d}  "
                f"itens={len(txns):>3}  domestico={domestic:>10,.2f}  "
                f"reconc={reconciliation:>9,.2f}  total={imported_total:>10,.2f}"
                + ("" if total is None else f"  (fatura={total:,.2f})")
            )

        print(f"\n💰 total geral importado: R$ {grand_total:,.2f}")
        return 0
    finally:
        db.close()


def main():
    ap = argparse.ArgumentParser(description="Import Itaú PDF statements into SpendTrack")
    ap.add_argument("directory", help="directory containing Itaú *.pdf statements")
    ap.add_argument("--user", default="diego", help="username or email to attach expenses to")
    ap.add_argument("--reset", action="store_true",
                    help="delete the user's existing expenses/invoices before importing")
    args = ap.parse_args()
    sys.exit(import_dir(args.directory, args.user, args.reset))


if __name__ == "__main__":
    main()
