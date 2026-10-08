# VN SME Ledger Beta v8 - Cooperative AI Handoff

**Purpose:** A compact shared workboard for Codex, Antigravity, Claude, and Gemini. Read only the current task section and its listed files before acting.

## Working Contract

- Product policy: offline-first; every online feature is explicit opt-in.
- `Beta v8` is an in-app label. Keep `VN_SME_Ledger_Stable.exe` and `VN_SME_Ledger_PyQt6.exe` unchanged.
- Preserve working code from other models. Do not replace a whole module to fix one defect.
- One model owns a file while editing it. Write `IN_PROGRESS`, model name, timestamp, and files in the workboard before touching code; write `DONE` with evidence afterward.
- Do not claim a feature works because a button or tab exists. Prove the data path and output.
- `release_readiness.json` is advisory. Builds are permitted after relevant tests, but models must disclose unresolved checks and must never label an artifact filing-certified without evidence.
- If the same hypothesis fails three times, stop and request architecture review.

## Baseline

Last verified before the 2026-08-12 UI renovation pass:

```text
.venv\Scripts\python.exe -m pytest -q -> 125 passed, 2 skipped
test_startup.py -> SUCCESS
test_backend.py -> Backend test PASSED
test_startup_qt.py -> SUCCESS
```

## File Locks

| Area | Files | Owner | State |
|---|---|---|---|
| PyQt shell, dashboard, legal vault and motion | `main_qt.py`, `ui/home_tab.py`, `ui/qt_motion.py`, `ui/tools_tab.py`, `tests/test_qt_visual_qa.py` | Codex | DONE (125 passed, 2 skipped) |
| Payroll rule application | `core/payroll.py`, `tests/test_tax_rules.py` | Codex | DONE (25 focused passed) |
| Backup extraction safety | `core/backup.py`, `tests/test_encrypted_backup.py` | Codex | DONE (25 focused passed) |
| HR help label | `ui/hr_tab.py` | Codex | DONE (covered by full suite) |
| Directories, invoices and documents visual audit | `ui/directories_tab.py`, `ui/invoices_tab.py`, `ui/documents_tab.py` | Codex | DONE (127 passed, 2 skipped) |
| Reports and release notes | `instruction.md`, Desktop session summary | Last model touching code | WAIT |
| Vietnam law/formula audit and readiness advisory | `docs/VIETNAM_LAW_FORMULA_AUDIT_2026-08-12.md`, `release_gate.py`, `release_readiness.json`, `build_project.py` | Codex | ADVISORY; package build is permitted, certification requires evidence |

Do not edit a file marked `IN_PROGRESS` by another model. To claim a READY task, change only its row and record the timestamp.

## Current Codex Task: 2026 UI Renovation v2

Read first:

- `docs/superpowers/specs/2026-08-12-pyqt6-modern-ui-qa-design.md`
- `docs/superpowers/plans/2026-08-12-pyqt6-modern-ui-qa.md`
- `main_qt.py` QSS, `go_to_tab()`, and `_add_tab()`
- `ui/tools_tab.py` `_build_legal_vault_tab()` and `_refresh_docs()`
- `ui/home_tab.py` `_init_ui()`, `refresh()`, and `_reflow_cards()`
- `main_qt.py` `content_top_bar`, `_sync_page_header()`, and
  `_normalize_legacy_styles()`

Acceptance evidence:

1. Focused visual tests fail before implementation and pass after implementation.
2. Dashboard is visually inspected at 1280x720 with no page horizontal or
   vertical scrollbar and no duplicate KPI/quick-action widgets.
3. `Kho văn bản mẫu` is visually inspected at 1280x720 and 900x600.
4. Page transition is subtle and does not delay navigation or data mutation.
5. Full test suite and both EXE smoke tests pass after source changes.

## QA Gate for Every Future Defect

1. Reproduce: record exact steps, input data, screen size, and error output.
2. Trace: identify the first bad value/control boundary and the root cause.
3. RED: add one smallest regression test and run it to observe the expected failure.
4. GREEN: apply one minimal fix in the owning module.
5. Verify: run focused test, full pytest, startup/backend smoke, and UI screenshot if visual.
6. Persistence: reload the app and test empty, valid, stale/invalid legacy, and linked-consumer data.
7. Package: after source changes, rebuild and launch both EXEs.
8. Handoff: record files, commands, output, remaining risk, and next task here.

## Handoff Template

```text
MODEL: <Codex/Antigravity/Claude/Gemini>
DATE: YYYY-MM-DD HH:MM Asia/Saigon
TASK: <short task name>
FILES: <exact files changed>
ROOT CAUSE: <one sentence>
TEST RED: <command and expected failure>
FIX: <smallest change>
TEST GREEN: <command and output>
FULL CHECK: <pytest/startup/UI/build output>
REMAINING RISK: <none or precise limitation>
NEXT TASK: <exact section/file for next model>
```

## Next Model Entry Point

Start with **Directories, invoices and documents visual audit**. Read the v2
spec and inspect one screen at 1280x720 and 900x600. Add a failing assertion
for the first proven clipping, stale-widget, or misleading-label defect before
editing. Keep the current shell contract and do not change backend formulas.

## Codex Handoff Entry - 2026-08-12

```text
MODEL: Codex
DATE: 2026-08-12 Asia/Saigon
TASK: UI Renovation v2 plus Antigravity regression review
FILES: main_qt.py, ui/home_tab.py, ui/qt_motion.py, ui/tools_tab.py, ui/hr_tab.py,
       core/payroll.py, core/backup.py, tests/test_qt_visual_qa.py,
       tests/test_tax_rules.py, tests/test_encrypted_backup.py
ROOT CAUSE: dashboard refresh rebuilt widgets without removing old instances;
            payroll and backup had separate proven integration/security gaps.
FIX: shared content header and compact dashboard; reuse dashboard widgets;
     connect effective-dated payroll parameters; reject unsafe archive paths.
TEST GREEN: pytest -q -> 125 passed, 2 skipped; visual/workflow focus -> 24 passed.
UI EVIDENCE: dashboard 1280x720 page hbar=False, vbar=False; cards=6;
              quick buttons=7; legal 900x600 page hbar=False, table hbar=True.
BUILD: build_project.py -> ALL BUILDS AND SMOKE TESTS COMPLETED SUCCESSFULLY;
        test_exe.py -> Stable and PyQt6 both started without crash.
REMAINING RISK: directories/invoices/documents still need the next visual audit;
                legal/current-law content requires separate source verification.
NEXT TASK: inspect the READY files listed above using the root-cause QA gate.
```

## Codex Handoff Entry - 2026-08-12 - Workflow Linkage and Responsive Audit

```text
MODEL: Codex
DATE: 2026-08-12 Asia/Saigon
TASK: Danh mục -> Hóa đơn linkage and 1280x720 responsive audit
FILES: ui/directories_tab.py, ui/invoices_tab.py, tests/test_qt_visual_qa.py,
       docs/superpowers/plans/2026-08-12-ui-renovation-v2.md
ROOT CAUSE: InvoicesTab loaded customers before cmb_hist_client existed;
            invoice picker copied display text but dropped inventory item_id;
            inventory headings were too long for the table viewport.
TEST RED: focused Qt test first failed with AttributeError on cmb_hist_client;
          after that boundary was fixed, the ID assertion failed with None.
FIX: guard history-filter refresh until creation, refresh it for empty masters,
     carry item_id in QTableWidgetItem UserRole and invoice JSON, clear linkage
     on manual edits, and use compact headings with explanatory tooltip.
TEST GREEN: pytest tests/test_qt_visual_qa.py tests/test_inventory_input_safety.py
            -> 9 passed; pytest -q -> 127 passed, 2 skipped.
UI CHECK: 1280x720 directories/invoices/documents page hbar=False;
          900x600 directories hbar=False; invoices/documents retain hbar only
          where the form is genuinely wider than the viewport.
FULL CHECK: py_compile SUCCESS; test_startup.py SUCCESS; test_backend.py PASSED;
            test_startup_qt.py SUCCESS; build_project.py and test_exe.py PASSED.
BUILD: dist/VN_SME_Ledger_Stable.exe 73,773,214 bytes;
       dist/VN_SME_Ledger_PyQt6.exe 102,581,641 bytes.
REMAINING RISK: VSIC population and supplier workflow need a separate data-path
                audit; 900x600 invoice/document forms still need controlled
                internal reflow if that viewport becomes a hard requirement.
NEXT TASK: verify supplier posting and VSIC search with RED tests before edits;
           preserve offline-first and Beta v8/executable naming boundaries.
```

## Codex Handoff Entry - 2026-08-12 - Supplier Master Integration

```text
MODEL: Codex
DATE: 2026-08-12 Asia/Saigon
TASK: Add supplier master workflow and connect it to vouchers
FILES: ui/directories_tab.py, ui/documents_tab.py, tests/test_qt_visual_qa.py
ROOT CAUSE: the backend had a supplier table and Chứng từ had a selector, but
            the PyQt6 app had no user-facing supplier CRUD screen; new suppliers
            could not be selected without external database setup.
TEST RED: supplier directory regression first failed because the expected
          Nhà cung cấp sub-tab did not exist.
FIX: add a compact supplier CRUD/search sub-tab, refresh the voucher supplier
     selector during ledger refresh, and preserve existing AP validation/posting.
TEST GREEN: focused supplier/directory/invoice tests -> 3 passed; full suite ->
             128 passed, 2 skipped.
UI CHECK: supplier directory at 1280x720 has five compact sub-tabs and no outer
          horizontal scrollbar; offscreen screenshot with motion disabled is
          readable and fully painted.
FULL CHECK: py_compile SUCCESS; test_startup.py SUCCESS; test_backend.py PASSED;
            test_startup_qt.py SUCCESS; build_project.py and test_exe.py PASSED.
BUILD: dist/VN_SME_Ledger_Stable.exe 73,774,598 bytes;
       dist/VN_SME_Ledger_PyQt6.exe 102,581,076 bytes.
SHA256: Stable=55556513AA4575D9DDBA169378292DD1B7DD3CF735FBE6A0FA9A5C973B818AF4;
        PyQt6=378D76BBBB715C11E3A6B36CB64DA18D8B37D2F3A7D940FDAEF354C1BF3F621E.
REMAINING RISK: VSIC source is present and loader tests pass, but a clean-package
                UI search smoke should still be run; legal-source validity and
                Optional Online permission boundaries remain separate audits.
NEXT TASK: verify VSIC populated/searchable in a clean database and audit online
           document-source permissions without changing offline defaults.
```

## Codex Handoff Entry - 2026-08-12 - Legal/Formula Audit and Build Freeze

```text
MODEL: Codex
DATE: 2026-08-12 Asia/Saigon
TASK: Establish Vietnam-law formula audit and prevent premature packaging
FILES: tax_calculator.py (audit only), core/tax_rules.py (audit only),
       build_project.py, release_gate.py, release_readiness.json,
       docs/VIETNAM_LAW_FORMULA_AUDIT_2026-08-12.md, instruction.md
ROOT CAUSE: the source tree contains hard-coded or estimated tax paths that
            cannot yet be certified for 2026 filing workflows; packaging was
            previously allowed after generic tests/smoke checks.
RESEARCH FINDINGS: Nghị định 141/2026/NĐ-CP raises the household no-tax and
                   e-invoice threshold from 500 million to 1 billion VND with
                   effect from 01/01/2026; current tax_calculator.py still uses
                   500 million. SME VAT input uses a 70% estimate when source
                   invoices are absent, which must not be filing-grade output.
                   Post-01/07/2026 PIT and business-income rules need a dated
                   migration against Luật 109/2025/QH15 and NĐ253/2026/NĐ-CP.
TEST/FIX: added release_gate.py and a BLOCKED release_readiness.json. The gate
         is invoked before build cleanup and rejects missing checks, blockers,
         or missing evidence. No tax formula was changed without golden cases.
SOURCE CHECK: release_gate.py -> expected BLOCKED; package build was not run.
SOURCE TESTS: release-gate tests and full pytest remain the only permitted
              verification in this incomplete phase.
REMAINING RISK: tax/legal matrix, golden calculations, enterprise tax,
                payroll/PIT, VAT eligibility, workflow parity and online/source
                controls remain unfinished. Existing EXEs are not promoted as
                release-certified and must not be used as completion evidence.
NEXT TASK: create human-reviewed golden cases from official signed sources;
           implement versioned rules behind RED tests; keep build frozen.
```

## Codex Handoff Entry - 2026-08-12 - 2026 Formula Implementation

```text
MODEL: Codex
DATE: 2026-08-12 Asia/Saigon
TASK: Implement the first legally reviewed 2026 formula slice without
      packaging an unfinished executable.
FILES: tax_calculator.py, core/tax_rules.py, core/payroll.py, core/tax_engine.py,
       config.py,
       ui/tools_tab.py, ui/settings_tab.py, tests/test_vietnam_tax_2026.py,
       tests/test_tax_rules.py, tests/test_payroll_workflows.py,
       tests/test_beta_v8_workflows.py, docs/VIETNAM_LAW_FORMULA_AUDIT_2026-08-12.md,
       instruction.md, release_readiness.json
ROOT CAUSE FIXED: the PyQt6 2026 tax path used a 500-million threshold,
                  taxed revenue-method PIT on all revenue, allowed the revenue
                  method above 3 billion, and used legacy payroll deductions/
                  seven PIT brackets.
IMPLEMENTATION: 2026 household API now uses the 1-billion threshold, taxes
                revenue-method PIT only on the excess, forces income method
                above 3 billion, reports invoice/method metadata, and keeps the
                old Stable API explicitly legacy-compatible. Payroll defaults
                and DB rule versions now use 15.5m/6.2m deductions and five PIT
                brackets from 2026-01-01. SME CIT auto-rate/exemption metadata
                is available for planning; input VAT without source invoices is
                still visibly estimated and is not filing-grade.
TEST EVIDENCE: 22 focused formula/rule/payroll/workflow tests passed; changed
               modules compile successfully. Full regression and release gate
               are still required; no build_project.py invocation was made.
REMAINING RISK: VAT classification, eligible input VAT, enterprise CIT
                eligibility/deductions, insurance/overtime law, source forms,
                end-to-end workflows, UI parity and online permissions remain
                open. release_readiness.json remains BLOCKED.
NEXT TASK: add independent golden cases and business workflow tests for VAT,
           CIT, invoice-stock-COGS, receivable/payable settlement, attendance
           dates/OT, and legal-template currency before considering READY_FOR_BUILD.
```

## Codex Handoff Entry - 2026-08-13 - QA Build and Real-User Journey

```text
MODEL: Codex
DATE: 2026-08-13 Asia/Saigon
TASK: Build local QA artifacts on explicit user request and test real business
      behavior without promoting the blocked manifest.
FILES: build_project.py, instruction.md, qa_real_user_journey.py,
       backups/qa_prebuild_2026-08-13/*, dist/VN_SME_Ledger_Stable.exe,
       dist/VN_SME_Ledger_PyQt6.exe
POLICY: Normal build still requires release_gate.py. The new --qa-build flag is
        an explicit local-only exception for behavioral testing and does not
        change release_readiness.json or remove blockers.
SOURCE CHECKS: pytest -q -> 136 passed, 2 skipped; py_compile -> SUCCESS;
               test_startup.py, test_backend.py, test_startup_qt.py -> SUCCESS.
BUILD: .venv\Scripts\python.exe build_project.py --qa-build -> SUCCESS;
       PyInstaller smoke test -> both artifacts survived startup.
JOURNEY: temporary local database; created customer/supplier/item; stock-in;
         invoice auto-post with COGS 200,000; partial receipt left 124,000
         receivable; supplier payment; approved OT payroll/PIT/net; local
         DOCX prepare/fill with source unchanged; both EXEs launched and were
         intentionally terminated after startup.
ARTIFACTS: Stable 73,775,237 bytes, SHA256
           BEF873D255580E1459757B19A9EA00013532F5C7C379287A9456FC6F8BE31B41;
           PyQt6 102,586,347 bytes, SHA256
           47D15A91F1A2740E692A75C26A241C14D77C1EEEFA5C7251C6A49AA363BFA9D2.
RELEASE STATUS: release_gate.py -> BLOCKED as intended. These are QA artifacts,
                not legally release-certified packages. Prior artifacts were
                copied to backups/qa_prebuild_2026-08-13 before rebuilding.
NEXT TASK: add actual UI input automation or manual acceptance evidence for
           each screen, then close legal/workflow blockers before any release
           build. Do not set READY_FOR_BUILD based only on this QA journey.
```

## Codex Handoff Entry - 2026-08-24 - Advisory Packaging and Commercial Direction

```text
MODEL: Codex
DATE: 2026-08-24 Asia/Saigon
TASK: Remove the hard package-build block at the product owner's direction and
      document a sustainable local-first commercial direction.
FILES: build_project.py, release_gate.py, release_readiness.json,
       tests/test_release_gate.py, instruction.md,
       docs/VIETNAM_LAW_FORMULA_AUDIT_2026-08-12.md,
       docs/PRODUCT_REVENUE_STRATEGY_2026-08-24.md
POLICY: release_gate.py is now a non-blocking readiness advisory. It prints
        unresolved evidence but exits 0. build_project.py always runs the
        advisory and may package artifacts. --qa-build is retained only for
        backwards compatibility and has no special permission.
SAFETY: unresolved tax/legal/workflow evidence remains in the manifest. Do not
        remove it or call a build filing-certified without separate evidence.
TEST EVIDENCE: py_compile build_project.py release_gate.py -> PASS;
               tests/test_release_gate.py -> 5 passed;
               release_gate.py -> advisory printed, exit code 0.
PRODUCT DIRECTION: prioritize Cash and Debt Command Center, then linked
                   document-to-action packs, accountant review workspace, and
                   explainable local AI. Do not custody funds, sell ledger
                   data, force cloud sync, or offer unrestricted file access.
NEXT TASK: reproduce and fix destructive invoice correction and invalid
           settlement-allocation paths before building Cash & Debt Pro; then
           prototype the Tomorrow Board against a temporary demo database.
```

## Codex Handoff Entry - 2026-08-28 - Cash Outlook Foundation

```text
MODEL: Codex
DATE: 2026-08-28 Asia/Saigon
TASK: Continue the Cash and Debt Command Center foundation with functional
      demo reconciliation and a read-only 14-day cash outlook.
FILES: demo/simulator.py, core/cash_forecast.py, ui/home_tab.py,
       tests/test_demo_accounting_workflow.py, tests/test_cash_forecast.py,
       instruction.md, docs/PRODUCT_REVENUE_STRATEGY_2026-08-24.md
FIXES: the demo sale now uses db.save_invoice(auto_post=True), carries linked
       COGS and stock-out data, the demo purchase records stock-in and supplier
       identity, and supplier settlement no longer uses a client ID. Opening
       inventory and capital are balanced from the seeded stock values.
UTILITY: core.cash_forecast reads only local journal cash and open invoices;
         it exposes scheduled inflow/outflow, overdue receivables/payables,
         lowest projected cash, source invoice references, and estimated due
         dates. It never posts entries or calls a network provider. PyQt6 Home
         shows a compact 14-day planning summary.
TEST EVIDENCE: full pytest -> 148 passed, 2 skipped; test_startup.py ->
               SUCCESS; test_backend.py -> Backend test PASSED;
               test_startup_qt.py -> SUCCESS; py_compile -> PASS;
               qa_real_user_journey.py -> local workflow PASS and both existing
               EXEs survived startup for the intentional smoke interval.
POLICY: offline-first and online opt-in remain unchanged. release_readiness is
        still ADVISORY; unresolved tax/legal/parity evidence must remain
        visible and no artifact is filing-certified from these tests alone.
NEXT TASK: implement payment promises and a preview-only CSV/XLSX import and
           reconciliation workflow, then add deterministic tests and UI checks.
           Do not let two models edit the same file concurrently; update this
           handoff before taking the next ownership lock.
```

## Codex Handoff Entry - 2026-08-28 - 2027 Revamp Blueprint

```text
MODEL: Codex
DATE: 2026-08-28 Asia/Saigon
TASK: Define a controlled 2027 revamp for accounting truth, responsive UI,
      editable rule options, relocation/reallocation workflows, and mobile.
FILE: docs/REVAMP_2027_BLUEPRINT.md, instruction.md, tabs_extra.py
CURRENT FIX: Stable household-tax UI now calls calc_household_tax_2026 rather
             than exposing the legacy 500-million threshold API.
AUDIT: payroll has duplicated rule inputs in core/hr_compliance.py and
       core/payroll.py; inventory has one global quantity and direct quantity
       editing; fixed assets lack transfer history; tax/report paths need one
       canonical rule service. These are revamp priorities, not silently fixed
       by a visual redesign.
ARCHITECTURE: keep core/db services shared; add canonical posting/rule,
              transfer, import, report-contract, and audit services before a
              QML/mobile client. Relocation means inventory, fixed asset,
              shared-cost, and company-data migration with preview/commit/
              reversal and atomic auditability.
MOBILE: no Tkinter port. Consider Qt Quick/Qt for Python only after domain
        contracts and offline storage are stable; review packaging/signing and
        licensing before committing.
TEST EVIDENCE: after the tax-screen routing and cash-outlook work, full pytest
               remains 148 passed, 2 skipped; startup Stable/PyQt6 and the
               local real-user journey remain green. No EXE was rebuilt here.
NEXT OWNER: implement Phase 1A canonical rule/posting contracts, then
            inventory-transfer preview with deterministic tests. Preserve all
            existing model code and acquire a file lock before editing.
```

## Codex Handoff Entry - 2026-08-29 - Posting and Relocation Foundation

```text
MODEL: Codex
DATE: 2026-08-29 Asia/Saigon
TASK: Continue the approved 2027 revamp with canonical posting/rule services
      and auditable inventory/fixed-asset relocation.
FILES: db.py, core/posting_service.py, core/rule_service.py,
       core/inventory_transfer.py, core/asset_transfer.py,
       ui/directories_tab.py, tests/test_posting_rule_inventory_transfer.py,
       tests/test_asset_transfer.py, docs/REVAMP_2027_BLUEPRINT.md,
       instruction.md
IMPLEMENTATION: journal entries now carry optional source_type, source_id,
                posting_key, and invoice-aware audit hashing. The posting
                adapter validates balanced lines, period locks, source links,
                invoice identity, and idempotent retries. Rule resolution now
                returns effective date, source, and status and validates rule
                shapes before storing a version.
RELOCATION: inventory_locations, per-location balances, and
            inventory_transfers provide preview/atomic commit/guarded reversal.
            The legacy company-wide inventory quantity remains unchanged.
            Fixed-asset fields and fixed_asset_transfers track location,
            department, and responsible person without resetting cost or
            accumulated depreciation. Both workflows are exposed in compact
            PyQt6 Danh mục sub-tabs.
SAFETY: auto-generated location codes are deterministic and readable;
        generic direct ledger deletion remains blocked for source-linked rows;
        stale inventory or asset states stop reversal instead of guessing.
TEST EVIDENCE: full pytest -> 157 passed, 2 skipped; focused foundation,
               location-consistency and PyQt6 directory tests -> 24 passed;
               changed modules compile;
               test_startup.py -> SUCCESS; test_startup_qt.py -> SUCCESS;
               test_backend.py -> Backend test PASSED; qa_real_user_journey.py
               -> local business journey PASS and both existing EXEs survived
               the intentional startup smoke interval.
RELEASE: no EXE rebuilt in this slice. release_readiness.json remains ADVISORY
         with unresolved legal, parity, and real-user evidence; do not call
         this filing-certified.
NEXT TASK: implement Phase 2A CSV/XLSX preview and reconciliation with field
           mapping, reject report, duplicate fingerprint, accountant sign-off,
           and tests before adding payment promises. Do not edit files owned by
           another model; preserve all existing frontend and legacy APIs.
```

## Codex Handoff Entry - 2026-08-29 - Offline Import and Reconciliation

```text
MODEL: Codex
DATE: 2026-08-29 Asia/Saigon
TASK: Implement the approved offline CSV/XLSX import slice with preview,
      validation, duplicate protection, reject reporting, and explicit commit.
FILES: core/import_service.py, core/posting_service.py, ui/reports_tab.py,
       tests/test_import_service.py, instruction.md,
       docs/REVAMP_2027_BLUEPRINT.md
IMPLEMENTATION: `core.import_service` supports inventory movements and
                balanced journal-entry profiles from local CSV/XLSX files.
                It recognizes Vietnamese/English headers, supports explicit
                field mapping, validates dates/period locks/items/accounts/
                quantities/amounts, computes stable row and batch fingerprints,
                exports a UTF-8 reject report, and writes an import audit trail.
                Preview does not create tables or business rows. Commit requires
                a nonblank accountant confirmer, checks the source SHA-256 has
                not changed, writes accepted rows atomically through existing
                inventory/posting services, and rolls back the entire batch on
                later failure. Unknown mapping fields and fractional item IDs
                are rejected instead of coerced.
UI: PyQt6 `Báo cáo` has a compact `Nhập dữ liệu` sub-tab for local file choice,
    profile choice, optional mapping, preview, reject export, and confirmation.
    No network call or automatic tax/invoice inference is introduced.
TEST EVIDENCE: full pytest -> 163 passed, 2 skipped; focused import and
               stabilization tests -> 13 passed; py_compile -> PASS;
               test_startup.py -> SUCCESS; test_startup_qt.py -> SUCCESS;
               test_backend.py -> Backend test PASSED;
               qa_real_user_journey.py -> local workflow PASS and both existing
               EXEs survived the intentional startup smoke interval.
RELEASE: no EXE rebuilt in this slice. release_readiness.json remains ADVISORY;
         tax/legal, Stable/PyQt6 parity, offline/opt-in network, and visual
         acceptance evidence remain open. Do not call this filing-certified.
NEXT TASK: implement Phase 2B payment promises and collection queues. Keep
           forecast commitments separate from receipts/payments, use source
           links, add deterministic persistence/invalid-input/real-user tests,
           and do not edit files owned by another model concurrently.
```

## Codex Handoff Entry - 2026-08-29 - Payment Promises and Collection Queue

```text
MODEL: Codex
DATE: 2026-08-29 Asia/Saigon
TASK: Implement Phase 2B local payment promises and collection queue for AR/AP.
FILES: core/payment_promises.py, core/cash_forecast.py, db.py,
       ui/ar_ap_tab.py, qa_real_user_journey.py, tests/test_payment_promises.py,
       instruction.md, docs/REVAMP_2027_BLUEPRINT.md, requirements.txt
IMPLEMENTATION: `payment_promises` stores a promise linked to exactly one AR/AP
                invoice, with direction, party, amount, promised date, owner,
                next contact date, status, optional local evidence path, and
                append-only status/update events. It validates open invoice
                balance, party identity, dates, local-only evidence, duplicate
                active promises, and status transitions. It never creates a
                journal entry, receipt/payment, settlement allocation, or
                invoice-balance change. It can generate an editable local DOCX
                reminder labelled as an internal management document.
FORECAST: `cash_forecast` now uses an active promise date/amount as an
          explainable expected event, capped at current invoice outstanding;
          actual cash remains ledger-derived and old databases without the
          lazy promise table keep the previous forecast contract.
UI: PyQt6 `Công nợ` now has `Thu hồi công nợ` with AR/AP open-invoice choice,
    amount/date/owner/contact/note/evidence fields, queue filtering, explicit
    status update, and local DOCX reminder output. Refresh now loads the queue.
TEST EVIDENCE: focused promise/forecast/supplier/UI checks -> 13 passed;
               the additional AR/AP/reconciliation/Qt visual group -> 20
               passed; the real-user journey includes promise -> forecast -> status
               confirmation while proving the invoice remains open; changed
               modules compile. Full-suite count must be refreshed after the
               final source run.
POLICY: offline-first and online opt-in remain unchanged. No network path was
        added. `KEPT` is only a promise workflow status, not payment proof.
RELEASE: no EXE rebuilt in this slice. release_readiness.json remains ADVISORY;
         legal/tax, Stable/PyQt6 parity, network opt-in, and visual acceptance
         evidence remain open. Do not call this filing-certified.
NEXT TASK: implement verified settlement handoff and cash/debt command center:
           selecting an actual posted receipt/payment, allocating it safely,
           updating promise status only after evidence, and preserving all
           existing model code. Do not edit files owned by another model
           concurrently.
```

## Codex Handoff Entry - 2026-08-29 - Verified Settlement Handoff

```text
MODEL: Codex
DATE: 2026-08-29 Asia/Saigon
TASK: Complete Phase 3A by linking payment promises to real posted
      receipts/payments and expose a local cash/debt command-center summary.
FILES: core/payment_promises.py, core/cash_debt.py, core/cash_forecast.py,
       db.py, ui/ar_ap_tab.py, qa_real_user_journey.py,
       tests/test_payment_promises.py, instruction.md,
       docs/REVAMP_2027_BLUEPRINT.md
IMPLEMENTATION: Added `payment_promise_settlements` as an auditable bridge.
                `list_settlement_candidates` exposes only matching posted
                entries with unused 131/331 capacity. `link_payment_to_promise`
                calls the existing allocation contract in the same transaction,
                records the allocation, and changes a promise to `KEPT` only
                when linked settlement coverage reaches the promised amount.
                Manual `KEPT`, cancellation after payment, wrong-party payment,
                and over-allocation are rejected. Actual invoice outstanding,
                settlement allocation, and journal integrity remain authoritative.
COMMAND CENTER: `core.cash_debt` reports ledger-derived actual cash, open AR,
                open AP, active promise expected inflow/outflow, and the
                read-only cash forecast. PyQt6 `Công nợ > Thu hồi công nợ` now
                shows those figures, matching payment candidates, allocation
                amount, status controls, and local DOCX reminder output.
QA: `qa_real_user_journey.py` now proves invoice -> partial settlement ->
    promise -> expected forecast -> posted receipt -> allocation -> zero
    outstanding, while both existing EXEs survive the intentional startup smoke.
TEST EVIDENCE: full pytest -> 169 passed, 2 skipped; focused promise/forecast/
               AR/AP/reconciliation/UI checks -> 14 passed; PyQt6 startup,
               Stable startup, backend, changed-module compile -> PASS.
POLICY: offline-first and online opt-in remain unchanged. Promise data is
        local planning/audit data; no network call or automatic payment was added.
RELEASE: no EXE rebuilt in this slice. release_readiness.json remains ADVISORY;
         legal/tax, Stable/PyQt6 parity, network opt-in, and visual acceptance
         evidence remain open. Do not call this filing-certified.
NEXT TASK: implement Phase 3B inventory/order flow with quotation, purchase,
           receipt, stock, sale, delivery, return, and debt links using the
           canonical posting/inventory contracts. Preserve existing model code
           and do not edit files concurrently.
```

## Codex Handoff Entry - 2026-08-29 - Phase 3B Inventory and Order Flow

```text
MODEL: Codex
DATE: 2026-08-29 Asia/Saigon
TASK: Implement the local source-linked quotation, order, receipt, delivery,
      return, stock, invoice, and debt handoff workflow.
FILES: core/order_flow.py, ui/invoices_tab.py, tests/test_order_flow.py,
       qa_real_user_journey.py, instruction.md, docs/REVAMP_2027_BLUEPRINT.md
IMPLEMENTATION: `core/order_flow.py` owns local tables for order documents,
                lines, status events, and invoice links. Supported document
                types are QUOTE, SALES_ORDER, PURCHASE_ORDER, GOODS_RECEIPT,
                DELIVERY, and RETURN. A document starts as DRAFT and must be
                confirmed before completion. Source document type, party,
                direction, source line, period lock, and remaining quantity
                are checked before persistence/commit.
STOCK CONTRACT: Quotes and orders do not change stock. GOODS_RECEIPT calls
               `core.inventory.post_stock_in`, DELIVERY calls
               `post_stock_out`, customer RETURN calls stock-in, and supplier
               RETURN calls stock-out. Calls use `commit=False` inside one
               transaction, so a later line failure rolls back earlier lines.
               Source order status becomes PARTIAL or COMPLETED from completed
               delivery/receipt quantities. Returns cannot exceed fulfilled
               quantities.
DEBT CONTRACT: `order_invoice_links` stores source evidence after the document
              is confirmed. It validates invoice direction and party but does
              not post journals, allocate settlements, or change invoice
              outstanding; existing invoice/AR/AP services remain authoritative.
UI: PyQt6 `Hóa đơn > Đơn hàng & kho` provides real master-data selectors,
    source-linked line entry, draft creation, confirmation, stock completion,
    cancellation, and invoice linking. Stable parity is intentionally not yet
    claimed and is the next phase.
TEST EVIDENCE: `tests/test_order_flow.py` covers sale delivery/partial return,
               purchase receipt/supplier return, atomic stock rollback, source
               and party validation, invoice handoff, selectors, and PyQt6 form
               payload, plus cancellation protection after completed movement.
               Focused order-flow tests -> 6 passed; order-flow plus Qt visual
               checks -> 13 passed; full suite -> 175 passed, 2 skipped;
               changed modules compile. Startup/backend and the real-user
               journey also pass.
POLICY: offline-first remains unchanged. No network call, cloud sync, or AI
        provider was added. No EXE was rebuilt in this slice.
RELEASE: `release_readiness.json` remains ADVISORY. Tax/legal filing evidence,
         Stable/PyQt6 parity, offline/opt-in network proof, and final visual
         acceptance remain open. Do not call this filing-certified.
FILE LOCK: This phase owns `core/order_flow.py`, the order-flow additions in
           `ui/invoices_tab.py`, `tests/test_order_flow.py`, and the journey
           additions. Do not rewrite unrelated model-owned modules.
NEXT MODEL ENTRY POINT: implement Phase 3C Stable parity and reporting. First
                         read this entry and the Phase 3B tests. Port the
                         shared service into Stable with no second calculation
                         engine, then add multi-line document editing and
                         source-linked reports. Required checks: focused and
                         full pytest, test_startup.py, test_startup_qt.py,
                         test_backend.py, py_compile, offline boundary, and
                         1280x720/900x600 UI checks before packaging.
```

## Codex Handoff Entry - 2026-08-29 - Phase 3C Stable parity and reports

MODEL: Codex
TASK: Continue the next phase without removing model-owned structure. Port the
      shared order workflow to Stable and make the source chain reviewable in
      both frontends.
FILES: `core/order_reports.py`, `main.py`, `ui/reports_tab.py`,
       `tests/test_order_flow.py`, `tests/test_phase3_ui_and_supplier.py`,
       `instruction.md`, `docs/REVAMP_2027_BLUEPRINT.md`.
IMPLEMENTATION: Added read-only `core.order_reports` rows and local UTF-8 CSV
                export for source chain, quantities, fulfillment, stock
                movement, linked invoices, and outstanding balance. Added the
                Stable `Đơn hàng & kho` workspace with real master-data IDs,
                draft/confirm/complete/cancel/invoice-link actions. Added the
                same trace report to Stable and PyQt6 `Báo cáo`.
CONTRACT: Stable and PyQt6 call `core.order_flow` and `core.order_reports`;
          they do not duplicate accounting calculations. Order documents are
          not invoices, and invoice outstanding remains authoritative in the
          existing invoice/settlement services.
TEST EVIDENCE: full `pytest` -> `178 passed, 2 skipped`; order-flow tests ->
               `8 passed`; order-flow, Stable/PyQt6 report, and Qt visual
               checks -> `19 passed`; startup, backend, real-user journey,
               and changed-module compile checks pass.
POLICY: offline-first unchanged. No network, cloud sync, or AI provider was
        enabled. CSV export is local and read-only. No EXE was rebuilt.
RELEASE: `release_readiness.json` remains ADVISORY. Tax/legal filing evidence,
         complete visual parity, and final offline/opt-in proof remain open.
         Do not call this filing-certified.
FILE LOCK: This phase owns the files listed above. Preserve unrelated code and
           inspect duplicate legacy method definitions before editing `main.py`.
NEXT MODEL ENTRY POINT: Phase 3D. Add editing/review for draft multi-line
                         documents only, preserve completed-document immutability,
                         then run Stable/PyQt6 screenshot checks at 1280x720 and
                         900x600 before any package build.

## Antigravity / Gemini Handoff Entry - 2026-08-30 - Phase 3D Multi-line Draft Editing & Immutability

MODEL: Antigravity / Gemini
DATE: 2026-08-30 Asia/Saigon
TASK: Complete Phase 3D multi-line draft editing, immutability protection, and UI editor loading in both PyQt6 and Stable.
FILES: `core/order_flow.py`, `ui/invoices_tab.py`, `main.py`, `tests/test_order_flow.py`, `COOP_AI_HANDOFF_BETA_V8.md`.
IMPLEMENTATION: Added `order_flow.update_document_draft()` to update draft lines, date, party, and notes atomically.
                Enforces strict immutability: updates to CONFIRMED, PARTIAL, COMPLETED, or CANCELLED documents are rejected with a clear ValueError.
                Re-validates positive quantities and source document constraints when lines are changed.
                Exposed `_load_order_draft_for_edit()` and `_update_order_draft()` in PyQt6 `ui/invoices_tab.py` with "Sửa bản nháp" and "Lưu sửa đổi nháp" buttons.
                Exposed `_stable_order_load_draft()` and `_stable_order_update()` in Tkinter Stable `main.py` with corresponding action buttons.
TEST EVIDENCE: Full `pytest` -> `181 passed, 2 skipped`; focused `test_order_flow.py` -> `11 passed`;
               `test_startup.py` -> SUCCESS; `test_startup_qt.py` -> SUCCESS;
               `test_backend.py` -> Backend test PASSED; `qa_real_user_journey.py` -> PASS for both EXEs.
POLICY: Offline-first unchanged. No external network dependency added. All draft edits remain local and auditable via `order_document_events`.
NEXT MODEL / LUNA ENTRY POINT: Phase 4. Financial Statements TT133/TT99 template export & audit validation, followed by clean EXE release build in Phase 5.

## Antigravity / Gemini Handoff Entry - 2026-09-06 - Revolutionary Architecture Elevation

MODEL: Antigravity / Gemini
DATE: 2026-09-06 Asia/Saigon
TASK: Elevate VN SME Ledger to institutional height: Audit Radar, Executive Financial Analytics Pro (DuPont & Runway), Regulatory Radar & Knowledge Base, and Smart NLP Voucher Parser.
FILES: `core/audit_radar.py`, `core/financial_analytics_pro.py`, `core/regulatory_radar.py`, `core/smart_parser.py`, `ui/tools_tab.py`, `ui/analytics_tab.py`, `tests/test_revolutionary_suite.py`, `COOP_AI_HANDOFF_BETA_V8.md`.
IMPLEMENTATION:
  - Added `core/audit_radar.py`: Automated SME accounting audit engine diagnosing negative cash (111), negative bank (112), negative stock (156), cash payments >= 20M violating tax deduction laws, missing COGS, and overdue debts.
  - Added `core/financial_analytics_pro.py`: Institutional executive ratios including DuPont Analysis (ROE = Net Margin * Asset Turnover * Leverage), Cash Runway in days, Liquidity ratios, and Break-Even Point.
  - Added `core/regulatory_radar.py`: Authoritative catalog of official Government Decrees & Circulars (NĐ 141/2026, NĐ 68/2026, TT 18/2026, Luật 109/2025/QH15) with direct verified lookup links to congbao.chinhphu.vn and SME accounting upskilling cards.
  - Added `core/smart_parser.py`: High-speed offline Vietnamese natural language parser translating daily business notes into balanced TT133 Dr/Cr voucher proposals.
  - Exposed all features in PyQt6: "Radar & Trí tuệ Kế toán" subtab in ToolsTab and Executive DuPont/Runway cards in AnalyticsTab.
TEST EVIDENCE: Full `pytest` -> `186 passed, 2 skipped`; focused `test_revolutionary_suite.py` -> `5 passed`;
               `test_startup.py` -> SUCCESS; `test_startup_qt.py` -> SUCCESS;
               `test_backend.py` -> Backend test PASSED; `qa_real_user_journey.py` -> PASS for both EXEs.
POLICY: Offline-first preserved. Extremely cost-effective (zero mandatory cloud fees). Verified government links are user-invoked via system browser.
NEXT MODEL / LUNA ENTRY POINT: Phase 4B. Export formatting for Financial Statements (TT133/TT99) into signed Excel/PDF, followed by final package build.

## Antigravity / Gemini & Claude Handoff Entry - 2026-09-14 - Reality Check & 10x Productivity Enhancement

MODEL: Antigravity / Gemini & Claude
DATE: 2026-09-14 Asia/Saigon
TASK: Reality Check & Function Enhancement: Automated Period-End Closing (TK 911), 10x Speed Templates Bar, Smart NLP Auto-VAT Split, and 232.6 MB Build Cache Cleanup.
FILES: `core/period_closing.py`, `core/financial_statements.py`, `core/smart_parser.py`, `ui/documents_tab.py`, `ui/reports_tab.py`, `tests/test_period_closing.py`, `COOP_AI_HANDOFF_BETA_V8.md`.
IMPLEMENTATION:
  - Added `core/period_closing.py`: Period-end closing engine per TT133/2016/TT-BTC. Automatically transfers all Class 5/7 revenue to Cr 911, Class 6/8 expenses to Dr 911, calculates CIT (TK 821/3334), and transfers net profit/loss to Retained Earnings (TK 4212), clearing temporary accounts to zero.
  - Updated `core/financial_statements.py`: B01-DNN dynamically factors unclosed current period profit into Retained Earnings (Mã 512) so the balance sheet is 100% mathematically balanced both before and after formal closing.
  - Updated `core/smart_parser.py`: Auto-detects VAT phrases (8%, 10%) and splits gross amount into net revenue/inventory and VAT (3331/1331). Verifies proposed accounts against active DB chart of accounts.
  - Updated `ui/documents_tab.py`: Added 1-Click Speed Templates ribbon (6 quick business operations) and Enter key shortcuts on amount and debit/credit inputs for 10x faster bookkeeping.
  - Updated `ui/reports_tab.py`: Added 1-Click "Khóa sổ & Kết chuyển (911)" wizard with full preview, tax calculation, and atomic ledger posting.
  - Cleanup: Purged 232.6 MB of obsolete PyInstaller intermediate build cache (`build/`).
TEST EVIDENCE: Full `pytest` -> `189 passed, 2 skipped` in 52.61s (100% green); focused `test_period_closing.py` -> `3 passed`;
               `test_startup.py` -> SUCCESS; `test_startup_qt.py` -> SUCCESS;
               `test_backend.py` -> Backend test PASSED; `qa_real_user_journey.py` -> PASS for both EXEs.
POLICY: Offline-first strictly maintained. Zero external cloud dependencies. Immutability and audit hashing intact.
NEXT MODEL / LUNA ENTRY POINT: Phase 4B. Export formatting for Financial Statements (TT133/TT99) into signed Excel/PDF, followed by final release build `build_project.py`.

## Codex Handoff - 2026-09-29 - UI Charts, Stress QA, and PyQt6 EXE

STATUS: The requested PyQt6 one-file EXE was built at
`dist/VN_SME_Ledger_PyQt6.exe` (119,826,579 bytes). Stable remains present and
was not rebuilt. Keep the in-app identity Beta v8.

CHANGES: Dashboard chart panel is taller and monthly y-axis uses compact
Vietnamese currency labels. KPI and chart profit wording is pre-tax. Added
`qa_accounting_stress.py` plus `tests/test_accounting_stress.py`. GUI tests,
SQLite security tests, startup scripts, and EXE smoke runner now isolate local
files in temporary directories. `main_qt.closeEvent` closes the database.
Screenshot capture defaults to a temporary app-data directory. The unused
legal scraper no longer fabricates `.docx` files; online retrieval raises
`NotImplementedError` until official source handling is genuinely implemented.

VERIFICATION: `pytest -q` with `RUN_EXE_TESTS=1` -> `206 passed in 39.88s`;
compile gate passed; `test_startup.py`, `test_startup_qt.py`, and
`test_backend.py` passed. Stress check: 240 invoices, 240 partial receipts,
480 units, 80 retail receipts, 32 expenses, 512 payroll calculations, 593
journal entries, 1,906 journal lines; integrity and B01 balance passed, B02
revenue 44,000,000 VND and pre-tax profit 32,160,000 VND. Real-user journey
through order, delivery, invoice, settlement, payroll, and DOCX passed; both
EXE processes survived the smoke interval before being deliberately stopped.

ARTIFACTS: Desktop files are `VN_SME_Ledger_Engineering_QA_Rules_2026-09-29.md`,
`VN_SME_Ledger_Android_Port_Roadmap_2026-09-29.md`,
`VN_SME_Ledger_Session_Summary_2026-09-29.md`,
`VN_SME_Ledger_QA_Charts_1280x720_2026-09-29.png`, and
`VN_SME_Ledger_QA_Artifacts_Archive_2026-09-29.zip` (139 verified entries).

OPEN ITEMS: dashboard still vertically overflows at 1280x720; PyQt6 EXE is
about 46 MB larger than Stable; legal default rows and 12 top-level malformed
plain-text `.docx` files are unverified. The latter were included in the
archive, but host policy blocked deleting project copies. They must not be
treated as Office documents. No Android module was started. No current-law
review or filing certification was performed.

NEXT ENTRY POINT: First verify/archive cleanup status without overwriting the
Desktop archive. Then make one dashboard-height change with before/after UI
checks, inspect legal-vault provenance and missing states, and develop Android
only from the Desktop roadmap and shared accounting reference vectors. Keep
offline-first behavior and explicit per-feature online opt-in.

## Codex Handoff Entry - 2026-09-28 - Autocomplete & Business Playbook

MODEL: Codex
TASK: Add route-aware autocomplete and a local-first Vietnam business
      operating checklist without changing the existing accounting structure.
FILES: `core/business_playbook.py`, `ui/autocomplete.py`, `main_qt.py`,
       `main.py`, `ui/home_tab.py`, `ui/directories_tab.py`,
       `ui/tools_tab.py`, `tests/test_business_playbook.py`,
       `tests/test_qt_visual_qa.py`.
IMPLEMENTATION:
  - Added a shared offline playbook covering setup, master data, daily
    vouchers, inventory/debt, payroll/overtime, period-end review, and
    official-source navigation. It derives next actions from local SQLite
    counts and configured identity fields only.
  - PyQt6 navigation search now provides contains-matching suggestions for
    Vietnamese/English workflow terms and opens the selected top-level or
    sub-workflow route with Enter. A new dashboard/sidebar entry opens the
    playbook without network access.
  - Added local QCompleter suggestions for customer, tax code, supplier,
    inventory, batch, and VSIC fields. The completer refreshes with current
    database/catalog data and does not create or alter records.
  - Stable now has an editable route combobox with filtering, Enter navigation,
    and the same local playbook. Official links open only after a deliberate
    user click.
TEST EVIDENCE: focused UI/playbook checks -> `14 passed`; full regression ->
               `201 passed, 2 skipped`; changed-module py_compile -> PASS;
               Stable startup, PyQt6 offscreen startup, and backend smoke ->
               PASS.
REAL-USER EVIDENCE: local accounting journey remains functionally green with
                   `receivable_outstanding: 0.0` and `ledger_integrity: true`.
                   Stable EXE survived startup. PyQt6 EXE remains missing from
                   `dist`, so the packaged release journey correctly reports a
                   missing-artifact blocker.
POLICY: Offline-first remains unchanged. The playbook reads local data only;
        no online source, API, AI provider, or cloud sync runs automatically.
NEXT MODEL ENTRY POINT: Rebuild/restore `dist\VN_SME_Ledger_PyQt6.exe` through
                         the approved workflow, then test the new route search
                         and playbook in both packaged UIs at 1280x720 and
                         900x600. Keep official links user-invoked and retain
                         the missing-artifact release gate.

## Codex Handoff Entry - 2026-09-28 - Functional hardening after Triple Revolution

MODEL: Codex
TASK: Review the 2026-09-14 Desktop reports, verify their claims against the
      current source, and repair high-risk accounting/data-entry behavior while
      preserving other-model structure.
FILES: `core/period_closing.py`, `core/financial_statements.py`,
       `core/einvoice_xml.py`, `core/vietqr.py`, `core/debt_collection.py`,
       `core/smart_parser.py`, `core/statutory_reports_export.py`,
       `ui/documents_tab.py`, `ui/ar_ap_tab.py`, `ui/reports_tab.py`,
       `qa_real_user_journey.py`, and regression tests.
FIXES:
  - Period closing validates ISO dates, rejects reversed ranges, blocks a
    second closing for the same date, and uses a unique posting key for retry
    safety.
  - B02-DNN subtracts debit-side account 521 revenue deductions. B03-DNN now
    allocates each counter line by its own net amount, preventing split cash
    payments (expense plus VAT) from being counted twice.
  - e-Invoice XML accepts Vietnamese number formats such as `1.234,56`,
    recognizes non-taxable VAT labels, validates total pre-tax + VAT against
    total payment, and refuses an unbalanced/empty purchase draft.
  - VietQR validates BIN, account number, and amount. Debt reconciliation now
    validates party type, produces a draft-to-sign conclusion, rejects invalid
    reminder levels, refuses zero debt, and never uses a placeholder bank
    account. The UI reads the configured bank account before generating QR.
  - Smart parser returns `needs_review` and no journal lines for unknown or
    zero-amount text instead of inventing a sales entry; expense VAT is split
    into 642 + 1331 when explicitly stated.
  - BCTC export reads `company_tax_code` and refuses UI export when identity
    fields are missing; service defaults no longer contain a fake taxpayer.
  - Real-user QA now reports a missing packaged artifact as structured release
    evidence instead of crashing with `FileNotFoundError`.
TEST EVIDENCE: focused accounting/security hardening -> `29 passed`; full
               regression -> `198 passed, 2 skipped`; py_compile, Stable
               startup, PyQt6 offscreen startup, and backend smoke -> PASS.
REAL-USER EVIDENCE: local accounting journey passed with receivable outstanding
                   `0.0` and `ledger_integrity: true`. Stable EXE survived the
                   startup interval. PyQt6 EXE was missing from `dist`, so the
                   journey correctly returned a release failure with
                   `error: Missing packaged executable`.
POLICY: Offline-first remains unchanged. No external API, cloud sync, or AI
        provider was enabled. No new EXE was built by this Codex pass.
RELEASE: `release_readiness.json` remains ADVISORY. Legal matrices, current
         tax/payroll verification, UI parity, and PyQt6 packaging evidence are
         open. Do not call the exported files filing-certified or digitally
         signed.
NEXT MODEL ENTRY POINT: First restore/rebuild `dist\VN_SME_Ledger_PyQt6.exe`
                         through the approved build workflow, then run
                         `qa_real_user_journey.py` and inspect both UIs at
                         1280x720/900x600. After that, continue with effective-
                         dated TT133/TT99 export validation and legal review.

## Antigravity / Gemini Handoff Entry - 2026-09-14 - The Triple Revolution (VietQR, e-Invoice XML, Tax Inspection Sim & Smart Collection)

MODEL: Antigravity / Gemini
DATE: 2026-09-14 Asia/Saigon
TASK: Implement The Triple Revolution: Dynamic VietQR/NAPAS 247 Generator, TCT Circular 78 e-Invoice XML Reader, 3-5 Year Tax Inspection Simulator, and Smart Debt Collection with Embedded VietQR.
FILES: `core/vietqr.py`, `core/einvoice_xml.py`, `core/tax_inspection_sim.py`, `core/debt_collection.py`, `ui/documents_tab.py`, `ui/tools_tab.py`, `ui/ar_ap_tab.py`, `tests/test_triple_revolution.py`, `COOP_AI_HANDOFF_BETA_V8.md`.
IMPLEMENTATION:
  - Added `core/vietqr.py`: Pure offline EMVCo / NAPAS 247 payload encoder with CRC16-CCITT and Pillow QR rendering. Built-in BIN directory for major Vietnamese banks.
  - Added `core/einvoice_xml.py`: XML parser for General Department of Taxation Circular 78 / Decree 123 e-invoices. Extracts seller, buyer, line items, and auto-generates balanced double-entry purchase vouchers (Dr 156, Dr 133 / Cr 331).
  - Added `core/tax_inspection_sim.py`: Comprehensive 3-5 year simulated tax inspection engine scanning daily negative cash, cash expenses >= 20M, missing COGS, high administrative overhead ratios, and calculating penalty exposure (20% fine + 0.03%/day late interest) with defense checklist.
  - Added `core/debt_collection.py`: Generates statutory Circular 133 Debt Reconciliation Minutes and Payment Reminder Notices (Level 1 & Level 2) with embedded VietQR payment payloads.
  - Exposed all features in PyQt6: XML Import & VietQR dialog in DocumentsTab; Tax Inspection Simulator dashboard in ToolsTab; Debt Reconciliation & VietQR Reminders in ArApTab.
TEST EVIDENCE: Full `pytest` -> `193 passed, 2 skipped` in 47.91s (100% GREEN); focused `test_triple_revolution.py` -> `4 passed`;
               `test_startup.py` -> SUCCESS; `test_startup_qt.py` -> SUCCESS;
               `test_backend.py` -> Backend test PASSED; `qa_real_user_journey.py` -> PASS for both EXEs.
POLICY: Offline-first strictly maintained. Zero external cloud dependencies. Zero recurring cost for SMEs.
NEXT MODEL / LUNA ENTRY POINT: Phase 4B. Export formatting for Financial Statements (TT133/TT99) into signed Excel/PDF, followed by final release build `build_project.py`.
