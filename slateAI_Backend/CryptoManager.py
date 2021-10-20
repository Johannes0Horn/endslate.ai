"""A class that handles encryption and decryption of strings and files.
"""

from Crypto import Random
from Crypto.Cipher import AES
import sys
from typing import Union

class CryptoManager:
    """Encrypts / decrypts strings and files.

    Attributes:
        key: The encryption key for all cryptographic operations.
    """

    def __init__(self, key: str = b"ieox261hca2(*292"):
        """Initializes the CryptoManager and its key.

        Default key length must be exactly 16 ASCII symbols.
        The key must be converted to byte format 16 byte.

        Args:
            key: The encryption key for all cryptographic operations.
        """

        self.key = key

    def pad(self, message: bytes) -> bytes:
        """Pads a byte message for AES.

        Args:
            message: Message to be padded.

        Returns:
            Appropriately padded message.
        """

        return message + b"\0" * (AES.block_size - len(message) % AES.block_size)

    def encrypt(self, message: bytes) -> bytes:
        """Encrypts a byte message using AES.

        Args:
            message: The message in need of encryption in byte form.

        Returns:
            Encrypted message.
        """

        message = self.pad(message)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(message)

    def encrypt_string(self, message: str) -> bytes:
        """Encrypts a string message using AES.

        Args:
            message: The message string in need of encryption.

        Returns:
            The encrypted message.
        """

        return self.encrypt(bytes(message, 'utf-8'))

    def decrypt(self, message: bytes) -> bytes:
        """Decrypts an AES encrypted message.

        Args:
            message: The message in need of decryption in byte form.

        Returns:
            The decrypted message as bytes.
        """

        iv = message[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        plaintext = cipher.decrypt(message[AES.block_size:])
        return plaintext.rstrip(b"\0")

    def decrypt_string(self, message: bytes) -> str:
        """Decrypts an AES encrypted message into a string.

        Args:
            message: The message in need of decryption in byte form.

        Returns:
            The decrypted message as a string.
        """

        return self.decrypt(message).decode("utf-8")

    def encrypt_file(self, file_path: str):
        """Encrypts the text inside a file using AES.

        Args:
            file_path: The path to the file in need of encryption.
        """

        with open(file_path, 'rb') as f:
            plaintext = f.read()

        enc = self.encrypt(plaintext)

        with open(file_path + ".enc", 'wb') as f:
            f.write(enc)

    def decrypt_file(self, file_path: str):
        """Decrypts the AES encrypted text inside a file.

        Args:
            file_path: The path to the file in need of decryption.
        """

        with open(file_path, 'rb') as f:
            ciphertext = f.read()

        dec = self.decrypt(ciphertext)

        with open(file_path[:-4], 'wb') as f:
            f.write(dec)

    def get_encrypted_string_from_file(self, file_path: str) -> Union[str, bool]:
        """Decrypts the AES encrypted text from a file and returns it.

        Args:
            file_path: The path to the file in need of decryption.

        Returns:
            The decrypted text from the file.
        """

        try:
            with open(file_path, 'rb') as fo:
                ciphertext = fo.read()
            return self.decrypt_string(ciphertext)
        except:
            print("Error:", sys.exc_info()[0])
            return False

    def write_encrypted_string_to_file(self, file_path: str, message: str):
        """Encrypts a message into a file using AES.

        Args:
            file_path: The path to the file the encrypted message needs to be saved in.
            message: The message in need of encryption.
        """

        encrypted_string = self.encrypt_string(message)
        with open(file_path, 'wb') as f:
            f.write(encrypted_string)
