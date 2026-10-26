"""Translate web admission failures at the tool boundary; core execution is unchanged."""
from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from wayfinder.api.errors import WebError


class WebAssistantUseCase(AssistantUseCase):
    def _tool(self, *args, **kwargs):
        try:
            return super()._tool(*args, **kwargs)
        except WebError as error:
            if error.code != 'rate_limited':
                raise
            return {'error': {'code': error.code, 'message': error.message, 'retry_after': error.retry_after}}
