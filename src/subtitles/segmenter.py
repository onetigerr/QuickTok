"""Subtitle segmentation into single-line events."""

import logging
from typing import List

from .models import SegmentationConfig, SubtitleEvent, WordBoundary

logger = logging.getLogger(__name__)


class SubtitleSegmenter:
    """Segments words into subtitle events for single-line display."""

    def __init__(self, config: SegmentationConfig = None):
        """Initialize segmenter.

        Args:
            config: Segmentation configuration
        """
        self.config = config or SegmentationConfig()

    def segment(self, word_boundaries: List[WordBoundary]) -> List[SubtitleEvent]:
        """Segment words into subtitle events.

        Args:
            word_boundaries: List of word boundaries with timing

        Returns:
            List of subtitle events
        """
        if not word_boundaries:
            return []

        events = []
        current_words = []
        current_char_count = 0

        for i, word in enumerate(word_boundaries):
            word_length = len(word.text)

            # Check if adding this word would exceed limits
            would_exceed_chars = (
                current_char_count + word_length + len(current_words)  # spaces
                > self.config.max_chars_per_line
            )
            would_exceed_words = len(current_words) >= self.config.max_words_per_segment

            # Should we break here?
            should_break = False

            if would_exceed_chars or would_exceed_words:
                should_break = True
            elif len(current_words) >= self.config.min_words_per_segment:
                # Check if this is a good breaking point (punctuation)
                if i < len(word_boundaries) - 1:  # Not last word
                    next_word = word_boundaries[i + 1].text
                    if self._is_sentence_end(word.text):
                        should_break = True

            # Create event if we should break and have words
            if should_break and current_words:
                event = self._create_event(current_words)
                events.append(event)
                current_words = []
                current_char_count = 0

            # Add current word to buffer
            current_words.append(word)
            current_char_count += word_length

        # Add remaining words as final event
        if current_words:
            event = self._create_event(current_words)
            events.append(event)

        logger.info(f"Segmented {len(word_boundaries)} words into {len(events)} events")
        return events

    def _create_event(self, words: List[WordBoundary]) -> SubtitleEvent:
        """Create subtitle event from word list.

        Args:
            words: List of words for this event

        Returns:
            SubtitleEvent
        """
        start_time_ms = words[0].audio_offset_ms
        last_word = words[-1]
        end_time_ms = last_word.audio_offset_ms + last_word.duration_ms

        return SubtitleEvent(
            start_time_ms=start_time_ms,
            end_time_ms=end_time_ms,
            words=words,
        )

    def _is_sentence_end(self, text: str) -> bool:
        """Check if text ends with sentence-ending punctuation.

        Args:
            text: Text to check

        Returns:
            True if text ends with sentence-ending punctuation
        """
        return text.rstrip().endswith((".", "!", "?", "。", "！", "？"))
