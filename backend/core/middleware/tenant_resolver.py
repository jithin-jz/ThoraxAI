"""
Tenant resolver middleware.

Resolves Host header → tenant context on request.state.
Never blocks requests — only annotates for downstream use.
"""

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from core.database import master_db
from core.redis_client import redis_client
from core.settings import settings
from core.tenancy import extract_subdomain, is_valid_subdomain

logger = logging.getLogger(__name__)

_CACHE_TTL = 60  # seconds


class TenantResolverMiddleware(BaseHTTPMiddleware):
    SKIP_PATHS = {"/docs", "/redoc", "/openapi.json", "/health"}

    async def dispatch(self, request: Request, call_next):
        request.state.subdomain = None
        request.state.tenant = None
        request.state.tenant_id = None

        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        # 1. Extract subdomain from Host header
        host = request.headers.get("host")
        sub = extract_subdomain(host)

        # 2. X-Tenant-Subdomain override — always accepted if Host-based resolution yields None
        if not sub:
            override = request.headers.get("x-tenant-subdomain", "").strip().lower()
            if override and is_valid_subdomain(override):
                sub = override

        if sub:
            request.state.subdomain = sub
            hospital = await self._resolve_tenant(sub)
            if hospital:
                request.state.tenant = hospital
                request.state.tenant_id = hospital.get("hospital_id")

        return await call_next(request)

    async def _resolve_tenant(self, subdomain: str) -> dict | None:
        """Look up tenant with Redis cache to avoid per-request DB hits."""
        cache_key = f"tenant_sub:{subdomain}"

        # Try cache first
        try:
            cached = await redis_client.get(cache_key)
            if cached == "__none__":
                return None
            if cached:
                import json

                return json.loads(cached)
        except Exception:
            pass  # Cache miss or Redis down — fall through to DB

        # DB lookup
        try:
            hospital = await master_db.hospitals.find_one({"subdomain": subdomain})
        except Exception as e:
            logger.error("Tenant lookup failed for subdomain=%s: %s", subdomain, e)
            return None

        # Cache result
        if hospital:
            cacheable = {
                "hospital_id": hospital.get("hospital_id"),
                "name": hospital.get("name"),
                "subdomain": hospital.get("subdomain"),
                "is_active": hospital.get("is_active", True),
            }
            try:
                import json

                await redis_client.setex(cache_key, _CACHE_TTL, json.dumps(cacheable))
            except Exception:
                pass
            return cacheable
        else:
            import contextlib

            with contextlib.suppress(Exception):
                await redis_client.setex(cache_key, _CACHE_TTL, "__none__")
            return None
