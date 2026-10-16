from __future__ import annotations

import os

from ragfusion.retrievald.app import create_app
from ragfusion.retrievald.config import RetrievaldConfig, build_backend
from ragfusion.registry import RegistryRO


def build_app(env=None):
    """Construct the retrievald ASGI app from environment config.

    This is the missing serving entrypoint: ``create_app`` is a factory that
    needs a backend + registry, and nothing in the package wired it to real
    config. ``build_app`` reads ``RetrievaldConfig.from_env`` (RETRIEVALD_BACKEND,
    RETRIEVALD_EMBED_MODEL, RETRIEVALD_DIMS, RETRIEVALD_REGISTRY_DB, ...), builds the backend,
    opens the registry read-only, and returns the app.

    Run it under uvicorn as a zero-arg factory::

        uvicorn ragfusion.retrievald.server:build_app --factory --host 0.0.0.0 --port 8081

    `env` is injectable for tests; it defaults to ``os.environ``.
    """
    env = os.environ if env is None else env
    config = RetrievaldConfig.from_env(env)
    if not config.registry_db:
        raise RuntimeError(
            "RETRIEVALD_REGISTRY_DB must point at the registry sqlite file retrievald serves from"
        )
    backend = build_backend(config)
    registry_ro = RegistryRO(config.registry_db)
    return create_app(backend, registry_ro, config)
