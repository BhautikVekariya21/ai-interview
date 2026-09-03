"""
NER inference engine. Loads the trained model and runs
entity recognition on preprocessed resume text.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from loguru import logger

try:
    from app.models.ner_model import (
        ResumeNERModel,
        IDX_TO_TAG,
        TAG_TO_IDX,
    )
except Exception as import_error:  # pragma: no cover - env dependent
    ResumeNERModel = None  # type: ignore[assignment]
    IDX_TO_TAG = ["O"]
    TAG_TO_IDX = {"O": 0}
    logger.warning(
        "PyTorch-backed NER model import unavailable; "
        "falling back to rule-based extraction only. "
        f"Import error: {import_error}"
    )
from app.core.config import settings
from app.core.exceptions import NERModelError, NERModelNotFoundError


class NEREngine:
    """
    Inference wrapper for the trained BiLSTM-CRF NER model.
    Handles tokenization, prediction, and entity aggregation.
    """

    def __init__(self):
        self.model: Optional[ResumeNERModel] = None
        self._is_loaded = False
        logger.info("NEREngine initialized")

    def load_model(self):
        """Load the trained NER model."""
        if ResumeNERModel is None:
            self._is_loaded = False
            return
        try:
            self.model = ResumeNERModel()
            self.model.load(settings.NER_MODEL_PATH)
            self._is_loaded = True
            logger.info("NER model loaded successfully")
        except Exception as e:
            logger.warning(
                f"Could not load NER model: {e}. "
                "Will use rule-based extraction only."
            )
            self._is_loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def predict(
        self, lines: List[str], tokens_per_line: List[List[str]]
    ) -> List[Dict]:
        """
        Run NER prediction on preprocessed lines.
        
        Args:
            lines: List of text lines
            tokens_per_line: Tokenized version of each line
            
        Returns:
            List of entity dicts with keys:
                - text: entity text
                - label: entity type (NAME, SKILL, etc.)
                - start_token: start token index
                - end_token: end token index
                - line_idx: which line it was found in
                - confidence: prediction confidence
        """
        if not self._is_loaded:
            logger.warning(
                "NER model not loaded, returning empty predictions"
            )
            return []

        all_entities = []

        # Process in batches
        batch_size = 32
        for batch_start in range(0, len(tokens_per_line), batch_size):
            batch_tokens = tokens_per_line[
                batch_start: batch_start + batch_size
            ]

            # Convert to IDs
            batch_ids = np.array([
                self.model.tokens_to_ids(tokens)
                for tokens in batch_tokens
            ])

            # Predict
            try:
                tag_sequences = self.model.predict_tags(batch_ids)
            except Exception as e:
                logger.error(f"NER prediction failed: {e}")
                continue

            # Extract entities from BIO tags
            for i, (tokens, tags) in enumerate(
                zip(batch_tokens, tag_sequences)
            ):
                line_idx = batch_start + i
                entities = self._extract_entities_from_bio(
                    tokens, tags, line_idx
                )
                all_entities.extend(entities)

        logger.info(f"NER extracted {len(all_entities)} entities")
        return all_entities

    def _extract_entities_from_bio(
        self,
        tokens: List[str],
        tags: List[str],
        line_idx: int,
    ) -> List[Dict]:
        """
        Convert BIO tag sequence to entity spans.
        
        BIO scheme:
            B-XXX = Beginning of entity XXX
            I-XXX = Inside entity XXX
            O = Outside any entity
        """
        entities = []
        current_entity = None
        current_tokens = []
        start_idx = 0

        for j, (token, tag) in enumerate(zip(tokens, tags)):
            if tag.startswith("B-"):
                # Save previous entity if exists
                if current_entity:
                    entities.append({
                        "text": " ".join(current_tokens),
                        "label": current_entity,
                        "start_token": start_idx,
                        "end_token": j - 1,
                        "line_idx": line_idx,
                        "confidence": 0.8,  # Default from model
                    })

                # Start new entity
                current_entity = tag[2:]
                current_tokens = [token]
                start_idx = j

            elif tag.startswith("I-") and current_entity == tag[2:]:
                # Continue current entity
                current_tokens.append(token)

            else:
                # O tag or mismatched I tag
                if current_entity:
                    entities.append({
                        "text": " ".join(current_tokens),
                        "label": current_entity,
                        "start_token": start_idx,
                        "end_token": j - 1,
                        "line_idx": line_idx,
                        "confidence": 0.8,
                    })
                    current_entity = None
                    current_tokens = []

        # Don't forget last entity
        if current_entity:
            entities.append({
                "text": " ".join(current_tokens),
                "label": current_entity,
                "start_token": start_idx,
                "end_token": len(tokens) - 1,
                "line_idx": line_idx,
                "confidence": 0.8,
            })

        return entities
