"""
Abstract base class for all workflows.

This module defines the interface that all workflows must implement.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from growth_agent.config import Settings
from growth_agent.core.schema import WorkflowResult
from growth_agent.core.storage import StorageManager


class Workflow(ABC):
    """
    Abstract base class for all workflows.

    All workflows (A, B, C) must inherit from this class and implement
    the required methods.
    """

    def __init__(self, settings: Settings, storage: StorageManager):
        """
        Initialize workflow.

        Args:
            settings: Application settings
            storage: Storage manager instance
        """
        self.settings = settings
        self.storage = storage
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def validate_prerequisites(self) -> bool:
        """
        Validate that all prerequisites are met before execution.

        This should check:
        - Required API keys are configured
        - Required data files exist
        - External dependencies are available

        Returns:
            True if prerequisites are met, False otherwise
        """
        pass

    @abstractmethod
    def execute(self) -> WorkflowResult:
        """
        Execute the workflow and return result.

        This is the main entry point for workflow execution.

        Returns:
            WorkflowResult with success status, items processed, and any errors
        """
        pass

    def cleanup(self) -> None:
        """
        Post-execution cleanup (override if needed).

        This method is called after execute() regardless of success or failure.
        Override this method to implement workflow-specific cleanup logic.
        """
        pass

    def run(self) -> WorkflowResult:
        """
        Run the complete workflow with validation and cleanup.

        This wrapper method handles the full workflow lifecycle:
        1. Validate prerequisites
        2. Execute workflow
        3. Perform cleanup

        Returns:
            WorkflowResult with execution details
        """
        workflow_name = self.__class__.__name__
        self.logger.info(f"Starting workflow: {workflow_name}")

        # Validate prerequisites
        if not self.validate_prerequisites():
            self.logger.error(f"Prerequisites validation failed for {workflow_name}")
            return WorkflowResult(
                success=False,
                items_processed=0,
                errors=["Prerequisites validation failed"],
            )

        # Execute workflow
        try:
            result = self.execute()
            self.logger.info(
                f"Workflow {workflow_name} completed: success={result.success}, "
                f"items={result.items_processed}"
            )
            return result
        except Exception as e:
            self.logger.exception(f"Workflow {workflow_name} failed with exception")
            return WorkflowResult(
                success=False,
                items_processed=0,
                errors=[f"Exception: {str(e)}"],
            )
        finally:
            # Always run cleanup
            try:
                self.cleanup()
            except Exception as e:
                self.logger.error(f"Cleanup failed: {e}")
