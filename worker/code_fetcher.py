import os
import shutil
import zipfile
import tarfile
import tempfile
from pathlib import Path
from typing import Optional

import httpx


async def fetch_code(job, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)

    # Priority: repo_url first, then code_path
    if job.repo_url:
        return await _clone_git(job.repo_url, target_dir)

    if job.code_path:
        return await _download_or_copy_code(job, target_dir)

    raise ValueError("No repo_url or code_path provided")


async def _clone_git(repo_url: str, target_dir: Path) -> Path:
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    clone_dir = target_dir / repo_name

    if clone_dir.exists():
        shutil.rmtree(clone_dir)

    try:
        import git

        print(f"[code_fetcher] Cloning {repo_url} -> {clone_dir}")
        git.Repo.clone_from(repo_url, clone_dir, depth=1)
        return clone_dir
    except ImportError:
        # fallback: use subprocess git
        import subprocess

        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(clone_dir)],
            check=True,
            capture_output=True,
        )
        return clone_dir
    except Exception as e:
        raise RuntimeError(f"Git clone failed: {e}")


async def _download_or_copy_code(job, target_dir: Path) -> Path:
    ext = os.path.splitext(job.code_path)[1].lower()
    code_file = target_dir / f"code{ext}"

    if job.code_path.startswith("http"):
        # Download from backend
        async with httpx.AsyncClient() as client:
            resp = await client.get(job.code_path)
            resp.raise_for_status()
            code_file.write_bytes(resp.content)
    elif os.path.exists(job.code_path):
        shutil.copy2(job.code_path, code_file)
    else:
        # code_path is a path on the backend filesystem — try via backend API
        base = job.backend_base_url or "http://backend:8000"
        download_url = f"{base}/api/audits/{job.audit_id}/download"
        async with httpx.AsyncClient() as client:
            resp = await client.get(download_url)
            resp.raise_for_status()
            code_file.write_bytes(resp.content)

    return _extract_if_archive(code_file, target_dir)


def _extract_if_archive(file_path: Path, target_dir: Path) -> Path:
    ext = file_path.suffix.lower()
    extract_dir = target_dir / "extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)

    if ext == ".zip":
        with zipfile.ZipFile(file_path, "r") as zf:
            zf.extractall(extract_dir)
        return extract_dir

    if ext in (".tar", ".gz", ".tgz", ".bz2"):
        mode = "r:gz" if ext in (".gz", ".tgz") else "r:bz2" if ext == ".bz2" else "r"
        with tarfile.open(file_path, mode) as tf:
            tf.extractall(extract_dir)
        return extract_dir

    # Not an archive — single file, wrap in a dir
    src_dir = target_dir / "source"
    src_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(file_path, src_dir / file_path.name)
    return src_dir
