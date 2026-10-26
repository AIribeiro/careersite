"""Choose a useful initial window without overriding a user's selection."""

WINDOW_KEY = "careersite_analytics_reporting_window"
PREFERENCE_KEY = "careersite_analytics_reporting_preference"
DEFAULT_WINDOWS = ("last_hour", "today", "this_week", "last_week",
                   "this_month", "last_month", "this_year", "all")
MANUAL_KEY = "careersite_reporting_manual_v2"


def initialize_reporting_period(state, fetch_dashboard):
    # Only an explicit choice is a preference. Automatic choices are refreshed
    # on rerun, so yesterday's empty window cannot become a sticky default.
    if state.get(MANUAL_KEY) and state.get(PREFERENCE_KEY) in DEFAULT_WINDOWS:
        state[WINDOW_KEY] = state[PREFERENCE_KEY]
        return
    for window in DEFAULT_WINDOWS:
        try:
            data = fetch_dashboard(window)
            totals = data.get("totals", {})
            sessions = totals.get("recorded_views", totals.get("sessions"))
            # Advance only on a confirmed zero. Unknown/error responses must
            # not silently masquerade as inactivity. Stop at the widest window.
            if sessions is None or float(sessions) != 0:
                break
        except (RuntimeError, ValueError, TypeError, AttributeError, TimeoutError):
            break
    state[WINDOW_KEY] = window


def remember_reporting_period(state):
    state[PREFERENCE_KEY] = state[WINDOW_KEY]
    state[MANUAL_KEY] = True
