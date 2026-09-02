from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase
from odoo.tools import config


class TestErrorLab(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lab = cls.env.ref("sentry_error_lab.lab_record")

    def armed(self, value="true"):
        return patch.dict(config.options, {"sentry_error_lab_enabled": value})

    def test_disabled_blocks_everything(self):
        with self.armed("false"):
            self.assertFalse(self.lab.enabled)
            with self.assertRaises(UserError):
                self.lab.action_python_error()
            with self.assertRaises(UserError):
                self.lab.action_js_component_error()
            # the poisoned record stays readable while disabled
            poison = self.env.ref("sentry_error_lab.poison_record")
            self.assertEqual(poison.poison, "lab disabled, record readable")

    def test_python_error(self):
        with self.armed(), self.assertRaises(ZeroDivisionError):
            self.lab.action_python_error()

    def test_poison_record_unreadable_when_armed(self):
        with self.armed(), self.assertRaises(LookupError):
            self.env.ref("sentry_error_lab.poison_record").poison

    def test_cron_disabled_is_noop(self):
        with self.armed("false"):
            self.assertIsNone(self.env["sentry.error.lab"]._cron_boom())

    def test_cron_armed_raises(self):
        with self.armed(), self.assertRaises(RuntimeError):
            self.env["sentry.error.lab"]._cron_boom()

    def test_client_actions(self):
        with self.armed():
            action = self.lab.action_js_uncaught_error()
        self.assertEqual(action["tag"], "sentry_error_lab.uncaught_error")

    def test_slow_request_clamped(self):
        self.lab.slow_seconds = 0
        with (
            self.armed(),
            patch("odoo.addons.sentry_error_lab.models.error_lab.time.sleep") as sleep,
        ):
            self.lab.action_slow_request()
        sleep.assert_called_once_with(1)
