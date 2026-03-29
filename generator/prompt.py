# generator/prompt.py

def build_schema_prompt(spec: dict) -> str:
    """
    Build a prompt asking the LLM to design a schema based on user spec.
    spec keys: industry, data_type, num_files, time_period, rows_per_file
    Returns a prompt that asks LLM to respond in JSON only.
    """
    if spec.get("random"):
        return """You are a synthetic data designer.

Invent a realistic business dataset entirely from scratch.
Choose the industry, data type, number of files, time period, and schema yourself.
Be creative — avoid generic examples like sales or employees.

Respond in JSON only. No explanation, no markdown, no backticks.
Use no more than 7 fields. Keep field names short and simple.
Use exactly this structure:
{
  "industry": "string",
  "data_type": "string",
  "num_files": integer  between 1 and 3,
  "time_period": "string",
  "rows_per_file": integer integer between 20 and 50,
  "filename_prefix": "string",
  "fields": [
    {
      "name": "string",
      "type": "string (int | float | string | date | bool)",
      "description": "string",
      "example_values": ["value1", "value2", "value3"]
    }
  ]
}"""

    return f"""You are a synthetic data designer.

Design a realistic schema for the following dataset:
- Industry: {spec['industry']}
- Data type: {spec['data_type']}
- Number of files: {spec['num_files']}
- Time period: {spec['time_period']}
- Approximate rows per file: {spec.get('rows_per_file', 'you decide, be realistic')}

Respond in JSON only. No explanation, no markdown, no backticks.
Use exactly this structure:
{{
  "industry": "string",
  "data_type": "string",
  "num_files": integer between 1 and 3,
  "time_period": "string",
  "rows_per_file": integer between 20 and 50,
  "filename_prefix": "string",
  "fields": [
    {{
      "name": "string",
      "type": "string (int | float | string | date | bool)",
      "description": "string",
      "example_values": ["value1", "value2", "value3"]
    }}
  ]
}}"""


def build_generation_prompt(schema: dict, file_index: int) -> str:
    """
    Build a prompt asking the LLM to generate rows matching the schema.
    file_index is used to vary the time period across files.
    """
    fields_summary = "\n".join([
        f"- {f['name']} ({f['type']}): {f.get('description', '')}. "
        f"Examples: {', '.join(str(v) for v in f.get('example_values', []))}"
        for f in schema['fields']
    ])

    return f"""You are a synthetic data generator.

Generate {schema['rows_per_file']} rows of realistic {schema['data_type']} data 
for the {schema['industry']} industry. This is file {file_index + 1} of {schema['num_files']}.

Fields:
{fields_summary}

Rules:
- Be realistic and varied — avoid repeating the same values
- Respect the data types strictly
- Dates should reflect file {file_index + 1} of the period: {schema['time_period']}
- Do not include a header row

Respond in JSON only. No explanation, no markdown, no backticks.
Use no more than 7 fields. Keep field names short and simple.
Return a JSON array of objects, one object per row:
[
  {{"field_name": value, ...}},
  ...
]"""