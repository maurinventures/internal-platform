"""
Usage Limits Service for Prompt 19

Implements token limits, daily user limits, usage warnings, and prompt caching
to control AI API costs and prevent overuse.
"""

import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from sqlalchemy import func, desc, and_

from scripts.db import DatabaseSession, AILog, AIPromptCache, User


class UsageLimitsService:
    """Service for managing AI usage limits and cost controls."""

    # Prompt 19 Requirements
    MAX_CONTEXT_TOKENS = 50000  # 50K context token limit per request
    MAX_DAILY_TOKENS_PER_USER = 500000  # 500K daily token limit per user
    WARNING_THRESHOLD = 0.8  # 80% usage warning

    # Model costs per 1K tokens (input, output)
    MODEL_COSTS = {
        'claude-sonnet': (0.003, 0.015),
        'claude-sonnet-4': (0.015, 0.075),
        'claude-opus': (0.015, 0.075),
        'claude-haiku': (0.0005, 0.0025),
        'gpt-4o': (0.0025, 0.01),
        'gpt-4o-mini': (0.00015, 0.0006),
    }

    @staticmethod
    def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> Tuple[float, float, float]:
        """Calculate cost for AI call.

        Returns:
            Tuple of (input_cost, output_cost, total_cost)
        """
        if model not in UsageLimitsService.MODEL_COSTS:
            # Default to Claude Sonnet pricing for unknown models
            input_rate, output_rate = UsageLimitsService.MODEL_COSTS['claude-sonnet']
        else:
            input_rate, output_rate = UsageLimitsService.MODEL_COSTS[model]

        input_cost = (input_tokens / 1000.0) * input_rate
        output_cost = (output_tokens / 1000.0) * output_rate
        total_cost = input_cost + output_cost

        return input_cost, output_cost, total_cost

    @staticmethod
    def check_context_limit(input_tokens: int) -> Dict[str, Any]:
        """Check if request exceeds context token limit.

        Returns:
            Dict with 'allowed', 'reason', 'limit', 'requested'
        """
        if input_tokens > UsageLimitsService.MAX_CONTEXT_TOKENS:
            return {
                'allowed': False,
                'reason': f'Context exceeds {UsageLimitsService.MAX_CONTEXT_TOKENS:,} token limit',
                'limit': UsageLimitsService.MAX_CONTEXT_TOKENS,
                'requested': input_tokens
            }

        return {
            'allowed': True,
            'limit': UsageLimitsService.MAX_CONTEXT_TOKENS,
            'requested': input_tokens
        }

    @staticmethod
    def check_daily_user_limit(user_id: str, additional_tokens: int = 0) -> Dict[str, Any]:
        """Check if user exceeds daily token limit.

        Returns:
            Dict with 'allowed', 'usage', 'limit', 'percentage', 'warning'
        """
        today = datetime.utcnow().date()
        tomorrow = today + timedelta(days=1)

        with DatabaseSession() as db_session:
            # Get today's total tokens for user
            result = db_session.query(
                func.sum(func.coalesce(AILog.input_tokens, 0) + func.coalesce(AILog.output_tokens, 0))
            ).filter(
                and_(
                    AILog.user_id == user_id,
                    AILog.created_at >= today,
                    AILog.created_at < tomorrow,
                    AILog.success == 1
                )
            ).scalar() or 0

            current_usage = int(result)
            total_with_new = current_usage + additional_tokens
            percentage = total_with_new / UsageLimitsService.MAX_DAILY_TOKENS_PER_USER

            return {
                'allowed': total_with_new <= UsageLimitsService.MAX_DAILY_TOKENS_PER_USER,
                'usage': current_usage,
                'additional': additional_tokens,
                'total_after': total_with_new,
                'limit': UsageLimitsService.MAX_DAILY_TOKENS_PER_USER,
                'percentage': percentage,
                'warning': percentage >= UsageLimitsService.WARNING_THRESHOLD,
                'reason': f'Daily limit exceeded ({total_with_new:,}/{UsageLimitsService.MAX_DAILY_TOKENS_PER_USER:,} tokens)' if total_with_new > UsageLimitsService.MAX_DAILY_TOKENS_PER_USER else None
            }

    @staticmethod
    def get_prompt_hash(prompt: str, model: str) -> str:
        """Generate hash for prompt caching."""
        content = f"{model}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()

    @staticmethod
    def check_prompt_cache(prompt: str, model: str) -> Optional[Dict[str, Any]]:
        """Check if prompt response is cached.

        Returns:
            Cached response dict if found, None otherwise
        """
        prompt_hash = UsageLimitsService.get_prompt_hash(prompt, model)

        with DatabaseSession() as db_session:
            cache_entry = db_session.query(AIPromptCache).filter(
                AIPromptCache.prompt_hash == prompt_hash
            ).first()

            if cache_entry:
                # Update usage stats
                cache_entry.hit_count += 1
                cache_entry.last_used_at = datetime.utcnow()
                db_session.commit()

                return {
                    'response': cache_entry.response,
                    'input_tokens': cache_entry.input_tokens,
                    'output_tokens': cache_entry.output_tokens,
                    'total_cost': cache_entry.total_cost,
                    'cached': True,
                    'hit_count': cache_entry.hit_count
                }

        return None

    @staticmethod
    def cache_prompt_response(
        prompt: str,
        model: str,
        response: str,
        input_tokens: int,
        output_tokens: int,
        total_cost: float
    ):
        """Cache a prompt response for future reuse."""
        prompt_hash = UsageLimitsService.get_prompt_hash(prompt, model)

        with DatabaseSession() as db_session:
            cache_entry = AIPromptCache(
                prompt_hash=prompt_hash,
                model=model,
                prompt=prompt[:10000],  # Truncate very long prompts
                response=response,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_cost=total_cost
            )
            db_session.add(cache_entry)
            try:
                db_session.commit()
            except Exception:
                # Handle duplicate hash (race condition)
                db_session.rollback()

    @staticmethod
    def get_user_usage_stats(user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive usage statistics for a user."""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        with DatabaseSession() as db_session:
            # Get usage stats
            logs = db_session.query(AILog).filter(
                and_(
                    AILog.user_id == user_id,
                    AILog.created_at >= start_date,
                    AILog.success == 1
                )
            ).all()

            total_calls = len(logs)
            total_input_tokens = sum(log.input_tokens or 0 for log in logs)
            total_output_tokens = sum(log.output_tokens or 0 for log in logs)
            total_cost = sum(log.total_cost or 0 for log in logs)

            # Today's usage
            today = datetime.utcnow().date()
            today_logs = [log for log in logs if log.created_at.date() == today]
            today_tokens = sum((log.input_tokens or 0) + (log.output_tokens or 0) for log in today_logs)
            today_percentage = today_tokens / UsageLimitsService.MAX_DAILY_TOKENS_PER_USER

            return {
                'period_days': days,
                'total_calls': total_calls,
                'total_input_tokens': total_input_tokens,
                'total_output_tokens': total_output_tokens,
                'total_tokens': total_input_tokens + total_output_tokens,
                'total_cost': total_cost,
                'today_tokens': today_tokens,
                'today_percentage': today_percentage,
                'daily_limit': UsageLimitsService.MAX_DAILY_TOKENS_PER_USER,
                'warning': today_percentage >= UsageLimitsService.WARNING_THRESHOLD,
                'models_used': list(set(log.model for log in logs if log.model))
            }

    @staticmethod
    def clean_old_cache(days: int = 30):
        """Clean old cached prompts to save storage."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        with DatabaseSession() as db_session:
            deleted = db_session.query(AIPromptCache).filter(
                AIPromptCache.last_used_at < cutoff_date
            ).delete()
            db_session.commit()
            return deleted