from __future__ import annotations


class RetrievaldError(Exception):
    code: str = "internal"
    http_status: int = 500

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details


class InvalidRequest(RetrievaldError):       code = "invalid_request";       http_status = 400
class IdentityRequired(RetrievaldError):     code = "identity_required";     http_status = 401
class RefNotFound(RetrievaldError):          code = "ref_not_found";         http_status = 404
class CtxUnsupported(RetrievaldError):       code = "ctx_unsupported";       http_status = 404
class NotAcceptable(RetrievaldError):        code = "not_acceptable";        http_status = 406
class UnsupportedMediaType(RetrievaldError): code = "unsupported_media_type"; http_status = 415
class UnsupportedMode(RetrievaldError):      code = "unsupported_mode";      http_status = 422
class UnsupportedDims(RetrievaldError):      code = "unsupported_dims";      http_status = 422
class BackendDegraded(RetrievaldError):      code = "backend_degraded";      http_status = 503
class BackendBusy(RetrievaldError):          code = "backend_busy";          http_status = 503
class Internal(RetrievaldError):             code = "internal";              http_status = 500
class AmbiguousSymbol(RetrievaldError):      code = "ambiguous_symbol";      http_status = 409
class UnsupportedOp(RetrievaldError):        code = "unsupported_op";        http_status = 400


def make_error_response(err: RetrievaldError, request_id: str) -> dict:
    body = {"code": err.code, "message": err.message, "request_id": request_id}
    if err.details is not None:
        body["details"] = err.details
    return {"error": body}
