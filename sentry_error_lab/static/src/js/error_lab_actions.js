/** @odoo-module **/

import { Component, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

const actions = registry.category("actions");

/** An OWL client action that throws while being set up. */
class ComponentErrorAction extends Component {
    static template = xml`<div class="p-4">unreachable</div>`;
    static props = { ...standardActionServiceProps };
    setup() {
        throw new Error("Error Lab: deliberate error in an OWL component setup()");
    }
}
actions.add("sentry_error_lab.component_error", ComponentErrorAction);

/** Uncaught error outside any promise: fires the window 'error' event. */
actions.add("sentry_error_lab.uncaught_error", (env) => {
    env.services.notification.add("Throwing an uncaught error in 100 ms", { type: "warning" });
    setTimeout(() => {
        throw new Error("Error Lab: deliberate uncaught JS error");
    }, 100);
});

/** Rejected promise nobody handles: fires 'unhandledrejection'. */
actions.add("sentry_error_lab.unhandled_rejection", (env) => {
    env.services.notification.add("Rejecting a promise nobody awaits", { type: "warning" });
    Promise.reject(new Error("Error Lab: deliberate unhandled promise rejection"));
});

/** Talks to the Loader's Sentry global directly: proves the browser SDK is there. */
actions.add("sentry_error_lab.capture_direct", (env) => {
    const Sentry = window.Sentry;
    if (!Sentry || typeof Sentry.captureException !== "function") {
        env.services.notification.add(
            "window.Sentry is missing: the Loader Script is not injected (sentry_mode != javascript?)",
            { type: "danger", sticky: true }
        );
        return;
    }
    const eventId = Sentry.captureException(new Error("Error Lab: Sentry.captureException from the browser"));
    env.services.notification.add(`Sent to Sentry, event ${eventId}`, { type: "success" });
});
