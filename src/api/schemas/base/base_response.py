from typing import Generic, TypeVar, Optional
from pydantic import BaseModel
from api.schemas.base.error_detail import ErrorDetail

T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None

    @classmethod
    def ok(cls, data: T) -> "BaseResponse[T]":
        return cls(success=True, data=data, error=None)

    @classmethod
    def fail(cls, code: str, message: str) -> "BaseResponse":
        return cls(success=False, data=None, error=ErrorDetail(code=code, message=message))
