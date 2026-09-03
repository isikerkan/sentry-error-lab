import logging
import time

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config

_logger = logging.getLogger(__name__)

try:
    import sentry_sdk
except ImportError:  # the lab works without the SDK, spans are just skipped
    sentry_sdk = None

TRUE_VALUES = ("1", "true", "yes", "on")


def lab_enabled():
    """The lab is armed only when the server config says so, so a stray
    install on a production instance cannot fire errors."""
    return str(config.get("sentry_error_lab_enabled", "")).strip().lower() in TRUE_VALUES


def ensure_enabled():
    if not lab_enabled():
        raise UserError(
            _(
                "The Sentry Error Lab is disabled. Set sentry_error_lab_enabled = true "
                "in the Odoo server configuration and restart."
            )
        )


def notify(message, kind="success", title="Sentry Error Lab"):
    return {
        "type": "ir.actions.client",
        "tag": "display_notification",
        "params": {"title": title, "message": message, "type": kind, "sticky": False},
    }


class SentryErrorLab(models.Model):
    _name = "sentry.error.lab"
    _description = "Sentry Error Lab"

    name = fields.Char(default="Sentry Error Lab", required=True)
    slow_seconds = fields.Integer(
        default=3, help="Duration of the deliberately slow request, 1 to 60 seconds."
    )
    enabled = fields.Boolean(compute="_compute_flags")
    queue_job_available = fields.Boolean(compute="_compute_flags")

    def _compute_flags(self):
        installed = (
            self.env["ir.module.module"]
            .sudo()
            .search_count([("name", "=", "queue_job"), ("state", "=", "installed")])
        )
        for lab in self:
            lab.enabled = lab_enabled()
            lab.queue_job_available = bool(installed)

    # backend errors --------------------------------------------------
    def action_python_error(self):
        ensure_enabled()
        raise ZeroDivisionError("Error Lab: deliberate Python exception")

    def action_sql_error(self):
        ensure_enabled()
        # UndefinedTable from PostgreSQL, surfaces as Odoo's "bad query"
        self.env.cr.execute("SELECT boom FROM sentry_error_lab_missing_table")

    def action_log_error(self):
        ensure_enabled()
        _logger.error("Error Lab: deliberate logged error (no exception raised)")
        return notify(_("Logged an ERROR record. Sentry receives it as an event."))

    def action_log_warning(self):
        ensure_enabled()
        _logger.warning("Error Lab: deliberate logged warning")
        return notify(_("Logged a WARNING record (event only if the level is warn)."))

    def action_slow_request(self):
        ensure_enabled()
        seconds = min(max(self.slow_seconds or 1, 1), 60)
        if sentry_sdk is not None:
            with sentry_sdk.start_span(op="error_lab.sleep", name="Error Lab: slow request"):
                time.sleep(seconds)
        else:
            time.sleep(seconds)
        return notify(_("Slept %s s inside the request. Check the trace in Performance.") % seconds)

    def action_open_poison(self):
        ensure_enabled()
        return {
            "type": "ir.actions.act_window",
            "res_model": "sentry.error.lab.poison",
            "res_id": self.env.ref("sentry_error_lab.poison_record").id,
            "view_mode": "form",
            "target": "current",
        }

    def action_trigger_cron(self):
        ensure_enabled()
        self.env.ref("sentry_error_lab.cron_error_lab")._trigger()
        return notify(_("Cron triggered. It fails on its next run, within about a minute."))

    def action_queue_job_error(self):
        ensure_enabled()
        if not self.queue_job_available:
            raise UserError(_("queue_job is not installed on this database."))
        self.with_delay(description="Error Lab: deliberate job failure")._job_boom()
        return notify(_("Job enqueued. It fails when the jobrunner picks it up."))

    def _job_boom(self):
        ensure_enabled()
        raise RuntimeError("Error Lab: deliberate queue_job failure")

    @api.model
    def _cron_boom(self):
        if not lab_enabled():
            _logger.info("Error Lab cron ran while the lab is disabled, nothing done")
            return
        raise RuntimeError("Error Lab: deliberate cron failure")

    def action_open_http_boom(self):
        ensure_enabled()
        return {"type": "ir.actions.act_url", "url": "/sentry_error_lab/http_boom", "target": "new"}

    # frontend errors -------------------------------------------------
    def _client(self, tag):
        ensure_enabled()
        return {"type": "ir.actions.client", "tag": tag}

    def action_js_component_error(self):
        return self._client("sentry_error_lab.component_error")

    def action_js_uncaught_error(self):
        return self._client("sentry_error_lab.uncaught_error")

    def action_js_rejection(self):
        return self._client("sentry_error_lab.unhandled_rejection")

    def action_js_capture_direct(self):
        return self._client("sentry_error_lab.capture_direct")


class SentryErrorLabPoison(models.Model):
    """A record that cannot be read while the lab is armed: opening its
    form fails inside web_read, the way a broken compute does in real life."""

    _name = "sentry.error.lab.poison"
    _description = "Sentry Error Lab Poisoned Record"

    name = fields.Char(required=True)
    poison = fields.Char(compute="_compute_poison")

    def _compute_poison(self):
        if lab_enabled():
            raise LookupError("Error Lab: deliberate compute failure while reading the record")
        for record in self:
            record.poison = "lab disabled, record readable"
