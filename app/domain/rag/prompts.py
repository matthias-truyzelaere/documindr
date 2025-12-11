"""Prompt templates for RAG and summarization tasks."""

from langchain_core.prompts import ChatPromptTemplate

from app.api.schemas.chat import SummaryLength


class PromptRegistry:
    """Central registry for all prompt templates used in the application."""

    # -------------------------------------------------------------------------
    # RAG Chat Prompts
    # -------------------------------------------------------------------------

    RAG_CHAT = """
Always answer in the same language as the question. 
Answering in any other language is considered incorrect.

You are a precise Retrieval-Augmented Generation assistant.
Your only knowledge is the text shown below.

You must obey these rules:
1. Always answer in the same language as the question.
2. Use clear, uniform plain-text style.
3. Do not use markdown formatting.
4. Do not use bold, italics, or surrounding symbols.
5. Do not insert spaces inside symbols. For example, write 50% and not 50 %.
6. Do not invent any information that is not clearly supported by the provided text.
7. If the answer is not contained in the provided text, say: "I cannot find this information in the provided text."
8. Write answers as complete sentences.
9. Prefer a short, well-structured paragraph. If it improves clarity, you may also use a short plain-text list.

Provided text:
{context}

Question (language must be preserved in the answer):
{query}

Answer in the same language as the question (start immediately, as full sentences, no blank lines):
"""

    # -------------------------------------------------------------------------
    # Summary Prompts
    # -------------------------------------------------------------------------

    SUMMARY_BASE = """
You are a precise document summarization assistant.
Your task is to create a {length_description} summary of the provided document.

Requirements:
{requirements}

Document content:
{context}

Provide a {length_name} summary ({sentence_count} sentences, start immediately):
"""

    SUMMARY_CONCISE = """
You are a precise document summarization assistant.
Your task is to create a CONCISE summary of the provided document.

Requirements:
1. Keep the summary brief - 3-5 sentences maximum
2. Focus only on the most important key points
3. Use clear, plain-text style (no markdown, no formatting)
4. Write in complete sentences
5. Do not invent information not present in the document
6. Capture the main topic and critical takeaways

Document content:
{context}

Provide a concise summary (3-5 sentences, start immediately):
"""

    SUMMARY_NORMAL = """
You are a precise document summarization assistant.
Your task is to create a NORMAL-LENGTH summary of the provided document.

Requirements:
1. Keep the summary moderate - 8-12 sentences
2. Cover the main points and important details
3. Use clear, plain-text style (no markdown, no formatting)
4. Write in complete sentences
5. Do not invent information not present in the document
6. Provide a balanced overview of the document's content

Document content:
{context}

Provide a normal-length summary (8-12 sentences, start immediately):
"""

    SUMMARY_COMPREHENSIVE = """
You are a precise document summarization assistant.
Your task is to create a COMPREHENSIVE summary of the provided document.

Requirements:
1. Create a detailed summary - 15-25 sentences
2. Cover all major points, important details, and supporting information
3. Use clear, plain-text style (no markdown, no formatting)
4. Write in complete sentences and well-structured paragraphs
5. Do not invent information not present in the document
6. Provide thorough coverage of the document's content and structure

Document content:
{context}

Provide a comprehensive summary (15-25 sentences, start immediately):
"""

    # -------------------------------------------------------------------------
    # Prompt Template Cache
    # -------------------------------------------------------------------------

    _templates = {}

    @classmethod
    def get_rag_chat_template(cls) -> ChatPromptTemplate:
        """Get cached RAG chat prompt template."""
        if "rag_chat" not in cls._templates:
            cls._templates["rag_chat"] = ChatPromptTemplate.from_template(cls.RAG_CHAT)
        return cls._templates["rag_chat"]

    @classmethod
    def get_summary_template(cls, length: SummaryLength) -> ChatPromptTemplate:
        """Get cached summary prompt template for specified length."""
        cache_key = f"summary_{length.value}"
        if cache_key not in cls._templates:
            prompt_text = cls._get_summary_prompt_text(length)
            cls._templates[cache_key] = ChatPromptTemplate.from_template(prompt_text)
        return cls._templates[cache_key]

    @classmethod
    def _get_summary_prompt_text(cls, length: SummaryLength) -> str:
        """Get raw summary prompt text for specified length."""
        mapping = {
            SummaryLength.CONCISE: cls.SUMMARY_CONCISE,
            SummaryLength.NORMAL: cls.SUMMARY_NORMAL,
            SummaryLength.COMPREHENSIVE: cls.SUMMARY_COMPREHENSIVE,
        }
        return mapping[length]

    @classmethod
    def clear_cache(cls):
        """Clear the template cache (useful for testing)."""
        cls._templates.clear()


# Convenience functions for backward compatibility
def get_rag_chat_template() -> ChatPromptTemplate:
    """Get RAG chat prompt template."""
    return PromptRegistry.get_rag_chat_template()


def get_summary_template(length: SummaryLength) -> ChatPromptTemplate:
    """Get summary prompt template for specified length."""
    return PromptRegistry.get_summary_template(length)
