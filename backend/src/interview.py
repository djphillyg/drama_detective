from datetime import datetime

from .agents.drift_detector import DriftDetectorAgent
from .agents.fact_and_goal_updater import FactAndGoalUpdater
from .agents.goal_generator import GoalGeneratorAgent
from .agents.question_generator import QuestionGeneratorAgent
from .agents.summary_and_goal_generator import SummaryAndGoalGenerator
from .agents.summary_extractor import SummaryExtractorAgent
from .api_client import ClaudeClient
from .models import Answer, Message, Session, SessionStatus, ExtractedSummary


class InterviewOrchestrator:
    """Orchestrates the sequential agent pipeline for conducting interviews."""

    def __init__(self, session: Session):
        # TODO: Store session
        self.session: Session = session
        # Store session_id for context isolation
        self.session_id: str = session.session_id
        # Initialize turn_count from session to preserve state across requests
        self.turn_count = session.turn_count
        # Initialize all agent instances
        self.claude_client = ClaudeClient()
        # Separate agents (for image-based summaries)
        self.summary_extractor: SummaryExtractorAgent = SummaryExtractorAgent(
            client=self.claude_client
        )
        self.goal_generator: GoalGeneratorAgent = GoalGeneratorAgent(
            client=self.claude_client
        )
        # Combined agents for optimization (text-only)
        self.summary_and_goal_generator: SummaryAndGoalGenerator = SummaryAndGoalGenerator(
            client=self.claude_client
        )
        self.fact_and_goal_updater: FactAndGoalUpdater = FactAndGoalUpdater(
            client=self.claude_client
        )
        self.drift_detector: DriftDetectorAgent = DriftDetectorAgent(
            client=self.claude_client
        )
        self.question_generator: QuestionGeneratorAgent = QuestionGeneratorAgent(
            client=self.claude_client
        )

    def initialize_investigation(self, summary: str, image_data_list: list[dict]) -> str:
        # Store raw summary in session
        self.session.summary = summary

        # OPTIMIZATION: Use combined agent for text-only summaries
        if not image_data_list or len(image_data_list) == 0:
            # Text-only: Combined summary extraction + goal generation in single API call
            extracted_summary, goals = self.summary_and_goal_generator.extract_and_generate(
                summary,
                session_id=self.session_id
            )
            self.session.extracted_summary = extracted_summary
            self.session.goals = goals
        else:
            # With images: Use sequential agents (multi-tool + images not yet implemented)
            extracted_summary = self.summary_extractor.extract_summary(
                summary,
                image_data_list=image_data_list,
                session_id=self.session_id
            )
            print(extracted_summary)
            self.session.extracted_summary = extracted_summary
            self.session.goals = self.goal_generator.generate_goals(
                extracted_summary, session_id=self.session_id
            )
        # Use question_generator to create first question
        question_data = self.question_generator.generate_question_with_answers(
            self.session.goals,
            self.session.facts,
            self.session.messages,
            extracted_summary=self.session.extracted_summary,
            drift_redirect="",
            session_id=self.session_id,
            interviewee_name=self.session.interviewee_name,
            interviewee_role=self.session.interviewee_role,
            confidence_threshold=self.session.confidence_threshold,
        )
        first_question = question_data.question
        self.session.current_question = question_data.question
        self.session.answers = question_data.answers
        # Store question in session.current_question
        # Add assistant message to session.messages
        self.session.messages.append(
            Message(
                role="assistant",
                content=self.session.current_question,
                timestamp=datetime.now().isoformat(),
            )
        )
        # Return first question
        return first_question

    def process_answer(self, answer: Answer) -> tuple[str, bool]:
        """
        Process user's answer through agent pipeline.
        Returns: (next_question, is_complete)
        """
        # TODO: Increment turn_count
        self.turn_count += 1
        # Add user message to session.messages
        self.session.messages.append(
            Message(
                role="user",
                # TODO: extend answer context
                content=answer.answer,
                timestamp=datetime.now().isoformat(),
            )
        )
        # OPTIMIZATION: Combined fact extraction + goal tracking in single API call
        gen_facts, updated_goals = self.fact_and_goal_updater.extract_and_update(
            self.session.current_question,
            answer,
            self.session.goals,
            session_id=self.session_id
        )
        # Add facts to session.facts
        self.session.facts.extend(gen_facts)
        # Update goals
        self.session.goals = updated_goals

        # MVP: Drift detection disabled for performance - re-enable for v2
        drift_redirect = ""
        # if self.turn_count % 3 == 0:
        #     drift_analysis = self.drift_detector.check_drift(
        #         self.session.current_question, answer.answer, session_id=self.session_id
        #     )
        #     if not drift_analysis.addressed_question:
        #         drift_redirect = drift_analysis.redirect_suggestion

        # Step 4: Generate next question
        question_data = self.question_generator.generate_question_with_answers(
            self.session.goals,
            self.session.facts,
            self.session.messages,
            extracted_summary=self.session.extracted_summary, # type: ignore
            drift_redirect=drift_redirect,
            session_id=self.session_id,
            interviewee_name=self.session.interviewee_name,
            interviewee_role=self.session.interviewee_role,
            confidence_threshold=self.session.confidence_threshold,
        )

        # Check if interview is complete
        is_complete = question_data.target_goal == "wrap_up"

        next_question = question_data.question
        self.session.current_question = next_question
        self.session.answers = question_data.answers
        self.session.turn_count = self.turn_count

        # Add to message history
        self.session.messages.append(
            Message(
                role="assistant",
                content=next_question,
                timestamp=datetime.now().isoformat(),
            )
        )

        if is_complete:
            self.session.status = SessionStatus.COMPLETE

        return next_question, is_complete
