# generator/llm.py
import json
import requests
from config import OLLAMA_MODEL, OLLAMA_URL


def _call_ollama(prompt: str) -> str:
    response = requests.post(OLLAMA_URL, json={
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    })
    return response.json()["response"].strip()


def _parse_json_response(raw: str) -> any:
    """
    Safely parse JSON from LLM response.
    Handles markdown fences, missing closing brackets, and truncated arrays.
    """
    # Step 1: strip markdown code fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1])

    # Fix leading zeros on integers e.g. 001 → 1 (invalid JSON)
    import re
    cleaned = re.sub(r':\s*0+(\d+)', r': \1', cleaned)

    cleaned = re.sub(r'\[("[\w]+":)', r'{\1', cleaned)
    cleaned = re.sub(r'(,\s*"[\w]+":\s*"[^"]*")\]', r'\1}', cleaned)

    # Step 2: try a clean parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Step 3: recovery — the model often generates valid rows but forgets
    # the closing bracket, or gets cut off mid-array. We try two fixes:
        if cleaned.startswith("{"):
            cleaned = "[" + cleaned

        # Fix A: just append the missing closing bracket
        # This covers the most common case — all rows present, just no ]
        try:
            return json.loads(cleaned + "]")
        except json.JSONDecodeError:
            pass

        # Fix B: salvage complete rows up to where it got cut off
        # rfind finds the last complete row ending with },
        # we discard everything after that and close the array cleanly
        last_complete = cleaned.rfind("},")
        if last_complete != -1:
            salvaged = cleaned[:last_complete + 1] + "\n]"
            try:
                rows = json.loads(salvaged)
                print(f"    Warning: truncated response, salvaged {len(rows)} rows")
                return rows
            except json.JSONDecodeError:
                pass


    # Handle array-of-arrays format — model returned headers + rows instead of objects
    # e.g. [["col1","col2"], ["val1","val2"]] → [{"col1": "val1", "col2": "val2"}]
    if cleaned.startswith("["):
        try:
            raw_array = json.loads(cleaned + "]") if not cleaned.endswith("]") else json.loads(cleaned)
            if isinstance(raw_array, list) and len(raw_array) > 1:
                if isinstance(raw_array[0], list):
                    headers = raw_array[0]
                    rows = []
                    for row in raw_array[1:]:
                        if isinstance(row, list) and len(row) == len(headers):
                            rows.append(dict(zip(headers, row)))
                    if rows:
                        print(f"    Warning: converted array-of-arrays to {len(rows)} row objects")
                        return rows
        except (json.JSONDecodeError, TypeError):
            pass

    raise ValueError(
        f"LLM returned invalid JSON — could not parse or salvage.\n"
        f"Error preview: {cleaned[:200]}"
    )


def design_schema(spec: dict) -> dict:
    """
    First LLM call — ask the model to design a schema from the user spec.
    Returns a validated schema dict.
    """
    from generator.prompt import build_schema_prompt

    print("  Designing schema...")
    prompt = build_schema_prompt(spec)
    raw = _call_ollama(prompt)
    schema = _parse_json_response(raw)

    # Basic validation
    required_keys = ["industry", "data_type", "num_files", "rows_per_file", "fields"]
    for key in required_keys:
        if key not in schema:
            raise ValueError(f"Schema missing required key: {key}")

    print(f"  Schema designed: {len(schema['fields'])} fields, "
          f"{schema['rows_per_file']} rows/file, "
          f"{schema['num_files']} files")

    return schema


def generate_rows(schema: dict, file_index: int) -> list[dict]:
    """
    Second LLM call — generate actual data rows matching the schema.
    Returns a list of row dicts.
    """
    from generator.prompt import build_generation_prompt

    prompt = build_generation_prompt(schema, file_index)
    raw = _call_ollama(prompt)
    rows = _parse_json_response(raw)

    if not isinstance(rows, list):
        raise ValueError(f"Expected a list of rows, got: {type(rows)}")

    return rows