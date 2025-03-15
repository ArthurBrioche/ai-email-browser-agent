"""
Task execution engine for the AI Email Browser Agent.
This module handles executing browser automation tasks using browser-use.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple

from browser_use import Agent
from langchain_openai import ChatOpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TaskExecutor:
    """
    A class to execute browser automation tasks using browser-use.
    
    This class takes a task description and uses browser-use Agent to
    perform browser automation tasks, handling both success and failure cases.
    """
    
    def __init__(self, openai_api_key: str, model_name: str = "gpt-4o"):
        """
        Initialize the TaskExecutor with API credentials.
        
        Args:
            openai_api_key: API key for OpenAI
            model_name: Name of the OpenAI model to use for the agent
        """
        self.openai_api_key = openai_api_key
        self.model_name = model_name
        
    async def execute_task(self, task_description: str, additional_context: Optional[Dict[str, Any]] = None) -> Tuple[bool, Dict[str, Any], List[str]]:
        """
        Execute a browser task using browser-use Agent.
        
        Args:
            task_description: Description of the task to execute
            additional_context: Additional context information for the agent
            
        Returns:
            A tuple containing (success_status, task_results, action_log)
        """
        logger.info(f"Executing task: {task_description}")
        
        # Prepare the task with additional context if provided
        if additional_context:
            contextualized_task = f"{task_description}\n\nAdditional context:\n"
            for key, value in additional_context.items():
                contextualized_task += f"- {key}: {value}\n"
        else:
            contextualized_task = task_description
            
        # Action log to track steps taken
        action_log = []
        
        try:
            # Initialize the browser-use agent
            agent = Agent(
                task=contextualized_task,
                llm=ChatOpenAI(api_key=self.openai_api_key, model=self.model_name),
                # Additional configuration can be added here
            )
            
            # Optional callback to log actions as they happen
            async def log_action(action):
                action_description = f"{action.get('action', 'Unknown action')}: {action.get('description', '')}"
                logger.info(f"Browser action: {action_description}")
                action_log.append(action_description)
            
            # Execute the browser task
            results = await agent.run()
            
            # Process the results
            success = True  # Assume success if no exception was raised
            result_data = {
                'completed': True,
                'results': results
            }
            
            logger.info("Task execution completed successfully")
            return success, result_data, action_log
            
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            # Return failure with error information
            return False, {'error': str(e), 'completed': False}, action_log
            
    async def handle_task_with_confirmation(self, 
                                      task_description: str, 
                                      confirmation_callback, 
                                      additional_context: Optional[Dict[str, Any]] = None) -> Tuple[bool, Dict[str, Any], List[str]]:
        """
        Execute a task with confirmation steps if needed.
        
        This method is designed to handle tasks that might require user confirmation
        during execution, such as when multiple options are found.
        
        Args:
            task_description: Description of the task to execute
            confirmation_callback: Async function to call when confirmation is needed
            additional_context: Additional context information for the agent
            
        Returns:
            A tuple containing (success_status, task_results, action_log)
        """
        # Custom agent implementation that can pause for confirmation would go here
        # For now, we'll use a simplified approach
        
        # Initial execution
        success, results, actions = await self.execute_task(task_description, additional_context)
        
        # Check if confirmation is needed
        if success and results.get('needs_confirmation'):
            logger.info("Task requires confirmation from user")
            
            # Get confirmation options
            options = results.get('confirmation_options', [])
            
            # Call the confirmation callback
            confirmation_result = await confirmation_callback(options)
            
            # If we have a confirmation, continue with the task
            if confirmation_result:
                # Update additional context with the confirmation
                updated_context = additional_context or {}
                updated_context['user_confirmation'] = confirmation_result
                
                # Execute the task again with the confirmation
                continue_task = f"{task_description}\n\nConfirmation received: {confirmation_result}"
                return await self.execute_task(continue_task, updated_context)
        
        # If no confirmation needed or task failed, return the original results
        return success, results, actions