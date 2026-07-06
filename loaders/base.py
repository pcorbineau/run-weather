from abc import ABC, abstractmethod

from models import Activity


class ActivityLoader(ABC):
    @abstractmethod
    def load(self, path: str) -> Activity:
        ...
