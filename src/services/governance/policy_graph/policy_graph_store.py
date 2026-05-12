from abc import ABC, abstractmethod
from typing import Iterable, List

from src.services.event_sourcing.canonical_event import CanonicalEvent
from .policy_version import PolicyVersion


class PolicyGraphStore(ABC):
    @abstractmethod
    def replace_from_projection(self, versions: Iterable[PolicyVersion], events: Iterable[CanonicalEvent]) -> None:
        raise NotImplementedError

    @abstractmethod
    def repair_from_projection(self, versions: Iterable[PolicyVersion], events: Iterable[CanonicalEvent]) -> None:
        raise NotImplementedError

    @abstractmethod
    def load_events(self) -> List[CanonicalEvent]:
        raise NotImplementedError

    @abstractmethod
    def load_versions(self) -> List[dict]:
        raise NotImplementedError

    @abstractmethod
    def load_parent_edges(self) -> List[dict]:
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError
