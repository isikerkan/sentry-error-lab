import time

from odoo import http
from odoo.http import request
from werkzeug.exceptions import Forbidden

from ..models.error_lab import lab_enabled


class ErrorLabController(http.Controller):
    """Endpoints for load-test journeys: a known, steady error volume
    while a load test runs. All routes need a logged-in user and the
    sentry_error_lab_enabled server flag."""

    def _check(self):
        if not lab_enabled():
            raise Forbidden("sentry_error_lab_enabled is not set on this server")

    @http.route("/sentry_error_lab/boom", type="json", auth="user")
    def boom(self, **kwargs):
        self._check()
        raise RuntimeError("Error Lab: deliberate JSON-RPC failure")

    @http.route("/sentry_error_lab/sql", type="json", auth="user")
    def sql(self, **kwargs):
        self._check()
        request.env.cr.execute("SELECT boom FROM sentry_error_lab_missing_table")
        return {"unreachable": True}

    @http.route("/sentry_error_lab/slow", type="json", auth="user")
    def slow(self, seconds=2, **kwargs):
        self._check()
        try:
            duration = min(max(float(seconds), 0.1), 30.0)
        except (TypeError, ValueError):
            duration = 2.0
        time.sleep(duration)
        return {"slept": duration}

    @http.route("/sentry_error_lab/http_boom", type="http", auth="user")
    def http_boom(self, **kwargs):
        self._check()
        raise RuntimeError("Error Lab: deliberate HTTP 500")
