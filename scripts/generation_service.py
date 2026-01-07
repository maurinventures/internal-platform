"""
Generation Service for Prompt 20: Long-Form Content Pipeline

Implements a multi-stage pipeline for generating long-form content:
1. Brief Analysis - Analyze user requirements
2. Outline Creation - Create detailed section breakdown
3. Consistency Docs - Generate style guide, fact sheet, character bible
4. Sectional Generation - Generate content section by section
5. Assembly - Combine sections into final document
6. Quality Check - Verify continuity and fact consistency

Each stage stores its artifacts in the database and can be resumed if interrupted.
"""

import json
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID

from .db import DatabaseSession, GenerationJob, User
from .config_loader import get_config

# Import AI service for generation calls
try:
    from web.services.ai_service import AIService
    from web.services.usage_limits_service import UsageLimitsService
except ImportError:
    from ..web.services.ai_service import AIService
    from ..web.services.usage_limits_service import UsageLimitsService


class GenerationService:
    """Service for managing long-form content generation pipeline."""

    # Pipeline stage constants
    STAGE_BRIEF_ANALYSIS = 'brief_analysis'
    STAGE_OUTLINE_CREATION = 'outline_creation'
    STAGE_CONSISTENCY_DOCS = 'consistency_docs'
    STAGE_SECTIONAL_GENERATION = 'sectional_generation'
    STAGE_ASSEMBLY = 'assembly'
    STAGE_QUALITY_CHECK = 'quality_check'
    STAGE_COMPLETED = 'completed'
    STAGE_FAILED = 'failed'

    PIPELINE_STAGES = [
        STAGE_BRIEF_ANALYSIS,
        STAGE_OUTLINE_CREATION,
        STAGE_CONSISTENCY_DOCS,
        STAGE_SECTIONAL_GENERATION,
        STAGE_ASSEMBLY,
        STAGE_QUALITY_CHECK,
        STAGE_COMPLETED
    ]

    # Content type templates
    CONTENT_FORMATS = {
        'blog_post': {
            'typical_sections': ['introduction', 'main_points', 'examples', 'conclusion'],
            'typical_word_count': 2000,
            'style_notes': 'Conversational, informative, SEO-friendly'
        },
        'linkedin_article': {
            'typical_sections': ['hook', 'personal_context', 'main_insights', 'call_to_action'],
            'typical_word_count': 1500,
            'style_notes': 'Professional, personal, actionable'
        },
        'script': {
            'typical_sections': ['opening', 'problem_setup', 'solution', 'examples', 'closing'],
            'typical_word_count': 3000,
            'style_notes': 'Conversational, engaging, natural speech patterns'
        },
        'report': {
            'typical_sections': ['executive_summary', 'background', 'analysis', 'recommendations'],
            'typical_word_count': 4000,
            'style_notes': 'Formal, data-driven, actionable'
        }
    }

    @staticmethod
    def create_generation_job(
        brief: str,
        job_name: str = None,
        job_type: str = 'article',
        content_format: str = 'blog_post',
        target_word_count: int = None,
        target_audience: str = None,
        user_id: str = None
    ) -> str:
        """Create a new generation job and return its ID."""

        if not job_name:
            job_name = f"{content_format.title()} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        if not target_word_count:
            target_word_count = GenerationService.CONTENT_FORMATS.get(
                content_format, {'typical_word_count': 2000}
            )['typical_word_count']

        with DatabaseSession() as db_session:
            job = GenerationJob(
                job_name=job_name,
                job_type=job_type,
                brief=brief,
                content_format=content_format,
                target_word_count=target_word_count,
                target_audience=target_audience or "General audience",
                created_by=UUID(user_id) if user_id else None,
                status=GenerationService.STAGE_BRIEF_ANALYSIS
            )

            db_session.add(job)
            db_session.commit()

            print(f"[GENERATION] Created job {job.id}: {job_name}")
            return str(job.id)

    @staticmethod
    def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
        """Get current status and progress of a generation job."""

        with DatabaseSession() as db_session:
            job = db_session.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if not job:
                return None

            progress_percentage = 0
            if job.status == GenerationService.STAGE_COMPLETED:
                progress_percentage = 100
            elif job.status in GenerationService.PIPELINE_STAGES:
                stage_index = GenerationService.PIPELINE_STAGES.index(job.status)
                progress_percentage = (stage_index / len(GenerationService.PIPELINE_STAGES)) * 100

            return {
                'job_id': str(job.id),
                'job_name': job.job_name,
                'status': job.status,
                'progress_percentage': progress_percentage,
                'sections_completed': job.sections_completed,
                'sections_total': job.sections_total,
                'target_word_count': job.target_word_count,
                'actual_word_count': job.word_count_actual,
                'total_cost': job.total_cost,
                'created_at': job.created_at.isoformat(),
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'error_message': job.error_message
            }

    @staticmethod
    def continue_pipeline(job_id: str, model: str = "claude-sonnet") -> Dict[str, Any]:
        """Continue pipeline execution from current stage."""

        with DatabaseSession() as db_session:
            job = db_session.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if not job:
                return {'error': 'Job not found'}

            if job.status == GenerationService.STAGE_COMPLETED:
                return {'message': 'Job already completed', 'status': job.status}

            if job.status == GenerationService.STAGE_FAILED:
                job.status = GenerationService.STAGE_BRIEF_ANALYSIS  # Reset to retry
                job.retry_count += 1
                db_session.commit()

            try:
                # Execute next pipeline stage
                if job.status == GenerationService.STAGE_BRIEF_ANALYSIS:
                    result = GenerationService._stage_brief_analysis(job, model)
                elif job.status == GenerationService.STAGE_OUTLINE_CREATION:
                    result = GenerationService._stage_outline_creation(job, model)
                elif job.status == GenerationService.STAGE_CONSISTENCY_DOCS:
                    result = GenerationService._stage_consistency_docs(job, model)
                elif job.status == GenerationService.STAGE_SECTIONAL_GENERATION:
                    result = GenerationService._stage_sectional_generation(job, model)
                elif job.status == GenerationService.STAGE_ASSEMBLY:
                    result = GenerationService._stage_assembly(job, model)
                elif job.status == GenerationService.STAGE_QUALITY_CHECK:
                    result = GenerationService._stage_quality_check(job, model)
                else:
                    result = {'error': f'Unknown stage: {job.status}'}

                # Save progress
                db_session.commit()
                return result

            except Exception as e:
                job.status = GenerationService.STAGE_FAILED
                job.error_message = str(e)
                db_session.commit()
                print(f"[GENERATION ERROR] Job {job_id} failed: {e}")
                return {'error': str(e), 'status': 'failed'}

    @staticmethod
    def _stage_brief_analysis(job: GenerationJob, model: str) -> Dict[str, Any]:
        """Stage 1: Analyze the brief and extract requirements."""

        prompt = f"""Analyze this content generation brief and extract key requirements:

BRIEF: "{job.brief}"

Content Format: {job.content_format}
Target Word Count: {job.target_word_count}
Target Audience: {job.target_audience}

Please provide a structured analysis in JSON format:
{{
  "refined_topic": "Clear, specific topic statement",
  "key_points": ["Point 1", "Point 2", "Point 3"],
  "tone": "Professional/Casual/Technical/etc",
  "style_requirements": ["requirement 1", "requirement 2"],
  "special_considerations": ["consideration 1", "consideration 2"],
  "estimated_sections": 4,
  "suggested_word_distribution": {{"section1": 500, "section2": 600}}
}}

Focus on understanding what the user actually wants to achieve."""

        # Make AI call with usage tracking
        try:
            response = GenerationService._make_ai_call(
                prompt=prompt,
                model=model,
                job_id=str(job.id),
                stage="brief_analysis"
            )

            # Parse JSON response
            analysis = json.loads(response['content'])

            # Update job with analysis
            job.status = GenerationService.STAGE_OUTLINE_CREATION
            job.total_cost += response.get('cost', 0)
            job.total_tokens_used += response.get('tokens', 0)

            print(f"[GENERATION] Brief analysis completed for job {job.id}")
            return {
                'stage': 'brief_analysis',
                'status': 'completed',
                'analysis': analysis,
                'next_stage': GenerationService.STAGE_OUTLINE_CREATION
            }

        except json.JSONDecodeError as e:
            job.error_message = f"Failed to parse brief analysis: {e}"
            raise Exception(f"AI response was not valid JSON: {e}")

    @staticmethod
    def _stage_outline_creation(job: GenerationJob, model: str) -> Dict[str, Any]:
        """Stage 2: Create detailed outline with sections and word targets."""

        # Get content format template
        format_info = GenerationService.CONTENT_FORMATS.get(job.content_format, {})
        typical_sections = format_info.get('typical_sections', ['introduction', 'body', 'conclusion'])

        prompt = f"""Create a detailed outline for this content generation project:

BRIEF: "{job.brief}"
Content Format: {job.content_format}
Target Word Count: {job.target_word_count}
Target Audience: {job.target_audience}

Typical sections for {job.content_format}: {typical_sections}

Create a JSON outline with specific sections and word targets:
{{
  "title": "Compelling title for the piece",
  "sections": [
    {{
      "section_number": 1,
      "section_name": "Introduction",
      "purpose": "Hook the reader and introduce the topic",
      "key_points": ["Point 1", "Point 2"],
      "target_word_count": 300,
      "tone_notes": "Engaging and welcoming"
    }},
    {{
      "section_number": 2,
      "section_name": "Main Content",
      "purpose": "Deliver core value",
      "key_points": ["Key insight", "Supporting evidence"],
      "target_word_count": 800,
      "tone_notes": "Informative and authoritative"
    }}
  ],
  "total_sections": 4,
  "estimated_total_words": {job.target_word_count}
}}

Make sure word counts add up to approximately {job.target_word_count} words."""

        try:
            response = GenerationService._make_ai_call(
                prompt=prompt,
                model=model,
                job_id=str(job.id),
                stage="outline_creation"
            )

            outline = json.loads(response['content'])

            # Store outline and update job
            job.outline = outline
            job.sections_total = len(outline['sections'])
            job.status = GenerationService.STAGE_CONSISTENCY_DOCS
            job.total_cost += response.get('cost', 0)
            job.total_tokens_used += response.get('tokens', 0)

            print(f"[GENERATION] Outline created for job {job.id}: {job.sections_total} sections")
            return {
                'stage': 'outline_creation',
                'status': 'completed',
                'outline': outline,
                'next_stage': GenerationService.STAGE_CONSISTENCY_DOCS
            }

        except json.JSONDecodeError as e:
            job.error_message = f"Failed to parse outline: {e}"
            raise Exception(f"AI response was not valid JSON: {e}")

    @staticmethod
    def _stage_consistency_docs(job: GenerationJob, model: str) -> Dict[str, Any]:
        """Stage 3: Create style guide, fact sheet, and character bible."""

        prompt = f"""Create consistency documents for this content generation project:

BRIEF: "{job.brief}"
OUTLINE: {json.dumps(job.outline, indent=2) if job.outline else 'None'}
Content Format: {job.content_format}
Target Audience: {job.target_audience}

Generate comprehensive consistency documents in JSON format:
{{
  "style_guide": {{
    "tone": "Professional/Casual/Technical/etc",
    "voice": "First person/Third person/etc",
    "writing_style": ["Active voice", "Short sentences", "etc"],
    "formatting_rules": ["Use bullet points", "Bold key terms", "etc"],
    "words_to_use": ["industry term 1", "preferred phrase 2"],
    "words_to_avoid": ["jargon 1", "overused term 2"]
  }},
  "fact_sheet": {{
    "established_facts": [
      "Key fact that cannot be contradicted",
      "Important statistic or date",
      "Core principle or methodology"
    ],
    "key_definitions": {{
      "term1": "definition",
      "term2": "definition"
    }},
    "references": ["Source 1", "Source 2"]
  }},
  "character_bible": {{
    "main_subject": {{
      "name": "If writing about a person/company",
      "background": "Key background info",
      "personality": "Character traits",
      "expertise": "Areas of knowledge"
    }},
    "supporting_characters": []
  }}
}}

These documents will ensure consistency across all sections."""

        try:
            response = GenerationService._make_ai_call(
                prompt=prompt,
                model=model,
                job_id=str(job.id),
                stage="consistency_docs"
            )

            consistency_docs = json.loads(response['content'])

            # Store consistency docs and update job
            job.style_guide = consistency_docs.get('style_guide', {})
            job.fact_sheet = consistency_docs.get('fact_sheet', {})
            job.character_bible = consistency_docs.get('character_bible', {})
            job.status = GenerationService.STAGE_SECTIONAL_GENERATION
            job.total_cost += response.get('cost', 0)
            job.total_tokens_used += response.get('tokens', 0)

            print(f"[GENERATION] Consistency docs created for job {job.id}")
            return {
                'stage': 'consistency_docs',
                'status': 'completed',
                'consistency_docs': consistency_docs,
                'next_stage': GenerationService.STAGE_SECTIONAL_GENERATION
            }

        except json.JSONDecodeError as e:
            job.error_message = f"Failed to parse consistency docs: {e}"
            raise Exception(f"AI response was not valid JSON: {e}")

    @staticmethod
    def _stage_sectional_generation(job: GenerationJob, model: str) -> Dict[str, Any]:
        """Stage 4: Generate content section by section."""

        if not job.outline:
            raise Exception("Cannot generate sections without outline")

        sections = job.outline.get('sections', [])
        current_section_num = job.current_section + 1

        if current_section_num > len(sections):
            # All sections completed, move to assembly
            job.status = GenerationService.STAGE_ASSEMBLY
            job.sections_completed = len(sections)
            return {
                'stage': 'sectional_generation',
                'status': 'all_sections_completed',
                'next_stage': GenerationService.STAGE_ASSEMBLY
            }

        current_section = sections[current_section_num - 1]

        # Build context from previous sections
        previous_content = ""
        if job.sections_content and len(job.sections_content) > 0:
            previous_sections = []
            for i in range(1, current_section_num):
                if str(i) in job.sections_content:
                    prev_section = job.sections_content[str(i)]
                    previous_sections.append(f"Section {i}: {prev_section[:200]}...")
            previous_content = "\\n\\n".join(previous_sections)

        prompt = f"""Generate section {current_section_num} of this long-form content:

FULL OUTLINE:
{json.dumps(job.outline, indent=2)}

STYLE GUIDE:
{json.dumps(job.style_guide, indent=2) if job.style_guide else 'None'}

FACT SHEET (maintain consistency with these facts):
{json.dumps(job.fact_sheet, indent=2) if job.fact_sheet else 'None'}

CHARACTER BIBLE:
{json.dumps(job.character_bible, indent=2) if job.character_bible else 'None'}

PREVIOUS SECTIONS SUMMARY:
{previous_content if previous_content else 'This is the first section'}

CURRENT SECTION TO GENERATE:
Section {current_section_num}: {current_section['section_name']}
Purpose: {current_section['purpose']}
Key Points: {current_section.get('key_points', [])}
Target Word Count: {current_section.get('target_word_count', 500)}
Tone Notes: {current_section.get('tone_notes', 'Match overall style')}

Generate ONLY the content for this section. Do not include section headers or numbers. Write approximately {current_section.get('target_word_count', 500)} words. Ensure smooth flow from previous sections."""

        try:
            response = GenerationService._make_ai_call(
                prompt=prompt,
                model=model,
                job_id=str(job.id),
                stage=f"section_{current_section_num}"
            )

            section_content = response['content'].strip()

            # Store section content
            if not job.sections_content:
                job.sections_content = {}
            job.sections_content[str(current_section_num)] = section_content

            # Update progress
            job.current_section = current_section_num
            job.sections_completed = current_section_num
            job.total_cost += response.get('cost', 0)
            job.total_tokens_used += response.get('tokens', 0)

            print(f"[GENERATION] Section {current_section_num}/{len(sections)} completed for job {job.id}")

            # Check if this was the last section
            if current_section_num >= len(sections):
                job.status = GenerationService.STAGE_ASSEMBLY
                return {
                    'stage': 'sectional_generation',
                    'section_number': current_section_num,
                    'status': 'all_sections_completed',
                    'next_stage': GenerationService.STAGE_ASSEMBLY
                }
            else:
                return {
                    'stage': 'sectional_generation',
                    'section_number': current_section_num,
                    'status': 'section_completed',
                    'sections_remaining': len(sections) - current_section_num,
                    'next_stage': GenerationService.STAGE_SECTIONAL_GENERATION
                }

        except Exception as e:
            job.error_message = f"Failed to generate section {current_section_num}: {e}"
            raise

    @staticmethod
    def _stage_assembly(job: GenerationJob, model: str) -> Dict[str, Any]:
        """Stage 5: Assemble sections into final document."""

        if not job.sections_content or not job.outline:
            raise Exception("Cannot assemble without sections and outline")

        sections = job.outline.get('sections', [])
        title = job.outline.get('title', job.job_name)

        # Assemble content
        assembled_parts = [f"# {title}\\n"]

        for i, section in enumerate(sections, 1):
            section_name = section['section_name']
            section_content = job.sections_content.get(str(i), f"[Section {i} content missing]")

            assembled_parts.append(f"## {section_name}\\n")
            assembled_parts.append(section_content + "\\n")

        assembled_content = "\\n".join(assembled_parts)

        # Count words
        word_count = len(assembled_content.split())

        # Store final content
        job.assembled_content = assembled_content
        job.word_count_actual = word_count
        job.status = GenerationService.STAGE_QUALITY_CHECK

        print(f"[GENERATION] Content assembled for job {job.id}: {word_count} words")

        return {
            'stage': 'assembly',
            'status': 'completed',
            'word_count': word_count,
            'target_word_count': job.target_word_count,
            'next_stage': GenerationService.STAGE_QUALITY_CHECK
        }

    @staticmethod
    def _stage_quality_check(job: GenerationJob, model: str) -> Dict[str, Any]:
        """Stage 6: Check for continuity and fact consistency."""

        if not job.assembled_content:
            raise Exception("Cannot quality check without assembled content")

        prompt = f"""Review this completed content for quality issues:

ORIGINAL BRIEF: "{job.brief}"

FACT SHEET (check consistency):
{json.dumps(job.fact_sheet, indent=2) if job.fact_sheet else 'None'}

ASSEMBLED CONTENT:
{job.assembled_content[:5000]}{'...' if len(job.assembled_content) > 5000 else ''}

Analyze the content and provide feedback in JSON format:
{{
  "continuity_issues": [
    "Issue 1: Description of continuity problem",
    "Issue 2: Another issue"
  ],
  "fact_conflicts": [
    "Conflict 1: Content contradicts established fact",
    "Conflict 2: Another contradiction"
  ],
  "overall_quality": "Excellent/Good/Fair/Poor",
  "recommendations": [
    "Suggestion 1",
    "Suggestion 2"
  ],
  "meets_brief": true
}}

Focus on logical flow, factual consistency, and meeting the original brief requirements."""

        try:
            response = GenerationService._make_ai_call(
                prompt=prompt,
                model=model,
                job_id=str(job.id),
                stage="quality_check"
            )

            quality_check = json.loads(response['content'])

            # Store quality check results
            job.continuity_issues = quality_check.get('continuity_issues', [])
            job.fact_conflicts = quality_check.get('fact_conflicts', [])
            job.status = GenerationService.STAGE_COMPLETED
            job.completed_at = datetime.utcnow()
            job.total_cost += response.get('cost', 0)
            job.total_tokens_used += response.get('tokens', 0)

            print(f"[GENERATION] Quality check completed for job {job.id} - Status: {quality_check.get('overall_quality', 'Unknown')}")

            return {
                'stage': 'quality_check',
                'status': 'completed',
                'quality_results': quality_check,
                'next_stage': GenerationService.STAGE_COMPLETED,
                'job_completed': True
            }

        except json.JSONDecodeError as e:
            # If JSON parsing fails, still mark as completed but note the issue
            job.status = GenerationService.STAGE_COMPLETED
            job.completed_at = datetime.utcnow()
            job.error_message = f"Quality check completed but parsing failed: {e}"
            return {
                'stage': 'quality_check',
                'status': 'completed_with_warning',
                'warning': f"Quality analysis parsing failed: {e}",
                'job_completed': True
            }

    @staticmethod
    def _make_ai_call(prompt: str, model: str, job_id: str, stage: str) -> Dict[str, Any]:
        """Make an AI call with proper cost tracking."""

        start_time = time.time()

        # Use the AI service to make the call
        # For now, we'll use a simplified call - in a real implementation, this would
        # integrate with the actual AIService.generate_script_with_ai method

        # Simulate AI response for now (replace with actual AI call)
        # In real implementation, you would call AIService methods here

        # This is a placeholder - replace with actual AI integration
        if "JSON" in prompt:
            if "brief analysis" in prompt.lower():
                mock_response = '''{"refined_topic": "Sample topic", "key_points": ["Point 1", "Point 2"], "tone": "Professional", "style_requirements": ["Clear", "Engaging"], "special_considerations": ["Audience appropriate"], "estimated_sections": 3, "suggested_word_distribution": {"section1": 400, "section2": 600, "section3": 400}}'''
            elif "outline" in prompt.lower():
                mock_response = '''{"title": "Sample Article Title", "sections": [{"section_number": 1, "section_name": "Introduction", "purpose": "Hook and introduce", "key_points": ["Hook", "Preview"], "target_word_count": 300, "tone_notes": "Engaging"}, {"section_number": 2, "section_name": "Main Content", "purpose": "Deliver value", "key_points": ["Core insight"], "target_word_count": 800, "tone_notes": "Informative"}], "total_sections": 2, "estimated_total_words": 1100}'''
            elif "consistency" in prompt.lower():
                mock_response = '''{"style_guide": {"tone": "Professional", "voice": "Third person", "writing_style": ["Clear", "Concise"], "formatting_rules": ["Short paragraphs"], "words_to_use": ["precise"], "words_to_avoid": ["jargon"]}, "fact_sheet": {"established_facts": ["Sample fact"], "key_definitions": {"term": "definition"}, "references": ["Source 1"]}, "character_bible": {"main_subject": {"name": "Subject", "background": "Background", "personality": "Professional", "expertise": "Field"}}}'''
            elif "quality" in prompt.lower():
                mock_response = '''{"continuity_issues": [], "fact_conflicts": [], "overall_quality": "Good", "recommendations": ["Well structured"], "meets_brief": true}'''
            else:
                mock_response = '''{"status": "completed", "message": "Generated successfully"}'''
        else:
            mock_response = "This is sample generated content for the requested section. In a real implementation, this would be generated by the AI model based on the specific prompt and context provided."

        # Calculate mock costs (replace with real token counting)
        estimated_tokens = len(prompt.split()) * 1.3  # Rough estimate
        input_cost, output_cost, total_cost = UsageLimitsService.calculate_cost(
            model, int(estimated_tokens), int(len(mock_response.split()) * 1.3)
        )

        latency_ms = (time.time() - start_time) * 1000

        print(f"[GENERATION AI] {stage} for job {job_id}: ${total_cost:.4f} | {latency_ms:.0f}ms")

        return {
            'content': mock_response,
            'cost': total_cost,
            'tokens': int(estimated_tokens + len(mock_response.split()) * 1.3),
            'latency_ms': latency_ms
        }

    @staticmethod
    def get_completed_content(job_id: str) -> Optional[Dict[str, Any]]:
        """Get the final assembled content for a completed job."""

        with DatabaseSession() as db_session:
            job = db_session.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if not job:
                return None

            return {
                'job_id': str(job.id),
                'job_name': job.job_name,
                'status': job.status,
                'assembled_content': job.assembled_content,
                'word_count': job.word_count_actual,
                'target_word_count': job.target_word_count,
                'total_cost': job.total_cost,
                'continuity_issues': job.continuity_issues,
                'fact_conflicts': job.fact_conflicts,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None
            }

    @staticmethod
    def list_user_jobs(user_id: str) -> List[Dict[str, Any]]:
        """List all generation jobs for a user."""

        with DatabaseSession() as db_session:
            jobs = db_session.query(GenerationJob).filter(
                GenerationJob.created_by == user_id
            ).order_by(GenerationJob.created_at.desc()).all()

            return [
                {
                    'job_id': str(job.id),
                    'job_name': job.job_name,
                    'job_type': job.job_type,
                    'status': job.status,
                    'progress_percentage': (GenerationService.PIPELINE_STAGES.index(job.status) / len(GenerationService.PIPELINE_STAGES)) * 100 if job.status in GenerationService.PIPELINE_STAGES else 0,
                    'word_count': job.word_count_actual,
                    'target_word_count': job.target_word_count,
                    'total_cost': job.total_cost,
                    'created_at': job.created_at.isoformat(),
                    'completed_at': job.completed_at.isoformat() if job.completed_at else None
                }
                for job in jobs
            ]