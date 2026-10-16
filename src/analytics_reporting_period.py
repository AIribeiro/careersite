"""Choose a useful initial window without overriding a user's selection."""

WINDOW_KEY = "careersite_analytics_reporting_window"
PREFERENCE_KEY = "careersite_analytics_reporting_preference"
DEFAULT_WINDOWS = ("last_hour", "today", "7d", "30d", "90d", "365d")


def initialize_reporting_period(state, fetch_dashboard):
    if WINDOW_KEY in state:
        return
    if PREFERENCE_KEY in state:
        state[WINDOW_KEY] = state[PREFERENCE_KEY]
        return
    for window in DEFAULT_WINDOWS:
        try:
            data = fetch_dashboard(window)
            sessions = data.get("totals", {}).get("sessions")
            # Advance only on a confirmed zero. Unknown/error responses must
            # not silently masquerade as inactivity. Stop at the widest window.
            if sessions is None or float(sessions) != 0:
                break
        except (RuntimeError, ValueError, TypeError, AttributeError, TimeoutError):
            break
    state[WINDOW_KEY] = window
    state[PREFERENCE_KEY] = window


def remember_reporting_period(state):
    state[PREFERENCE_KEY] = state[WINDOW_KEY]
