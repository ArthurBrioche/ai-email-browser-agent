"""
Query understanding engine for the AI Email Browser Agent.
This module interprets email queries and determines if clarification is needed.
"""

import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Output schemas for the LLM
class TaskDetails(BaseModel):
    """Schema for task details extracted from the query"""
    website: str = Field(description="Website where the task needs to be performed")
    action_type: str = Field(description="Type of action to be performed (e.g., 'search', 'add connection', 'apply')")
    target: Optional[str] = Field(None, description="Target of the action (e.g., person name, job title)")
    additional_context: Optional[Dict[str, Any]] = Field(None, description="Any additional context provided in the query")

class QueryInterpretation(BaseModel):
    """Schema for the query interpretation results"""
    task_type: str = Field(description="High-level type of task being requested")
    requires_clarification: bool = Field(description="Whether clarification is needed before proceeding")
    clarification_questions: Optional[List[str]] = Field(None, description="Questions to ask for clarification")
    task_details: TaskDetails = Field(description="Extracted details about the task")

class QueryUnderstanding:
    """
    A class to understand and interpret email queries using LangChain and LLMs.
    
    This class analyzes the content of an email to determine the requested task,
    extract relevant details, and identify if any clarification is needed.
    """
    
    def __init__(self, openai_api_key: str, model_name: str = "gpt-4o"):
        """
        Initialize the QueryUnderstanding with an LLM.
        
        Args:
            openai_api_key: API key for OpenAI
            model_name: Name of the OpenAI model to use
        """
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model=model_name,
            temperature=0.1  # Keep temperature low for consistent results
        )
        
    async def interpret_query(self, email_content: str) -> QueryInterpretation:
        """
        Interpret an email query to understand the task and required details.
        
        Args:
            email_content: The content of the email to interpret
            
        Returns:
            QueryInterpretation object with task details and clarification needs
        """
        # Set up the parser for structured output
        parser = PydanticOutputParser(pydantic_object=QueryInterpretation)
        
        # Create the prompt template
        prompt_template = """
        You are an AI assistant that specializes in understanding email requests for browser automation tasks.
        Analyze the following email content carefully and extract all relevant information:
        
        EMAIL CONTENT:
        {email_content}
        
        Determine the following:
        1. What type of browser task is being requested (browsing, searching, form filling, etc.)
        2. If any clarification is needed before the task can be executed properly
        3. Specific details about the task (website, action, target, etc.)
        
        If the request is ambiguous or lacks critical information, indicate that clarification is needed 
        and list specific questions to ask the user.
        
        {format_instructions}
        """
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["email_content"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        # Create and run the chain
        chain = LLMChain(llm=self.llm, prompt=prompt)
        try:
            logger.info("Interpreting email query")
            result = await chain.arun(email_content=email_content)
            logger.info("Query interpretation complete")
            
            # Parse the result into our structured format
            interpretation = parser.parse(result)
            return interpretation
            
        except Exception as e:
            logger.error(f"Error interpreting query: {e}")
            # Provide a fallback response if parsing fails
            return QueryInterpretation(
                task_type="unknown",
                requires_clarification=True,
                clarification_questions=["Could you please provide more details about what you'd like me to do?"],
                task_details=TaskDetails(
                    website="",
                    action_type="unknown"
                )
            )