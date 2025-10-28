"""API routes."""
from flask import Blueprint, request, jsonify
from flask_cors import CORS
from src.interview import InterviewOrchestrator
from src.agents.agent_analysis import AnalysisAgent
from src.api_client import ClaudeClient
from src.models import Session, Answer
from src.session import SessionManager

api_bp = Blueprint('api', __name__)

# enable CORS for all routes
# TODO: allow specific origin
@api_bp.route("/investigate", methods=["POST"])
def investigate():
    data = request.get_json()
    incident_name = data["incident_name"]
    summary: str = data["summary"]

    # create session
    session_manager: SessionManager = SessionManager()
    session: Session = session_manager.create_session(incident_name)

    # initialize investigation
    orchestrator: InterviewOrchestrator = InterviewOrchestrator(session)
    orchestrator.initialize_investigation(summary)
    
    session_manager.save_session(session)
    # Return response
    return jsonify({
        'session_id': session.session_id,
        'incident_name': session.incident_name,
        'question': session.current_question,
        'answers': [a.model_dump() for a in session.answers],
        'turn_count': session.turn_count,
        'goals': [g.model_dump() for g in session.goals]
    })

# {
#   "session_id": "uuid-string",
#   "answer": {
#     "answer": "Because Rob is his good friend",
#     "reasoning": "This explains the relationship dynamic"
#   }
# }

@api_bp.route('/answer', methods=['POST'])
def submit_answer():
    data = request.get_json()
    session_id = data['session_id']
    answer_data = data['answer']
    
    # Load session
    session_manager = SessionManager()
    session = session_manager.load_session(session_id)
    
    # Process answer
    orchestrator = InterviewOrchestrator(session)
    answer_obj = Answer(**answer_data)
    next_question, is_complete = orchestrator.process_answer(answer_obj)

    # Save session
    session_manager.save_session(session)
    if is_complete:
        return jsonify({
            'is_complete': True,
            'session_id': session_id,
            'message': 'Interview complete. Proceed to analysis.'
        })
    return jsonify({
        'question': next_question,
        'answers': [a.model_dump() for a in session.answers],
        'is_complete': False,
        'turn_count': session.turn_count,
        'goals': [g.model_dump() for g in session.goals],
        'facts_count': len(session.facts)
    })

@api_bp.route('/sessions', methods=['GET'])
def list_sessions():
    session_manager = SessionManager()
    sessions = session_manager.list_sessions()

    sessions_data = []
    for session in sessions:
        # Calculate progress
        if session.goals:
            avg_confidence = sum(g.confidence for g in session.goals) / len(session.goals)
        else:
            avg_confidence = 0

        sessions_data.append({
            'session_id': session.session_id,
            'incident_name': session.incident_name,
            'status': session.status.value,
            'created_at': session.created_at,
            'turn_count': session.turn_count,
            'progress': int(avg_confidence)
        })

    return jsonify({'sessions': sessions_data})

@api_bp.route('/analysis/<session_id>', methods=['GET'])
def get_analysis(session_id):
    session_manager = SessionManager()
    session = session_manager.load_session(session_id)

    # Generate analysis
    analysis_agent = AnalysisAgent(client=ClaudeClient())
    analysis = analysis_agent.generate_analysis(
        session.model_dump(),
        session_id=session_id
    )

    return jsonify({
        'incident_name': session.incident_name,
        'analysis': analysis
    })