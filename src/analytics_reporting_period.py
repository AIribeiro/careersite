"""Choose a useful initial window without overriding a user's selection."""

WINDOW_KEY = "careersite_analytics_reporting_window"
PREFERENCE_KEY = "careersite_analytics_reporting_preference"


def initialize_reporting_period(state, fetch_dashboard):
    if WINDOW_KEY in state:
        return
    if PREFERENCE_KEY in state:
        state[WINDOW_KEY] = state[PREFERENCE_KEY]
        return
    window = "last_hour"
    try:
        data = fetch_dashboard("last_hour")
        sessions = data.get("totals", {}).get("sessions")
        # Missing/error responses are unknown, not evidence of zero activity.
        if sessions is not None and float(sessions) == 0:
            window = "today"
    except (RuntimeError, ValueError, TypeError, AttributeError, TimeoutError):
        pass
    state[WINDOW_KEY] = window
    state[PREFERENCE_KEY] = window


def remember_reporting_period(state):
    state[PREFERENCE_KEY] = state[WINDOW_KEY]
