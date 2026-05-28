from abc import ABC, abstractmethod


class Runner(ABC):
    """Abstract interface for runner implementations."""

    @abstractmethod
    def run(self, suite: str, test: str) -> None:
        """Run the specified test suite and test."""
