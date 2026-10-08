# VN SME Ledger Android Port Plan

**Status:** architecture proposal; no Android application has been scaffolded yet.
**Prepared:** 2026-10-07

## Recommendation

Build a native Kotlin Android client. Do not wrap the PyQt6 desktop UI or embed the desktop Python runtime: neither approach provides a maintainable touch-first application, and neither automatically makes the existing desktop workflows usable on phones.

Keep the Android client offline-first and compatible with the desktop accounting data contract. Port accounting rules deliberately, with shared golden test cases, rather than attempting to reuse desktop UI modules.

## Platform Baseline

- Use Kotlin, Jetpack Compose, Material 3, a single activity, Navigation, ViewModels, repositories, coroutines, and `Flow` for UI state. Android's current architecture guidance recommends layered data/UI boundaries, repositories, and Compose for new applications.
- Use Room over SQLite for local structured accounting data, explicit schema migrations, and compile-time checked queries.
- Set `compileSdk` and `targetSdk` to API 36 or newer at release time. As of 2026-10-06, Google Play requires new mobile apps and updates to target Android 16 / API 36 from 2026-08-31. Recheck this policy before each release.
- Provisional `minSdk`: API 29 (Android 10) for device reach. Confirm against customer-device research and security-support requirements before implementation; raise it if the supported security baseline requires it.
- Support phones, tablets, foldables, rotation, split-screen, and resizable windows. Choose layouts from current window-size classes, not device model or orientation alone. Target API 36 behavior must be tested on large-screen devices.

## Product Requirements

1. **Local accounting is complete without network:** company setup, customers/suppliers, item and inventory tracking, sales/purchase workflow, balanced vouchers, receivable/payable, attendance/overtime/payroll, dashboards, reports, and local document editing/export.
2. **Online is explicit opt-in:** separate controls for legal-source checks, exchange-rate lookup, AI providers, and any future sync. No network request during startup. Explain what data leaves the device before a request; show source and retrieval time; never silently post AI-suggested entries.
3. **Desktop interoperability:** define a versioned export/import contract for ledger records, attachments, and IDs. Keep XLSX/CSV and DOCX/PDF workflows compatible; make encrypted backup/restore available through Android's system document picker. Do not rely on shared live SQLite files across devices.
4. **Vietnamese and international use:** Vietnamese and English strings; locale-aware dates, decimal separators, currencies, timezone, and tax profiles; explicit business/jurisdiction selection. Tax rules and legal-document metadata must carry source, effective date, and review status.
5. **Accessible, touch-first UI:** minimum 48dp touch targets, scalable text, TalkBack labels, high contrast, state retention across rotation/folding, list-detail layouts on wide screens, and no desktop-style dense tables forced onto narrow phones.

## Data, Security, and Privacy

- Preserve accounting invariants in database transactions: balanced journal entries, stable source IDs, audit history, foreign-key integrity, and tested migrations. A failed posting must leave no partial ledger update.
- Store records in app-private storage. Use Android Keystore-backed key management with a vetted, license-reviewed encryption approach for sensitive local data and user-created backups. Room/SQLite alone should not be described as encrypted.
- Disable automatic backup of plaintext financial data. Offer a user-initiated encrypted export/restore flow with clear recovery-key handling and integrity checks.
- Request only permissions needed for an invoked action. Prefer the system document picker for importing/exporting and avoid broad storage access. Camera access, if used for QR/document capture, is requested only when that workflow is selected.
- No analytics, advertising SDKs, account requirement, cloud AI, or background sync by default. Any later online provider must be independently opt-in and covered by privacy disclosures and data-safety declarations.
- Threat-model stolen/unlocked devices, malicious backups, exported files, local database tampering, and AI prompt/data leakage before beta distribution.

## Delivery Phases

1. **Domain contract:** inventory the Python accounting functions and SQLite schema; document rounding, sign conventions, tax assumptions, period rules, and source IDs. Create input/output fixtures for representative and boundary cases.
2. **Android foundation:** Gradle/Kotlin project, CI, app signing, Compose navigation, Room entities/DAOs, migration tests, app-private storage, localization, and accessibility baseline.
3. **Core workflows:** company profile, counterparties, items, vouchers, posting/rollback, cash, inventory, and receivables/payables. Prove parity against Python golden fixtures before adding screens.
4. **Workforce and reporting:** daily attendance with overtime approval, payroll/tax calculation, dashboards/charts, and export/print flows. Mark any unsupported desktop behavior explicitly rather than silently approximating it.
5. **Optional online services:** legal-source refresh, exchange rates, then AI assistance, each as isolated consent-gated adapters with offline tests and request previews. Keep synchronization out of the first release unless a conflict-resolution contract is approved.
6. **Beta and release:** device-matrix QA, security/privacy review, Play policy checks, signed Android App Bundle, staged rollout, crash/performance monitoring only with consent, and tested rollback/migration plan.

## Release Gates

- Cold launch p95 under 2 seconds on a documented mid-range reference device; first useful local screen must not wait for a network call.
- Unit/golden parity for currency rounding, balanced posting, inventory movement, overtime/payroll, and tax boundaries. No tax/legal rule may ship without a named source and validity date.
- Room migration tests from every supported schema version; interrupted writes, low storage, process death, and backup restore must not corrupt posted entries.
- UI tests on compact (<600dp), medium (600-840dp), and expanded (>=840dp) windows; Android 10 through current target release; phones, tablets/foldables, font scaling, TalkBack, and offline/no-permission states.
- Security review of key lifecycle, backup exclusions, export sharing, permissions, WebView/external links, dependency licenses, and every network payload.
- No Play release until the Play target API, privacy policy, Data safety form, signing, and all enabled online providers are reviewed.

## Source References

- [Google Play target API requirements](https://support.google.com/googleplay/android-developer/answer/11926878?hl=en)
- [Android architecture recommendations](https://developer.android.com/topic/architecture/recommendations)
- [Android offline-first architecture](https://developer.android.com/topic/architecture/data-layer/offline-first)
- [Room local database](https://developer.android.com/training/data-storage/room)
- [Adaptive Android layouts and window size classes](https://developer.android.com/develop/adaptive-apps/guides/use-window-size-classes)
- [Android Keystore](https://developer.android.com/privacy-and-security/keystore)
- [Android backup security recommendations](https://developer.android.com/privacy-and-security/risks/backup-best-practices)
