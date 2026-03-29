# config.py

OLLAMA_MODEL = "llama3.2:3b"
OLLAMA_URL = "http://localhost:11434/api/generate"

OUTPUT_PATH = "./output"

# Dirty data defaults — can be overridden at runtime
DIRTY_CONFIG = {
    "enabled": False,
    "outlier_rate": 0.02,      # 2% of numeric rows get an outlier value
    "null_rate": 0.01,         # 1% of fields get nulled out
    "duplicate_rate": 0.01     # 1% of rows get duplicated
}