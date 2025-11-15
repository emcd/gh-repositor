"""
Minimal type stubs for nacl.encoding module.
"""

from abc import ABCMeta, abstractmethod
from typing import SupportsBytes, Type

class _Encoder(metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def encode(data: bytes) -> bytes:
        """Transform raw data to encoded data."""
        ...

    @staticmethod
    @abstractmethod
    def decode(data: bytes) -> bytes:
        """Transform encoded data back to raw data."""
        ...

Encoder = Type[_Encoder]

class RawEncoder(_Encoder):
    @staticmethod
    def encode(data: bytes) -> bytes:
        ...

    @staticmethod
    def decode(data: bytes) -> bytes:
        ...

class Base64Encoder(_Encoder):
    @staticmethod
    def encode(data: bytes) -> bytes:
        ...

    @staticmethod
    def decode(data: bytes) -> bytes:
        ...

class Encodable:
    def encode(self: SupportsBytes, encoder: Encoder = ...) -> bytes:
        ...
