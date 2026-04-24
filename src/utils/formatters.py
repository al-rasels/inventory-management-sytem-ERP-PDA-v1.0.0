from src.core.config import DEFAULT_CURRENCY
from datetime import datetime

class Formatter:
    @staticmethod
    def format_currency(value: float) -> str:
        return f"{DEFAULT_CURRENCY} {value:,.2f}"

    @staticmethod
    def format_date(date_str: str) -> str:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%d %b %Y")
        except:
            return date_str

    @staticmethod
    def format_percent(value: float) -> str:
        return f"{value:.1f}%"
