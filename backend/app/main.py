from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import get_settings
from app.database import init_db
from app.limiter import limiter
from app.routers import auth, audits, reports, admin

settings = get_settings()

class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        valid_origins = [
            o.strip()
            for o in settings.CORS_ORIGINS.split(",")
            if o.strip() and o.strip() != "*"
        ]

        host = request.headers.get("host", "").split(":")[0].lower()
        allowed_hosts = {"localhost", "127.0.0.1", "backend", "frontend", "worker"}
        for o in valid_origins:
            allowed_hosts.add(o.split("://")[-1].split(":")[0])
        if host and host not in allowed_hosts:
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid Host header"},
            )

        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            origin = request.headers.get("origin", "")
            referer = request.headers.get("referer", "")
            if origin and origin not in valid_origins:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Origin not allowed"},
                )
            if referer and not any(
                referer.startswith(o) for o in valid_origins
            ):
                if origin == "":
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Referer not allowed"},
                    )

        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="SAST IA - Security Audit Platform",
    description="Plateforme d'audit de sécurité automatisé",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SecurityMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(auth.router)
app.include_router(audits.router)
app.include_router(reports.router)
app.include_router(admin.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}
