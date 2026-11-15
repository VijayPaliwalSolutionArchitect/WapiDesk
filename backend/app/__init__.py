"""WapiDesk backend package.

A WhatsApp & Web AI Support Hub: a FastAPI service that receives customer
conversations from WhatsApp (Meta Cloud API webhook) and a web widget, answers
knowledge questions grounded in a seeded knowledge base, performs order / booking /
complaint actions against business systems, keeps per-customer memory and hands off
to a human with full context.

The implementation mirrors the "One brain, many channels, strict action layer"
reference architecture described in the WapiDesk playbook chapter (Project Six).
"""

__version__ = "1.0.0"