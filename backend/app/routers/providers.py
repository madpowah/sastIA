import json
import uuid
import os
import httpx
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Provider
from app.schemas import ProviderCreate, ProviderResponse, ModelInfo, ProviderGroup
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


KNOWN_PROVIDERS: list[tuple[str, str, list[tuple[str, str]]]] = [
    ("opencode-go", "OpenCode Go", [
        ("deepseek-v4-flash", "Deepseek V4 Flash (rapide)"),
        ("deepseek-v4-pro", "Deepseek V4 Pro (complet)"),
    ]),
    ("opencode", "OpenCode (free)", [
        ("deepseek-v4-flash-free", "Deepseek V4 Flash (gratuit)"),
    ]),
    ("ollama-cloud", "Ollama Cloud", [
        ("deepseek-v4-flash", "Deepseek V4 Flash"),
        ("deepseek-v4-pro", "Deepseek V4 Pro"),
    ]),
]


def _get_provider_groups() -> list[ProviderGroup]:
    config = _read_opencode_config()
    config_providers = config.get("provider", {})
    groups: list[ProviderGroup] = []

    for provider_id, display_name, models in KNOWN_PROVIDERS:
        group_models = [
            ModelInfo(id=f"{provider_id}/{mid}", name=mname, provider=provider_id, built_in=True)
            for mid, mname in models
        ]
        groups.append(ProviderGroup(provider=provider_id, name=display_name, models=group_models))

    for provider_id, provider_cfg in config_providers.items():
        provider_name = provider_cfg.get("name", provider_id)
        provider_models = provider_cfg.get("models", {})
        if not provider_models:
            continue
        group_models = [
            ModelInfo(
                id=f"{provider_id}/{model_id}",
                name=model_cfg.get("name", model_id),
                provider=provider_id,
                built_in=True,
            )
            for model_id, model_cfg in provider_models.items()
        ]
        groups.append(ProviderGroup(provider=provider_id, name=provider_name, models=group_models))

    return groups


@router.get("/groups", response_model=list[ProviderGroup])
def list_provider_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    groups = _get_provider_groups()

    user_providers = db.query(Provider).filter(Provider.user_id == current_user.id).all()
    for provider in user_providers:
        if not provider.models_json:
            continue
        try:
            models_data = json.loads(provider.models_json)
        except json.JSONDecodeError:
            continue
        group_models = [
            ModelInfo(
                id=f"{provider.name}/{m.get('id', m.get('_id', ''))}",
                name=m.get("name", m.get("id", "")),
                provider=provider.name,
                built_in=False,
            )
            for m in models_data
            if m.get("id") or m.get("_id")
        ]
        if group_models:
            groups.append(ProviderGroup(provider=provider.name, name=provider.name, models=group_models))

    return groups


@router.get("/models", response_model=list[ModelInfo])
def list_available_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    groups = list_provider_groups(current_user, db)
    models = []
    for g in groups:
        models.extend(g.models)
    return models


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
