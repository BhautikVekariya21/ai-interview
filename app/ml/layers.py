"""
Custom PyTorch layers for the NER model.
Includes a CRF decoder and multi-head self-attention block.
"""

from __future__ import annotations

from typing import Optional

import torch
from torch import nn


class CRFLayer(nn.Module):
    """Linear-chain CRF for batched sequence labeling."""

    def __init__(self, num_tags: int):
        super().__init__()
        self.num_tags = num_tags
        self.transition_params = nn.Parameter(torch.empty(num_tags, num_tags))
        nn.init.xavier_uniform_(self.transition_params)

    def viterbi_decode(
        self,
        emissions: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        if emissions.ndim != 3:
            raise ValueError("emissions must have shape (batch, seq, tags)")

        batch_size, seq_len, _ = emissions.shape
        if mask is None:
            mask = torch.ones(
                batch_size, seq_len, dtype=torch.bool, device=emissions.device
            )
        else:
            mask = mask.to(dtype=torch.bool, device=emissions.device)

        score = emissions[:, 0, :]
        history = []

        for t in range(1, seq_len):
            transition_scores = score.unsqueeze(2) + self.transition_params.unsqueeze(0)
            best_score, best_path = transition_scores.max(dim=1)
            next_score = best_score + emissions[:, t, :]
            mask_t = mask[:, t].unsqueeze(1)
            score = torch.where(mask_t, next_score, score)
            history.append(best_path)

        best_last_tags = score.argmax(dim=1)
        best_paths = emissions.new_zeros((batch_size, seq_len), dtype=torch.long)
        best_paths[:, -1] = best_last_tags

        for step in range(seq_len - 2, -1, -1):
            if step < len(history):
                backpointer = history[step]
                prev_tags = backpointer.gather(1, best_last_tags.unsqueeze(1)).squeeze(1)
                valid = mask[:, step + 1]
                best_last_tags = torch.where(valid, prev_tags, best_last_tags)
            best_paths[:, step] = best_last_tags

        return best_paths

    def log_likelihood(
        self,
        emissions: torch.Tensor,
        tags: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        batch_size, seq_len, _ = emissions.shape
        if mask is None:
            mask = torch.ones(
                batch_size, seq_len, dtype=torch.bool, device=emissions.device
            )
        else:
            mask = mask.to(dtype=torch.bool, device=emissions.device)

        gold_score = self._compute_score(emissions, tags, mask)
        partition = self._compute_log_partition(emissions, mask)
        return (gold_score - partition).mean()

    def _compute_score(
        self,
        emissions: torch.Tensor,
        tags: torch.Tensor,
        mask: torch.Tensor,
    ) -> torch.Tensor:
        batch_size, seq_len, _ = emissions.shape
        batch_index = torch.arange(batch_size, device=emissions.device)
        score = emissions[batch_index, 0, tags[:, 0]]

        for t in range(1, seq_len):
            mask_t = mask[:, t]
            emit_t = emissions[batch_index, t, tags[:, t]]
            trans_t = self.transition_params[tags[:, t - 1], tags[:, t]]
            score = score + (emit_t + trans_t) * mask_t

        return score

    def _compute_log_partition(
        self,
        emissions: torch.Tensor,
        mask: torch.Tensor,
    ) -> torch.Tensor:
        score = emissions[:, 0, :]
        seq_len = emissions.size(1)

        for t in range(1, seq_len):
            transition_scores = score.unsqueeze(2) + self.transition_params.unsqueeze(0)
            next_score = torch.logsumexp(transition_scores, dim=1) + emissions[:, t, :]
            mask_t = mask[:, t].unsqueeze(1)
            score = torch.where(mask_t, next_score, score)

        return torch.logsumexp(score, dim=1)


class MultiHeadSelfAttention(nn.Module):
    """Thin wrapper around PyTorch multi-head self-attention."""

    def __init__(self, embed_dim: int, num_heads: int = 4):
        super().__init__()
        if embed_dim % num_heads != 0:
            raise ValueError("embed_dim must be divisible by num_heads")
        self.attention = nn.MultiheadAttention(
            embed_dim=embed_dim,
            num_heads=num_heads,
            dropout=0.1,
            batch_first=True,
        )
        self.output_proj = nn.Linear(embed_dim, embed_dim)

    def forward(
        self,
        inputs: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        key_padding_mask = None
        if mask is not None:
            key_padding_mask = ~mask.to(dtype=torch.bool, device=inputs.device)
        attended, _ = self.attention(
            inputs,
            inputs,
            inputs,
            key_padding_mask=key_padding_mask,
            need_weights=False,
        )
        return self.output_proj(attended)
