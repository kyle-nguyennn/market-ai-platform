from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

class OptionType(StrEnum):
    CALL = "call"
    PUT = "put"

class OptionContract(BaseModel):
    underlying: str
    strike: float
    expiry: datetime
    option_type: OptionType

    @property
    def symbol(self) -> str:
        """Generate a standardized option symbol, e.g. 'AAPL_20240119_CALL_150.00'."""
        return f"{self.underlying}_{self.expiry:%Y%m%d}_{self.option_type.value}_{self.strike:.2f}"
