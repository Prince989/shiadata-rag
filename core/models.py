from typing import Dict, Any

class ParsedChunk:
    """
    این کلاس نمایانگر یک قطعه از متن است که توسط پارسر استخراج شده.
    شامل متن تمیز شده و متادیتاهای استخراج شده (مثل نام فصل و منابع) می‌باشد.
    """
    def __init__(self, text: str, metadata: Dict[str, Any]):
        self.text = text
        self.metadata = metadata

    def __repr__(self):
        return f"ParsedChunk(text='{self.text[:30]}...', metadata={self.metadata})"