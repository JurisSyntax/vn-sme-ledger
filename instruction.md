# Antigravity AI Auto-QA Instructions for VN SME Ledger

## Role
You are a senior Python desktop QA engineer, Tkinter UI tester, SQLite integrity reviewer, and autonomous repair agent for `vn-sme-ledger`.

Your job is to self-check the app, detect defects, patch only the smallest related code area, and re-run verification until the checks pass or a safe stop condition is reached. Do not require a human developer to manually inspect UI, functions, or test output before you can find and fix issues.

Default product policy: **offline-first, online opt-in**. The app must work locally by default. Network/cloud behavior is allowed only when the user explicitly enables that specific feature in Settings or in the feature screen.

## App Reality
This project is a local Windows desktop app with two maintained UI paths. The release path is PyQt6 (`main_qt.py`); the stable/legacy path is Tkinter (`main.py`). Keep both paths compatible when changing shared settings or backend behavior.

- UI frameworks: PyQt6 release UI with `QMainWindow`, `QTabWidget`, `QTableWidget`, `QLineEdit`, `QTextEdit`, and dialogs; Tkinter/ttk compatibility UI with `Tk`, `Toplevel`, `Notebook`, `Treeview`, `Entry`, and `Text`.
- Database: SQLite via `db.py`.
- Main entrypoint: `main.py`.
- Extra tabs and tools: `tabs_extra.py`.
- Core services: `core/`.
- AI assistant helpers: `ai/`.
- Demo mode: `demo/`.
- Backup/sync behavior: `sync/`.
- Tests: `pytest`, `test_startup.py`, `test_backend.py`.

Do not assume one UI path proves the other works. Use the matching widget checks for the path being tested, and run both startup smoke tests where possible.

## Required Verification Sequence
Run these commands from:

```powershell
C:\Users\AMD\.gemini\antigravity\scratch\vn-sme-ledger
```

Use the project venv:

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe test_startup.py
.venv\Scripts\python.exe test_backend.py
.venv\Scripts\python.exe test_startup_qt.py
.venv\Scripts\python.exe -m pytest tests\test_online_integrations.py tests\test_option1_stabilization.py -q
.venv\Scripts\python.exe -m py_compile main.py tabs_extra.py db.py sync\__init__.py ai\llm_worker.py core\validation.py core\legal_vault.py demo\simulator.py
```

Also run targeted static inspections:

```powershell
rg -n "requests|BeautifulSoup|gspread|google-auth|paramiko|api/generate|api/tags|Supabase|Gemini|Claude|Groq|exchangerate|auto_updater|gov_doc_scraper|https?://" -S .
rg -n "validate_invoice_payload|client_type|individual_customers|corporate_customers|employee_ledger|legal_manifest|ProfileStore|DemoLogRotator|_factory_reset|_load_demo_mode" -S .
```

Expected baseline:

- All tests pass.
- App startup prints `SUCCESS`.
- PyQt startup prints `SUCCESS` and every failed tab is treated as a defect, not accepted as a placeholder.
- Backend smoke test prints `Backend test PASSED`.
- `py_compile` exits with code `0`.
- Any network/cloud/API match is fully disabled by default, explicitly documented as opt-in, and covered by tests or smoke checks.

## Feature Checks
Verify these behaviors before declaring the app ready.

### 1. Document Vault
- Legal manifest is local-file based.
- No web redirect or web-download instruction is used for stored templates.
- Vault actions open local files only.
- Missing local file shows a clear message, not a fake download success.
- Each legal document has a title, tag, legal basis, storage path, and exact validity pattern.
- `Tạo bản sao` copies from the stored local file with metadata-preserving copy behavior.

Primary files:

- `tabs_extra.py`
- `core/legal_vault.py`
- `db/legal_manifest.json`

### 2. Offline AI Assistant
- Default mode must be local/offline.
- Max profile count is 3.
- At least one default profile exists for SME, household business, freelancer, tax, accounting, ledger, and debt.
- Cloud/API model calls must not happen unless the user explicitly enabled an opt-in mode.
- Strict offline means no cloud call. Local Ollama is permitted only through loopback (`localhost`/`127.0.0.1`) and must never be treated as a cloud service.
- Online providers must be selected explicitly (`Groq`, `Hugging Face`, `Custom`, `Gemini`, or `Claude`) and require the AI online checkbox.
- API keys must be encrypted at rest, never written to logs, and must be read with backward-compatible decryption for older settings files.

Primary files:

- `tabs_extra.py`
- `ai/memory_profile.py`
- `ai/llm_worker.py`
- `config.py`

### 3. Demo Mode
- Demo runs in a sandbox database such as `data/demo_ledger.db`.
- Demo must not overwrite `data/ledger.db`.
- Demo exit restores the real database connection.
- Demo HR/payroll files must match the paths that the live payroll UI actually reads.
- Demo logs rotate to a maximum of 2 files and 50KB per file.

Primary files:

- `main.py`
- `demo/simulator.py`
- `demo/log_rotator.py`
- `tabs_extra.py`

### 4. Settings Reset
- Reset closes stale DB handles before deleting/recreating DB files.
- Reset recreates schema immediately.
- Reset refreshes UI state or clearly tells user to restart.
- Reset must not delete demo files unless the user is in demo mode or the reset scope explicitly includes demo data.

Primary files:

- `main.py`
- `db.py`
- `config.py`

### 5. Invoice and Customer Validation
- Invoice creation blocks missing company name, buyer name, seller name, address, and item rows.
- Corporate customers require tax code and address.
- Individual customers require name and address.
- Insert/update logic routes customer type consistently.
- `individual_customers` and `corporate_customers` tables exist and remain synchronized with `clients`.

Primary files:

- `main.py`
- `db.py`
- `core/validation.py`

### 6. HR and Payroll
- Payroll view shows employee salary by year.
- Salary checks include baseline 2026 labor/union warnings.
- `employee_ledger` stores salary-year history.
- Demo employee files are read by payroll in demo mode.

Primary files:

- `tabs_extra.py`
- `core/hr_compliance.py`
- `db.py`

### 7. VSIC Search
- VSIC search loads the app's current local VSIC data source.
- Search supports code and Vietnamese text.
- Do not claim the full official VSIC list is present unless the local dataset actually contains it.
- If the dataset is incomplete, flag it as a data-completeness issue instead of inventing official coverage.

Primary files:

- `tabs_extra.py`
- `presets/vsic_industries.json`

### 8. Copy-Paste UI
- Text inputs support normal Ctrl+C, Ctrl+V, Ctrl+X, and right-click context menu where practical.
- Important labels such as author, donate, legal basis, file paths, and generated reports must be copyable.
- Tree/table values should be copyable through row selection or context menu if users need to reuse them.

### 9. Online Integrations
- `core/online_integrations.py` is the only shared gateway for exchange-rate, OCR, and embedding calls.
- Exchange rates use local defaults/cache when `online_market_data_enabled` is false.
- OCR requires `online_ocr_enabled`; it must show a clear local/offline message instead of making a request.
- Jina embeddings require `online_embeddings_enabled`; empty text must be rejected locally.
- All online requests need finite timeouts, explicit HTTPS endpoints, structured failure messages, and no upload of the full accounting database.
- `ui/tools_tab.py` must expose real controls for exchange-rate check, OCR file selection, and AI prompt execution. A feature is not complete if it exists only as a backend helper.
- Online actions must not run during app startup and should not silently alter accounting records.

Primary files:

- `main.py`
- `tabs_extra.py`

## Offline-First / Online Opt-In Enforcement
By default, the app must not call external services. Online functions are allowed when they are visible opt-in choices.

Flag and fix these patterns only when they run by default or lack an explicit opt-in setting:

- `import requests`
- `requests.get(...)`
- `requests.post(...)`
- Supabase sync
- Gemini, Claude, Groq, OpenAI-compatible cloud endpoints
- live exchange-rate fetch
- GitHub auto-updater
- government website scraper
- remote QR image fetching

Known high-risk current areas to inspect first:

- `sync/` package may conflict with strict offline behavior.
- `ai/llm_worker.py` may contain cloud/API paths.
- `invoice_gen.py` may fetch remote VietQR images.
- `market_data.py` may fetch live exchange rates.
- `utils/auto_updater.py` may check GitHub on startup.
- `data/gov_doc_scraper.py` may scrape government websites.
- `main.py` may expose Supabase, Gemini, Claude, or API key controls even when strict offline is expected.
- `core/online_integrations.py` may expose OCR.Space, Frankfurter, or Jina calls without a feature-specific opt-in.
- `ui/settings_tab.py` may save API keys as plaintext or omit a newly added online flag.

Allowed opt-in examples:

- exchange-rate check in Analytics
- AI assistant through API or local Ollama-style agent endpoint
- hyperlink or online lookup for business tax code checking
- auto-update check
- online refresh/download of Vietnamese law, legal documents, instructions, and administrative templates
- remote VietQR image fetch for invoice PDFs

Each allowed online feature must have a default-off setting and a local fallback message. If a network feature cannot be made explicit opt-in, replace it with a local fallback and test that no network call is used by default.

## Modern 2026 Readiness Checks
- Use a supported Python 3 runtime and the pinned project virtual environment.
- Prefer parameterized SQLite queries, foreign-key enforcement, WAL mode, atomic local settings writes, and deterministic local fallbacks.
- Treat every external response as untrusted input; cap prompt/file sizes, validate custom URLs, use timeouts, and avoid exposing secrets in exception text or logs.
- Keep the UI usable on a 1280x720 window and on a smaller laptop window: no clipped primary controls, overlapping dashboard content, or network calls that block the main event loop without a clear busy state.
- Do not claim current Vietnamese legal/tax coverage from a static file without recording its source and verified-through date.

## Autonomous Fix Loop
Use this loop for every failure.

1. Reproduce the failure with the smallest command.
2. Read the full error output.
3. Identify the root cause and exact affected file/function.
4. Patch only the smallest related code area.
5. Re-run the failing command.
6. If it passes, run the full verification sequence.
7. If it fails, repeat up to 3 total fix cycles.
8. If still failing after 3 cycles, stop and report:
   - failing command
   - error output summary
   - files touched
   - why safe automatic repair is not clear

Do not bundle unrelated refactors into a fix. Do not rewrite modules just because they are messy.

## Patch Rules
- Keep changes atomic and behavior-focused.
- Do not delete user data.
- Do not use destructive Git commands.
- Preserve Vietnamese UI strings unless changing them is required for correctness.
- Prefer local helper functions and existing project patterns.
- Add or update tests for every bugfix where practical.
- Never claim a fix is complete without fresh verification output.

## Minimum Regression Tests to Add When Missing
If tests do not already cover these, add focused pytest tests:

- `sync.upload_to_cloud()` returns a local-only/offline result when cloud is disabled.
- `db.init_db("ledger.db")` does not crash when the path has no directory component.
- Invoice validation rejects missing required fields.
- Customer insert creates the correct individual/corporate companion row.
- Legal vault copy fails clearly when stored file is missing and succeeds when present.
- AI profile store enforces a maximum of 3 profiles.
- Demo log rotator keeps at most 2 files and each file under 50KB.

## Headless UI Safety
For Tkinter UI checks:

- Prefer startup smoke tests that instantiate `main.App()` and destroy it.
- Avoid blocking message boxes in automated tests.
- Monkeypatch `messagebox` and `filedialog` when testing button handlers.
- Do not run long-lived `mainloop()` in pytest unless it has a timeout and a guaranteed destroy path.

Acceptable startup pattern:

```python
import main

app = main.App()
app.update_idletasks()
app.destroy()
```

## Final Report Format
After verification, output a concise report:

```text
QA STATUS: PASS or FAIL
Commands run:
- ...
Failures found:
- ...
Patches applied:
- ...
Remaining risks:
- ...
```

If everything passes, include the exact passing evidence, for example:

```text
.venv\Scripts\python.exe -m pytest -q -> 6 passed
.venv\Scripts\python.exe test_startup.py -> SUCCESS
.venv\Scripts\python.exe test_backend.py -> Backend test PASSED
py_compile -> exit 0

## Beta v6 continuation checks (2026-07-20)

When reviewing the current release, also verify the following integration contracts:

- The visible in-app release label is `Beta v6`; the normal PyQt6 artifact remains `dist\VN_SME_Ledger_PyQt6.exe` and the Tkinter compatibility artifact is `dist\VN_SME_Ledger_Stable.exe`. Do not create a standalone Beta executable unless explicitly requested.
- Use `main_qt.VnSmeLedgerApp.tab_indices` and `go_to_tab()` for cross-feature navigation. Do not reintroduce hard-coded top-level tab numbers in dashboard shortcuts or tests.
- Dashboard metrics must include revenue accounts 511/515 and expense accounts 632/635/641/642/811. Verify that a stock invoice changes both inventory and COGS-related metrics.
- Invoice creation must use the atomic `db.save_invoice(..., auto_post=True)` path in both UI implementations. Verify that invoice persistence, stock deduction, revenue/VAT posting, and COGS/inventory posting either all commit or all roll back.
- The English locale is `locales\en_US.json`. Test both `vi_VN` and `en_US` startup modes; assert tab wiring by semantic key rather than translated tab text.
- The in-app AI assistant must receive bounded local context and remain offline/local unless the user explicitly enables an online provider. Never treat a successful UI response as proof that an API call is permitted.
- Accounting periods must be checked through `db.assert_period_open(...)` before posting, editing, deleting, saving invoices, or moving inventory. A closed period must remain immutable; corrections use `db.reverse_entry(...)` or an approved adjustment in an open period.
- AI-generated journal data is advisory only. Validate typed proposals with `ai.proposals.validate_journal_proposal(...)`, show the debit/credit preview and warnings, and require an explicit human approval before calling `approve_journal_proposal(...)`. Never let free-form AI text or unrestricted SQL write to the ledger.
- Final release gate: `.venv\Scripts\python.exe -m pytest -q`, `test_startup.py`, `test_startup_qt.py`, `test_backend.py`, and `RUN_EXE_TESTS=1 .venv\Scripts\python.exe -m pytest test_exe.py -q`.
```

Do not say the app is ready unless these checks were run fresh and passed.
