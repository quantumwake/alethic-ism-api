import os
from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ismcore.model.base_model import InstructionTemplate
from openai import OpenAI

from environment import storage
from api.template_examples import TemplateExamples, AVAILABLE_MODELS

template_router = APIRouter()

# Initialize OpenAI client (API key from environment)
openai_client = None
try:
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        openai_client = OpenAI(api_key=api_key)
except Exception as e:
    print(f"Warning: OpenAI client not initialized: {e}")


class StateColumnInfo(BaseModel):
    """Information about state columns for autocompletion"""
    state_id: str
    state_name: Optional[str] = None
    columns: Dict[str, str]  # column_name -> column_type/description


class StateSampleData(BaseModel):
    """Sample data from a state for AI context"""
    state_id: str
    state_name: Optional[str] = None
    columns: List[str]
    sample_rows: List[Dict]  # Up to 10 sample rows
    total_rows: int


class ChatCompletionRequest(BaseModel):
    """Request model for chat completion"""
    template_type: str
    user_message: str
    model: str = "gpt-4o-mini"
    current_template: Optional[str] = None
    state_columns: Optional[List[StateColumnInfo]] = None  # Available state columns for context
    state_samples: Optional[List[StateSampleData]] = None  # Sample data for context


class ChatCompletionResponse(BaseModel):
    """Response model for chat completion"""
    content: str
    model: str
    examples: List[Dict]


class AutocompletionRequest(BaseModel):
    """Request model for autocompletion"""
    state_columns: Optional[List[StateColumnInfo]] = None


class StateColumnsResponse(BaseModel):
    """Response model for state columns"""
    state_id: str
    state_name: Optional[str] = None
    state_type: Optional[str] = None
    columns: Dict[str, str]  # column_name -> data_type


class CompletionItem(BaseModel):
    """A single autocompletion item compatible with Monaco and other editors"""
    label: str  # Display text in autocomplete dropdown
    insertText: str  # Text to insert when selected
    documentation: Optional[str] = None  # Help text / description
    kind: str  # Type: variable, function, snippet, keyword, method, property
    detail: Optional[str] = None  # Additional detail (e.g., return type, source state)
    sortText: Optional[str] = None  # Custom sort order


class AutocompletionResponse(BaseModel):
    """Complete autocompletion response for editors and AI tools"""
    template_type: str
    completions: List[CompletionItem]
    # Grouped for convenience
    variables: List[CompletionItem]
    functions: List[CompletionItem]
    snippets: List[CompletionItem]
    keywords: List[str]
    # Raw state info for AI context
    states: Optional[List[Dict]] = None


@template_router.get('/models')
async def get_available_models() -> List[str]:
    """
    Get list of available OpenAI models for chat completion.
    """
    return AVAILABLE_MODELS


@template_router.get('/examples/{template_type}')
async def get_template_examples(template_type: str) -> List[Dict]:
    """
    Get example templates for a specific template type.
    """
    examples = TemplateExamples.get_examples_for_type(template_type)

    if not examples:
        raise HTTPException(
            status_code=404,
            detail=f"No examples available for template type: {template_type}"
        )

    return examples


@template_router.get("/{template_id}")
async def fetch_instruction_template(template_id: str) -> Optional[InstructionTemplate]:
    return storage.fetch_template(template_id=template_id)


@template_router.post('/create')
async def merge_instruction_template(template: InstructionTemplate) -> InstructionTemplate:
    storage.insert_template(template=template)
    return template


@template_router.post('/create/text')
async def merge_instruction_template_text(template_id: str,
                                          template_path: str,
                                          template_content: str,
                                          template_type: str,
                                          project_id: str = None):
    # create an instruction template object
    instruction = InstructionTemplate(
        template_id=template_id,
        template_path=template_path,
        template_content=template_content,
        template_type=template_type,
        project_id=project_id
    )

    return merge_instruction_template(instruction)


@template_router.put('/{template_id}/rename/{new_name}')
async def rename_template(template_id: str, new_name: str) -> Optional[InstructionTemplate]:
    template = storage.fetch_template(template_id=template_id)
    template.template_path = new_name
    storage.insert_template(template=template)
    return template


@template_router.post('/chat/completion')
async def chat_completion(request: ChatCompletionRequest) -> ChatCompletionResponse:
    """
    Chat completion endpoint for template assistance.
    Provides AI-powered help for creating templates using few-shot examples.
    """
    if not openai_client:
        raise HTTPException(
            status_code=503,
            detail="OpenAI client not initialized. Please set OPENAI_API_KEY environment variable."
        )

    if request.model not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model. Available models: {', '.join(AVAILABLE_MODELS)}"
        )

    # Get system prompt and examples for the template type
    system_prompt = TemplateExamples.get_system_prompt_for_type(request.template_type)
    examples = TemplateExamples.get_examples_for_type(request.template_type)

    # Build messages with few-shot examples
    messages = [
        {"role": "system", "content": system_prompt}
    ]

    # Add few-shot examples
    for example in examples:
        messages.append({
            "role": "user",
            "content": f"Create a template for: {example['use_case']}"
        })
        messages.append({
            "role": "assistant",
            "content": f"Here's a {request.template_type} template for {example['use_case']}:\n\n```\n{example['template']}\n```"
        })

    # Build the user message with all available context
    user_content_parts = []

    # Add state column information if provided (column names/types only, not data)
    if request.state_columns:
        state_info = "Available state columns for use in your template:\n\n"
        for state in request.state_columns:
            state_name = state.state_name or state.state_id
            state_info += f"**{state_name}** (state_id: {state.state_id}):\n"
            for col_name, col_type in state.columns.items():
                state_info += f"  - `{col_name}`: {col_type}\n"
            state_info += "\n"
        user_content_parts.append(state_info)

    # Note: state_samples intentionally not sent to LLM to avoid token bloat

    # Add current template if provided
    if request.current_template:
        user_content_parts.append(f"I'm currently working on this template:\n\n```\n{request.current_template}\n```\n")

    # Add the user's message
    user_content_parts.append(request.user_message)

    # Combine all parts
    messages.append({
        "role": "user",
        "content": "\n".join(user_content_parts)
    })

    try:
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model=request.model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )

        content = response.choices[0].message.content

        return ChatCompletionResponse(
            content=content,
            model=request.model,
            examples=examples
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OpenAI API error: {str(e)}"
        )


@template_router.post('/autocompletion/{template_type}')
async def get_autocompletion_hints(
    template_type: str,
    request: AutocompletionRequest
) -> Dict:
    """
    Get autocompletion hints for Monaco editor based on template type.
    Returns snippets, keywords, and available methods/APIs.
    Optionally includes state column completions if state_columns are provided.
    """
    hints = TemplateExamples.get_autocompletion_hints_for_type(template_type)

    if not hints.get("snippets") and not hints.get("keywords"):
        raise HTTPException(
            status_code=404,
            detail=f"No autocompletion hints available for template type: {template_type}"
        )

    # Add state column completions if provided
    if request.state_columns:
        state_column_snippets = []
        state_column_keywords = []

        for state in request.state_columns:
            state_name = state.state_name or state.state_id

            # Add snippets for each column
            for col_name, col_type in state.columns.items():
                if template_type.lower() == "mako":
                    # For Mako templates, add variable snippets
                    state_column_snippets.append({
                        "label": f"{col_name} (from {state_name})",
                        "insertText": f"${{{col_name}}}",
                        "documentation": f"Column from state '{state_name}': {col_type}"
                    })
                elif template_type.lower() == "python":
                    # For Python templates, add dictionary access snippets
                    state_column_snippets.append({
                        "label": f"{col_name} (from {state_name})",
                        "insertText": f"query.get('{col_name}')",
                        "documentation": f"Column from state '{state_name}': {col_type}"
                    })

                # Add column names as keywords
                state_column_keywords.append(col_name)

        # Merge with existing hints
        hints["snippets"] = hints.get("snippets", []) + state_column_snippets
        hints["keywords"] = hints.get("keywords", []) + state_column_keywords
        hints["state_columns"] = [
            {
                "state_id": state.state_id,
                "state_name": state.state_name or state.state_id,
                "columns": state.columns
            }
            for state in request.state_columns
        ]

    return hints


@template_router.get('/editor/completions/{template_type}/{project_id}')
async def get_editor_completions(
    template_type: str,
    project_id: str
) -> AutocompletionResponse:
    """
    Get complete autocompletion data for editors (Monaco, etc.) and AI tools.
    Fetches states from the database and builds completion items with:
    - Variables from state columns (state_name.column_name format)
    - Available functions from BaseSecureRunnable
    - Code snippets for the template type
    - Language keywords
    """
    template_type_lower = template_type.lower()

    variables: List[CompletionItem] = []
    functions: List[CompletionItem] = []
    snippets: List[CompletionItem] = []
    states_info: List[Dict] = []

    # Fetch states and their columns from the database
    try:
        states = storage.fetch_states(project_id=project_id)
        if states:
            for s in states:
                # Load state with config and columns
                state = storage.load_state_metadata(state_id=s.id)
                if not state or not state.columns:
                    continue

                # Get state name from config, fallback to truncated ID
                state_name = state.config.name if state.config and state.config.name else state.id[:8]
                columns = state.columns

                # Store state info for AI context (include column data types)
                state_info = {
                    "state_id": state.id,
                    "state_name": state_name,
                    "state_type": state.state_type,
                    "columns": {
                        col_name: col_def.data_type
                        for col_name, col_def in columns.items()
                    }
                }
                states_info.append(state_info)

                # Create completion items for each column
                for col_name, col_def in columns.items():
                    is_json_column = col_def.data_type == 'json'

                    if template_type_lower == "mako":
                        # Mako variable format
                        variables.append(CompletionItem(
                            label=f"{state_name}.{col_name}",
                            insertText=f"${{{col_name}}}",
                            documentation=f"Column '{col_name}' from state '{state_name}' (type: {col_def.data_type})",
                            kind="variable",
                            detail=f"State: {state_name} ({col_def.data_type})",
                            sortText=f"0_{state_name}_{col_name}"
                        ))
                        # Also add without state prefix for direct access
                        variables.append(CompletionItem(
                            label=col_name,
                            insertText=f"${{{col_name}}}",
                            documentation=f"Column '{col_name}' (from {state_name}, type: {col_def.data_type})",
                            kind="variable",
                            detail=f"{state_name} ({col_def.data_type})",
                            sortText=f"1_{col_name}"
                        ))

                        # Add JSON-specific completions for complex types
                        if is_json_column:
                            # Iteration snippet for arrays
                            snippets.append(CompletionItem(
                                label=f"for item in {col_name}",
                                insertText=f"% for item in {col_name}:\n${{item}}\n% endfor",
                                documentation=f"Iterate over '{col_name}' array from state '{state_name}'",
                                kind="snippet",
                                detail=f"Iterate {col_name} (json)",
                                sortText=f"0_{state_name}_{col_name}_iter"
                            ))
                            # Iteration with index
                            snippets.append(CompletionItem(
                                label=f"for i, item in {col_name}",
                                insertText=f"% for i, item in enumerate({col_name}):\n${{i}}: ${{item}}\n% endfor",
                                documentation=f"Iterate over '{col_name}' with index from state '{state_name}'",
                                kind="snippet",
                                detail=f"Iterate {col_name} with index",
                                sortText=f"0_{state_name}_{col_name}_iter_idx"
                            ))
                            # Dictionary key access
                            variables.append(CompletionItem(
                                label=f"{col_name}['key']",
                                insertText=f"${{{col_name}['${{1:key}}']}}",
                                documentation=f"Access key in '{col_name}' dict from state '{state_name}'",
                                kind="variable",
                                detail=f"Dict access ({col_name})",
                                sortText=f"0_{state_name}_{col_name}_key"
                            ))
                            # Dictionary .get() access
                            variables.append(CompletionItem(
                                label=f"{col_name}.get()",
                                insertText=f"${{{col_name}.get('${{1:key}}', ${{2:default}})}}",
                                documentation=f"Safe access key in '{col_name}' dict with default",
                                kind="variable",
                                detail=f"Dict get ({col_name})",
                                sortText=f"0_{state_name}_{col_name}_get"
                            ))
                            # Length check
                            variables.append(CompletionItem(
                                label=f"len({col_name})",
                                insertText=f"${{len({col_name})}}",
                                documentation=f"Get length of '{col_name}' array/dict",
                                kind="variable",
                                detail=f"Length of {col_name}",
                                sortText=f"0_{state_name}_{col_name}_len"
                            ))

                    elif template_type_lower == "python":
                        # Python query access format
                        variables.append(CompletionItem(
                            label=f"{state_name}.{col_name}",
                            insertText=f"query.get('{col_name}')",
                            documentation=f"Access column '{col_name}' from state '{state_name}' (type: {col_def.data_type})",
                            kind="variable",
                            detail=f"State: {state_name} ({col_def.data_type})",
                            sortText=f"0_{state_name}_{col_name}"
                        ))
                        variables.append(CompletionItem(
                            label=col_name,
                            insertText=f"query['{col_name}']",
                            documentation=f"Column '{col_name}' (from {state_name}, type: {col_def.data_type})",
                            kind="variable",
                            detail=f"{state_name} ({col_def.data_type})",
                            sortText=f"1_{col_name}"
                        ))

                        # Add JSON-specific completions for complex types
                        if is_json_column:
                            # Iteration snippet for arrays
                            snippets.append(CompletionItem(
                                label=f"for item in {col_name}",
                                insertText=f"for item in query.get('{col_name}', []):\n    ${{1:# process item}}",
                                documentation=f"Iterate over '{col_name}' array from state '{state_name}'",
                                kind="snippet",
                                detail=f"Iterate {col_name} (json)",
                                sortText=f"0_{state_name}_{col_name}_iter"
                            ))
                            # Iteration with index
                            snippets.append(CompletionItem(
                                label=f"for i, item in {col_name}",
                                insertText=f"for i, item in enumerate(query.get('{col_name}', [])):\n    ${{1:# process item}}",
                                documentation=f"Iterate over '{col_name}' with index from state '{state_name}'",
                                kind="snippet",
                                detail=f"Iterate {col_name} with index",
                                sortText=f"0_{state_name}_{col_name}_iter_idx"
                            ))
                            # List comprehension
                            snippets.append(CompletionItem(
                                label=f"[x for x in {col_name}]",
                                insertText=f"[${{1:x}} for x in query.get('{col_name}', [])]",
                                documentation=f"List comprehension over '{col_name}' array",
                                kind="snippet",
                                detail=f"Comprehension ({col_name})",
                                sortText=f"0_{state_name}_{col_name}_comp"
                            ))
                            # Dictionary key access with default
                            variables.append(CompletionItem(
                                label=f"{col_name}.get('key')",
                                insertText=f"query.get('{col_name}', {{}}).get('${{1:key}}', ${{2:None}})",
                                documentation=f"Safe access nested key in '{col_name}' dict",
                                kind="variable",
                                detail=f"Dict get ({col_name})",
                                sortText=f"0_{state_name}_{col_name}_get"
                            ))
                            # Dictionary keys iteration
                            snippets.append(CompletionItem(
                                label=f"for key in {col_name}.keys()",
                                insertText=f"for key in query.get('{col_name}', {{}}).keys():\n    value = query['{col_name}'][key]\n    ${{1:# process key, value}}",
                                documentation=f"Iterate over keys in '{col_name}' dict",
                                kind="snippet",
                                detail=f"Dict keys ({col_name})",
                                sortText=f"0_{state_name}_{col_name}_keys"
                            ))
                            # Dictionary items iteration
                            snippets.append(CompletionItem(
                                label=f"for k, v in {col_name}.items()",
                                insertText=f"for key, value in query.get('{col_name}', {{}}).items():\n    ${{1:# process key, value}}",
                                documentation=f"Iterate over key-value pairs in '{col_name}' dict",
                                kind="snippet",
                                detail=f"Dict items ({col_name})",
                                sortText=f"0_{state_name}_{col_name}_items"
                            ))
                            # Length check
                            variables.append(CompletionItem(
                                label=f"len({col_name})",
                                insertText=f"len(query.get('{col_name}', []))",
                                documentation=f"Get length of '{col_name}' array/dict",
                                kind="variable",
                                detail=f"Length of {col_name}",
                                sortText=f"0_{state_name}_{col_name}_len"
                            ))
    except Exception as ex:
        # Log but don't fail - just return without state variables
        print(f"Warning: Could not fetch states: {ex}")

    # Add available functions from BaseSecureRunnable (for Python templates)
    if template_type_lower == "python":
        functions.extend([
            CompletionItem(
                label="self.query_state_data",
                insertText="self.query_state_data(state_id='${1:state_id}', filters=[${2}])",
                documentation="Query data from another state with filters. Returns dict with query results.",
                kind="method",
                detail="-> Dict"
            ),
            CompletionItem(
                label="self.pivot_list_of_dicts",
                insertText="self.pivot_list_of_dicts(${1:data})",
                documentation="Pivot a list of row data (with data_index, column_name, data_value) into a list of dictionaries.",
                kind="method",
                detail="-> List[Dict]"
            ),
            CompletionItem(
                label="self.context",
                insertText="self.context['${1:key}']",
                documentation="Access the secure context storage for stateful data between calls.",
                kind="property",
                detail="SecureContext"
            ),
            CompletionItem(
                label="self.logger.info",
                insertText="self.logger.info('${1:message}')",
                documentation="Log an info message (truncated at 1000 chars).",
                kind="method",
                detail="-> None"
            ),
            CompletionItem(
                label="self.logger.error",
                insertText="self.logger.error('${1:message}')",
                documentation="Log an error message (truncated at 1000 chars).",
                kind="method",
                detail="-> None"
            ),
            CompletionItem(
                label="self.requests.get",
                insertText="self.requests.get('${1:url}')",
                documentation="Send HTTP GET request (rate-limited, domain-restricted).",
                kind="method",
                detail="-> Response"
            ),
            CompletionItem(
                label="self.requests.post",
                insertText="self.requests.post('${1:url}', json=${2:payload})",
                documentation="Send HTTP POST request (rate-limited, domain-restricted).",
                kind="method",
                detail="-> Response"
            ),
            CompletionItem(
                label="self.requests.put",
                insertText="self.requests.put('${1:url}', json=${2:payload})",
                documentation="Send HTTP PUT request (rate-limited, domain-restricted).",
                kind="method",
                detail="-> Response"
            ),
            CompletionItem(
                label="self.requests.delete",
                insertText="self.requests.delete('${1:url}')",
                documentation="Send HTTP DELETE request (rate-limited, domain-restricted).",
                kind="method",
                detail="-> Response"
            ),
        ])

    # Get snippets from template examples
    hints = TemplateExamples.get_autocompletion_hints_for_type(template_type)
    for snippet in hints.get("snippets", []):
        snippets.append(CompletionItem(
            label=snippet.get("label", ""),
            insertText=snippet.get("insertText", ""),
            documentation=snippet.get("documentation", ""),
            kind="snippet"
        ))

    keywords = hints.get("keywords", [])

    # Combine all completions
    all_completions = variables + functions + snippets

    return AutocompletionResponse(
        template_type=template_type,
        completions=all_completions,
        variables=variables,
        functions=functions,
        snippets=snippets,
        keywords=keywords,
        states=states_info if states_info else None
    )


def _convert_state_data_to_rows(state) -> List[Dict]:
    """Convert state column data to row format for AI context"""
    if not state or not state.data or not state.columns:
        return []

    rows = []
    # Get the number of rows from the first column
    first_col = next(iter(state.data.values()), None)
    if not first_col or not first_col.values:
        return []

    num_rows = len(first_col.values)

    for i in range(num_rows):
        row = {}
        for col_name, col_data in state.data.items():
            if col_data and col_data.values and i < len(col_data.values):
                row[col_name] = col_data.values[i]
        rows.append(row)

    return rows


@template_router.get('/state/sample/{state_id}')
async def get_state_sample_data(
    state_id: str,
    limit: int = 10
) -> StateSampleData:
    """
    Get sample data from a state for AI template generation context.
    Returns up to `limit` rows of sample data along with column info.
    """
    try:
        # Load state with data (limited rows)
        state = storage.load_state(state_id=state_id, load_data=True, offset=0, limit=limit)

        if not state:
            raise HTTPException(status_code=404, detail=f"State not found: {state_id}")

        if not state.columns:
            raise HTTPException(status_code=404, detail=f"State has no columns: {state_id}")

        # Get state name
        state_name = state.config.name if state.config and state.config.name else state_id[:8]

        # Convert column data to row format
        sample_rows = _convert_state_data_to_rows(state)

        return StateSampleData(
            state_id=state_id,
            state_name=state_name,
            columns=list(state.columns.keys()),
            sample_rows=sample_rows,
            total_rows=state.count or 0
        )

    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Error fetching state data: {str(ex)}")


@template_router.get('/state/samples/{project_id}')
async def get_project_state_samples(
    project_id: str,
    limit: int = 10
) -> List[StateSampleData]:
    """
    Get sample data from all states in a project for AI template generation.
    Returns up to `limit` rows from each state.
    """
    samples = []

    try:
        states = storage.fetch_states(project_id=project_id)

        if not states:
            return samples

        for s in states:
            try:
                # Load state with limited data
                state = storage.load_state(state_id=s.id, load_data=True, offset=0, limit=limit)

                if not state or not state.columns:
                    continue

                state_name = state.config.name if state.config and state.config.name else s.id[:8]
                sample_rows = _convert_state_data_to_rows(state)

                samples.append(StateSampleData(
                    state_id=s.id,
                    state_name=state_name,
                    columns=list(state.columns.keys()),
                    sample_rows=sample_rows,
                    total_rows=state.count or 0
                ))
            except Exception as ex:
                # Skip states that fail to load
                print(f"Warning: Could not load state {s.id}: {ex}")
                continue

        return samples

    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Error fetching project states: {str(ex)}")


class GenerateTemplateRequest(BaseModel):
    """Request for generating a template from state data"""
    template_type: str
    state_id: str
    user_instructions: Optional[str] = None
    model: str = "gpt-4o-mini"
    sample_limit: int = 10


@template_router.post('/generate/from-state')
async def generate_template_from_state(request: GenerateTemplateRequest) -> ChatCompletionResponse:
    """
    Generate a template by analyzing state columns and sample data.
    The AI will create an appropriate template based on the data structure.
    """
    if not openai_client:
        raise HTTPException(
            status_code=503,
            detail="OpenAI client not initialized. Please set OPENAI_API_KEY environment variable."
        )

    # Fetch state metadata (no data needed)
    try:
        state = storage.load_state_metadata(state_id=request.state_id)

        if not state:
            raise HTTPException(status_code=404, detail=f"State not found: {request.state_id}")

        if not state.columns:
            raise HTTPException(status_code=404, detail=f"State has no columns: {request.state_id}")

    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Error loading state: {str(ex)}")

    state_name = state.config.name if state.config and state.config.name else request.state_id[:8]

    # Build column metadata (types only, no data)
    state_column_info = StateColumnInfo(
        state_id=request.state_id,
        state_name=state_name,
        columns={
            col_name: col_def.data_type
            for col_name, col_def in state.columns.items()
        }
    )

    # Build user message
    user_message = f"""Create a {request.template_type} template for processing data from the state "{state_name}".

The state has {state.count or 0} total rows.

Create an appropriate template that:
1. Uses the actual column names from the data
2. Handles the data types appropriately
3. Produces useful structured output (JSON format preferred)
"""

    if request.user_instructions:
        user_message += f"\n\nAdditional instructions: {request.user_instructions}"

    # Create the chat completion request with column metadata only
    chat_request = ChatCompletionRequest(
        template_type=request.template_type,
        user_message=user_message,
        model=request.model,
        state_columns=[state_column_info]
    )

    return await chat_completion(chat_request)
