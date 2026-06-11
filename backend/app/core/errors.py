from fastapi import HTTPException, status


class ApiError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(status_code=status_code, detail={"code": code, "message": message})


def invalid_credentials() -> ApiError:
    return ApiError(status.HTTP_401_UNAUTHORIZED, "INVALID_CREDENTIALS", "Invalid email or password")


def unauthorized(message: str = "Authentication required") -> ApiError:
    return ApiError(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", message)


def forbidden(code: str, message: str) -> ApiError:
    return ApiError(status.HTTP_403_FORBIDDEN, code, message)


def bad_request(code: str, message: str) -> ApiError:
    return ApiError(status.HTTP_400_BAD_REQUEST, code, message)


def conflict(code: str, message: str) -> ApiError:
    return ApiError(status.HTTP_409_CONFLICT, code, message)
