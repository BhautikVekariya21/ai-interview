"""
BiLSTM-Attention-CRF NER model built with PyTorch.
Designed for resume entity recognition with the existing BIO tag scheme.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

import numpy as np
import torch
from loguru import logger
from torch import nn

from app.core.config import settings
from app.ml.layers import CRFLayer, MultiHeadSelfAttention


NER_TAGS = [
    "O", "B-NAME", "I-NAME", "B-EMAIL", "I-EMAIL", "B-PHONE", "I-PHONE",
    "B-LOCATION", "I-LOCATION", "B-URL", "I-URL", "B-DEGREE", "I-DEGREE",
    "B-INSTITUTION", "I-INSTITUTION", "B-FIELD", "I-FIELD", "B-GPA", "I-GPA",
    "B-DATE", "I-DATE", "B-COMPANY", "I-COMPANY", "B-ROLE", "I-ROLE",
    "B-SKILL", "I-SKILL", "B-PROJECT", "I-PROJECT", "B-CERT", "I-CERT",
    "B-ACHIEVEMENT", "I-ACHIEVEMENT", "B-PUBLICATION", "I-PUBLICATION", "PAD",
]

TAG_TO_IDX = {tag: idx for idx, tag in enumerate(NER_TAGS)}
IDX_TO_TAG = {idx: tag for tag, idx in TAG_TO_IDX.items()}
NUM_TAGS = len(NER_TAGS)


class ResumeNERTagger(nn.Module):
    """PyTorch module for token-level emission scoring."""

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int,
        lstm_units: int,
        dropout_rate: float,
        num_tags: int,
        pad_idx: int = 0,
    ):
        super().__init__()
        hidden_size = max(1, lstm_units // 2)
        output_dim = hidden_size * 2

        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=pad_idx)
        self.embedding_dropout = nn.Dropout(dropout_rate)
        self.lstm_1 = nn.LSTM(
            embedding_dim, hidden_size, batch_first=True, bidirectional=True
        )
        self.norm_1 = nn.LayerNorm(output_dim)
        self.lstm_2 = nn.LSTM(
            output_dim, hidden_size, batch_first=True, bidirectional=True
        )
        self.norm_2 = nn.LayerNorm(output_dim)
        self.self_attention = MultiHeadSelfAttention(embed_dim=output_dim, num_heads=4)
        self.residual_norm = nn.LayerNorm(output_dim)
        self.dropout = nn.Dropout(dropout_rate)
        self.projection = nn.Linear(output_dim, hidden_size)
        self.projection_activation = nn.ReLU()
        self.dropout_2 = nn.Dropout(dropout_rate / 2)
        self.emission_head = nn.Linear(hidden_size, num_tags)

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        mask = input_ids != 0
        lengths = mask.sum(dim=1).clamp(min=1).cpu()

        x = self.embedding(input_ids)
        x = self.embedding_dropout(x)

        packed = nn.utils.rnn.pack_padded_sequence(
            x, lengths, batch_first=True, enforce_sorted=False
        )
        packed_out, _ = self.lstm_1(packed)
        x, _ = nn.utils.rnn.pad_packed_sequence(
            packed_out, batch_first=True, total_length=input_ids.size(1)
        )
        x = self.norm_1(x)

        packed = nn.utils.rnn.pack_padded_sequence(
            x, lengths, batch_first=True, enforce_sorted=False
        )
        packed_out, _ = self.lstm_2(packed)
        x, _ = nn.utils.rnn.pad_packed_sequence(
            packed_out, batch_first=True, total_length=input_ids.size(1)
        )
        x = self.norm_2(x)

        attention_output = self.self_attention(x, mask=mask)
        x = self.residual_norm(x + attention_output)
        x = self.dropout(x)
        x = self.projection_activation(self.projection(x))
        x = self.dropout_2(x)
        return self.emission_head(x)


class ResumeNERModel:
    """Wrapper preserving the previous model API while using PyTorch internals."""

    def __init__(
        self,
        vocab_size: int = 50000,
        embedding_dim: int = None,
        lstm_units: int = None,
        dropout_rate: float = None,
        max_seq_length: int = None,
    ):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim or settings.EMBEDDING_DIM
        self.lstm_units = lstm_units or settings.LSTM_UNITS
        self.dropout_rate = dropout_rate or settings.DROPOUT_RATE
        self.max_seq_length = max_seq_length or settings.MAX_SEQUENCE_LENGTH
        self.num_tags = NUM_TAGS
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.model: Optional[ResumeNERTagger] = None
        self.optimizer: Optional[torch.optim.Optimizer] = None
        self.word_to_idx: Dict[str, int] = {"<PAD>": 0, "<UNK>": 1}
        self.idx_to_word: Dict[int, str] = {0: "<PAD>", 1: "<UNK>"}
        self.crf_layer = CRFLayer(num_tags=self.num_tags).to(self.device)

    def build_model(self) -> ResumeNERTagger:
        logger.info("Building PyTorch BiLSTM-Attention-CRF NER model...")
        self.model = ResumeNERTagger(
            vocab_size=self.vocab_size,
            embedding_dim=self.embedding_dim,
            lstm_units=self.lstm_units,
            dropout_rate=self.dropout_rate,
            num_tags=self.num_tags,
        ).to(self.device)
        logger.info("NER model built successfully")
        return self.model

    def compile_model(self):
        if self.model is None:
            self.build_model()
        params = list(self.model.parameters()) + list(self.crf_layer.parameters())
        self.optimizer = torch.optim.Adam(params, lr=settings.LEARNING_RATE)
        logger.info("NER model optimizer configured")

    def _crf_loss(self, tags: torch.Tensor, emissions: torch.Tensor) -> torch.Tensor:
        mask = tags != TAG_TO_IDX["PAD"]
        return -self.crf_layer.log_likelihood(emissions, tags, mask)

    def predict_tags(self, token_ids: np.ndarray) -> List[List[str]]:
        if self.model is None:
            raise RuntimeError("NER model has not been built")

        self.model.eval()
        token_tensor = torch.as_tensor(token_ids, dtype=torch.long, device=self.device)
        mask = token_tensor != 0

        with torch.no_grad():
            emissions = self.model(token_tensor)
            best_paths = self.crf_layer.viterbi_decode(emissions, mask)

        best_paths = best_paths.cpu().numpy()
        results: List[List[str]] = []
        for i in range(len(token_ids)):
            seq_tags = []
            for j in range(len(token_ids[i])):
                if token_ids[i][j] == 0:
                    break
                seq_tags.append(IDX_TO_TAG.get(int(best_paths[i][j]), "O"))
            results.append(seq_tags)
        return results

    def build_vocabulary(self, texts: List[List[str]]):
        word_freq: Dict[str, int] = {}
        for tokens in texts:
            for token in tokens:
                token_lower = token.lower()
                word_freq[token_lower] = word_freq.get(token_lower, 0) + 1

        sorted_words = sorted(
            word_freq.items(), key=lambda item: item[1], reverse=True
        )[: self.vocab_size - 2]

        for idx, (word, _) in enumerate(sorted_words, start=2):
            self.word_to_idx[word] = idx
            self.idx_to_word[idx] = word

        logger.info(f"Vocabulary built: {len(self.word_to_idx)} words")

    def tokens_to_ids(self, tokens: List[str]) -> np.ndarray:
        ids = [self.word_to_idx.get(token.lower(), 1) for token in tokens[: self.max_seq_length]]
        ids.extend([0] * (self.max_seq_length - len(ids)))
        return np.array(ids, dtype=np.int32)

    def save(self, path: str):
        if self.model is None:
            raise RuntimeError("Cannot save before building the model")

        os.makedirs(path, exist_ok=True)
        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "crf_state_dict": self.crf_layer.state_dict(),
            },
            os.path.join(path, "model_state.pt"),
        )

        vocab_data = {
            "word_to_idx": self.word_to_idx,
            "config": {
                "vocab_size": self.vocab_size,
                "embedding_dim": self.embedding_dim,
                "lstm_units": self.lstm_units,
                "dropout_rate": self.dropout_rate,
                "max_seq_length": self.max_seq_length,
            },
        }
        with open(os.path.join(path, "vocab.json"), "w", encoding="utf-8") as file:
            json.dump(vocab_data, file)

        logger.info(f"Model saved to {path}")

    def load(self, path: str):
        vocab_path = os.path.join(path, "vocab.json")
        if os.path.exists(vocab_path):
            with open(vocab_path, "r", encoding="utf-8") as file:
                vocab_data = json.load(file)
            self.word_to_idx = vocab_data["word_to_idx"]
            self.idx_to_word = {idx: word for word, idx in self.word_to_idx.items()}
            config = vocab_data.get("config", {})
            self.vocab_size = int(config.get("vocab_size", self.vocab_size))
            self.embedding_dim = int(config.get("embedding_dim", self.embedding_dim))
            self.lstm_units = int(config.get("lstm_units", self.lstm_units))
            self.dropout_rate = float(config.get("dropout_rate", self.dropout_rate))
            self.max_seq_length = int(config.get("max_seq_length", self.max_seq_length))
            logger.info(f"Vocabulary loaded: {len(self.word_to_idx)} words")

        self.build_model()
        self.compile_model()

        weights_path = os.path.join(path, "model_state.pt")
        if os.path.exists(weights_path):
            # weights_only=True restricts unpickling to plain tensors/state-dicts,
            # preventing arbitrary code execution (CWE-502) if a checkpoint file
            # is ever tampered with or sourced from an untrusted location.
            checkpoint = torch.load(weights_path, map_location=self.device, weights_only=True)
            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.crf_layer.load_state_dict(checkpoint["crf_state_dict"])
            self.model.eval()
            logger.info(f"Model weights loaded from {weights_path}")
        else:
            logger.warning(f"No weights found at {weights_path}, using random initialization")
