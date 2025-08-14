import asyncio
import logging
import traceback
from typing import Dict, Any

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    FilePart,
    InternalError,
    InvalidParamsError,
    Part,
    Task,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import are_modalities_compatible, new_agent_text_message
from a2a.utils.errors import ServerError

from agent import ask_genie

logger = logging.getLogger(__name__)


class PydanticAIAgentExecutor(AgentExecutor):
    """PydanticAI AgentExecutor implementation for GitHub Genie."""

    SUPPORTED_INPUT_TYPES = [
        'text/plain',
        'text',
    ]
    SUPPORTED_OUTPUT_TYPES = ['text', 'text/plain']

    def __init__(self):
        # Store session context if needed for multi-turn conversations
        self.session_states: Dict[str, Dict[str, Any]] = {}

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the GitHub Genie agent logic."""
        error = self._validate_request(context)
        if error:
            raise ServerError(error=InvalidParamsError())

        context_id = context.context_id
        task_id = context.task_id
        
        try:
            # Emit an initial task object
            updater = TaskUpdater(event_queue, task_id, context_id)
            await updater.submit()

            # Extract the question from the message parts
            question = self._extract_question(context)
            
            # Send status update that we're processing
            await updater.update_status(
                TaskState.working,
                new_agent_text_message("Analyzing repository and processing your question...", context_id, task_id),
            )

            logger.info(f"Processing question for session {context_id}: {question[:100]}...")

            # Create dependencies with A2A progress reporter
            from agent.dependencies import GenieDependencies
            from .progress_reporter import A2AProgressReporter
            
            progress_reporter = A2AProgressReporter(updater)
            deps = GenieDependencies(progress_reporter=progress_reporter)
            
            # Call the existing GitHub Genie agent with A2A-enabled dependencies
            response = await ask_genie(question, deps=deps)

            logger.info(f"GitHub Genie response received for session {context_id}")

            # Create the response artifact
            await updater.add_artifact(
                [Part(root=TextPart(text=response))],
                name='github_genie_analysis',
                metadata={'question': question}
            )
            await updater.complete()

        except Exception as e:
            logger.error(f'An error occurred while processing the request: {e}')
            logger.error(traceback.format_exc())

            # Clean up session state in case of error
            if context_id in self.session_states:
                del self.session_states[context_id]
            
            raise ServerError(
                error=InternalError(
                    message=f'An error occurred while processing the request: {e}'
                )
            )

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        """Cancel an ongoing task (not supported by GitHub Genie)."""
        raise ServerError(error=UnsupportedOperationError())

    def _validate_request(self, context: RequestContext) -> bool:
        """Validate the request. True means invalid, False means valid."""
        invalid_output = self._validate_output_modes(
            context, self.SUPPORTED_OUTPUT_TYPES
        )
        return invalid_output or self._validate_push_config(context)

    def _extract_question(self, context: RequestContext) -> str:
        """Extract the question text from message parts."""
        text_parts = []
        
        for p in context.message.parts:
            part = p.root
            if isinstance(part, TextPart):
                text_parts.append(part.text)
            elif isinstance(part, FilePart):
                # GitHub Genie doesn't handle file attachments directly,
                # but we could potentially support them in the future
                logger.warning("File attachments are not currently supported by GitHub Genie")
            else:
                logger.warning(f'Unsupported part type: {type(part)}')

        return '\n'.join(text_parts)

    def _validate_output_modes(
        self,
        context: RequestContext,
        supported_types: list[str],
    ) -> bool:
        """Validate output modes are compatible."""
        accepted_output_modes = (
            context.configuration.acceptedOutputModes
            if context.configuration
            else []
        )
        if not are_modalities_compatible(
            accepted_output_modes,
            supported_types,
        ):
            logger.warning(
                'Unsupported output mode. Received %s, Support %s',
                accepted_output_modes,
                supported_types,
            )
            return True
        return False

    def _validate_push_config(
        self,
        context: RequestContext,
    ) -> bool:
        """Validate push notification configuration."""
        push_notification_config = (
            context.configuration.pushNotificationConfig
            if context.configuration
            else None
        )
        if push_notification_config and not push_notification_config.url:
            logger.warning('Push notification URL is missing')
            return True

        return False
