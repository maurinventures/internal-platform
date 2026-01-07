#!/usr/bin/env python3
"""
Analyze AI usage patterns from the database.
This script reads from the ai_logs table to calculate token usage and costs.
"""

import sys
import os
from statistics import mean, median
from collections import Counter, defaultdict
from datetime import datetime, timedelta

# Add the current directory to sys.path so we can import our modules
sys.path.append('/Users/josephs./internal-platform/web')
sys.path.append('/Users/josephs./internal-platform')

try:
    from scripts.db import DatabaseSession, AILog
except ImportError:
    print("Could not import database modules")
    sys.exit(1)


def analyze_token_usage():
    """Analyze token usage patterns from AI logs."""
    print("Analyzing AI usage patterns from database...")

    stats = {
        'total_calls': 0,
        'successful_calls': 0,
        'failed_calls': 0,
        'input_tokens': [],
        'output_tokens': [],
        'total_tokens': [],
        'by_model': defaultdict(lambda: {'calls': 0, 'input_tokens': [], 'output_tokens': []}),
        'by_request_type': defaultdict(lambda: {'calls': 0, 'input_tokens': [], 'output_tokens': []}),
        'recent_calls': 0,  # Last 30 days
        'costs_by_model': defaultdict(float)
    }

    # Define token costs (per 1K tokens)
    token_costs = {
        # Claude models (input cost, output cost per 1K tokens)
        'claude-sonnet': (0.003, 0.015),  # Sonnet 3.5
        'claude-sonnet-4': (0.015, 0.075),  # Sonnet 4 - estimated
        'claude-opus': (0.015, 0.075),  # Opus 3
        'claude-haiku': (0.0005, 0.0025),  # Haiku 3.5
        # OpenAI models
        'gpt-4o': (0.0025, 0.01),  # GPT-4o
        'gpt-4o-mini': (0.00015, 0.0006),  # GPT-4o mini
        'gpt-4': (0.03, 0.06),  # GPT-4
        'gpt-3.5-turbo': (0.001, 0.002),  # GPT-3.5 Turbo
    }

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    try:
        with DatabaseSession() as db_session:
            # Get all AI logs
            logs = db_session.query(AILog).order_by(AILog.created_at.desc()).all()

            print(f"Found {len(logs)} AI log entries")

            for log in logs:
                stats['total_calls'] += 1

                if log.created_at >= thirty_days_ago:
                    stats['recent_calls'] += 1

                if log.success:
                    stats['successful_calls'] += 1
                else:
                    stats['failed_calls'] += 1

                # Track tokens
                if log.input_tokens:
                    stats['input_tokens'].append(log.input_tokens)
                    stats['by_model'][log.model]['input_tokens'].append(log.input_tokens)
                    stats['by_request_type'][log.request_type]['input_tokens'].append(log.input_tokens)

                if log.output_tokens:
                    stats['output_tokens'].append(log.output_tokens)
                    stats['by_model'][log.model]['output_tokens'].append(log.output_tokens)
                    stats['by_request_type'][log.request_type]['output_tokens'].append(log.output_tokens)

                total = (log.input_tokens or 0) + (log.output_tokens or 0)
                if total > 0:
                    stats['total_tokens'].append(total)

                # Track by model
                stats['by_model'][log.model]['calls'] += 1
                stats['by_request_type'][log.request_type]['calls'] += 1

                # Calculate costs
                if log.input_tokens and log.output_tokens:
                    model_name = log.model.lower()
                    base_model = None

                    # Map model names to cost keys
                    for cost_key in token_costs.keys():
                        if cost_key in model_name:
                            base_model = cost_key
                            break

                    if base_model:
                        input_cost, output_cost = token_costs[base_model]
                        cost = (log.input_tokens / 1000 * input_cost) + (log.output_tokens / 1000 * output_cost)
                        stats['costs_by_model'][log.model] += cost

    except Exception as e:
        print(f"Error querying database: {e}")
        return None

    return stats


def print_analysis(stats):
    """Print formatted analysis results."""
    if not stats:
        print("No stats available")
        return

    print("\n" + "="*60)
    print("AI USAGE ANALYSIS RESULTS")
    print("="*60)

    # Overall statistics
    print(f"\nOVERALL STATISTICS:")
    print(f"  Total AI calls: {stats['total_calls']:,}")
    print(f"  Successful calls: {stats['successful_calls']:,}")
    print(f"  Failed calls: {stats['failed_calls']:,}")
    print(f"  Recent calls (30 days): {stats['recent_calls']:,}")
    if stats['successful_calls'] > 0:
        success_rate = (stats['successful_calls'] / stats['total_calls']) * 100
        print(f"  Success rate: {success_rate:.1f}%")

    # Token usage statistics
    if stats['input_tokens']:
        print(f"\nTOKEN USAGE STATISTICS:")
        print(f"  Input tokens:")
        print(f"    Average: {mean(stats['input_tokens']):,.0f}")
        print(f"    Median: {median(stats['input_tokens']):,.0f}")
        print(f"    Min: {min(stats['input_tokens']):,}")
        print(f"    Max: {max(stats['input_tokens']):,}")

    if stats['output_tokens']:
        print(f"  Output tokens:")
        print(f"    Average: {mean(stats['output_tokens']):,.0f}")
        print(f"    Median: {median(stats['output_tokens']):,.0f}")
        print(f"    Min: {min(stats['output_tokens']):,}")
        print(f"    Max: {max(stats['output_tokens']):,}")

    if stats['total_tokens']:
        print(f"  Total tokens per request:")
        print(f"    Average: {mean(stats['total_tokens']):,.0f}")
        print(f"    Median: {median(stats['total_tokens']):,.0f}")

    # By model
    print(f"\nUSAGE BY MODEL:")
    for model, data in sorted(stats['by_model'].items(), key=lambda x: x[1]['calls'], reverse=True):
        print(f"  {model}:")
        print(f"    Calls: {data['calls']:,}")
        if data['input_tokens']:
            print(f"    Avg input tokens: {mean(data['input_tokens']):,.0f}")
        if data['output_tokens']:
            print(f"    Avg output tokens: {mean(data['output_tokens']):,.0f}")

    # By request type
    print(f"\nUSAGE BY REQUEST TYPE:")
    for req_type, data in sorted(stats['by_request_type'].items(), key=lambda x: x[1]['calls'], reverse=True):
        print(f"  {req_type}:")
        print(f"    Calls: {data['calls']:,}")
        if data['input_tokens']:
            print(f"    Avg input tokens: {mean(data['input_tokens']):,.0f}")
        if data['output_tokens']:
            print(f"    Avg output tokens: {mean(data['output_tokens']):,.0f}")

    # Cost analysis
    total_cost = sum(stats['costs_by_model'].values())
    if total_cost > 0:
        print(f"\nCOST ANALYSIS:")
        print(f"  Total estimated cost: ${total_cost:.2f}")
        for model, cost in sorted(stats['costs_by_model'].items(), key=lambda x: x[1], reverse=True):
            if cost > 0:
                print(f"    {model}: ${cost:.2f}")

        # Monthly estimate based on recent usage
        if stats['recent_calls'] > 0:
            monthly_estimate = total_cost * (stats['recent_calls'] / stats['total_calls']) * 12
            print(f"  Estimated monthly cost: ${monthly_estimate:.2f}")


if __name__ == "__main__":
    try:
        stats = analyze_token_usage()
        print_analysis(stats)
    except Exception as e:
        print(f"Error running analysis: {e}")
        import traceback
        traceback.print_exc()