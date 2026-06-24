"""OpenRouter provider implementation."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import httpx
from config.settings import get_settings
from core.anthropic import iter_provider_stream_error_sse_events
from core.anthropic.native_sse_block_policy import (
    NativeSseBlockPolicyState,
    is_terminal_openrouter_done_event,
    parse_native_sse_event,
    transform_native_sse_block_event,
)
from providers.anthropic_messages import AnthropicMessagesTransport, StreamChunkMode, _maybe_await_aclose
from providers.base import ProviderConfig
from providers.defaults import OPENROUTER_DEFAULT_BASE
from providers.model_listing import (
    ProviderModelInfo,
    extract_openrouter_tool_model_ids,
    extract_openrouter_tool_model_infos,
)

from .key_manager import OpenRouterKeyManager, logger as rotation_logger
from .request import build_request_body

_ANTHROPIC_VERSION = "2023-06-01"


class OpenRouterProvider(AnthropicMessagesTransport):
    """OpenRouter provider using the native Anthropic-compatible messages API."""

    stream_chunk_mode: StreamChunkMode = "event"

    def __init__(self, config: ProviderConfig):
        super().__init__(
            config,
            provider_name="OPENROUTER",
            default_base_url=OPENROUTER_DEFAULT_BASE,
        )
        settings = get_settings()
        from config.paths import openrouter_keys_path
        keys_file = settings.open_router_api_keys_file
        if not keys_file and openrouter_keys_path().is_file():
            keys_file = str(openrouter_keys_path())
        
        self.key_manager = OpenRouterKeyManager(
            api_key=settings.open_router_api_key,
            api_keys_file=keys_file
        )

    async def _validated_stream_send(
        self, body: dict, *, req_tag: str
    ) -> httpx.Response:
        max_retries = max(1, len(self.key_manager.keys))
        
        send_response = None
        for attempt in range(max_retries):
            send_response = await self._send_stream_request(body)
            if send_response.status_code == 200:
                return send_response
                
            if send_response.status_code in (401, 402, 429):
                error_msg = f"HTTP {send_response.status_code}"
                if send_response.status_code == 402:
                    self.key_manager.mark_key_exhausted(error_msg)
                else:
                    self.key_manager.rotate_key(error_msg)
                rotation_logger.info("Retry performed")
                
                if not send_response.is_closed:
                    await _maybe_await_aclose(send_response)
                continue
                
            break
            
        if send_response is not None and send_response.status_code != 200:
            try:
                await self._raise_for_status(send_response, req_tag=req_tag)
            finally:
                if not send_response.is_closed:
                    await _maybe_await_aclose(send_response)
                    
        return send_response

    async def _send_model_list_request(self) -> httpx.Response:
        max_retries = max(1, len(self.key_manager.keys))
        
        response = None
        for attempt in range(max_retries):
            response = await self._client.get("/models", headers=self._model_list_headers())
            if response.status_code == 200:
                return response
                
            if response.status_code in (401, 402, 429):
                error_msg = f"HTTP {response.status_code}"
                if response.status_code == 402:
                    self.key_manager.mark_key_exhausted(error_msg)
                else:
                    self.key_manager.rotate_key(error_msg)
                rotation_logger.info("Retry performed")
                
                if not response.is_closed:
                    await response.aclose()
                continue
            
            break
            
        return response

    def _build_request_body(
        self, request: Any, thinking_enabled: bool | None = None
    ) -> dict:
        """Internal helper for tests and direct request dispatch."""
        return build_request_body(
            request,
            thinking_enabled=self._is_thinking_enabled(request, thinking_enabled),
        )

    def _request_headers(self) -> dict[str, str]:
        """Return OpenRouter's Anthropic-compatible messages headers."""
        return {
            "Accept": "text/event-stream",
            "Authorization": f"Bearer {self.key_manager.get_current_key()}",
            "Content-Type": "application/json",
            "anthropic-version": _ANTHROPIC_VERSION,
        }

    def _model_list_headers(self) -> dict[str, str]:
        """Return OpenRouter's OpenAI-compatible model-list headers."""
        return {"Authorization": f"Bearer {self.key_manager.get_current_key()}"}

    def _extract_model_ids_from_model_list_payload(
        self, payload: Any
    ) -> frozenset[str]:
        """Only advertise OpenRouter models that can run Claude Code tools."""
        return extract_openrouter_tool_model_ids(
            payload, provider_name=self._provider_name
        )

    def _extract_model_infos_from_model_list_payload(
        self, payload: Any
    ) -> frozenset[ProviderModelInfo]:
        """Advertise OpenRouter tool models with reasoning capability metadata."""
        return extract_openrouter_tool_model_infos(
            payload, provider_name=self._provider_name
        )

    def _new_stream_state(self, request: Any, *, thinking_enabled: bool) -> Any:
        """Create per-stream state for thinking block filtering."""
        return NativeSseBlockPolicyState()

    def _transform_stream_event(
        self,
        event: str,
        state: Any,
        *,
        thinking_enabled: bool,
    ) -> str | None:
        """Drop provider-specific terminal noise and hidden thinking events."""
        if isinstance(state, NativeSseBlockPolicyState):
            event_name, data_text = parse_native_sse_event(event)
            if state.message_stopped or is_terminal_openrouter_done_event(
                event_name, data_text
            ):
                return None
            if event_name == "message_stop":
                state.message_stopped = True

        if isinstance(state, NativeSseBlockPolicyState):
            return transform_native_sse_block_event(
                event, state, thinking_enabled=thinking_enabled
            )
        return event

    def _emit_error_events(
        self,
        *,
        request: Any,
        input_tokens: int,
        error_message: str,
        sent_any_event: bool,
    ) -> Iterator[str]:
        """Emit the Anthropic SSE error shape expected by Claude clients."""
        yield from iter_provider_stream_error_sse_events(
            request=request,
            input_tokens=input_tokens,
            error_message=error_message,
            sent_any_event=sent_any_event,
            log_raw_sse_events=self._config.log_raw_sse_events,
        )
