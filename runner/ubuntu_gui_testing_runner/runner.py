from abc import ABC, abstractmethod


class Runner(ABC):
    """Abstract interface for runner implementations."""

    @abstractmethod
    def run(self, suite: str, test: str) -> int:
        """Run the specified test suite and test. Return the process exit code."""
