import json
import uuid
import os
import httpx
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Provider
from app.schemas import ProviderCreate, ProviderResponse, ModelInfo
from app.auth import get_current_user

router = APIRouter(prefix="/api/providers", tags=["Providers"])

OPCODE_CONFIG_PATH = Path(os.path.expanduser("~/.config/opencode/config.json"))


def _read_opencode_config() -> dict:
    if not OPCODE_CONFIG_PATH.exists():
        return {"providers": {}}
    try:
        return json.loads(OPCODE_CONFIG_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return {"providers": {}}


OPCODE_DEFAULT_MODELS = [
    ModelInfo(id="opencode-go/deepseek-v4-flash", name="Deepseek V4 Flash (rapide)", provider="OpenCode", built_in=True),
    ModelInfo(id="opencode-go/deepseek-v4-pro", name="Deepseek V4 Pro (complet)", provider="OpenCode", built_in=True),
    ModelInfo(id="opencode/deepseek-v4-flash-free", name="Deepseek V4 Flash (gratuit)", provider="OpenCode", built_in=True),
]


def _get_built_in_models() -> list[ModelInfo]:
    config = _read_opencode_config()
    providers = config.get("provider", {})
    models = list(OPCODE_DEFAULT_MODELS)

    for provider_id, provider_cfg in providers.items():
        provider_name = provider_cfg.get("name", provider_id)
        provider_models = provider_cfg.get("models", {})
        for model_id, model_cfg in provider_models.items():
            models.append(ModelInfo(
                id=model_id,
                name=model_cfg.get("name", model_id),
                provider=provider_name,
                built_in=True,
            ))

    return models


@router.get("/models", response_model=list[ModelInfo])
def list_available_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    built_in = _get_built_in_models()

    user_providers = db.query(Provider).filter(Provider.user_id == current_user.id).all()
    user_models: list[ModelInfo] = []
    for provider in user_providers:
        if provider.models_json:
            try:
                models_data = json.loads(provider.models_json)
                for m in models_data:
                    user_models.append(ModelInfo(
                        id=m.get("id", m.get("_id", "")),
                        name=m.get("name", m.get("id", "")),
                        provider=provider.name,
                        built_in=False,
                    ))
            except json.JSONDecodeError:
                pass

    return built_in + user_models


@router.get("/", response_model=list[ProviderResponse])
def list_providers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    providers = db.query(Provider).filter(Provider.user_id == current_user.id).order_by(Provider.created_at.desc()).all()
    return [ProviderResponse.model_validate(p) for p in providers]


@router.post("/", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
def create_provider(
    data: ProviderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    provider = Provider(
        user_id=current_user.id,
        name=data.name,
        base_url=data.base_url.rstrip("/"),
        api_key=data.api_key,
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return ProviderResponse.model_validate(provider)


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_provider(
    provider_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    provider = db.query(Provider).filter(
        Provider.id == provider_id,
        Provider.user_id == current_user.id,
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    db.delete(provider)
    db.commit()


@router.post("/{provider_id}/fetch-models", response_model=list[ModelInfo])
def fetch_provider_models(
    provider_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    provider = db.query(Provider).filter(
        Provider.id == provider_id,
        Provider.user_id == current_user.id,
    ).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    headers = {
        "Content-Type": "application/json",
    }
    if provider.api_key:
        headers["Authorization"] = f"Bearer {provider.api_key}"

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(f"{provider.base_url}/models", headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch models from {provider.base_url}/models: {e}",
        )

    models_data = data.get("data", data if isinstance(data, list) else [])
    if isinstance(models_data, dict):
        models_data = [models_data]

    models: list[dict] = []
    for m in models_data:
        mid = m.get("id", m.get("_id", ""))
        mname = m.get("name", mid)
        models.append({"id": mid, "name": mname})

    provider.models_json = json.dumps(models)
    db.commit()
    db.refresh(provider)

    return [
        ModelInfo(id=m["id"], name=m["name"], provider=provider.name, built_in=False)
        for m in models
    ]
