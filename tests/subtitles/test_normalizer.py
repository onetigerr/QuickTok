"""Tests for text normalizer."""

import pytest

from src.subtitles.normalizer import TextNormalizer, Token, TokenType
from src.subtitles.models import NormalizationConfig


def test_normalize_whitespace():
    """Test whitespace normalization."""
    normalizer = TextNormalizer()
    text = "Hello    world  \n  test"
    result = normalizer.normalize(text)
    assert result == "Hello world test"


def test_normalize_quotes():
    """Test quote normalization."""
    normalizer = TextNormalizer()
    # Using fancy left/right quotes
    text = chr(0x201C) + "Hello" + chr(0x201D)
    result = normalizer.normalize(text)
    # Should not contain fancy quotes
    assert all(ord(c) != 0x201C and ord(c) != 0x201D for c in result)
    # Should contain standard quote (0x22)
    assert chr(0x22) in result


def test_normalize_dashes():
    """Test dash normalization."""
    normalizer = TextNormalizer()
    text = "Test—dash–example"
    result = normalizer.normalize(text)
    assert result == "Test-dash-example"


def test_tokenize_basic():
    """Test basic tokenization."""
    normalizer = TextNormalizer()
    text = "Hello world!"
    tokens = normalizer.tokenize(text)

    assert len(tokens) == 4
    assert tokens[0].text == "Hello"
    assert tokens[0].type == TokenType.WORD
    assert tokens[1].text == " "
    assert tokens[1].type == TokenType.WHITESPACE
    assert tokens[2].text == "world"
    assert tokens[2].type == TokenType.WORD
    assert tokens[3].text == "!"
    assert tokens[3].type == TokenType.PUNCTUATION


def test_tokenize_mixed():
    """Test tokenization with mixed content."""
    normalizer = TextNormalizer()
    text = "Hello, world! Test123."
    tokens = normalizer.tokenize(text)

    word_tokens = [t for t in tokens if t.type == TokenType.WORD]
    punct_tokens = [t for t in tokens if t.type == TokenType.PUNCTUATION]

    assert len(word_tokens) == 3
    assert len(punct_tokens) == 3


def test_get_word_tokens():
    """Test extraction of word tokens only."""
    normalizer = TextNormalizer()
    text = "Hello, world! How are you?"
    words = normalizer.get_word_tokens(text)

    assert words == ["Hello", "world", "How", "are", "you"]


def test_config_disable_whitespace_collapse():
    """Test disabling whitespace collapse."""
    config = NormalizationConfig(collapse_whitespace=False)
    normalizer = TextNormalizer(config)
    text = "Hello    world"
    result = normalizer.normalize(text)
    assert result == "Hello    world"


def test_config_disable_quote_normalization():
    """Test disabling quote normalization."""
    config = NormalizationConfig(normalize_quotes=False)
    normalizer = TextNormalizer(config)
    text = "\u201cHello\u201d"
    result = normalizer.normalize(text)
    assert result == "\u201cHello\u201d"
