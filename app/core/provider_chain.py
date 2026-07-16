"""
Shared provider-fallback primitive.

TTS, ASR, and LLM services all follow the same pattern: a priority-ordered
list of providers, a runtime-availability filter, an optional forced-provider
override, ordered fallback iteration, and the ability to demote a provider that
fails at runtime. This class captures that pattern once so each service stops
hand-rolling its own copy.

It holds only provider *names* (strings); dispatching to the concrete provider
object stays in the owning service. Construction takes the already-availability-
filtered list in priority order, so callers keep full control over provider-
specific availability rules (e.g. a provider intentionally excluded by policy
even when importable).
"""

from typing import List, Optional


class ProviderChain:
    def __init__(
        self,
        priority: List[str],
        available: List[str],
        forced: Optional[str] = None,
        normalize_case: bool = True,
    ) -> None:
        # Canonical priority order — used to sort the available list and to
        # render the display fallback order; it may list providers that are
        # not currently available.
        self.priority: List[str] = list(priority)

        # Available providers, sorted into priority order with any providers
        # not named in `priority` appended in the order the caller supplied.
        in_priority = [p for p in self.priority if p in available]
        rest = [p for p in available if p not in self.priority]
        self._available: List[str] = in_priority + rest

        forced_norm = forced or None
        if forced_norm and normalize_case:
            forced_norm = forced_norm.lower().strip() or None
        self.forced: Optional[str] = (
            forced_norm if forced_norm in self._available else None
        )
        if self.forced:
            # Keep the forced provider first so it is preferred.
            self._available = [self.forced] + [
                p for p in self._available if p != self.forced
            ]

        if self.forced:
            self.active: Optional[str] = self.forced
        elif self._available:
            self.active = self._available[0]
        else:
            self.active = None

    @property
    def available(self) -> List[str]:
        """Available providers in preference order (a copy)."""
        return list(self._available)

    def order_for(self, requested: Optional[str] = None) -> List[str]:
        """Fallback order for a request, optionally preferring one provider."""
        if requested and requested in self._available:
            return [requested] + [p for p in self._available if p != requested]
        return list(self._available)

    def fallback_order(self) -> List[str]:
        """Available providers rendered in canonical priority order."""
        return [p for p in self.priority if p in self._available]

    def remove(self, name: str) -> None:
        """Demote a provider that has become unusable this process."""
        if name in self._available:
            self._available = [p for p in self._available if p != name]
        if self.active == name:
            self.active = self._available[0] if self._available else None

    def mark_active(self, name: str) -> None:
        """Record the provider that most recently served a request."""
        self.active = name
