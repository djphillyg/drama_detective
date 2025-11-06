"""API routes."""
from flask import Blueprint, request, jsonify
from flask_cors import CORS
from ..interview import InterviewOrchestrator
from ..agents.agent_analysis import AnalysisAgent
from ..api_client import ClaudeClient
from ..models import Session, Answer
from ..session import SessionManager

api_bp = Blueprint('api', __name__)

# enable CORS for all routes
# TODO: allow specific origin
@api_bp.route("/investigate", methods=["POST"])
def investigate():
    try:
        data = request.get_json()
        incident_name = data["incident_name"]
        summary: str = data["summary"]
        interviewee_name = data["interviewee_name"]
        interviewee_role = data["interviewee_role"]
        images = data["images"]
        
           # Process images into format for API client
        image_data_list = []
        if images:
            for img_base64 in images:
                # Detect media type from base64 prefix or default to jpeg
                if img_base64.startswith('/9j/'):  # JPEG magic bytes
                    media_type = "image/jpeg"
                elif img_base64.startswith('iVBORw'):  # PNG magic bytes
                    media_type = "image/png"
                elif img_base64.startswith('R0lG'):  # GIF magic bytes
                    media_type = "image/gif"
                elif img_base64.startswith('UklGR'):  # WebP magic bytes
                    media_type = "image/webp"
                else:
                    media_type = "image/jpeg"  # Default fallback

                image_data_list.append({
                    "data": img_base64,
                    "media_type": media_type
                })

        # Validate required fields
        if not incident_name or not summary:
            return jsonify({'error': 'incident_name and summary are required'}), 400

        # create session
        session_manager: SessionManager = SessionManager()
        session: Session = session_manager.create_session(incident_name, interviewee_name, interviewee_role)

        # initialize investigation
        orchestrator: InterviewOrchestrator = InterviewOrchestrator(session)
        # Pass images to orchestrator (we'll update this next)
        orchestrator.initialize_investigation(
            summary if summary else "",
            image_data_list=image_data_list
        )

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
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# {
#   "session_id": "uuid-string",
#   "answer": {
#     "answer": "Because Rob is his good friend",
#     "reasoning": "This explains the relationship dynamic"
#   }
# }

@api_bp.route('/answer', methods=['POST'])
def submit_answer():
    try:
        data = request.get_json()
        session_id = data['session_id']
        answer_data = data['answer']

        # Validate required fields
        if not session_id or not answer_data:
            return jsonify({'error': 'session_id and answer are required'}), 400

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
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions', methods=['GET'])
def list_sessions():
    try:
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
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/analysis/<session_id>', methods=['GET'])
def get_analysis(session_id):
    try:
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
            'analysis': analysis.model_dump()
        })
    except FileNotFoundError:
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500