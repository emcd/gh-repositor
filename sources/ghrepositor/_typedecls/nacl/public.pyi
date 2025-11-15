"""
Minimal type stubs for nacl.public module.
"""

from nacl import encoding

class PublicKey(encoding.Encodable):
    """
    Curve25519 public key for encrypting messages.

    :param public_key: Encoded Curve25519 public key
    :param encoder: A class that is able to decode the public_key
    """
    def __init__(self, public_key: bytes, encoder: encoding.Encoder = ...) -> None:
        ...

class PrivateKey(encoding.Encodable):
    """
    Curve25519 private key for decrypting messages.

    :param private_key: The private key used to decrypt messages
    :param encoder: The encoder class used to decode the given keys
    """
    def __init__(self, private_key: bytes, encoder: encoding.Encoder = ...) -> None:
        ...

class SealedBox(encoding.Encodable):
    """
    SealedBox encrypts messages using ephemeral sender key pairs.

    :param recipient_key: PublicKey used to encrypt or PrivateKey used to decrypt
    """
    def __init__(self, recipient_key: PublicKey | PrivateKey) -> None:
        ...

    def encrypt(self, plaintext: bytes, encoder: encoding.Encoder = ...) -> bytes:
        """
        Encrypts plaintext using a random ephemeral key pair.

        :param plaintext: The plaintext message to encrypt
        :param encoder: The encoder to use to encode the ciphertext
        :return: Encoded ciphertext
        """
        ...

    def decrypt(self, ciphertext: bytes, encoder: encoding.Encoder = ...) -> bytes:
        """
        Decrypts ciphertext using the SealedBox private key.

        :param ciphertext: The encrypted message to decrypt
        :param encoder: The encoder used to decode the ciphertext
        :return: The original plaintext
        """
        ...
