"""AI-powered market analysis advisor using multiple LLM providers."""

import os
from typing import Optional, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from my_agent.utils.config import config
from my_agent.utils.constants import (
    AI_TEMPERATURE,
    DEFAULT_CLAUDE_MODEL,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_OPENAI_MODEL,
    AIProvider,
)
from my_agent.utils.logger import log_info, log_warning, log_error


class AIAdvisor:
    """AI advisor for enhanced trading decisions using LLM."""

    def __init__(self, provider: str = "gemini", model: Optional[str] = None, enabled: bool = True):
        """
        Initialize AI advisor with multiple provider support.

        Args:
            provider: LLM provider ("gemini", "openai", "claude")
            model: Specific model (auto-selected if None)
            enabled: Whether to use AI (fallback to rules-only if False)
        """
        self.provider = provider.lower()
        self.enabled = enabled
        self.llm = None
        self.is_gemini_direct = False

        if not self.enabled:
            log_info("AI Advisor disabled by user")
            return

        # Try to initialize the selected provider
        try:
            if self.provider == AIProvider.GEMINI:
                self._init_gemini(model or DEFAULT_GEMINI_MODEL)
            elif self.provider == AIProvider.OPENAI:
                self._init_openai(model or DEFAULT_OPENAI_MODEL)
            elif self.provider == AIProvider.CLAUDE:
                self._init_claude(model or DEFAULT_CLAUDE_MODEL)
            else:
                log_warning(f"Unknown provider: {provider}, trying Gemini as fallback")
                self._init_gemini(DEFAULT_GEMINI_MODEL)

        except Exception as e:
            log_warning(f"AI Advisor initialization failed: {e}")
            log_info("Falling back to rules-only mode")
            self.enabled = False

    def _init_gemini(self, model: str):
        """Initialize Google Gemini using direct SDK."""
        import google.generativeai as genai

        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not found")

        genai.configure(api_key=api_key)
        self.llm = genai.GenerativeModel(DEFAULT_GEMINI_MODEL)
        self.is_gemini_direct = True  # Flag for custom handling

        log_info(f"🤖 AI Advisor initialized (Gemini Direct: {DEFAULT_GEMINI_MODEL})")

    def _init_openai(self, model: str):
        """Initialize OpenAI."""
        from langchain_openai import ChatOpenAI

        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found")

        self.llm = ChatOpenAI(
            model=model,
            temperature=AI_TEMPERATURE,
            api_key=config.OPENAI_API_KEY
        )
        log_info(f"🤖 AI Advisor initialized (OpenAI: {model})")

    def _init_claude(self, model: str):
        """Initialize Anthropic Claude."""
        from langchain_anthropic import ChatAnthropic

        api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")

        self.llm = ChatAnthropic(
            model=model,
            temperature=AI_TEMPERATURE,
            anthropic_api_key=api_key
        )
        log_info(f"🤖 AI Advisor initialized (Claude: {model})")

    def analyze_market_sentiment(
        self,
        market_question: str,
        current_prob: float,
        position_summary: Dict,
        rule_based_action: str
    ) -> Dict:
        """
        Get AI analysis of market conditions.

        Args:
            market_question: The market question being traded
            current_prob: Current YES probability
            position_summary: Dictionary with position details
            rule_based_action: Action recommended by rule-based strategy

        Returns:
            Dictionary with AI analysis and recommendation
        """
        if not self.enabled:
            return {
                "ai_enabled": False,
                "recommendation": rule_based_action,
                "confidence": None,
                "reasoning": "AI disabled - using rules only"
            }

        try:
            # Construct prompt
            system_prompt = self._get_system_prompt()
            user_prompt = self._construct_market_analysis_prompt(
                market_question=market_question,
                current_prob=current_prob,
                position_summary=position_summary,
                rule_based_action=rule_based_action
            )

            # Get AI response
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            # Handle different LLM providers
            if hasattr(self, 'is_gemini_direct') and self.is_gemini_direct:
                # Gemini direct SDK
                full_prompt = system_prompt + "\n\n" + user_prompt
                response = self.llm.generate_content(full_prompt)
                ai_response = response.text
            else:
                # Langchain (OpenAI, Claude)
                response = self.llm.invoke(messages)
                ai_response = response.content

            # Parse response
            analysis = self._parse_ai_response(ai_response, rule_based_action)

            return analysis

        except Exception as e:
            log_error(f"AI analysis failed: {e}")
            return {
                "ai_enabled": True,
                "recommendation": rule_based_action,
                "confidence": None,
                "reasoning": f"AI error: {str(e)} - using rules only",
                "error": str(e)
            }

    def _get_system_prompt(self) -> str:
        """Get system prompt for AI advisor."""
        return """You are an expert trading advisor for prediction markets on Polymarket.

Your role is to analyze market conditions and provide trading recommendations.
You must be:
1. Conservative - prioritize capital preservation
2. Data-driven - focus on probabilities and position metrics
3. Clear - provide specific reasoning for recommendations

When analyzing, consider:
- Current market probability vs historical levels
- Position risk (PnL, exposure)
- Market dynamics (is this a reasonable probability?)
- Risk management (when to cut losses, when to lock profits)

IMPORTANT: You can recommend one of these actions:
- CONFIRM: Agree with rule-based recommendation
- OVERRIDE_HOLD: Suggest holding instead (provide strong reasoning)
- OVERRIDE_SELL: Suggest selling/stop-loss instead (provide strong reasoning)
- OVERRIDE_TAKE_PROFIT: Suggest taking profit instead (provide strong reasoning)

Format your response as:
RECOMMENDATION: [action]
CONFIDENCE: [0-100]
REASONING: [2-3 sentences explaining your analysis]
"""

    def _construct_market_analysis_prompt(
        self,
        market_question: str,
        current_prob: float,
        position_summary: Dict,
        rule_based_action: str
    ) -> str:
        """Construct prompt for market analysis."""

        yes_shares = position_summary.get('yes_shares', 0)
        no_shares = position_summary.get('no_shares', 0)
        total_invested = position_summary.get('total_invested', 0)
        net_pnl = position_summary.get('net_pnl', 0)
        roi = position_summary.get('roi', 0)

        prompt = f"""Analyze this Polymarket trading situation:

MARKET: {market_question}

CURRENT SITUATION:
- Market probability: {current_prob * 100:.2f}%
- Your position: {yes_shares:.0f} YES shares, {no_shares:.0f} NO shares
- Total invested: ${total_invested:,.2f}
- Current P&L: ${net_pnl:,.2f} ({roi:.1f}% ROI)

RULE-BASED RECOMMENDATION: {rule_based_action}

ANALYSIS NEEDED:
1. Is the current probability ({current_prob * 100:.1f}%) reasonable for this market?
2. Given the position and P&L, what's the risk/reward of holding vs exiting?
3. Should we follow the rule-based recommendation or override it?

Provide your recommendation (CONFIRM, OVERRIDE_HOLD, OVERRIDE_SELL, or OVERRIDE_TAKE_PROFIT),
confidence level (0-100), and clear reasoning.
"""
        return prompt

    def _parse_ai_response(self, response: str, fallback_action: str) -> Dict:
        """
        Parse AI response into structured format.

        Args:
            response: Raw AI response
            fallback_action: Action to use if parsing fails

        Returns:
            Dictionary with parsed recommendation
        """
        try:
            lines = response.strip().split('\n')
            result = {
                "ai_enabled": True,
                "recommendation": fallback_action,
                "confidence": 50,
                "reasoning": response
            }

            for line in lines:
                line = line.strip()

                if line.startswith("RECOMMENDATION:"):
                    rec = line.split(":", 1)[1].strip().upper()

                    # Map AI recommendation to action
                    if "CONFIRM" in rec:
                        result["recommendation"] = fallback_action
                    elif "OVERRIDE_HOLD" in rec or "HOLD" in rec:
                        result["recommendation"] = "HOLD"
                    elif "OVERRIDE_SELL" in rec or "STOP" in rec:
                        result["recommendation"] = "STOP_LOSS"
                    elif "OVERRIDE_TAKE_PROFIT" in rec or "TAKE_PROFIT" in rec:
                        result["recommendation"] = "TAKE_PROFIT"

                elif line.startswith("CONFIDENCE:"):
                    try:
                        conf_str = line.split(":", 1)[1].strip()
                        # Extract first number found
                        import re
                        numbers = re.findall(r'\d+', conf_str)
                        if numbers:
                            result["confidence"] = min(100, max(0, int(numbers[0])))
                    except:
                        result["confidence"] = 50

                elif line.startswith("REASONING:"):
                    result["reasoning"] = line.split(":", 1)[1].strip()

            return result

        except Exception as e:
            log_warning(f"Failed to parse AI response: {e}")
            return {
                "ai_enabled": True,
                "recommendation": fallback_action,
                "confidence": 50,
                "reasoning": f"Parse error - using rules: {response[:200]}",
                "error": str(e)
            }

    def get_quick_confidence_score(self, market_question: str, current_prob: float) -> Optional[int]:
        """
        Get a quick confidence score (0-100) for current probability.

        Args:
            market_question: Market question
            current_prob: Current probability

        Returns:
            Confidence score 0-100, or None if AI disabled
        """
        if not self.enabled:
            return None

        try:
            prompt = f"""Rate your confidence (0-100) that this probability is accurate:

Market: {market_question}
Current probability: {current_prob * 100:.1f}%

Respond with ONLY a number 0-100."""

            response = self.llm.invoke([HumanMessage(content=prompt)])

            # Extract number
            import re
            numbers = re.findall(r'\d+', response.content)
            if numbers:
                return min(100, max(0, int(numbers[0])))

            return 50

        except Exception as e:
            log_warning(f"Quick confidence check failed: {e}")
            return None


def create_ai_advisor(
    enabled: bool = True,
    provider: str = "gemini",
    model: Optional[str] = None
) -> AIAdvisor:
    """
    Create AI advisor instance with multi-provider support.

    Args:
        enabled: Whether to enable AI (fallback to rules if disabled/fails)
        provider: LLM provider ("gemini", "openai", "claude")
        model: Specific model (auto-selected if None)

    Returns:
        AIAdvisor instance

    Examples:
        create_ai_advisor(provider="gemini")  # Free!
        create_ai_advisor(provider="openai", model="gpt-4")
        create_ai_advisor(provider="claude", model="claude-3-opus-20240229")
    """
    return AIAdvisor(provider=provider, model=model, enabled=enabled)
