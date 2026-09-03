# Sentry Error Lab

Odoo 18 addon that produces failures on demand, so you can watch how Sentry
receives them: error events, logged errors, slow traces, cron and queue_job
failures, frontend errors and Session Replay.

Menu: **Settings > Technical > Sentry Error Lab** (system administrators).

## Arming the lab

Nothing fires unless the server config contains:

```ini
sentry_error_lab_enabled = true
```

Without the flag every button shows an access message, the poisoned record is
readable, the cron is a no-op and the HTTP endpoints answer 403.

## What each button does

| Button | Effect | Where to look in Sentry |
| --- | --- | --- |
| Python exception | `ZeroDivisionError` in a button method | Issues |
| SQL error | query against a missing table, Odoo's `bad query` | Issues |
| Broken compute on read | opens a record whose compute raises in `web_read` | Issues, Replay (error dialog in the browser) |
| HTTP 500 page | `/sentry_error_lab/http_boom` in a new tab | Issues |
| Log an ERROR / WARNING | `_logger.error()` / `_logger.warning()` without exception | Issues, Logs |
| Slow request | `time.sleep` inside a span | Performance, trace view |
| Failing cron | triggers the lab cron, it raises on its next run | Issues, Crons |
| Failing queue_job | enqueues a job that raises (only with `queue_job` installed) | Issues, job tags |
| JS error in component | OWL client action throws in `setup()` | Issues (browser), Replay |
| JS uncaught error | `throw` inside `setTimeout` | Issues (browser), Replay |
| JS unhandled rejection | rejected promise nobody awaits | Issues (browser), Replay |
| Sentry.captureException | uses the Loader's `window.Sentry` directly | Issues (browser), Replay |

Frontend buttons need the OCA `sentry` addon with `sentry_mode = javascript`
so the Loader Script is injected; Session Replay is recorded according to the
loader's `replaysOnErrorSampleRate`.

## Endpoints for load testing

All routes need a logged-in user and the flag above. They are used by the
`ErrorLab` journey of the Odoo load-test toolkit to give Sentry a steady,
known error volume during a run.

| Route | Type | Effect |
| --- | --- | --- |
| `POST /sentry_error_lab/boom` | JSON-RPC | raises `RuntimeError` |
| `POST /sentry_error_lab/sql` | JSON-RPC | bad SQL query |
| `POST /sentry_error_lab/slow` | JSON-RPC | sleeps `seconds` (0.1 to 30), returns |
| `GET /sentry_error_lab/http_boom` | HTTP | real 500 page |
