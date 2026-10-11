"""Inloggning och roller på servern.

Webbläsaren skickar Firebase-inloggningens ID-token som `Authorization: Bearer …`. Servern kontrollerar den med
Firebase Admin SDK (signatur, giltighet, och att kontot inte är avstängt eller utloggat). Ingen användare och ingen
nyckel är inskriven i koden:

* FIREBASE_PROJECT_ID – Firebase-projektet (vid lokal utveckling läses det ur web/.env.local om det saknas).
* ADMIN_UIDS och/eller ADMIN_EMAILS – kommaseparerade; den eller de som får använda admin-funktionerna och
  rapporterna som bara är för grundaren. E-post räknas bara om Google har verifierat den.
* FIRESTORE_DATABASE – Firestore-databasen (standard "vitki").

Admin-funktionerna (lista och stänga av konton, skicka meddelanden) behöver Googles standardbehörighet på servern
(Application Default Credentials: på Cloud Run tjänstekontot, lokalt `gcloud auth application-default login`).
"""
from __future__ import annotations

import logging
import os
import re
from functools import lru_cache
from typing import Optional

from fastapi import Depends, Header, HTTPException

logger = logging.getLogger("vitki.auth")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def project_id() -> str:
    pid = os.environ.get("FIREBASE_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT") or ""
    if not pid:  # local development: the same project as the web app
        try:
            m = re.search(r'^NEXT_PUBLIC_FIREBASE_PROJECT_ID="?([\w-]+)"?', open(os.path.join(ROOT, "web", ".env.local")).read(), re.M)
            pid = m.group(1) if m else ""
        except OSError:
            pass
    return pid


@lru_cache(maxsize=1)
def firebase_app():
    import firebase_admin
    pid = project_id()
    if not pid:
        raise HTTPException(status_code=503, detail="Inloggningen är inte konfigurerad på servern (FIREBASE_PROJECT_ID saknas).")
    try:
        return firebase_admin.get_app("vitki")
    except ValueError:
        return firebase_admin.initialize_app(options={"projectId": pid}, name="vitki")


def _split(name: str) -> set[str]:
    return {x.strip() for x in os.environ.get(name, "").split(",") if x.strip()}


def is_admin(claims: dict) -> bool:
    if claims.get("uid") in _split("ADMIN_UIDS"):
        return True
    email = (claims.get("email") or "").lower()
    return bool(email and claims.get("email_verified") and email in {e.lower() for e in _split("ADMIN_EMAILS")})


def verify(token: str) -> dict:
    """Kontrollerar en ID-token och returnerar dess uppgifter med 'admin'. Avstängda och utloggade konton nekas."""
    from firebase_admin import auth as fb_auth
    app = firebase_app()
    try:
        try:
            claims = fb_auth.verify_id_token(token, app=app, check_revoked=True)
        except (fb_auth.UserDisabledError, fb_auth.RevokedIdTokenError):
            raise
        except (fb_auth.InvalidIdTokenError, fb_auth.ExpiredIdTokenError, fb_auth.CertificateFetchError):
            raise
        except Exception as e:  # no admin credentials (local development): the token itself is still checked
            logger.warning("Kunde inte kontrollera om kontot är avstängt (%r); kontrollerar bara token.", e)
            claims = fb_auth.verify_id_token(token, app=app, check_revoked=False)
    except fb_auth.UserDisabledError:
        raise HTTPException(status_code=403, detail="Kontot är avstängt.")
    except fb_auth.RevokedIdTokenError:
        raise HTTPException(status_code=401, detail="Inloggningen har återkallats. Logga in igen.")
    except fb_auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Inloggningen har gått ut. Logga in igen.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Ogiltig inloggning.")
    return {**claims, "uid": claims.get("uid") or claims.get("sub"), "admin": is_admin(claims)}


def optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """FastAPI-beroende: den inloggade användaren, eller None om anropet saknar inloggning."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return verify(authorization.split(" ", 1)[1].strip())


def require_user(user: Optional[dict] = Depends(optional_user)) -> dict:
    if not user:
        raise HTTPException(status_code=401, detail="Logga in för att använda den här funktionen.")
    return user


def require_admin(user: Optional[dict] = Depends(optional_user)) -> dict:
    if not user or not user.get("admin"):
        raise HTTPException(status_code=403, detail="Bara för appens grundare.")
    return user


def firestore():
    """Firestore med serverns behörighet (förbi säkerhetsreglerna), för admin-funktionerna."""
    from firebase_admin import firestore as fs
    return fs.client(app=firebase_app(), database_id=os.environ.get("FIRESTORE_DATABASE", "vitki"))
