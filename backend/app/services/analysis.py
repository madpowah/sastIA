import httpx
import json
import os
from sqlalchemy.orm import Session
from app.models import Audit, AuditStatus, DockerStatus
from app.config import get_settings

settings = get_settings()


async def send_to_analysis_worker(audit: Audit, db: Session):
    payload = {
        "audit_id": str(audit.id),
        "user_id": str(audit.user_id),
        "code_path": audit.code_file_path,
        "repo_url": audit.repo_url,
        "analysis_type": audit.analysis_type,
        "docker_analysis": bool(audit.docker_analysis_enabled),
        "callback_url": f"{os.getenv('BACKEND_URL', 'http://backend:8000')}/api/audits/{audit.id}/callback",
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(settings.ANALYSIS_WEBHOOK_URL, json=payload)
            response.raise_for_status()
    except Exception as e:
        audit.status = AuditStatus.FAILED
        audit.error_message = f"Failed to submit analysis: {str(e)}"
        db.commit()


def generate_mock_report(audit: Audit) -> str:
    import random
    from datetime import datetime

    crit = random.randint(0, 5)
    high = random.randint(1, 8)
    med = random.randint(3, 12)
    low = random.randint(5, 15)

    audit.vulnerabilities_critical = crit
    audit.vulnerabilities_high = high
    audit.vulnerabilities_medium = med
    audit.vulnerabilities_low = low

    report = f"""# Rapport d'Audit de Sécurité

**Application :** {audit.name}
**Date :** {datetime.now().strftime("%d/%m/%Y")}
**Type d'analyse :** {"Code + Docker" if audit.docker_analysis_enabled else "Code"}
**Statut :** {"Succès" if audit.docker_status != DockerStatus.FAILED else "Échec Docker"}

---

## Résumé des Vulnérabilités

| Sévérité | Nombre |
|----------|-------:|
| 🔴 Critique | {crit} |
| 🟠 Élevée | {high} |
| 🟡 Moyenne | {med} |
| 🔵 Basse | {low} |
| **Total** | **{crit + high + med + low}** |

---

## Détail par Sévérité

### 🔴 Critique ({crit} trouvée(s))

"""
    if crit > 0:
        for i in range(crit):
            report += f"""#### C-{i+1}: Injection SQL dans la connexion utilisateur
- **Fichier :** `src/login.php:45`
- **CVSS :** 9.8
- **Description :** Les entrées utilisateur ne sont pas assainies avant d'être utilisées dans une requête SQL.
- **Impact :** Accès non autorisé à la base de données, vol de données.
- **Recommandation :** Utiliser des requêtes préparées ou un ORM.

"""
    else:
        report += "*Aucune vulnérabilité critique détectée.*\n\n"

    report += f"""### 🟠 Élevée ({high} trouvée(s))

"""
    if high > 0:
        for i in range(high):
            report += f"""#### H-{i+1}: Stockage de mot de passe en clair
- **Fichier :** `src/config/database.yml:12`
- **CVSS :** 7.5
- **Description :** Les mots de passe sont stockés sans hachage dans la configuration.
- **Impact :** Compromission des identifiants en cas de fuite de données.
- **Recommandation :** Utiliser bcrypt ou argon2 pour le hachage.

"""
    else:
        report += "*Aucune vulnérabilité élevée détectée.*\n\n"

    report += f"""### 🟡 Moyenne ({med} trouvée(s))

"""
    if med > 0:
        for i in range(min(med, 3)):
            report += f"""#### M-{i+1}: Headers de sécurité manquants
- **Fichier :** `nginx.conf`
- **CVSS :** 5.0
- **Description :** Les headers X-Content-Type-Options et X-Frame-Options ne sont pas configurés.
- **Impact :** Risque de clickjacking et MIME-type sniffing.
- **Recommandation :** Ajouter les headers de sécurité dans la configuration du serveur web.

"""
    else:
        report += "*Aucune vulnérabilité moyenne détectée.*\n\n"

    report += f"""### 🔵 Basse ({low} trouvée(s))

"""
    if low > 0:
        report += """#### L-1: Version de framework obsolète
- **Fichier :** `package.json`
- **CVSS :** 2.5
- **Description :** Une version ancienne d'un framework est utilisée.
- **Impact :** Faible, mais peut exposer à des vulnérabilités connues.
- **Recommandation :** Mettre à jour vers la dernière version stable.

"""
    else:
        report += "*Aucune vulnérabilité basse détectée.*\n\n"

    if audit.docker_analysis_enabled:
        report += """---

## Analyse Docker

| Test | Statut |
|------|--------|
| Image basée sur une version sécurisée | ✅ OK |
| Pas de secret dans les layers | ✅ OK |
| Ports exposés minimaux | ✅ OK |
| Utilisateur non-root configuré | ❌ KO |
| HEALTHCHECK configuré | ❌ KO |

"""
        if audit.docker_status == DockerStatus.FAILED:
            report += """> ⚠️ **Attention :** L'installation Docker n'a pas pu être validée. Certains tests d'exploitation n'ont pas pu être réalisés.
"""
        else:
            report += """> ✅ **Succès :** L'environnement Docker a été installé et validé avec succès. Les tests d'exploitation ont été réalisés.
"""

    report += """---

## Recommandations Générales

1. **Mettre en place un pipeline de sécurité CI/CD** avec analyse statique automatique
2. **Former les développeurs** aux bonnes pratiques de sécurité (OWASP Top 10)
3. **Réaliser des audits réguliers** (au moins trimestriels)
4. **Corriger les vulnérabilités critiques** sous 24h, élevées sous 72h

---

*Rapport généré automatiquement par SAST IA - Plateforme d'Audit de Sécurité*
"""
    return report
