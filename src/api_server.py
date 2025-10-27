from flask import Flask, request

from interview import InterviewOrchestrator
from models import Session
from session import SessionManager

app = Flask(__name__)

# enable CORS for all routes


@app.route("/api/investigate", methods=["POST"])
def investigate():
    data = request.get_json()
    incident_name = data["incident_name"]
    _ = data["summary"]  # TODO: use summary in session creation

    # create session
    session_manager: SessionManager = SessionManager()
    session: Session = session_manager.create_session(incident_name)

    # initialize investigation
    _ = InterviewOrchestrator(session)  # TODO: implement orchestrator logic

    # TODO: return response


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
