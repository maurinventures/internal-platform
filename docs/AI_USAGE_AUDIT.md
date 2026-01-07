# AI Usage Audit Report
## Internal Platform - Current AI Usage Patterns and Cost Analysis

**Generated:** 2026-01-06
**Analysis Period:** Code-based analysis (database currently empty)

---

## Executive Summary

⚠️ **CRITICAL COST WARNING**: Current implementation sends full transcript context directly to AI models without RAG optimization. This pattern could result in **$1.50+ per query** vs **$0.01 with RAG** as noted in documentation.

**Key Findings:**
- No caching mechanism for AI responses or transcript contexts
- Token usage tracking is implemented but database is currently empty
- Different models have different token limits (Claude: 200K, OpenAI: 30K)
- Context expansion adds 30 seconds (≈4 segments) around each match
- No cost controls or daily limits implemented

---

## Current AI Data Flow Analysis

### How Transcripts are Sent to AI Models

**Process Flow:**
1. User makes chat request in `AIService.generate_script_with_ai()`
2. System searches transcripts via `TranscriptService.search_for_context()`
3. **Context Expansion**: Each match gets 30 seconds of surrounding context (±15 seconds)
4. Results limited by character count, not tokens:
   - **Claude models**: 300 segments, 100,000 characters max
   - **OpenAI models**: 80 segments, 20,000 characters max
5. Full context sent to AI model with user query
6. Response logged in `AILog` table

**File Locations:**
- Main AI processing: `/services/ai_service.py:150-480`
- Transcript search: `/services/transcript_service.py:33-175`
- Token logging: `/scripts/db.py:365-402` (AILog model)

---

## Token Usage Patterns and Limits

### Model-Specific Limits

| Model Type | Max Segments | Max Characters | Estimated Max Tokens | Context Window |
|------------|-------------|----------------|---------------------|----------------|
| Claude Sonnet 4 | 300 | 100,000 | ~25,000 | 200,000 |
| Claude Sonnet 3.5 | 300 | 100,000 | ~25,000 | 200,000 |
| Claude Haiku | 300 | 100,000 | ~25,000 | 200,000 |
| GPT-4o | 80 | 20,000 | ~5,000 | 128,000 |
| GPT-4o Mini | 80 | 20,000 | ~5,000 | 128,000 |

**Character-to-Token Estimation:** ~4 characters per token (conservative estimate)

### Context Expansion Impact

**Per Search Result:**
- Base segment: ~200-500 characters
- 30-second context (4 segments): ~800-2,000 characters
- **Expansion factor: 4x per match**

**Projected Token Usage:**
- Small query (10 matches): ~2,000-5,000 tokens
- Medium query (50 matches): ~10,000-25,000 tokens
- Large query (300 matches): ~75,000-125,000 tokens

---

## Caching Analysis

### Current Caching Status: ❌ **NONE IMPLEMENTED**

**No AI Response Caching:**
- Identical queries result in duplicate AI calls
- No cache for frequently accessed transcript contexts
- No prompt/response deduplication

**Video Caching Only:**
- Local video file caching exists (`/services/video_service.py:48-360`)
- 24-hour cache expiry for video downloads
- **Does not apply to transcript/AI processing**

**Recommendation:** Implement response caching for identical prompts and contexts.

---

## Cost Estimation

### Token Cost Matrix (per 1K tokens)

| Model | Input Cost | Output Cost | Total per Query* |
|-------|------------|-------------|------------------|
| **Claude Sonnet 4** | $0.015 | $0.075 | **$1.50-3.75** |
| Claude Sonnet 3.5 | $0.003 | $0.015 | $0.30-0.75 |
| Claude Haiku | $0.0005 | $0.0025 | $0.05-0.13 |
| **GPT-4o** | $0.0025 | $0.01 | **$0.25-0.63** |
| GPT-4o Mini | $0.00015 | $0.0006 | $0.02-0.04 |

*Based on 25K input + 500 output tokens for large context queries

### Projected Monthly Costs

**Current Pattern (No RAG):**
- 10 queries/day × Claude Sonnet 4: **$450-1,125/month**
- 10 queries/day × GPT-4o: **$75-190/month**

**With RAG Implementation:**
- Context reduced from 25K → 5K tokens per query
- Cost reduction: **80-90%**
- 10 queries/day × Claude Sonnet 4: **$90-225/month**

---

## Risk Assessment

### High-Risk Patterns

1. **Unlimited Context Loading**
   - System can load up to 300 segments (300K+ tokens)
   - No user/daily token limits implemented
   - Risk: Single query could cost $10-20+

2. **No Cost Controls**
   - No monitoring of daily/monthly usage
   - No user limits or warnings
   - No cost estimation before API calls

3. **Inefficient Search**
   - Up to 1,000 search results (default limit)
   - 30-second context expansion multiplies data 4x
   - No semantic deduplication

### Medium-Risk Patterns

1. **Model Selection**
   - Defaults allow expensive models (Sonnet 4, GPT-4o)
   - No automatic model downgrading for simple queries

2. **No Response Streaming**
   - Full responses loaded before returning
   - Increases perceived latency

---

## Recommendations

### Immediate Actions (Before Heavy Usage)

1. **Implement RAG System** (Prompts 14-18 in documentation)
   - Add pgvector extension to RDS
   - Create embedding service using OpenAI text-embedding-3-small
   - Process transcripts into searchable chunks (~400 tokens each)
   - Reduce context from 25K → 5K tokens per query

2. **Add Cost Controls**
   - Daily user token limits (suggest 50K tokens/day)
   - Query cost estimation before API calls
   - Usage monitoring dashboard
   - Automatic model downgrading for large contexts

3. **Implement Basic Caching**
   - Cache identical prompts for 1 hour
   - Cache transcript contexts by query hash
   - Response deduplication

### Medium-Term Optimizations

1. **Smart Context Selection**
   - Semantic similarity ranking
   - Remove duplicate/similar segments
   - Dynamic context sizing based on query complexity

2. **Model Selection Logic**
   - Route simple queries to cheaper models (Haiku, GPT-4o Mini)
   - Use Sonnet 4 only for complex analysis

3. **Usage Analytics**
   - Cost tracking by user/project
   - Query complexity analysis
   - Model performance comparison

---

## Current Implementation Status

### ✅ Implemented Features

- **Token Usage Logging**: AILog table tracks input/output tokens
- **Model Support**: Multiple AI models (Claude, OpenAI)
- **Error Handling**: Failed calls logged with error messages
- **Request Classification**: Different request types tracked

### ❌ Missing Features

- **RAG/Vector Search**: No semantic search optimization
- **Caching**: No AI response or context caching
- **Cost Limits**: No usage limits or warnings
- **Cost Calculation**: Token counts logged but costs not calculated
- **Context Optimization**: No deduplication or smart sizing

### 🔄 Partially Implemented

- **Context Limiting**: Character limits exist but not token-based
- **Model Selection**: Available but no automatic optimization

---

## Technical Debt

1. **Character vs Token Limits**: System uses character limits but AI models charge by tokens
2. **Search Inefficiency**: No pre-filtering before context expansion
3. **Logging Volume**: Full prompts/responses stored (10K-50K chars each)
4. **No Batch Processing**: Each query results in separate AI calls

---

## Data Infrastructure Assessment

**Current State:** Database is empty (development environment)
- 0 videos, transcripts, conversations in database
- 1 external content item only
- No historical usage data for analysis

**Production Readiness:**
- Database schema supports tracking (AILog table ready)
- Logging infrastructure in place
- Ready for data ingestion and usage monitoring

---

## Monitoring Recommendations

### Immediate Metrics to Track

1. **Cost Metrics**
   - Daily/monthly spend by model
   - Cost per query
   - Token usage trends

2. **Performance Metrics**
   - Average response time
   - Context size distribution
   - Query success rates

3. **Usage Patterns**
   - Queries per user
   - Model preferences
   - Peak usage times

### Alert Thresholds

- Daily cost > $50
- Single query > 100K tokens
- Query failure rate > 5%
- Response time > 30 seconds

---

## Next Steps

1. **Priority 1**: Implement RAG system (Prompts 14-18) before adding significant data
2. **Priority 2**: Add cost monitoring and user limits
3. **Priority 3**: Implement basic response caching
4. **Priority 4**: Optimize context selection algorithms

**Estimated Implementation Time:** 2-3 weeks for RAG system, 1 week for cost controls

---

*This audit was generated by analyzing the codebase structure and patterns. Once the system has production data, run `python3 analyze_ai_usage.py` for actual usage statistics.*