from __future__ import annotations

import hashlib
import json

from ragfusion.retrievald.errors import IdentityRequired


class CallerIdentity:
    def __init__(self, login: str, name: str | None):
        self.login = login
        self.name = name


def extract_identity(headers, default_login=None) -> CallerIdentity:
    """Identify the caller from the tailnet-injected header.

    `default_login` is an opt-in fallback (RETRIEVALD_DEFAULT_IDENTITY) for running
    retrievald WITHOUT the `tailscale serve` proxy — local dev and the static eval
    stand-up. It is None in production, so a missing header still 401s.
    """
    login = headers.get("Tailscale-User-Login") or default_login
    if not login:
        raise IdentityRequired("missing Tailscale-User-Login header")
    return CallerIdentity(login, headers.get("Tailscale-User-Name"))


def _h(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def audit_log(logger, identity, request_id, repo, ref, op, stale,
              text=None, symbol=None, log_raw=False) -> None:
    rec = {"caller": identity.login, "request_id": request_id,
           "repo": repo, "ref": ref, "op": op, "stale": stale}
    if text is not None:
        rec.update({"text": text} if log_raw else {"text_sha256": _h(text), "text_len": len(text)})
    if symbol is not None:
        rec.update({"symbol": symbol} if log_raw
                   else {"symbol_sha256": _h(symbol), "symbol_len": len(symbol)})
    logger.info(json.dumps(rec))
