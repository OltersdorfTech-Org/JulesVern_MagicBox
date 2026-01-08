"""Web UI for the Magic Box."""

from collections import deque
import importlib
import importlib.util

from magicbox import config


TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Jules Verne Magic Box</title>
  <style>
    body { font-family: sans-serif; margin: 2rem; }
    .card { border: 1px solid #ccc; padding: 1rem; margin-bottom: 1rem; }
    button { padding: 0.5rem 1rem; }
    .logs { white-space: pre-wrap; background: #f5f5f5; padding: 1rem; }
  </style>
</head>
<body>
  <h1>Jules Verne Magic Box</h1>
  <div class="card">
    <form method="post" action="{{ url_for('update_state') }}">
      <label>
        <input type="checkbox" name="message_received" {% if state.message_received %}checked{% endif %}>
        Message/Object Received
      </label>
      <br>
      <label>
        <input type="checkbox" name="gpio_enabled" {% if state.gpio_enabled %}checked{% endif %}>
        GPIO Enable
      </label>
      <br><br>
      <button type="submit">Update State</button>
    </form>
  </div>

  <div class="card">
    <form method="post" action="{{ url_for('export_logs') }}">
      <button type="submit">Export Logs</button>
      <span>{{ export_message }}</span>
    </form>
  </div>

  <div class="card">
    <form method="get" action="{{ url_for('show_logs') }}">
      <button type="submit">Show Logs</button>
    </form>
    {% if logs %}
      <div class="logs">{{ logs }}</div>
    {% endif %}
  </div>
</body>
</html>
"""


def create_app(state_store, log_exporter, logger):
    spec = importlib.util.find_spec("flask")
    if spec is None:
        raise RuntimeError("Flask is required to run the web UI")

    flask = importlib.import_module("flask")
    app = flask.Flask(__name__)

    @app.route("/", methods=["GET"])
    def index():
        snapshot = state_store.snapshot()
        return flask.render_template_string(
            TEMPLATE,
            state=snapshot,
            export_message="",
            logs=None,
        )

    @app.route("/state", methods=["POST"])
    def update_state():
        message_received = flask.request.form.get("message_received") == "on"
        gpio_enabled = flask.request.form.get("gpio_enabled") == "on"
        logger.info("Web state update requested: message=%s gpio_enabled=%s", message_received, gpio_enabled)
        state_store.update_web_state(message_received, gpio_enabled)
        return flask.redirect(flask.url_for("index"))

    @app.route("/export", methods=["POST"])
    def export_logs():
        logger.info("Web log export requested")
        result = log_exporter.export_logs()
        snapshot = state_store.snapshot()
        return flask.render_template_string(
            TEMPLATE,
            state=snapshot,
            export_message=result.message,
            logs=None,
        )

    @app.route("/logs", methods=["GET"])
    def show_logs():
        snapshot = state_store.snapshot()
        logger.info("Web log view requested")
        logs = tail_log(config.RUNTIME_LOG_PATH, 200, logger)
        return flask.render_template_string(
            TEMPLATE,
            state=snapshot,
            export_message="",
            logs=logs,
        )

    @app.route("/health", methods=["GET"])
    def health():
        return {"status": "ok"}

    return app


def tail_log(path: str, max_lines: int, logger) -> str:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            lines = deque(handle, maxlen=max_lines)
        return "".join(lines)
    except OSError as exc:
        logger.warning("Log file unavailable: %s", exc)
        return "Log file unavailable."
