{
    "name": "Sentry Error Lab",
    "summary": "Produce errors on demand to exercise Sentry: exceptions, SQL errors, "
    "slow requests, cron and queue_job failures, frontend errors and Session Replay",
    "version": "18.0.1.0.0",
    "category": "Tools",
    "author": "isikerkan",
    "website": "https://github.com/isikerkan/sentry-error-lab",
    "license": "LGPL-3",
    "depends": ["web"],
    "data": [
        "security/ir.model.access.csv",
        "data/error_lab_data.xml",
        "views/error_lab_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "sentry_error_lab/static/src/js/error_lab_actions.js",
        ],
    },
    "installable": True,
    "application": False,
}
