from datetime import datetime
from src.models import Session, SessionStatus, Answer, Message
from src.api_client import ClaudeClient
from src.agents.goal_generator import GoalGeneratorAgent
from src.agents.fact_extractor import FactExtractorAgent
from src.agents.drift_detector import DriftDetectorAgent
from src.agents.goal_tracker import GoalTrackerAgent
from src.agents.question_generator import QuestionGeneratorAgent


class InterviewOrchestrator:
    """Orchestrates the sequential agent pipeline for conducting interviews."""

    def __init__(self, session: Session):
        # TODO: Store session
        self.session: Session = session
        # Initialize turn_count to 0
        self.turn_count = 0
        # Initialize all agent instances
        self.claude_client = ClaudeClient()
        self.goal_generator: GoalGeneratorAgent = GoalGeneratorAgent(client=self.claude_client)
        self.fact_extractor: FactExtractorAgent = FactExtractorAgent(client=self.claude_client)
        self.drift_detector: DriftDetectorAgent = DriftDetectorAgent(client=self.claude_client)
        self.goal_tracker: GoalTrackerAgent = GoalTrackerAgent(client=self.claude_client)
        self.question_generator: QuestionGeneratorAgent = QuestionGeneratorAgent(client=self.claude_client)

    def initialize_investigation(self, summary: str) -> str:
        # TODO: Store summary in session
        self.session.summary = summary
        # Use goal_generator to create goals
        self.session.goals = self.goal_generator.generate_goals(summary)
        # Use question_generator to create first question
        question_data = self.question_generator.generate_question_with_answers(
            self.session.goals,
            self.session.facts,
            self.session.messages,
            # leave out drift redirect for now
        )
        first_question = question_data["question"]
        self.session.current_question = question_data["question"]
        self.session.answers = [Answer(**a) for a in question_data["answers"]]
        # Store question in session.current_question
        # Add assistant message to session.messages
        self.session.messages.append(Message(
            role="assistant",
            content=self.session.current_question,
            timestamp=datetime.now().isoformat()
        ))
        # Return first question
        return first_question

    def process_answer(self, answer: Answer) -> tuple[str, bool]:
        """
        Process user's answer through agent pipeline.
        Returns: (next_question, is_complete)
        """
        # TODO: Increment turn_count
        self.turn_count +=1
        # Add user message to session.messages
        self.session.messages.append(Message(
            role="user",
            # TODO: extend answer context
            content=answer.answer,
            timestamp=datetime.now().isoformat()
        ))
        # Extract facts using fact_extractor
        gen_facts = self.fact_extractor.extract_facts(self.session.current_question, answer)
        # Add facts to session.facts
        self.session.facts.extend(gen_facts)
        # Check drift every 3 turns using drift_detector
        drift_redirect = ""
        if self.turn_count % 3 == 0:
            drift_analysis = self.drift_detector.check_drift(
                self.session.current_question,
                answer.answer
            )
            if not drift_analysis["addressed_question"]:
                drift_redirect = drift_analysis["redirect_suggestion"]
      # Step 3: Update goal confidence scores
        self.session.goals = self.goal_tracker.update_goals(
            self.session.goals,
            gen_facts
        )

        # Step 4: Generate next question
        question_data = self.question_generator.generate_question_with_answers(
            self.session.goals,
            self.session.facts,
            self.session.messages,
            drift_redirect
        )

        # Check if interview is complete
        is_complete = question_data["target_goal"] == "wrap_up"

        next_question = question_data["question"]
        self.session.current_question = next_question
        self.session.answers = [Answer(**a) for a in question_data["answers"]]
        self.session.turn_count = self.turn_count

        # Add to message history
        self.session.messages.append(Message(
            role="assistant",
            content=next_question,
            timestamp=datetime.now().isoformat()
        ))

        if is_complete:
            self.session.status = SessionStatus.COMPLETE

        return next_question, is_complete