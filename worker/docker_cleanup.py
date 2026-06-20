import os
import shutil
import subprocess


DOCKER_BIN = shutil.which("docker")


def _run(*args: str) -> bool:
    if not DOCKER_BIN:
        return False
    try:
        r = subprocess.run(
            [DOCKER_BIN, *args],
            capture_output=True,
            timeout=30,
        )
        return r.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def cleanup_audit(container_name: str) -> bool:
    _run("stop", container_name)
    _run("rm", "-f", container_name)
    _run("rmi", container_name)


def cleanup_audit_by_id(audit_id: str) -> bool:
    container_name = f"sastia-audit-{audit_id}"
    return cleanup_audit(container_name)
