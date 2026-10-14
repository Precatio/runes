"""Admin för appens grundare: registrerade konton, avstängning och meddelanden i appen.

Alla anrop kräver en inloggning med admin-roll (api/auth.py). Konton läses och stängs av med Firebase Admin SDK;
meddelanden skrivs till Firestore-samlingen `messages`, som användarna läser i appen (firestore.rules).
"""
from __future__ import annotations

import datetime as dt
from collections import Counter
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.auth import firebase_app, firestore, optional_user, require_admin
from api.errors import server_error

router = APIRouter()


@router.get("/me")
def me(user: dict | None = Depends(optional_user)):
    """Vem som är inloggad och om kontot har admin-roll (för att visa admin-sidan och alla rapporter)."""
    if not user:
        return {"signed_in": False, "admin": False}
    return {"signed_in": True, "uid": user["uid"], "email": user.get("email"), "admin": user["admin"]}


def _ms(ts) -> str | None:
    return dt.datetime.fromtimestamp(ts / 1000, dt.timezone.utc).isoformat() if ts else None


@router.get("/admin/users")
def list_users(_: dict = Depends(require_admin)):
    """Alla registrerade konton med registrering, senaste inloggning och status, och en sammanfattning."""
    from firebase_admin import auth as fb_auth
    try:
        users = list(fb_auth.list_users(app=firebase_app()).iterate_all())
    except Exception as e:
        raise server_error(e, "Kontona kunde inte hämtas. Servern behöver behörighet till Firebase "
                              "(Application Default Credentials).", status_code=503)
    now = dt.datetime.now(dt.timezone.utc).timestamp() * 1000
    day = 86_400_000
    rows = sorted(({
        "uid": u.uid, "email": u.email, "name": u.display_name, "photo": u.photo_url, "disabled": u.disabled,
        "created": _ms(u.user_metadata.creation_timestamp), "last_sign_in": _ms(u.user_metadata.last_sign_in_timestamp),
        "providers": [p.provider_id for p in u.provider_data],
    } for u in users), key=lambda r: r["created"] or "", reverse=True)
    created = [u.user_metadata.creation_timestamp or 0 for u in users]
    last = [u.user_metadata.last_sign_in_timestamp or 0 for u in users]
    per_month = Counter(r["created"][:7] for r in rows if r["created"])
    return {
        "summary": {"total": len(users), "disabled": sum(u.disabled for u in users),
                    "new_7d": sum(c > now - 7 * day for c in created), "new_30d": sum(c > now - 30 * day for c in created),
                    "active_30d": sum(t > now - 30 * day for t in last)},
        "per_month": dict(sorted(per_month.items())),
        "users": rows,
    }


class BanRequest(BaseModel):
    reason: str = Field("", max_length=500)


@router.post("/admin/users/{uid}/ban")
def ban_user(uid: str, req: BanRequest, admin: dict = Depends(require_admin)):
    """Stänger av kontot: det kan inte logga in, pågående inloggningar återkallas och Firestore nekar det åtkomst."""
    from firebase_admin import auth as fb_auth
    if uid == admin["uid"]:
        raise HTTPException(status_code=400, detail="Du kan inte stänga av ditt eget konto.")
    try:
        fb_auth.update_user(uid, disabled=True, app=firebase_app())
        fb_auth.revoke_refresh_tokens(uid, app=firebase_app())
        firestore().collection("banned").document(uid).set(
            {"reason": req.reason, "at": dt.datetime.now(dt.timezone.utc), "by": admin["uid"]})
    except fb_auth.UserNotFoundError:
        raise HTTPException(status_code=404, detail="Kontot finns inte.")
    except Exception as e:
        raise server_error(e, "Kontot kunde inte stängas av.", status_code=503)
    return {"uid": uid, "disabled": True}


@router.post("/admin/users/{uid}/unban")
def unban_user(uid: str, _: dict = Depends(require_admin)):
    from firebase_admin import auth as fb_auth
    try:
        fb_auth.update_user(uid, disabled=False, app=firebase_app())
        firestore().collection("banned").document(uid).delete()
    except fb_auth.UserNotFoundError:
        raise HTTPException(status_code=404, detail="Kontot finns inte.")
    except Exception as e:
        raise server_error(e, "Kontot kunde inte öppnas igen.", status_code=503)
    return {"uid": uid, "disabled": False}


class MessageRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    body: str = Field(..., min_length=1, max_length=4000)
    to: str = Field("all", max_length=128)  # "all" or a user's uid
    level: Literal["info", "viktigt"] = "info"


# The messages to everyone, for the bell in the top bar: read on the server and kept for a minute, so that visitors who
# are not signed in do not need to load Firestore in the browser (web/src/components/Messages.tsx)
_PUBLIC: dict = {"at": 0.0, "messages": None}


@router.get("/messages")
def public_messages():
    """Meddelandena till alla, nyaste först (utan avsändarens konto)."""
    import time
    if _PUBLIC["messages"] is not None and time.time() - _PUBLIC["at"] < 60:
        return {"messages": _PUBLIC["messages"]}
    try:
        docs = firestore().collection("messages").where("to", "==", "all").stream()
        msgs = [{"id": d.id, **{k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in d.to_dict().items()
                                if k in ("title", "body", "to", "level", "createdAt")}} for d in docs]
    except Exception as e:
        raise server_error(e, "Meddelandena kunde inte hämtas.", status_code=503)
    msgs.sort(key=lambda m: m.get("createdAt") or "", reverse=True)
    _PUBLIC.update(at=time.time(), messages=msgs)
    return {"messages": msgs}


@router.get("/admin/github")
def github(refresh: bool = False, _: dict = Depends(require_admin)):
    """Repots statistik på GitHub: stjärnor, forkar, releaser och, med GITHUB_TOKEN, kloner och besök (src/github_stats.py)."""
    from src import github_stats
    try:
        return github_stats.stats(refresh)
    except Exception as e:  # noqa: BLE001
        raise server_error(e, "GitHub svarar inte just nu.", status_code=503)


@router.get("/admin/messages")
def list_messages(_: dict = Depends(require_admin)):
    try:
        docs = firestore().collection("messages").order_by("createdAt", direction="DESCENDING").limit(100).stream()
        return {"messages": [{"id": d.id, **{k: (v.isoformat() if hasattr(v, "isoformat") else v)
                                              for k, v in d.to_dict().items()}} for d in docs]}
    except Exception as e:
        raise server_error(e, "Meddelandena kunde inte hämtas.", status_code=503)


@router.post("/admin/messages")
def send_message(req: MessageRequest, admin: dict = Depends(require_admin)):
    """Ett meddelande i appen till alla eller till ett konto; det visas under klockan i sidhuvudet."""
    data = {"title": req.title.strip(), "body": req.body.strip(), "to": req.to or "all", "level": req.level,
            "createdAt": dt.datetime.now(dt.timezone.utc), "from": "Vitki", "by": admin["uid"]}
    try:
        ref = firestore().collection("messages").document()
        ref.set(data)
        _PUBLIC.update(at=0.0, messages=None)
    except Exception as e:
        raise server_error(e, "Meddelandet kunde inte skickas.", status_code=503)
    return {"id": ref.id, **{k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in data.items()}}


@router.delete("/admin/messages/{message_id}")
def delete_message(message_id: str, _: dict = Depends(require_admin)):
    try:
        firestore().collection("messages").document(message_id).delete()
        _PUBLIC.update(at=0.0, messages=None)
    except Exception as e:
        raise server_error(e, "Meddelandet kunde inte tas bort.", status_code=503)
    return {"id": message_id, "deleted": True}


@router.get("/admin/site/votes")
def site_votes(_: dict = Depends(require_admin)):
    """Röstningen på den publika webbplatsen (web/src/components/SiteVote.tsx): antal röster per fråga och svar, och
    när den första och den senaste rösten kom. Rösterna läses med serverns egen behörighet; webbläsare kan inte läsa dem."""
    try:
        docs = list(firestore().collection("site_votes").stream())
    except Exception as e:  # noqa: BLE001
        raise server_error(e, "Rösterna kunde inte hämtas.", status_code=503)
    by: dict[str, Counter] = {}
    times: dict[str, list] = {}
    for d in docs:
        v = d.to_dict() or {}
        q = v.get("question", "?")
        by.setdefault(q, Counter())[v.get("choice", "?")] += 1
        if d.create_time:
            times.setdefault(q, []).append(d.create_time)
    return {"questions": [{"question": q, "total": sum(c.values()), "choices": dict(c),
                           "first": min(times[q]).isoformat() if times.get(q) else None,
                           "last": max(times[q]).isoformat() if times.get(q) else None} for q, c in by.items()]}
