# Sistema de Inventario / Inventory System

A local desktop inventory, sales, and reporting application for a small
mom-and-pop shop. Single user, single machine, no server, no cloud, no
accounts. Data lives in one SQLite file next to the app.

Bilingual interface: Spanish and Arabic, with automatic right-to-left
layout when Arabic is selected. Every product is stored with both an
Arabic name and a Spanish name regardless of which language the interface
chrome is currently showing.

## Stack

- Python 3.13
- PySide6 (Qt for Python) - UI
- SQLAlchemy 2.x - ORM over SQLite
- Pillow - product image handling
- pytest + pytest-qt - tests
- PyInstaller - Windows packaging

## Project layout

```text
main.py                     Entry point
app/
  errors.py                 AppError hierarchy (translatable messages)
  i18n.py                   es/ar string tables, t(), RTL handling
  logging_setup.py          Rotating file logging + excepthook
  database/
    database.py             Engine, SQLite pragmas, transaction wiring
    models.py                items / stock_purchases / sales / sale_items / settings
    types.py                 Money TypeDecorator (Decimal <-> scaled INTEGER)
    repositories/            Thin data-access layer used only by services
  services/
    costing.py                Weighted-average cost formula (pure)
    sale_draft.py              In-memory sale-in-progress (pure)
    inventory_service.py       Product CRUD + add-stock transaction
    sales_service.py           complete_sale transaction
    report_service.py          All report calculations
    settings_service.py        Key/value app settings
    backup_service.py          SQLite online backup
  ui/
    main_window.py            Shell: nav, language toggle, menus
    app_context.py            Wires services together for the UI
    dashboard/, products/, sales/, reports/, widgets/
  utils/
    money.py, dates.py, paths.py, images.py
images/items/                Product photos (created at runtime)
logs/                        app.log (created at runtime)
tests/                       pytest suite (see "Testing" below)
InventorySystem.spec         PyInstaller build spec (see "Windows build")
```

## Setup

Requires Python 3.13 (PySide6 6.11 and PyInstaller both support 3.10-3.15;
3.13 is used here for the widest compatibility with both). Using
[`uv`](https://docs.astral.sh/uv/) to manage the virtual environment:

```bash
uv venv --python 3.13 .venv
uv pip install -r requirements-dev.txt --python .venv/bin/python
```

`requirements.txt` lists only the runtime dependencies (what a packaged
build needs); `requirements-dev.txt` adds pytest, pytest-qt, and
PyInstaller on top for development.

## Running the app

```bash
.venv/bin/python main.py
```

On first run this creates, next to `main.py`:

- `store.db` - the SQLite database (tables + default settings)
- `images/items/` - where product photos are saved
- `logs/app.log` - rotating application log (1 MB x 3 files)
- `backups/` - created on first use of File > Backup Database

### Where is the database?

`app/utils/paths.py` resolves a single writable "base directory":

- Running `python main.py` normally: the project root (next to `main.py`).
- Running the packaged `.exe`: the folder containing the executable.
- Running tests: overridden via the `INVENTORY_APP_DATA_DIR` environment
  variable (set automatically by the `session_factory` test fixture), so
  tests never touch a developer's real `store.db`.

The status bar at the bottom of the main window always shows the full
path to the database file currently in use.

## Testing

```bash
.venv/bin/python -m pytest
```

Every test uses a real temp-file SQLite database (via the `session_factory`
fixture in `tests/conftest.py`) rather than mocks, per the project's `tdd`
skill. The Qt smoke tests (`tests/test_smoke_ui.py`) build the real
`MainWindow` and drive its actual widgets end-to-end (create a product, add
stock at a new price, complete a sale, generate a report) with
`QT_QPA_PLATFORM=offscreen`, which `tests/conftest.py` sets automatically
so the suite runs without a display (e.g. over SSH or in CI). If a display
is available and `QT_QPA_PLATFORM` is already set in your environment,
that value is respected instead.

Test files:

| File | Covers |
|---|---|
| `test_money.py`, `test_dates.py` | Pure money/date utilities |
| `test_schema.py` | Constraints, cascades, FK enforcement, transaction rollback |
| `test_purchase_cost.py` | `weighted_average_cost` (including the spec's 0.7333 example) |
| `test_sale_draft.py` | In-memory `SaleDraft`: merging, oversell rejection |
| `test_inventory.py` | `InventoryService`: create/update/archive/delete/add-stock |
| `test_sales.py` | `SalesService.complete_sale`: rollback, cost snapshotting |
| `test_reports.py` | `ReportService`: every report field, period boundaries |
| `test_smoke_ui.py` | Full UI workflows against a real database |

## Backups

**File > Backup Database** copies `store.db` using SQLite's online backup
API (safe to run while the app has the database open, including under
WAL mode) into `backups/store-YYYYMMDD-HHMMSS.db`, plus a
`backups/images-YYYYMMDD-HHMMSS.zip` of the product photos.

There is no cloud/remote backup target built in. To keep an off-machine
copy, periodically copy the `backups/` folder (or the whole app folder) to
a USB drive or a cloud-synced folder (Dropbox, Google Drive, OneDrive)
from outside the app.

## Windows build

PyInstaller cannot cross-compile: **the `.exe` must be built on a Windows
machine.** This repository ships `InventorySystem.spec`; running it is a
two-step process:

1. On a Windows machine, install Python 3.13 (matching the development
   environment's minor version avoids subtle binary-compatibility issues)
   and set up the same virtual environment:

   ```powershell
   py -3.13 -m venv .venv
   .venv\Scripts\pip install -r requirements-dev.txt
   ```

2. Build:

   ```powershell
   .venv\Scripts\pyinstaller InventorySystem.spec --clean --noconfirm
   ```

This produces a one-folder (`--onedir`) windowed build under `dist/`:

```text
dist/InventorySystem/
  InventorySystem.exe
  _internal/                 (PySide6, SQLAlchemy, Pillow, etc.)
  store.db                   (created on first launch)
  images/items/               (created on first launch)
  logs/                       (created on first launch)
  backups/                    (created on first backup)
```

One-folder rather than one-file: this keeps `store.db` and `images/`
genuinely adjacent to the executable, avoiding one-file mode's temp-extraction
directory (which would otherwise make "where is my data" ambiguous). To
distribute the app, zip the entire `InventorySystem/` folder; to move an
existing installation (with its data) to a new machine, copy the whole
folder, not just the `.exe`.

## Known limitations (by design, v1)

These were explicitly out of scope for this version rather than oversights:

- No stock adjustments for damage, theft, or shrinkage -- only purchases
  and sales move stock.
- No sale returns or voids.
- Quantities are always whole numbers (no fractional/weighted units).
- No multi-user accounts, logins, or cashier tracking -- single shop,
  single operator.
- Timestamps are naive local time (no timezone handling); a report window
  spanning a daylight-saving transition will be off by an hour. Fine for a
  single-location shop.
- Weighted-average cost is quantized to 4 decimal places after every
  purchase, so repeated re-averaging can drift the recorded inventory cost
  by a fraction of a cent over many purchases. This is an accepted,
  well-understood property of weighted-average costing, not a bug.
- `low_stock_threshold` is one global setting, not configurable per
  product.
# pos
