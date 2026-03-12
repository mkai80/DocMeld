"""Pydantic models for document elements extracted from PDFs."""
from __future__ import annotations

from typing import Any, Dict, Literal, Optional, Tuple

from pydantic import BaseModel, Field


class TitleElement(BaseModel):
    type: Literal["title"]
    level: int = Field(ge=0, le=5)
    content: str = Field(min_length=1)
    page_no: int = Field(ge=1)
    element_id: str = ""
    parent_id: str = ""


class TextElement(BaseModel):
    type: Literal["text"]
    content: str = Field(min_length=1)
    page_no: int = Field(ge=1)
    element_id: str = ""
    parent_id: str = ""


class TableElement(BaseModel):
    type: Literal["table"]
    content: str = Field(min_length=1)
    summary: str
    page_no: int = Field(ge=1)
    element_id: str = ""
    parent_id: str = ""
    table_data: Optional[Dict[str, Any]] = None


class ImageElement(BaseModel):
    type: Literal["image"]
    image_name: str
    content: str
    image: str
    image_id: str
    bbox: Tuple[float, float, float, float]
    page_no: int = Field(ge=1)
    element_id: str = ""
    parent_id: str = ""


BronzeElement = TitleElement | TextElement | TableElement | ImageElement


def parse_element(data: dict[str, Any]) -> BronzeElement:
    """Parse a raw dict into the appropriate element model."""
    element_type = data.get("type")
    if element_type == "title":
        return TitleElement(**data)
    elif element_type == "text":
        return TextElement(**data)
    elif element_type == "table":
        return TableElement(**data)
    elif element_type == "image":
        return ImageElement(**data)
    else:
        raise ValueError(f"Unknown element type: {element_type}")
