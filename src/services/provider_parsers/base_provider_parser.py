from abc import ABC, abstractmethod
from src.models.bill_data import BillData

class BaseProviderParser(ABC):
    @abstractmethod
    def can_handle(self, bill_data: BillData) -> bool:
        pass

    @abstractmethod
    def refine(self, bill_data: BillData) -> BillData:
        pass
