# BigCommerce Coupon Code Uploader CLI

Easily bulk‑upload coupon codes to **BigCommerce**. A *promotion* in BigCommerce is a marketing rule (e.g. “10 % off”) that can optionally be redeemed with unique coupon codes; this CLI automates pushing long lists of those codes straight to your store.

---

## ✨ Features

- **Bulk uploads** – send up to 100 codes per run (override with `--max-codes`)
- **CSV sanity checks** – detects empty files, missing columns, negative numbers, etc.
- **Promotion discovery** – list existing promotions so you can copy the ID
- **Per‑code limits** – assign `max_uses` & `max_uses_per_customer` per line
- **Clear summary** – success count plus a preview of the first few errors
- Pure Python ≥ 3.8, only standard library + [`requests`](https://pypi.org/project/requests/) 📦

---

## ⚙️ Requirements

| Requirement | Details |
|-------------|---------|
| Python      | 3.8 or newer |
| BigCommerce | API token with scope `content:modify promotions` – see [API scopes](https://developer.bigcommerce.com/api-docs/store-management/authentication#scopes) and [creating API accounts](https://developer.bigcommerce.com/api-docs/getting-started/api-accounts#create-a-store-api-account) |

Install dependencies (recommended inside a virtual environment):

```bash
pip install -r requirements.txt
```

---

## 🛠 Installation

Clone the repo and make the script executable:

```bash
git clone git@github.com:springmerchant/bigcommerce-bulk-coupon-importer.git
cd bigcommerce-bulk-coupon-importer
chmod +x bc_coupon_uploader.py
```

Or install globally with [`pipx`](https://pipx.pypa.io/):

```bash
pipx install git+https://github.com/springmerchant/bigcommerce-bulk-coupon-importer.git
```

---

## ⚡ Quick‑start

```bash
# 1. List promotions to grab an ID
./bc_coupon_uploader.py --store-hash ABC123 --token $BC_TOKEN --list-promotions

# 2. Upload codes from a CSV to promotion 42
./bc_coupon_uploader.py --store-hash ABC123 --token $BC_TOKEN --promotion-id 42 --file sample_file.csv
```

---

## 🚀 Detailed Usage

### CSV format

```
Code,MaxUses,MaxUsesPerCustomer
SAVE10,1,1
WELCOME20,50,1
FREESHIP,,
```

- Use 0 for **MaxUses** or **MaxUsesPerCustomer** if you want unlimited uses.
- The default upload cap is **100** rows (override with `--max-codes`).

### Command‑line options

| Flag                | Required       | Description                                     |
| ------------------- | -------------- | ----------------------------------------------- |
| `--store-hash`      | ✅              | Your BigCommerce store hash                     |
| `--token`           | ✅              | API access token                                |
| `--promotion-id`    | When uploading | Target promotion ID                             |
| `--file`            | When uploading | Path to CSV file                                |
| `--list-promotions` |                | List available promotions and exit              |
| `--max-codes`       |                | Upload cap (default 100)                        |

---

## 🐞 Error Handling & Exit Codes

| Exit code | Meaning                           |
|-----------|-----------------------------------|
| **0**     | Success or user‑cancelled upload  |
| **1**     | Fatal error (invalid CSV, API error, etc.) |

During an upload the CLI streams warnings to `stdout`; redirect output to capture logs:

```bash
./bc_coupon_uploader.py ... 2>&1 | tee upload.log
```

---

## 🖥️ Prefer a GUI? Try CouponBrew

If you’d rather manage coupons through a point‑and‑click interface—or need to import **hundreds of thousands** (even **millions**) of codes—check out our companion BigCommerce app [**CouponBrew**](https://www.bigcommerce.com/apps/couponbrew/).

- Upload & generate massive coupon files.
- Pprogress dashboards and detailed error reporting.
- Bulk actions (delete), and works with both legacy and promotional coupon codes

Install it from the BigCommerce App Marketplace and start pushing giant code lists in minutes.

---

## 🤝 Contributing

Pull requests welcome! Please format with `ruff` / `black` and add unit tests for new behaviour.

---

## 📄 License

MIT – see `LICENSE`.

---

## 💬 Need Help?

- Official docs: <https://developer.bigcommerce.com/docs>
- Open an issue in this repo for bugs or feature requests.
