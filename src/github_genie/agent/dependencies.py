"""Dependencies and interfaces for GitHub Genie agent."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


class ProgressReporter(ABC):
    """Abstract interface for reporting tool execution progress."""
    
    @abstractmethod
    async def report_progress(self, message: str) -> None:
        """Report progress with a message."""
        pass


@dataclass
class GenieDependencies:
    """Essential state for the GitHub Genie agent."""
    current_repo_path: str | None = None
    progress_reporter: ProgressReporter | None = None  # Optional for progress reporting
