"""A2A-specific progress reporter implementation."""

from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState
from a2a.utils import new_agent_text_message

from ..agent.dependencies import ProgressReporter


class A2AProgressReporter(ProgressReporter):
    """A2A-specific implementation of ProgressReporter."""
    
    def __init__(self, task_updater: TaskUpdater):
        """Initialize with a TaskUpdater instance.
        
        Args:
            task_updater: The A2A TaskUpdater instance to use for progress reporting.
        """
        self.task_updater = task_updater
    
    async def report_progress(self, message: str) -> None:
        """Report progress by sending an A2A status update.
        
        Args:
            message: The progress message to send.
        """
        await self.task_updater.update_status(
            TaskState.working,
            new_agent_text_message(
                message, 
                self.task_updater.context_id, 
                self.task_updater.task_id
            )
        )
