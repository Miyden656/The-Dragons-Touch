"""Training-data tooling for the future custom Commander model.

This package is the data-curation half of the north star: the AI layer generates
persona-grounded answers, the user approves the good ones (the Commander Guide
panel's "Save as training example" button writes them to
Outputs/commander_ai_training_data.jsonl), and these tools inspect, validate,
de-duplicate, and export that corpus into clean training data.

Nothing here calls Ollama or the engine's scoring chain — it only reads/writes
the JSONL corpus. Deleting ai/training/ leaves the rest of the layer intact.
"""
