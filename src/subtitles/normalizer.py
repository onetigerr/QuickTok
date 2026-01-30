"""Text normalization for TTS synthesis."""

import re
import unicodedata
from enum import Enum
from typing import List

from .models import NormalizationConfig


class TokenType(str, Enum):
    """Type of text token."""

    WORD = "word"
    PUNCTUATION = "punctuation"
    WHITESPACE = "whitespace"


class Token:
    """Represents a single token from text."""

    def __init__(self, text: str, token_type: TokenType):
        """Initialize token.

        Args:
            text: Token text
            token_type: Type of token
        """
        self.text = text
        self.type = token_type

    def __repr__(self) -> str:
        return f"Token({self.text!r}, {self.type})"


class TextNormalizer:
    """Normalizes text for consistent TTS synthesis."""

    def __init__(self, config: NormalizationConfig = None):
        """Initialize text normalizer.

        Args:
            config: Normalization configuration
        """
        self.config = config or NormalizationConfig()

    def normalize(self, text: str) -> str:
        """Normalize text for TTS synthesis.

        Args:
            text: Input text to normalize

        Returns:
            Normalized text
        """
        result = text

        # Strip control characters
        if self.config.strip_control_chars:
            result = "".join(
                ch for ch in result if unicodedata.category(ch)[0] != "C" or ch in "\n\t"
            )

        # Normalize quotes
        if self.config.normalize_quotes:
            # Convert fancy quotes to standard
            result = result.replace("\u201c", '"').replace("\u201d", '"')  # Left/right double quotes
            result = result.replace("\u2018", "'").replace("\u2019", "'")  # Left/right single quotes
            result = result.replace("\u00ab", '"').replace("\u00bb", '"')  # Guillemets

        # Normalize dashes
        if self.config.normalize_dashes:
            # Convert em/en dashes to hyphen
            result = result.replace("—", "-").replace("–", "-")

        # Collapse whitespace
        if self.config.collapse_whitespace:
            result = re.sub(r"\s+", " ", result)
            result = result.strip()

        return result

    def tokenize(self, text: str) -> List[Token]:
        """Split text into word and punctuation tokens.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        tokens = []

        # Pattern to split into words, punctuation, and whitespace
        pattern = r"(\w+|[^\w\s]|\s+)"
        matches = re.finditer(pattern, text)

        for match in matches:
            token_text = match.group(0)

            if not token_text:
                continue

            # Determine token type
            if token_text.isspace():
                token_type = TokenType.WHITESPACE
            elif re.match(r"\w+", token_text):
                token_type = TokenType.WORD
            else:
                token_type = TokenType.PUNCTUATION

            tokens.append(Token(token_text, token_type))

        return tokens

    def get_word_tokens(self, text: str) -> List[str]:
        """Extract only word tokens from text.

        Args:
            text: Text to extract words from

        Returns:
            List of word strings
        """
        tokens = self.tokenize(text)
        return [token.text for token in tokens if token.type == TokenType.WORD]
