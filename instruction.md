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
.venv\Scripts\python.exe -m py_compile main.py tabs_extra.py db.py sync\__init__.py ai\llm_worker.py core\validation.py core\legal_vault.py core\import_service.py core\payment_promises.py core\cash_forecast.py core\order_flow.py core\order_reports.py ui\ar_ap_tab.py ui\invoices_tab.py demo\simulator.py
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

### 9. Local CSV/XLSX Import
- `Báo cáo > Nhập dữ liệu` accepts only local CSV/XLSX files within the configured size and row limits.
- Preview must not create import tables, inventory logs, journal rows, invoices, or other business data.
- Validate the selected profile, required columns, date/period lock, inventory item identity, direction, quantity, cost, account lines, and journal balance.
- Vietnamese and English headers may be recognized, but an explicit mapping must reject unknown fields and missing source columns.
- Duplicate rows must be marked by stable fingerprints. Never silently merge, overwrite, or coerce malformed values such as fractional inventory IDs.
- Export rejected and duplicate rows to a local UTF-8 report. Commit requires an identifiable accountant confirmation and an unchanged source hash.
- Commit accepted rows through existing inventory/posting services in one transaction. A later failure must rollback the complete batch, including audit rows.

Primary files:

- `core/import_service.py`
- `core/inventory.py`
- `core/posting_service.py`
- `ui/reports_tab.py`

### 10. Payment Promises and Collection Queue
- A payment promise is a local planning record linked to exactly one open AR/AP invoice.
- It must store direction, party, promised amount/date, owner, next-contact date, status, optional local evidence path, and an audit event history.
- Creating or changing a promise must not create a receipt/payment, allocate a settlement, reduce an invoice balance, or rewrite journal rows.
- Allow only explicit status transitions. A completed promise is a workflow status, not proof that money was received or paid.
- The cash forecast may use the active promised amount/date as an explainable expected event, capped at the current invoice outstanding amount; actual cash remains ledger-derived.
- The collection queue must surface overdue contact/payment actions, settled invoices with stale promises, party names, invoice references, and the remaining balance.
- Generated reminders must be local editable DOCX files and clearly labelled internal management documents, not legal or filing-certified notices.

Primary files:

- `core/payment_promises.py`
- `core/cash_forecast.py`
- `ui/ar_ap_tab.py`

### 11. Online Integrations
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

## Beta v7 continuation checks (2026-08-02)

When reviewing the current release, also verify the following integration contracts:

- The visible in-app release label is `Beta v8`; the normal PyQt6 artifact remains `dist\VN_SME_Ledger_PyQt6.exe` and the Tkinter compatibility artifact is `dist\VN_SME_Ledger_Stable.exe`. Do not create a standalone Beta executable unless explicitly requested.
- Use `main_qt.VnSmeLedgerApp.tab_indices` and `go_to_tab()` for cross-feature navigation. Do not reintroduce hard-coded top-level tab numbers in dashboard shortcuts or tests.
- Dashboard metrics must include revenue accounts 511/515 and expense accounts 632/635/641/642/811. Verify that a stock invoice changes both inventory and COGS-related metrics.
- Invoice creation must use the atomic `db.save_invoice(..., auto_post=True)` path in both UI implementations. Verify that invoice persistence, stock deduction, revenue/VAT posting, and COGS/inventory posting either all commit or all roll back.
- The English locale is `locales\en_US.json`. Test both `vi_VN` and `en_US` startup modes; assert tab wiring by semantic key rather than translated tab text.
- The in-app AI assistant must receive bounded local context and remain offline/local unless the user explicitly enables an online provider. Never treat a successful UI response as proof that an API call is permitted.
- Accounting periods must be checked through `db.assert_period_open(...)` before posting, editing, deleting, saving invoices, or moving inventory. A closed period must remain immutable; corrections use `db.reverse_entry(...)` or an approved adjustment in an open period.
- AI-generated journal data is advisory only. Validate typed proposals with `ai.proposals.validate_journal_proposal(...)`, show the debit/credit preview and warnings, and require an explicit human approval before calling `approve_journal_proposal(...)`. Never let free-form AI text or unrestricted SQL write to the ledger.
- Cash and bank workflow checks must cover receipt, payment, cash-to-bank transfer, other income/expense, owner capital, loan receipt/repayment, tax payment, and payroll settlement. Each preset must balance and must refresh ledger, cash/bank, receivable/payable, report, and dashboard data.
- The dashboard must show real cash/bank, receivable, payable, revenue, expense, and profit values from the ledger. Do not accept placeholder cards or a visually normal dashboard as proof of correct accounting.
- Legal-source buttons may open the approved 68/2025 and 89/2026 source pages only after `online_document_fetch_enabled` is enabled. Do not silently scrape, auto-download, bypass login/access controls, or treat third-party copies as authoritative without source metadata.
- At 100%, 125%, and 150% Windows display scaling, verify that the left navigation, `Danh mục` sub-tabs including `Tài sản cố định`, inventory category `Công cụ`, forms, table headers, buttons, and long Vietnamese labels do not overlap or clip.
- Final release gate: `.venv\Scripts\python.exe -m pytest -q`, `test_startup.py`, `test_startup_qt.py`, `test_backend.py`, and `RUN_EXE_TESTS=1 .venv\Scripts\python.exe -m pytest test_exe.py -q`.
```

Do not say the app is ready unless these checks were run fresh and passed.

## User-reported regression follow-up (2026-08-02)

When a user reports clipped text, blank VSIC, a narrow AI panel, a dead Help button, API failure, or a document-vault crash, verify the actual workflow as follows:

- Test both launchers. `run.bat` starts the Tkinter `main.py`; the PyQt6 release starts `main_qt.py`. A fix in an unused launcher is not sufficient.
- Start the Tkinter app with `test_startup.py` and the PyQt6 app with `QT_QPA_PLATFORM=offscreen .venv\Scripts\python.exe test_startup_qt.py`.
- Verify VSIC data from a different current working directory. Load through `utils.get_resource_path(...)`; do not use only `presets/...` relative to the current directory. The current local dataset must show nonzero rows and a count in the UI.
- Verify top-level PyQt pages are inside a resizable `QScrollArea`. At 100%, 125%, and 150% scaling, long headers, forms, tables, and Vietnamese labels must remain readable or reachable by scrolling.
- Verify the Analytics metric cards reflow from three to two to one columns as width decreases. Do not use a fixed five-card horizontal row that compresses labels.
- Verify the Tkinter Help button opens the Tools notebook and selects the Manual sub-tab. Verify the PyQt Tools header Help button displays actionable instructions.
- Verify the AI panel has a resizable chat area, a vertical scrollbar, a wrapped configuration area, a full-width prompt, and an explicit offline/API mode indicator.
- For exchange rates, use the verified Frankfurter v2 endpoint `https://api.frankfurter.dev/v2/rates` with `base` and `quotes`. Parse both the v2 list response and the older object response for compatibility. Keep offline fallback visible as offline reference data, not as an apparent successful API response.
- For Gemini, send the key through `x-goog-api-key`; never place it in a query string. Groq remains the documented OpenAI-compatible provider at `https://api.groq.com/openai/v1/chat/completions`. Both require the AI online opt-in flag and an API key.
- The document vault must validate Office container signatures. A renamed text file with `.docx` or `.xlsx` extension is not an official template and must be shown as an invalid internal draft.
- The `Thêm văn bản` workflow must validate the title, reject duplicate IDs, write the manifest atomically, and show a message instead of crashing. The PyQt dialog must use `QDialogButtonBox.StandardButton.Save | Cancel`.
- Timesheets must preserve regular, weekend, and holiday overtime separately, require an approval flag for payable overtime, retain a reason, and show warnings for negative values or monthly limits.

Do not mark the online/legal workflow as verified merely because a button exists. Run one live opt-in exchange-rate request, one mocked provider request, one offline-disabled request, one real local Office-file integrity check, and one duplicate-document rejection test.

## Beta v7 packaging and UI checks (2026-08-03)

- Treat `Beta v7` as the visible in-app version label only. Keep the normal artifacts named `VN_SME_Ledger_Stable.exe` and `VN_SME_Ledger_PyQt6.exe` unless the user explicitly requests an artifact rename.
- Use the bundled Be Vietnam font from `assets/fonts` for Vietnamese and English UI text. It is distributed under the included SIL Open Font License file. Register it for the current process only; do not install fonts globally or download fonts at runtime.
- Preserve the lean PyInstaller profile: exclude `pytest`, `_pytest`, and optional `scipy` from release bundles; exclude PyQt6/PySide6 from the Tkinter bundle. Do not exclude pandas, matplotlib, openpyxl, fpdf2, or Plotly if a user-facing workflow depends on them.
- The PyQt6 shell must keep one authoritative outer page scroll owner, use semantic sidebar routing, and avoid fixed-width rows that clip Vietnamese labels. Metric cards must show their labels and values and reflow from three to two to one columns as width decreases.
- Do not use emoji as structural UI icons when the bundled font cannot guarantee those glyphs. Prefer readable text, tooltips, or a real icon resource so screenshots and packaged launches do not contain missing-glyph boxes.
- Recheck the dashboard at 900x600 and 1280x860, the `Danh mục` asset and inventory forms, `Phân tích`, `Nhân sự`, `Công cụ`, and `Cài đặt`. Use screenshot inspection in addition to widget existence checks.
- Record the final one-file sizes and run `RUN_EXE_TESTS=1 .venv\Scripts\python.exe -m pytest test_exe.py -q` after every packaging change.

Latest verified evidence for this pass:

```text
.venv\Scripts\python.exe -m pytest -q -> 77 passed, 2 skipped
.venv\Scripts\python.exe test_startup.py -> SUCCESS
QT_QPA_PLATFORM=offscreen .venv\Scripts\python.exe test_startup_qt.py -> SUCCESS
RUN_EXE_TESTS=1 .venv\Scripts\python.exe -m pytest test_exe.py -q -> 2 passed
dist\VN_SME_Ledger_Stable.exe -> 73,299,380 bytes
dist\VN_SME_Ledger_PyQt6.exe -> 102,035,457 bytes
```

## Beta v7 accessibility and financial-insight pass (2026-08-03)

When reviewing the application for older or low-confidence computer users, test the workflow rather than only the visual appearance:

- The PyQt6 shell uses a larger Be Vietnam UI font, larger primary controls, 20px system icons, and a minimum 40px navigation row. Confirm that Vietnamese and English labels remain readable at 100%, 125%, and 150% Windows scaling.
- The left navigation has an accent-insensitive `Tìm tính năng...` search. Searching `phan` must find `Phân tích`, and clearing the search must restore every top-level workspace.
- The left navigation list has its own scroll area at 900x600 so `Hướng dẫn sử dụng` and the `Offline mặc định · Online khi bật` policy remain visible. The Help action must open the existing practical Tools help dialog.
- Do not use a blank dashboard, blank chart, or zero-value card as evidence that a feature works. With an empty ledger, show the first concrete action. With posted entries, verify that the chart canvas has real axes and that the visible recommendation matches the ledger state.
- `core/financial_insights.py` is the single source for dashboard and analytics metrics. Verify revenue from credit 511/515, expenses from debit 632/635/641/642/811, cash from 111/112/113, receivables from 131/138, payables from credit-nature 331/333/334/338, VAT output/input from 3331/133, and non-negative CIT estimates from profit before tax.
- Run `tests/test_financial_insights.py` with both empty and populated DataFrames. Confirm that recommendations route to the relevant top-level tab without changing ledger data.
- At 900x600 and 1280x860, inspect `Trang chủ`, `Phân tích`, `Danh mục`, `Nhân sự`, `Công cụ`, and `Cài đặt`. Check that card values, table headers, long Vietnamese labels, the action panel, and chart guidance are not clipped.

Fresh evidence for this pass:

```text
.venv\Scripts\python.exe -m pytest -q -> 77 passed, 2 skipped
.venv\Scripts\python.exe test_startup.py -> SUCCESS
QT_QPA_PLATFORM=offscreen .venv\Scripts\python.exe test_startup_qt.py -> SUCCESS
.venv\Scripts\python.exe test_backend.py -> Backend test PASSED
RUN_EXE_TESTS=1 .venv\Scripts\python.exe -m pytest test_exe.py -q -> 2 passed in 14.11s
populated analytics smoke -> 5 chart axes, 5 metric cards, chart guidance hidden
900x600 UI smoke -> Help and offline policy visible; navigation scroll active
dist\VN_SME_Ledger_PyQt6.exe -> 102,485,203 bytes
```

## Desktop `Mau` document-import checks (2026-08-03)

When the user supplies Vietnamese accounting drafts in `C:\Users\AMD\Desktop\Mau`, treat them as user data and preserve the originals. Do not overwrite, rename, or silently convert a source `.doc` file.

Required workflow:

1. Inventory all `.doc`, `.docx`, `.xls`, `.xlsx`, and `.pdf` files recursively and record the source filename, SHA-256, relative folder, and detected legal references.
2. Copy sources into `docs/templates_2026/mau_sources` and create editable DOCX copies in `docs/templates_2026/mau_editable`. A source `.docx` must pass ZIP/container validation before preparation.
3. Use `core.document_templates.prepare_editable_docx(...)` to add named placeholders without rebuilding the document layout. Handle Word text runs where a label and dotted blank are split across XML nodes, including leading `:` and non-breaking spaces.
4. Use `fill_docx_template(...)` to write a new working copy only. Never fill in place. Verify the output is a valid DOCX and that supplied values replace the expected tokens.
5. Import metadata into `db/legal_manifest.json` atomically. Every row must include title, purpose, legal basis, source path, storage path, source hash, review date, legal status, and editable fields.
6. In PyQt6, verify `Công cụ -> Kho văn bản mẫu` shows the imported rows, double-click opens the field form for DOCX rows, the preview changes while typing, `Save` writes under `docs/working_copies`, and `Xem file` remains available for free-form Word editing. A preserved `.doc` source row must show `needs_conversion` and must not pretend to be an editable DOCX.

Legal-status policy for the 2026 review:

- `Thông tư 58/2026/TT-BTC` is current for the micro-enterprise accounting scope from 01/07/2026; record the official Government Gazette URL and verified-through date.
- `Thông tư 99/2025/TT-BTC` is current for its enterprise accounting scope from 01/01/2026; record the official Government Gazette URL and verified-through date.
- Older invoice drafts, sample symbols, dates, and generic business names must be marked `reference_only_outdated` unless the current legal source is verified. Do not present them as current issuance forms.
- Public-asset, national-reserve, warehouse, and other scope-limited forms must be `needs_legal_review` when the source or authorized user scope is not established.
- A user-provided `.doc` that cannot be converted safely in the current environment must be `needs_conversion`; catalog the source hash and link the verified official DOCX replacement when available.
- A legal warning is not a deletion instruction. Keep the draft available for internal editing, but make the warning visible and prevent a claim that it is legally approved.

DOCX acceptance tests:

```powershell
.venv\Scripts\python.exe -m pytest -q tests\test_document_templates.py
.venv\Scripts\python.exe -m py_compile core\document_templates.py core\legal_vault.py ui\tools_tab.py
```

Run `render_docx.py` on at least one invoice and one accounting report when LibreOffice/Word rendering is available. If no renderer is installed, report that limitation and rely only on ZIP/XML integrity and fill/round-trip tests; do not claim visual layout approval.

Current imported-document evidence is recorded in:

- `C:\Users\AMD\Desktop\VN_SME_Ledger_Mau_Review_2026-08-03.md`
- `docs\templates_2026\mau_editable`
- `db\legal_manifest.json`

## Claude/Gemini integration review (2026-08-09)

The implementation reports on the Desktop are claims to verify against the source tree, not acceptance evidence. In particular, backend Phase 3 services do not count as complete until the PyQt6 Reports tab exposes the workflow and tests exercise it.

### Office application interoperability

- `core\office_integration.py` is the local launcher boundary for Microsoft Office, LibreOffice, Apache OpenOffice, SoftMaker FreeOffice, WPS Office, Polaris Office, and ONLYOFFICE Desktop Editors.
- The app may detect only executables installed on the local machine. It must never download an office suite or send a document to a cloud service.
- The system-default option must always be available. A missing suite must produce a readable message, not a crash or a false success.
- Word-compatible files (`.doc`, `.docx`, `.docm`, `.odt`, `.rtf`) and spreadsheet-compatible files (`.xls`, `.xlsx`, `.xlsm`, `.ods`, `.csv`) must be opened with the appropriate local editor where available.
- `Mở bằng...` must exist in both Tkinter and PyQt6 document-vault flows. It is an external-editor handoff; it is not evidence that the app can render every Office layout internally.
- Test unknown suite IDs, missing files, unsupported extensions, system-default selection, and a monkeypatched local executable. Do not require a particular office suite to be installed in CI.

### Accounting integration checks added after the reports

- AP journal entries use `journal_entries.supplier_id`; AR continues to use `client_id`. Existing databases must receive both columns through idempotent migrations.
- A voucher containing TK 331 must require a selected local supplier in the PyQt6 Documents tab. Verify that the posted row is visible under `Công nợ -> Phải trả (AP)` with the supplier name.
- `get_open_invoices(..., supplier_id=...)` must filter by supplier. Settlement allocation must reject a missing invoice, missing payment entry, non-positive amount, or amount above the outstanding invoice balance.
- Reports must expose both `Dòng tiền theo tháng` (TK 111/112) and `Đối chiếu ngân hàng`. Reconciliation is read-only: importing a CSV must never create, edit, or delete a journal entry.
- Reconciliation must show matched rows, unmatched bank rows, unmatched ledger rows, and malformed CSV rows. Amount parsing must cover common Vietnamese separators and date parsing must cover ISO and `DD/MM/YYYY` exports.
- AR/AP export must produce a real `.xlsx` workbook with separate AR/AP sheets when `openpyxl` is available, or a UTF-8 CSV when selected. A placeholder message is not acceptable.

### Required evidence for this integration pass

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m pytest -q tests\test_phase3_ui_and_supplier.py tests\test_supplier_settlement.py tests\test_phase3_reconciliation_cashflow.py tests\test_office_integration.py
.venv\Scripts\python.exe test_startup.py
.venv\Scripts\python.exe test_startup_qt.py
.venv\Scripts\python.exe test_backend.py
.venv\Scripts\python.exe -m py_compile db.py core\ar_ap.py core\office_integration.py core\reconciliation.py ui\documents_tab.py ui\ar_ap_tab.py ui\reports_tab.py
```

Do not report Phase 1 or Phase 3 as complete if any of these checks fail, if the installed EXE was not rebuilt after source changes, or if an external Office application was assumed present without local detection.

## 2026 Office and attendance follow-up (2026-08-09)

The current implementation extends the offline-first policy without making online access implicit:

- `core\office_integration.py` is the local handoff boundary for Microsoft Office, LibreOffice, Apache OpenOffice, SoftMaker FreeOffice, WPS Office, Polaris Office, and ONLYOFFICE Desktop Editors. Detect only locally installed executables; never download an Office suite.
- The document vault supports local preview and fill-the-blank working copies for valid `.docx` and `.xlsx` containers. Other supported formats remain editable through a selected local Office application. Never edit the preserved source file in place.
- Official 2026 registration sources are catalogued in `core\legal_sources.py`. Fetching requires the explicit online setting and the update button. Validate ZIP/XML integrity, preserve the downloaded original, prepare a separate editable copy, update `db\legal_manifest.json` atomically, and show network/certificate errors instead of weakening TLS verification.
- The official 2026 catalog includes the household-registration application and enterprise forms 4, 7, 8, and 10 from the National Business Registration Portal. The portal page remains the authority for the latest version and scope; the app must show the source page and a legal-review warning before filing.
- `ui\hr_tab.py` stores daily attendance in `data\attendance_days*.json`. Each row must show an actual date, employee, attendance status, regular hours, normal/weekend/holiday overtime, approval status, and reason. Monthly timesheets and payroll must use the same selected month, and daily rows must aggregate into the monthly record before payroll calculation.
- `main_qt.py` must load `logo.ico` through `utils.get_resource_path`, set the Qt application/window icon, and set the Windows AppUserModelID before the window is shown so the taskbar icon is stable in packaged launches.

Additional evidence required after changes in this section:

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m pytest -q tests\test_document_templates.py tests\test_daily_attendance.py tests\test_office_integration.py
.venv\Scripts\python.exe test_startup.py
.venv\Scripts\python.exe test_startup_qt.py
.venv\Scripts\python.exe test_backend.py
.venv\Scripts\python.exe -m py_compile core\document_templates.py core\legal_vault.py core\legal_sources.py ui\tools_tab.py ui\hr_tab.py main_qt.py
```

Do not call a document workflow complete merely because an external editor opens. Verify that a filled working copy is created, the source remains unchanged, the output is a valid Office container, and a source update can fail safely when online access is disabled or unavailable.

## Beta v8 local workflow and integration checks (2026-08-09)

`Beta v8` is the visible in-app release label only. Keep the executable names
`VN_SME_Ledger_Stable.exe` and `VN_SME_Ledger_PyQt6.exe` unchanged unless the
user explicitly asks for an artifact rename.

### File/template rules

- `core\legal_vault.resolve_original_path()` is the source-of-truth path for
  `Xem mẫu gốc`, `Mở mẫu gốc bằng...`, and `Tải văn bản mẫu`. It must point to
  an untouched local source copy whenever `source_path` exists.
- `resolve_storage_path()` is the editable/prepared working copy. The fill
  form may write only to `docs\working_copies`; never edit the source in place.
- Preserve `.doc`, `.docx`, `.xls`, `.xlsx`, `.pdf`, and user-provided source
  hashes. Validate Office ZIP containers before presenting a file as valid.
- `Đưa mẫu vào AI local` may pass extracted text from the selected document,
  never a filesystem path. The assistant has no arbitrary file browser and
  must not read data outside the ledger database and explicitly selected text.
- External Word/Excel-compatible editing is a local handoff through
  `core\office_integration.py`. Missing applications must show an actionable
  message; do not download or upload an Office suite.

### Accounting workflow checks

- Hóa đơn selects customers by stable database ID, not by display name. The
  invoice history query must join `clients` and expose `client_name` without
  breaking old invoices.
- Chứng từ must show supplier selection for AP/331 entries, balanced debit and
  credit lines, and a readable ledger table without requiring horizontal drag
  at normal fullscreen size.
- Nhân sự profile fields must remain visible at 100%, 125%, and 150% scaling.
  Daily attendance must retain actual date, employee, status, regular hours,
  normal/weekend/holiday OT, approval, reason, and monthly aggregation.
- Settings must retain VND and common trade currencies and offer a local
  catalogue of Vietnamese banks, e-wallets, and mobile-money providers. This
  catalogue is reference data; verify provider eligibility before payment.
- Use `calc_household_tax_2026()` for the 2026 UI. Keep the legacy
  `calc_household_tax()` contract for compatibility. Show the NĐ68/2026 and
  NĐ141/2026 and TT18/2026 basis, the 1-billion threshold, chosen PIT method,
  the taxable revenue above the threshold, expenses, and
  a warning that filing eligibility must be confirmed against current guidance.

### Optional online and local Ollama checks

- Offline remains the default. Only explicit settings may enable exchange-rate
  fetch, OCR, legal-source updates, cloud/API AI, or synchronization.
- Ollama is local-only even when cloud AI is disabled. Use the configured
  `ollama_base_url`, accept only localhost/127.0.0.1/::1, probe `/api/version`
  and `/api/tags`, and use a locally available model. Never silently fall back
  to a cloud endpoint.
- The online/AI page must fit the PyQt6 fullscreen content viewport without a
  horizontal scrollbar. It must distinguish local Ollama status from cloud
  provider status and keep journal posting behind validation and explicit
  approval.

### Required evidence for Beta v8

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe test_startup.py
.venv\Scripts\python.exe test_startup_qt.py
.venv\Scripts\python.exe test_backend.py
.venv\Scripts\python.exe -m py_compile config.py db.py tax_calculator.py ai\llm_worker.py core\legal_vault.py core\legal_sources.py core\posting_service.py core\rule_service.py core\inventory_transfer.py core\asset_transfer.py ui\tools_tab.py ui\settings_tab.py ui\documents_tab.py ui\invoices_tab.py ui\hr_tab.py ui\directories_tab.py main_qt.py tabs_extra.py
```

The 2026 legal calculation and source claims must remain traceable to official
Government Gazette or Government policy pages. A successful UI startup is not
evidence that invoice linkage, tax formulas, source preservation, or Ollama
locality works; exercise each data path and assert its result.

## Cooperative root-cause QA gate (2026-08-12)

Use `COOP_AI_HANDOFF_BETA_V8.md` as the short handoff board when another AI
model continues work. Read the exact task section and file lock before editing.

For every bug or unexpected behavior:

1. Reproduce it with exact steps, data, screen size, and output.
2. Trace the first bad value or control boundary to the root cause.
3. Add the smallest regression test and run it once to observe the expected failure.
4. Make one minimal fix in the owning module; do not bundle unrelated cleanup.
5. Run the focused test, full `pytest`, startup/backend smoke, and UI screenshot checks when applicable.
6. Reload and test empty, valid, stale/invalid legacy, persisted, and linked-consumer data.
7. Run the focused test and the relevant end-to-end journey before rebuilding
   either EXE. `release_gate.py` is a non-blocking readiness advisory: builds
   are permitted at the product owner's direction, but unresolved checks must
   remain visible and must not be presented as filing certification.
8. Record files, commands, results, residual risk, and the next handoff task in `COOP_AI_HANDOFF_BETA_V8.md`.

Do not call a defect fixed because a widget exists, a tab opens, or startup is
green. If three root-cause hypotheses fail, stop and request architecture
review instead of applying a fourth patch. Never edit a file marked
`IN_PROGRESS` by another model in the cooperative handoff board.

### UI refresh safety rule

When a page refreshes, reloads data, switches sub-tabs, or attaches a deferred
chart, verify widget ownership and count before and after the operation. A
layout item being removed is not enough: the old widget must be reused or
disposed safely. Add a regression assertion for duplicate rows, cards,
buttons, or stale labels before accepting a visual result.

## Mandatory legal/formula audit and release-readiness advisory (2026-08-12, amended 2026-08-24)

The application is not release-ready merely because the UI opens or the test
suite is green. Before changing tax, payroll, invoice, accounting, legal-form,
or business-workflow code, read `docs/VIETNAM_LAW_FORMULA_AUDIT_2026-08-12.md`
and update the source/effective-date matrix. Use official Government legal
sources, preserve the signed source metadata locally, and separate filing-grade
calculations from planning estimates.

High-risk items currently blocking release include independent review of the
implemented 1-billion household threshold and post-01/07/2026 PIT regime,
dated VAT exclusions and rates, enterprise CIT eligibility/deductions, and the
invalid use of a 70% estimated VAT input in an accounting result.

`release_readiness.json` is an advisory checklist, not a package block.
`build_project.py` runs its report before cleaning `build/` or `dist/`, but
the report returns successfully even when evidence is incomplete. Passing
`pytest`, startup, or a previous EXE smoke test still does not turn an
unverified calculation into a filing-grade result.

When the full audit is complete, run the legal golden cases, end-to-end
accounting workflows, persistence/UI/offline tests, Stable/PyQt6 parity checks,
and package smoke tests. Record that evidence before describing a build as
filing-certified; package names remain unchanged.

## Build and real-user simulation (2026-08-13, amended 2026-08-24)

The normal build command always runs the non-blocking readiness advisory. Use:

```powershell
.venv\Scripts\python.exe build_project.py --qa-build
```

`--qa-build` is retained only for backwards compatibility and has the same
behavior as the normal build. Before any build, run the source suite and
compile checks. After a build, run both EXE smoke tests and the real-user
journey runner. Do not represent an artifact with unresolved advisory items as
legally or filing certified.

Rebuild and launch both EXEs after a source change whenever real process
behavior, startup, packaging, or UI integration is relevant.

The real-user journey must follow a coherent business day, not merely inspect
widgets:

1. Launch Stable and PyQt6, open each main area, resize to 1280x720 and
   900x600, and verify no crash, clipped primary action, blank state without
   explanation, or dead `Trợ giúp` action.
2. Create a customer, supplier, item, and employee; edit each record; reload
   the page; verify the saved values are still linked by stable IDs.
3. Record stock-in lots, create a sales invoice using the customer and item,
   verify stock-out/COGS, receivable, journal balance, and invoice history.
4. Record a partial customer settlement and supplier/AP payment; verify open
   balances and ageing after reload.
5. Enter attendance by actual date with regular hours and approved/unapproved
   normal, weekend, and holiday overtime; calculate payroll and verify the
   warning, PIT, insurance, advance, and net-pay outputs.
6. Open the untouched legal template, create a local editable copy, fill
   named fields in DOCX/XLSX, validate the Office container, and confirm the
   source hash/content is unchanged.
7. Use VSIC search with a known code and Vietnamese keyword; open Help for the
   current page; verify the user receives specific instructions.
8. With online options disabled, verify no network request is attempted. Turn
   on one opt-in provider in a controlled test, verify only that provider is
   called, then disable it and verify the offline boundary returns.
9. Close and relaunch the app, reload the same local database, and verify
   persistence. Run the same journey against both UI paths where the feature
   exists; differences are defects until documented.

Evidence must record exact inputs, expected and observed values, screenshots
or logs where relevant, process exit codes, executable sizes, and remaining
risks. A successful process launch alone is never functional evidence.

## 2027 Revamp Contract

For a major redesign, read `docs/REVAMP_2027_BLUEPRINT.md` before editing.
Treat it as an incremental architecture migration: preserve working backend
and other-model contributions, add a tested service boundary, and migrate one
workflow at a time. Do not create a second calculation engine for a new UI.

The working meaning of relocation/reallocation is inventory transfer between
locations, fixed-asset transfer, shared-cost allocation, and local company-data
migration. Each must have preview, source/destination, date, reason, operator,
atomic commit, and reversal. Never implement relocation by directly changing
stock quantity, asset value, or ledger rows without an auditable event.

For the 2027 UI, keep the full desktop workflow in PyQt6 first and preserve
Stable as a fallback until parity evidence exists. Mobile work must begin with
shared domain contracts and a read-only/offline proof; it must not duplicate
tax, payroll, inventory, or posting logic. Do not build an EXE or mobile
package until the milestone's functional, persistence, invalid-input, parity,
offline, and visual checks are complete.

## SME Operations Roadmap (2026-08-28)

After the accounting foundation is green, prioritize utilities that reduce
daily operating work for Vietnamese household businesses and SMEs:

1. Cash and Debt Command Center: show actual cash separately from expected
   collections/payments, link every amount to an invoice or voucher, surface
   overdue items, and never post forecast rows into the ledger.
2. Collection workflow: record a payment promise separately from a receipt,
   track owner, next-contact date, status, and evidence, then generate a local
   editable reminder or reconciliation document.
3. Import and reconciliation: preview CSV/XLSX imports, map columns, reject
   invalid rows before commit, deduplicate by a stable fingerprint, and keep a
   local import report that can be reviewed by an accountant.
4. Inventory and order flow: connect quotation, purchase, receipt, stock lot,
   sale, delivery, return, and debt so quantity, cost, revenue, and balance
   are explainable from source documents.
5. Industry packs: add validated workflows for retail, photocopy/printing,
   distribution, construction progress, and service retainers only when each
   pack has real fields, calculations, reports, and local document outputs.
6. Local AI copilot: allow only selected company records/documents, show the
   records used, separate facts from assumptions, preview edits, and require
   confirmation before writing or posting. Ollama is local; cloud providers
   remain feature-specific opt-in with the user's key.

For each roadmap feature, add a deterministic service test, a persistence
test, an invalid-input test, and a real-user journey check. A chart or button
is not evidence that the underlying accounting workflow works. Forecasts,
tax estimates, and legal guidance must be labelled as planning unless their
source, effective date, and golden cases are independently verified.

## Current Revamp Checkpoint (2026-08-29)

The first 2027 revamp foundation is implemented and must be reused by future
models instead of adding direct SQL in a tab:

- Use `core.posting_service` for new balanced journal writes. Include a source
  type, source ID where available, invoice ID where applicable, and a stable
  posting key for retries. Do not delete or edit source-linked entries through
  generic ledger controls.
- Use `core.rule_service` for effective-dated tax/payroll rule resolution.
  Preserve source/status metadata and reject unsafe free-form rate, amount, or
  PIT-bracket values before saving a rule version.
- Use `core.inventory_transfer` for warehouse/store/bin movement. A preview
  must not create a transfer; commit is atomic; reversal must stop when stock
  or destination cost is no longer unambiguous. The legacy company-wide stock
  total must remain unchanged by an internal transfer.
- Use `core.asset_transfer` for fixed-asset relocation. Never reset original
  cost, useful life, accumulated depreciation, or depreciation status during a
  location/department/person change. Reversal requires the asset to still be
  at the recorded destination.
- PyQt6 `Danh mục` now exposes compact inventory and fixed-asset transfer
  screens. Keep the form usable at 1280x720 and do not reintroduce wide,
  unnecessary table columns.
- PyQt6 `Báo cáo` now exposes `Nhập dữ liệu`: local CSV/XLSX preview with
  profile-based mapping, date/period/item/account validation, duplicate
  fingerprints, reject-report export, and explicit accountant confirmation.
  Preview must remain read-only. Commit only accepted rows in one transaction;
  if any later row fails, rollback the complete batch. Reject unknown mapping
  fields and non-integral inventory IDs rather than coercing user data.
- PyQt6 `Công nợ` now exposes `Thu hồi công nợ`: local AR/AP payment promises,
  next-contact queue, explicit status transitions, local DOCX reminder output,
  and no-posting planning semantics. Active promises may feed the explainable
  cash forecast, while invoice outstanding remains unchanged until settlement.
- A promise may move to `KEPT` only through a matching posted receipt/payment
  and settlement allocation. Manual status changes must never claim payment
  evidence. The command-center summary must keep actual cash, open AR/AP, and
  expected promise cash visibly separate.
- PyQt6 `Hóa đơn > Đơn hàng & kho` now exposes a local source-linked flow for
  `QUOTE`, `SALES_ORDER`, `PURCHASE_ORDER`, `GOODS_RECEIPT`, `DELIVERY`, and
  `RETURN`. Quotes/orders never change stock. Receipt, delivery, and return
  documents call `core.inventory` atomically; source quantities, party
  direction, period locks, and return limits are validated before commit.
  Invoice links are stored as source evidence only; invoice balance and
  settlement remain authoritative in the existing invoice/AR/AP services.
- Stable now exposes the same order-flow service in a dedicated `Đơn hàng & kho`
  workspace. Its selectors use stable customer/supplier and inventory IDs;
  draft, confirm, complete, cancel, and invoice-link actions call
  `core.order_flow` rather than duplicating SQL or calculations. The Stable
  tab is functional parity for this workflow, but Stable/PyQt6 visual parity
  is still a separate acceptance check.
- Both `Báo cáo` implementations expose the read-only `Truy vết luồng` report.
  It traces source chains, quantities, fulfillment, stock movement, linked
  invoices, and remaining invoice balance from `core.order_reports`. CSV
  export is local and must never post or modify business data.

Verified on this checkpoint: full `pytest` is `178 passed, 2 skipped`; the
order-flow tests are `8 passed`, and the order-flow, Stable/PyQt6 report, and
Qt visual group is green at `19 passed`. Startup, backend, real-user journey,
and changed-module compile checks also pass. This is functional evidence for
the implemented foundation, order workflow, and read-only trace reports, not
tax/legal filing certification. The next safe slice is multi-line document
editing and resolution-specific visual parity evidence at 1280x720/900x600.
Stable/PyQt6 parity is functional for the implemented order and report
contracts, not a claim that every legacy screen is pixel-identical.
Do not build a new EXE until the current source checks, startup/backend smoke,
real-user workflow, offline boundary, and visual checks are recorded.

## Current checkpoint - 2026-09-28

The 2026-09-14 Desktop reports were reviewed against the source rather than
accepted solely from their stated test counts. The current hardening pass added
regression coverage for period-closing idempotency, B02 revenue deductions,
split-payment cash-flow allocation, Vietnamese XML number formats, QR input
validation, debt-reminder safety, and ambiguous offline NLP parsing.

Current verification: full `pytest` is `198 passed, 2 skipped`; focused
hardening checks are `29 passed`; changed modules compile; Stable and PyQt6
source startup checks pass; backend smoke passes. The local accounting journey
passes through order, stock, invoice, settlement, payroll, and document steps
with `receivable_outstanding: 0.0` and `ledger_integrity: true`.

The packaged release is not green: `dist\VN_SME_Ledger_Stable.exe` exists but
`dist\VN_SME_Ledger_PyQt6.exe` is missing after an incomplete build. The QA
journey now reports this as a structured artifact blocker. Do not represent the
release as complete or filing-certified until both artifacts are rebuilt and
survive process smoke plus resolution-specific visual checks.

## Current checkpoint - 2026-09-28 - Autocomplete and operating guidance

The current source now includes `core/business_playbook.py`, a shared
offline-first checklist for operating a Vietnamese SME or household business.
It covers configuration, master data, daily vouchers, inventory and debt,
payroll/overtime, period-end review, and deliberate navigation to official
sources. It is guidance and a local checklist, not legal certification. It
does not fetch online data at startup.

`main_qt.py` and Stable `main.py` now expose route-aware autocomplete. PyQt6
search suggestions open top-level workflows or payroll/AI sub-workflows, while
Stable filters an editable route combobox and opens the selected workspace.
The PyQt6 dashboard and sidebar also expose the playbook. Local QCompleter
suggestions are installed for customer, supplier, inventory, batch, tax-code,
and VSIC fields using current local records/catalog data only.

Verification after this slice: `201 passed, 2 skipped`; focused playbook/UI
checks `14 passed`; changed modules compile; Stable startup, PyQt6 offscreen
startup, and backend smoke pass. The packaged PyQt6 executable is still
missing, so do not build or call the release complete until the artifact is
restored and the new routes are manually exercised at 1280x720 and 900x600.

## 2026-09-29 QA Safety and Release Checkpoint

This entry supersedes older packaging-status notes above. The user explicitly
requested and received a new PyQt6 EXE on this date. Keep the visible product
label Beta v8; do not rename the normal executable identity.

- Before editing, trace the workflow from UI to service and persisted SQLite
  state. Keep patches local to the defect and preserve other-model work.
- Every test, startup script, screenshot utility, and EXE run must use a
  disposable database and temporary working directory. Close SQLite handles
  and restore CWD before Windows temp cleanup. Never test reset against the
  project ledger.
- Tests must be import-safe. Only run a standalone GUI smoke behind
  `if __name__ == "__main__"`; do not initialize the process-wide Qt app while
  pytest imports a module.
- Verify posting outcomes, ledger balance/audit integrity, inventory and debt
  reconciliation, formula totals, and idempotence. A normal-looking screen is
  not functional proof.
- Online APIs remain opt-in. Mock network requests in tests and assert no call
  when settings are disabled. Never generate fictional legal forms or call a
  malformed `.docx` valid.
- Run `qa_accounting_stress.py` for deterministic volume checks. Its seeded
  VND figures test internal consistency only; they are not tax-law validation.
- Build only the requested spec after tests pass. Preserve Stable files and
  sidecars; launch EXEs from temporary working directories and separately
  record startup survival, visual checks, file size, and hashes.

Checkpoint evidence: full suite including both EXE smoke checks is `206 passed`;
the 240-invoice/512-payroll volume workload, Stable and PyQt6 startup, backend
smoke, and the real-user order-to-payment journey passed. PyQt6 was built at
`dist/VN_SME_Ledger_PyQt6.exe`. A 1280x720 dashboard screenshot exists on
Desktop; vertical overflow still needs a compact-height pass. A verified
Desktop archive holds 139 old/generated QA entries. Host policy blocked
recursive deletion, so archived originals remain in the project; do not claim
they were removed.

Next agent: continue with the dashboard compact-height layout, inspect legal
vault rows for missing/unverified sources, then use the Desktop Android roadmap.
No Android implementation was started, and no legal filing certification was
performed.

## 2026-09-29 PyQt6 Startup Failure - Corrected QA Evidence

This entry supersedes the earlier statement that the PyQt6 EXE smoke had
passed. The former `test_exe.py` check waited only five seconds and treated a
still-running process as success. A PyInstaller one-file build can show an
error dialog while the bootloader process remains alive; terminating only the
bootloader parent can also leave its app child and temporary SQLite file open.

The reported `Failed to execute script main_qt` was reproduced as
`ImportError: DLL load failed while importing QtWidgets: The specified
procedure could not be found.` PyInstaller had inherited unrelated native DLL
folders from the host `PATH` and collected CRT/API-set DLLs from Codex
`libheif` plus `icuuc.dll` from Codex `poppler`. A clean build `PATH` removed
those unrelated binaries; the source imports QtWidgets normally.

The PyQt6 release was rebuilt from `VN_SME_Ledger_PyQt6.spec` with a controlled
PATH and verified from a disposable working directory. The Qt app reported its
Beta v8 window title through an opt-in QA readiness marker, then closed with
exit code 0. The normal EXE behavior is unchanged: readiness/auto-quit logic is
active only when the QA environment variables are set. `build_exe.bat` now
starts at its own project directory and isolates PATH for the PyQt6 build.

Acceptance rule for future one-file EXEs: do not infer success from process
survival. Require the packaged app readiness marker/window identity, verify
clean exit, run from a temporary working directory, and terminate the full
process tree on timeout before cleaning temporary data. Keep the release
specification and Stable artifact unchanged unless explicitly requested.

Verification for this correction: `pytest -q` reports `204 passed, 2 skipped`
(the skips are opt-in EXE tests); `$env:RUN_EXE_TESTS='1';
.\.venv\Scripts\python.exe -m pytest -q test_exe.py` reports `2 passed`.
The final PyQt6 EXE passed the marker-based packaged launch check. Its size is
105,102,827 bytes. Stable was not rebuilt.
One direct-source title check was inadvertently run from the project working
directory and initialized `data/ledger.db`; the live database and Desktop
safety copy both pass SQLite integrity checks, have schema version 6 and 29
tables, with no populated business-record tables. The live database was not
restored or overwritten.

## 2026-09-29 Daily Frontend / Backend / Crash QA Runner

Run the same repeatable quality pass after each bug-fix day:

```powershell
.venv\Scripts\python.exe daily_qa.py
```

The runner executes the full pytest feature/UI suite, a separately reported
offline/privacy/online-opt-in security audit, Stable and PyQt6 startup checks,
an isolated SQLite posting smoke, the disposable accounting stress workload,
and both packaged EXE smoke tests. Any failed check or missing EXE returns a
non-zero result. Checks use temporary working data; do not point them at
`data\ledger.db`, and do not interpret passing tests as legal certification.
Run this command at the beginning and end of a bug-fix day; no Windows scheduled
task has been registered.

## 2026-09-29 Offline Update-Check Guard

The updater prompt helpers in both `utils` and `utils.auto_updater` now check
`update_check_enabled` themselves before calling the network-check function.
This is defense in depth in addition to the Tk startup guard. Regression tests
verify that configured API keys do not bypass disabled AI online access, both
updater paths stay offline by default, and opted-in update prompts still run.

## 2026-09-29 Autonomous Coverage Diagnostics and Invoice Regression

The daily runner's first check is `function_coverage_audit.py`. It parses and
compiles application Python sources without writing bytecode, runs the full
pytest suite, and reports application functions not reached by the suite.
Unreached functions are prioritized test gaps, not automatically defects; a
reached function is not proof that its outputs are correctly asserted. Use the
report to add a focused test for user-facing/business-critical workflows and
explain genuinely unreachable development-only paths.

`tests/test_invoice_generation.py` exercises both supported invoice PDF
generators, their amount calculations, offline behavior, and VietQR network
opt-in/temporary-file cleanup. The tests use a temporary working directory and
mock the HTTP call. The current `fpdf2` version emits deprecation warnings for
legacy `uni` and `ln` parameters in `invoice_gen.py`; generation works, but the
warnings should be addressed in a separate compatibility-focused patch.

The manual daily check command remains:

```powershell
.venv\Scripts\python.exe daily_qa.py
```

The latest fault-injection checks cover fixed-asset input validation and the
atomic boundary between posting depreciation and updating the asset balance.
Invoice-engine checks cover zero-rate VAT, negative/invalid line values,
double-entry rejection, and the tax-engine wrappers. `core/invoice_engine.py`
is an internal JSON/arithmetic guard only; it is not an official tax-authority
schema validator or a filing integration.

When the reachability report flags a business-critical module with zero
reached functions, inspect whether production UI/service code actually calls
it. If it is live, add a behavior assertion with realistic inputs and verify
persisted ledger results; if it is dormant, record that limitation instead of
claiming it was tested. Never convert reachability percentage into a release
quality claim. The intended autonomous loop is reproduce, capture the failing
assertion/trace, identify the smallest relevant defect, patch, rerun the focused
test, then rerun `daily_qa.py`; make at most three repair attempts before
stopping with evidence and a concise blocker report.

## 2026-09-29 Function-Reachability QA Follow-up

The function audit now covers both Stable Tk and PyQt6 production paths and
reports 876/957 reached (91.5%) on the latest full run: 288 passed, 2 skipped.
This metric is a test-planning signal, not a functional-readiness percentage.
Do not claim 100% correctness from reached functions, and do not invoke obsolete
callbacks solely to increase the score. `main.py` contains duplicate class
method definitions; inspect whether earlier definitions are shadowed before
classifying them as live gaps. Keep existing contributor code unless a proven
production defect requires a minimal patch.

This pass reproduced and fixed a live period-closing UI failure: the preview
and commit handlers called nonexistent `_get_cit_rate()` although the report
tab defines `_cit_rate()`. Tests must seed revenue and expense journal entries,
assert the displayed profit/CIT/net-profit amounts, commit once, verify the
closing journal balances, and verify duplicate-closing detection. Voucher-line
add/delete and invalid-number input, plus invoice validation/create/post/PDF
history behavior, are covered by real widget workflows using isolated SQLite.

The broader regression suite also covers prior narrowly fixed production issues
in order-to-delivery source selection, inventory row mapping, local XML import,
HR XLSX export and demo paths, analytics pie rendering, AR/AP QR-to-reconcile
transition, loopback-only Ollama endpoints, and Vietnamese route search.
External services are mocked; offline defaults and online opt-in boundaries
must remain explicit. Full verification command:

```powershell
.venv\Scripts\python.exe function_coverage_audit.py
```

Latest result: static audit compiled 92 production-scope Python files; pytest
reported 288 passed, 2 skipped, and 41 `fpdf2` deprecation warnings. Remaining
reachability gaps are listed by the audit. In particular, review live report
order-trace export, Plotly launch, default OS file opening, import-batch listing,
legal-vault local opening, and database helper paths; test them only where a
real supported user workflow exists. A run with skips/warnings is not a clean
warning-free release. Do not build an EXE as part of this source QA pass.
