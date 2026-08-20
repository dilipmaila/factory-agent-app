"""
Manufacturing Chat Agent Module.
Integrates with Google Gemini via LangChain to generate grounded, safety-compliant troubleshooting responses.
"""

import os
from typing import Optional, List, Any
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()


class ManufacturingChatAgent:
    """
    LLM Chat Agent wrapping Google Gemini Flash Lite for shopfloor troubleshooting.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.2,
        api_key: Optional[str] = None,
    ):
        """
        Initializes the Gemini Chat LLM.
        """
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is not set. Please add it to your .env file."
            )

        # Default to Gemini 3.5 Flash Lite (or user specified)
        self.model_name = model_name or os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
        self.temperature = temperature

        self._init_llm()

    def _init_llm(self) -> None:
        """
        Instantiates ChatGoogleGenerativeAI with robust fallback mechanism.
        """
        candidate_models = [self.model_name, "gemini-3.1-flash-lite", "gemini-2.5-flash-lite"]
        last_error = None

        for model in candidate_models:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model=model,
                    temperature=self.temperature,
                    google_api_key=self.api_key,
                )
                self.active_model = model
                return
            except Exception as e:
                last_error = e
                continue

        if last_error:
            # Fallback initialization
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=self.temperature,
                google_api_key=self.api_key,
            )
            self.active_model = "gemini-2.5-flash"

    @staticmethod
    def _extract_text(content: Any) -> str:
        """
        Safely unpacks LLM response content across string, list of dicts, or multimodal chunks.
        """
        if isinstance(content, str):
            return content.strip()
        elif isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict):
                    if item.get("type") == "text" and "text" in item:
                        text_parts.append(str(item["text"]))
                    elif "text" in item:
                        text_parts.append(str(item["text"]))
                    elif "content" in item:
                        text_parts.append(str(item["content"]))
                    else:
                        text_parts.append(str(item))
                elif hasattr(item, "text"):
                    text_parts.append(str(item.text))
                else:
                    text_parts.append(str(item))
            return "\n".join(text_parts).strip()
        elif isinstance(content, dict):
            if "text" in content:
                return str(content["text"]).strip()
            elif "content" in content:
                return str(content["content"]).strip()
        return str(content).strip()

    def generate_response(
        self,
        working_memory_text: str,
        user_query: Optional[str] = None,
        chat_history: Optional[List[Any]] = None,
    ) -> str:
        """
        Generates a troubleshooting response based on the working memory prompt.
        
        Args:
            working_memory_text: The complete prompt assembled by working_memory.build_prompt
            user_query: Optional user question (if not already embedded in working_memory_text)
            chat_history: Optional prior messages
            
        Returns:
            The generated clean markdown response string.
        """
        try:
            # In LangChain Chat, send working memory as the comprehensive prompt
            messages = [HumanMessage(content=working_memory_text)]
            response = self.llm.invoke(messages)
            
            if hasattr(response, "content"):
                return self._extract_text(response.content)
            return self._extract_text(response)

        except Exception as e:
            print(f"[ManufacturingChatAgent] Error generating response: {e}")
            # Try reinitializing with fallback model if 404/not found error
            if "NOT_FOUND" in str(e) or "not available" in str(e).lower():
                try:
                    self.llm = ChatGoogleGenerativeAI(
                        model="gemini-2.0-flash",
                        temperature=self.temperature,
                        google_api_key=self.api_key,
                    )
                    self.active_model = "gemini-2.0-flash"
                    response = self.llm.invoke([HumanMessage(content=working_memory_text)])
                    if hasattr(response, "content"):
                        return self._extract_text(response.content)
                    return self._extract_text(response)
                except Exception as fallback_err:
                    return (
                        f"⚠️ **Error connecting to AI service**: {fallback_err}\n\n"
                        f"Please check your API key and network connection."
                    )
            return f"⚠️ **Generation Error**: {e}"
