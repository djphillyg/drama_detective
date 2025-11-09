"""API routes."""
from flask import Blueprint, request, jsonify
from flask_cors import CORS
from functools import wraps
import jwt
import os
from datetime import datetime, timedelta
from ..interview import InterviewOrchestrator
from ..agents.agent_analysis import AnalysisAgent
from ..api_client import ClaudeClient
from ..models import Session, Answer
from ..session import SessionManager

api_bp = Blueprint('api', __name__)

# JWT configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-this')
JWT_ALGORITHM = 'HS256'
ACCESS_PASSWORD = os.getenv('ACCESS_PASSWORD')

# Token verification decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            # Verify token
            jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(*args, **kwargs)

    return decorated

@api_bp.route('/verify-password', methods=['POST'])
def verify_password():
    """Verify password and return JWT token."""
    try:
        data = request.get_json()
        password = data.get('password')

        if not password:
            return jsonify({'error': 'Password is required'}), 400

        if not ACCESS_PASSWORD:
            return jsonify({'error': 'Server configuration error'}), 500

        if password == ACCESS_PASSWORD:
            # Generate JWT token (expires in 24 hours)
            token = jwt.encode(
                {
                    'exp': datetime.utcnow() + timedelta(hours=24),
                    'iat': datetime.utcnow()
                },
                JWT_SECRET,
                algorithm=JWT_ALGORITHM
            )

            return jsonify({
                'success': True,
                'token': token
            })
        else:
            return jsonify({'error': 'Invalid password'}), 401

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# enable CORS for all routes
# TODO: allow specific origin
@api_bp.route("/investigate", methods=["POST"])
@token_required
def investigate():
    try:
        data = request.get_json()
        incident_name = data["incident_name"]
        summary: str = data.get("summary", "")
        interviewee_name = data["interviewee_name"]
        interviewee_role = data["interviewee_role"]
        confidence_threshold = data.get("confidence_threshold", 90)  # Default to 90 if not provided
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
        if not incident_name:
            return jsonify({'error': 'incident_name is required'}), 400

        # create session
        session_manager: SessionManager = SessionManager()
        session: Session = session_manager.create_session(incident_name, interviewee_name, interviewee_role, confidence_threshold)

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
@token_required
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
            'turn_count': orchestrator.turn_count,
            'goals': [g.model_dump() for g in session.goals],
            'facts_count': len(session.facts)
        })
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/sessions', methods=['GET'])
@token_required
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
@token_required
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