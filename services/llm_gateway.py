"""
Single entry point for Gemini calls, with key rotation via LiteLLM's Router.

Note on capacity: the router rotates across whatever distinct keys `Settings`
found. If those keys all belong to the same Google project they share a
project-level quota, so rotation buys failover but not throughput. The startup
log prints the real distinct-key count so this is visible rather than assumed.
"""

import logging

from litellm import Router
from pydantic import BaseModel

from core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class LLMGateway:
    _instance = None

    def __new__(cls, settings: Settings | None = None):
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._initialize_router(settings or get_settings())
            cls._instance = instance
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Drop the singleton. Used by tests."""
        cls._instance = None

    def _initialize_router(self, settings: Settings) -> None:
        self.settings = settings
        keys = settings.google_api_keys

        if not keys:
            # The message previously named GEMINI_API_KEY_X, a variable that is
            # read nowhere and set nowhere -- it sent people hunting for the
            # wrong thing. The code reads GOOGLE_API_KEY and GOOGLE_API_KEY1..N.
            raise ValueError(
                "No Google API keys found. Set GOOGLE_API_KEY or "
                "GOOGLE_API_KEY1..N in AIEngine/.env"
            )

        self.model_name = settings.gemini_model
        logger.info(
            "LLMGateway: %d distinct API key(s) detected for model %s",
            len(keys),
            self.model_name,
        )
        if len(keys) == 1:
            logger.warning(
                "Only one distinct Google API key is configured. Key rotation "
                "provides no additional quota; it is failover only."
            )

        model_list = [
            {
                "model_name": self.model_name,
                "litellm_params": {
                    "model": f"gemini/{self.model_name}",
                    "api_key": key,
                },
            }
            for key in keys
        ]

        self.router = Router(
            model_list=model_list,
            routing_strategy="simple-shuffle",
            num_retries=2,
            allowed_fails=1,
        )

    def invoke_structured(
        self, prompt: str, schema_class: type[BaseModel]
    ) -> BaseModel:
        """Send a prompt through the rotating router and validate the response."""
        response = self.router.completion(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            response_format=schema_class,
        )
        raw_json = response.choices[0].message.content
        return schema_class.model_validate_json(raw_json)
