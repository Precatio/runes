"""Felhantering: logga detaljer på servern, skicka generiska meddelanden till klienten."""
import logging

from fastapi import HTTPException

logger = logging.getLogger("runforskning")

QUOTA_MESSAGE = "API-kvoten för AI-motorn är tillfälligt slut. Vänligen vänta en minut och försök igen!"
AUTH_MESSAGE = "API-nyckeln avvisades. Kontrollera nyckeln under Inställningar."


def server_error(e: Exception, message: str, status_code: int = 500) -> HTTPException:
    logger.error("%s: %r", message, e, exc_info=e)
    return HTTPException(status_code=status_code, detail=message)


def ai_error(e: Exception, message: str = "Ett oväntat fel uppstod i AI-motorn.") -> HTTPException:
    text = str(e).lower()
    if "402" in text or "prepayment" in text or "credits are depleted" in text:
        logger.warning("AI credits depleted: %r", e)
        return HTTPException(status_code=402, detail=(
            "AI-kontots förbetalda krediter är slut. Fyll på i Google AI Studio (ai.studio/projects) eller använd en "
            "annan API-nyckel under Inställningar."))
    if "429" in text or "quota" in text or "exhausted" in text:
        logger.warning("AI quota exceeded: %r", e)
        return HTTPException(status_code=429, detail=QUOTA_MESSAGE)
    if "api key" in text or "api_key" in text or "401" in text or "permission_denied" in text:
        logger.warning("AI auth failed: %r", e)
        return HTTPException(status_code=401, detail=AUTH_MESSAGE)
    return server_error(e, message)
