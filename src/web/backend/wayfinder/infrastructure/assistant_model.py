"""Ignore model-supplied authorization fields; core binds tool execution to the actor."""
from dataclasses import replace
from doc2roadmap.application.ports.phase_b import ToolCall


class ActorBoundAssistantModel:
    def __init__(self, model):
        self.model = model

    def __getattr__(self, name):
        return getattr(self.model, name)

    def start_session(self, *args, **kwargs):
        session = self.model.start_session(*args, **kwargs)
        class BoundSession:
            def __getattr__(self, name):
                return getattr(session, name)

            def stream(self, *args, **kwargs):
                for event in session.stream(*args, **kwargs):
                    if isinstance(event, ToolCall):
                        # Scope and all ordinary arguments remain unchanged for SA69/core validation.
                        event = replace(event, args={k: v for k, v in event.args.items()
                            if k not in {'owner', 'doc_id', 'graph_version'}})
                    yield event
        return BoundSession()
