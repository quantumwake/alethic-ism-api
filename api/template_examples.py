"""
Template examples for chat completion assistance.
Loads examples from txt files for better maintainability.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

# Available models for chat completion
AVAILABLE_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-3.5-turbo"
]

# Base directory for templates
TEMPLATES_DIR = Path(__file__).parent / "templates"


class TemplateExamples:
    """Repository of template examples loaded from files"""

    _cache: Dict[str, any] = {}

    @staticmethod
    def _load_file(path: Path) -> Optional[str]:
        """Load content from a file"""
        try:
            if path.exists():
                return path.read_text(encoding='utf-8').strip()
        except Exception:
            pass
        return None

    @staticmethod
    def _load_examples_from_dir(template_type: str) -> List[Dict]:
        """Load all examples from a template type directory"""
        cache_key = f"examples_{template_type}"
        if cache_key in TemplateExamples._cache:
            return TemplateExamples._cache[cache_key]

        examples = []
        examples_dir = TEMPLATES_DIR / "examples" / template_type

        if not examples_dir.exists():
            return examples

        # Mapping of filename to description/use_case
        example_metadata = {
            "mako": {
                "qa_template": ("Simple question-answer template with JSON output", "Question answering with structured JSON output"),
                "summarization": ("Summarization template", "Content summarization with structured output"),
                "classification": ("Classification template with categories", "Text classification with confidence scoring"),
                "data_extraction": ("Data extraction template", "Structured data extraction from text"),
                "conditional": ("Data transformation template with conditional logic", "Conditional data formatting with loops and JSON output"),
                "conversation": ("Multi-turn conversation template", "Conversational assistant with context"),
            },
            "python": {
                "batch_passthrough": ("Basic batch passthrough", "Simple batch forwarding - passes all queries through unchanged"),
                "query_enrichment": ("Query enrichment with external data", "Stream processing with external API enrichment"),
                "data_transformation": ("Data transformation with filtering", "Batch transformation with filtering and logging"),
                "stateful_aggregation": ("Stateful aggregation", "Running aggregation across multiple batches"),
            }
        }

        metadata = example_metadata.get(template_type, {})

        for file_path in sorted(examples_dir.glob("*.txt")):
            content = TemplateExamples._load_file(file_path)
            if content:
                name = file_path.stem
                meta = metadata.get(name, (name, name))
                examples.append({
                    "description": meta[0],
                    "template": content,
                    "use_case": meta[1]
                })

        TemplateExamples._cache[cache_key] = examples
        return examples

    @staticmethod
    def get_examples_for_type(template_type: str) -> List[Dict]:
        """Get examples for a specific template type"""
        template_type = template_type.lower()
        if template_type in ("mako", "python"):
            return TemplateExamples._load_examples_from_dir(template_type)
        return []

    @staticmethod
    def get_system_prompt_for_type(template_type: str) -> str:
        """Get the system prompt for a specific template type"""
        template_type = template_type.lower()

        cache_key = f"prompt_{template_type}"
        if cache_key in TemplateExamples._cache:
            return TemplateExamples._cache[cache_key]

        prompt_file = TEMPLATES_DIR / "prompts" / f"{template_type}_system.txt"
        prompt = TemplateExamples._load_file(prompt_file)

        if prompt:
            TemplateExamples._cache[cache_key] = prompt
            return prompt

        return "You are a helpful assistant for creating templates."

    @staticmethod
    def get_autocompletion_hints_for_type(template_type: str) -> Dict:
        """Get autocompletion hints for Monaco editor"""
        template_type = template_type.lower()

        if template_type == "mako":
            return {
                "snippets": [
                    {
                        "label": "qa_template",
                        "insertText": """Answer the following question in brevity: "${1:question}"

Output your response in the following JSON format:

```json
{
  "answer": "[answer in brevity]",
  "justification": "[justification for your answer]"
}
```""",
                        "documentation": "Complete Q&A template with JSON output"
                    },
                    {
                        "label": "classification_template",
                        "insertText": """Classify the following text into one of the categories: ${1:categories}

Text: "${2:text}"

```json
{
  "category": "[selected category]",
  "confidence": "[high/medium/low]",
  "reasoning": "[brief explanation]"
}
```""",
                        "documentation": "Classification template with confidence scoring"
                    },
                    {
                        "label": "extraction_template",
                        "insertText": """Extract the following information from the text:
- Names
- Dates
- Key facts

Text: "${1:text}"

```json
{
  "names": [],
  "dates": [],
  "key_facts": []
}
```""",
                        "documentation": "Data extraction template"
                    },
                    {
                        "label": "variable",
                        "insertText": "${${1:variable_name}}",
                        "documentation": "Insert a variable"
                    },
                    {
                        "label": "if",
                        "insertText": "% if ${1:condition}:\n${2}\n% endif",
                        "documentation": "Conditional block"
                    },
                    {
                        "label": "for",
                        "insertText": "% for ${1:item} in ${2:items}:\n${3}\n% endfor",
                        "documentation": "Loop block"
                    },
                    {
                        "label": "if_else",
                        "insertText": "% if ${1:condition}:\n${2}\n% else:\n${3}\n% endif",
                        "documentation": "Conditional with else"
                    },
                    {
                        "label": "comment",
                        "insertText": "## ${1:comment}",
                        "documentation": "Single-line comment"
                    }
                ],
                "keywords": ["if", "elif", "else", "endif", "for", "endfor", "while", "endwhile"]
            }

        elif template_type == "python":
            return {
                "snippets": [
                    {
                        "label": "class",
                        "insertText": """## Template to customize a python state
class Runnable(BaseSecureRunnable):
    ## any initialization parameters you want to save (on a per event basis)
    def init(self):
        self.context['${1:key}'] = ${2:value}

    ## if the state is using a python state type (batch processing)
    def process(self, queries: List[Any]) -> List[Any]:
        ${3:return queries}

    ## if the state is using a stream state type (one at a time)
    def process_stream(self, query: Dict) -> Any:
        yield json.dumps(query, indent=2)
""",
                        "documentation": "Complete Runnable class template"
                    },
                    {
                        "label": "http_get",
                        "insertText": "response = self.requests.get('${1:url}')\nif response.status_code == 200:\n    data = response.json()\n    ${2}",
                        "documentation": "HTTP GET request with error handling"
                    },
                    {
                        "label": "http_post",
                        "insertText": "response = self.requests.post('${1:url}', json=${2:payload})\nif response.status_code == 200:\n    data = response.json()\n    ${3}",
                        "documentation": "HTTP POST request with error handling"
                    },
                    {
                        "label": "log_info",
                        "insertText": "self.logger.info('${1:message}')",
                        "documentation": "Log an info message"
                    },
                    {
                        "label": "context_set",
                        "insertText": "self.context['${1:key}'] = ${2:value}",
                        "documentation": "Set a context variable"
                    },
                    {
                        "label": "context_get",
                        "insertText": "self.context.get('${1:key}', ${2:default})",
                        "documentation": "Get a context variable with default"
                    }
                ],
                "keywords": [
                    "self", "context", "logger", "requests",
                    "BaseSecureRunnable", "List", "Dict", "Any",
                    "json", "math", "random", "hashlib", "re", "datetime", "time"
                ],
                "available_methods": [
                    "self.context",
                    "self.logger.info()",
                    "self.logger.error()",
                    "self.requests.get()",
                    "self.requests.post()",
                    "self.requests.put()",
                    "self.requests.delete()"
                ]
            }

        else:
            return {"snippets": [], "keywords": []}

    @staticmethod
    def clear_cache():
        """Clear the template cache"""
        TemplateExamples._cache.clear()