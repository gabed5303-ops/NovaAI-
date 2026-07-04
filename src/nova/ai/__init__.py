"""The AI "brains" for Nova.

`base.py` defines the contract every brain must follow. `ollama_provider.py`
and `anthropic_provider.py` are two brains that follow it. `registry.py` picks
the right one based on your settings.
"""
