"""The web layer (the "front door").

This layer is intentionally THIN: each route just receives a web request,
calls the matching Nova service (AI, memory, voice, commands), and returns the
result. All the real logic lives in the other modules, so Nova could later be
driven by a different front door (a CLI, a websocket) without rewriting anything.
"""
