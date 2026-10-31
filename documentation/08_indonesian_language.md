# Indonesian language (Bahasa Indonesia)

Indonesian uses the language code `id`. The frontend and backend load their
respective `id.json` dictionaries through the existing language loaders.

## Configuration

In `frontend/src/assets/main-settings.json`, set these existing fields:

```json
{
  "appSettings": { "language": "id" },
  "FullCalendarOptions": { "locale": "id" },
  "CKEditorConfig": { "language": { "ui": "id", "content": "id" } }
}
```

This is a partial example: edit the fields in the existing configuration and
retain the other settings. The report editor's existing Indonesian translation
asset is included in the Angular build and test scripts. For an Indonesian-only
deployment, also set `<html lang="id">` in `frontend/src/index.html` so assistive
technology identifies the document language correctly.

In the backend's configured `main.settings.yaml`, set:

```yaml
language: 'id'
```

Rebuild/redeploy the frontend and restart the backend after configuration changes.
The checked-in default remains English. Language settings are deployment-wide;
this change does not introduce a per-user language picker. Existing Angular date
formatting remains configured as `es-AR` in `app.module.ts`; the FullCalendar locale
is configured independently as shown above.

For Docker/Coolify deployments, set the existing environment variable
`SIRIUS_LANGUAJE=id` on both the frontend and backend (the spelling is part of the
existing configuration interface). Their startup templates populate the frontend
language, FullCalendar locale, CKEditor language, and backend response language
from this variable. Build the frontend and backend from this branch: the upstream
`opendicom/sirius-*` images do not include these repository changes.

## Scope and verification

Requested outcome: Indonesian language support using the existing localization
mechanism. Both dictionaries mirror every English key, including interface labels,
workflow states, validation errors, email text, and PDF/report messages. Technical
identifiers, interpolation tokens, HTML tags, and boundary spaces are preserved.
Patient-entered content and clinical templates are not translated automatically.

## Context and terminology decisions

Translate by the key's screen and data field, not by reusing a translation for
every identical English string. These decisions were checked against the current
templates, handlers, and PDF/email assembly:

| Context | Indonesian wording | Reason and implementation evidence |
| --- | --- | --- |
| Sign-in `document` input | Nomor identitas | `auth/components/signin` expects a typed identity number; this is not a file upload. Do not restrict it to KTP: the system also supports passports and other identity documents. |
| Patient `documents` table cells | Dokumen identitas | Identity records are separate from uploaded attachments, which remain `Berkas lampiran`. |
| Medical locker | Beban kerja pelaporan | `performing/components/medical-locker/locker` groups assigned reports by doctor and workflow state; it is not physical storage. Its first tab is `Laporan yang Ditugaskan`. |
| Scheduling slots and shifts | Slot jadwal pemeriksaan / ketersediaan alat | `slots/components/form` selects service, equipment, date, and time. These are equipment availability windows, not staff duty shifts. |
| Urgent scheduling flag | Mendesak | The boolean scheduling priority is distinct from the inpatient category `Emergency`, which remains `Gawat darurat`. |
| Report overview / booking summary | Ringkasan | The overview tab contains patient and examination details. |
| Clinical report `summary` field | Kesimpulan | `reports/components/form`, report review, advanced search, and both PDF generators refer to the report's conclusion. These labels must agree without renaming the overview tab. |
| Report delivery email | Hasil Pemeriksaan Radiologi | `PdfService.createPDF` sends the authenticated report attachment here; an appointment-confirmation subject would describe the wrong event even though English currently uses the same subject for both. |
| Mail action | Kirim ulang email | The `mail-delivery` dialog regenerates/resends the appointment or report email; it does not forward an existing message. |
| Waiting room board | Layar panggilan pasien | The board configuration includes a screen image, and the call dialog sends a patient and destination room to that display. |
| PET-CT activity fields | Aktivitas radioaktif; spuit penuh / sisa spuit | `performing/components/form` displays MBq/mCi and subtracts residual syringe activity from full syringe activity. Labels distinguish radioactivity from volume or absorbed dose. Calculations and units are unchanged. |
| Procedure reporting delay | Batas waktu penyelesaian laporan | `procedures/components/form` stores days allowed for reporting, distinct from the patient's rest/waiting time. |
| Renal insufficiency history flag | Insufisiensi ginjal | Preserve the source condition without strengthening it to a renal-failure diagnosis. |
| Administrative/medical request hold | Ditunda oleh administrasi / bagian medis | These are request-processing states, not physical detention of a patient. |

Clinical terminology was cross-checked with the Ministry of Health's
[SATUSEHAT DiagnosticReport documentation](https://satusehat.kemkes.go.id/platform/docs/id/fhir/resources/diagnostic-report/)
for examination requests and reports, and BAPETEN's
[diagnostic reference level guidance](https://www.bapeten.go.id/upload/53/821c8e0cf1-pedoman-penerapan-tingkat-panduan-diagnostik-indonesia2021.pdf)
for activity expressed in MBq. These references inform wording; they do not
certify this implementation or replace review by an Indonesian clinical user.

The report overview now uses the existing translated centimeter/kilogram labels
instead of hard-coded Spanish text. Dictionary keys, API fields, identity types,
workflow codes, interpolation tokens, and HTML markup remain unchanged.

Run from the repository root:

```bash
node frontend/src/assets/i18n/i18n-validate.js frontend/src/assets/i18n/en.json frontend/src/assets/i18n/id.json
node frontend/src/assets/i18n/i18n-validate.js backend/src/i18n/en.json backend/src/i18n/id.json
```

The validator checks key structure/order and string types. Runtime smoke checks
should also confirm that `require('./backend/src/main.languages')('id')` returns
Indonesian messages and that indexed report placeholders still interpolate.

For UI verification, configure `id`, build using `npm run build` inside `frontend`,
and check sign-in, appointment creation, report editing (including its toolbar),
calendar labels, and generated PDFs/emails. Have an Indonesian-speaking clinical
reviewer confirm terminology before production use.
