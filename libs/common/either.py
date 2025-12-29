# common/either.py
from __future__ import annotations
from typing import Callable, Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")
F = TypeVar("F")


class Either(Generic[T, E]):
    def is_right(self) -> bool:
        return isinstance(self, Right)

    def is_left(self) -> bool:
        return isinstance(self, Left)

    def map(self, func: Callable[[T], U]) -> Either[U, E]:
        if self.is_right():
            return Right(func(self.value))
        return self

    def map_left(self, func: Callable[[E], F]) -> Either[T, F]:
        if self.is_left():
            return Left(func(self.value))
        return self

    def bind(self, func: Callable[[T], Either[U, E]]) -> Either[U, E]:
        if self.is_right():
            return func(self.value)
        return self

    def unwrap(self) -> T:
        if self.is_right():
            return self.value
        raise ValueError(f"Cannot unwrap Left: {self.value}")

    def unwrap_or(self, default: T) -> T:
        return self.value if self.is_right() else default

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.value})"


class Left(Either[T, E]):
    def __init__(self, value: E) -> None:
        self.value: E = value


class Right(Either[T, E]):
    def __init__(self, value: T) -> None:
        self.value: T = value

