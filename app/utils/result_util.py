from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")

class Result(Generic[T, E]):
    def unwrap_or_raise(self) -> T:

        # Note: match is only valid on python 3.10 and above
        match self:
            case Ok(d):
                return d
            case Error(e):
                raise e

@dataclass(frozen=True)
class Ok(Result[T,E]):
    data: T

@dataclass(frozen=True)
class Error(Result[T,E]):
    error: E