"""Unit tests for Pydantic element models."""
import pytest
from pydantic import ValidationError


class TestTitleElement:
    def test_valid_title(self) -> None:
        from docmeld.bronze.element_types import TitleElement

        elem = TitleElement(type="title", level=0, content="Executive Summary", page_no=1)
        assert elem.type == "title"
        assert elem.level == 0
        assert elem.content == "Executive Summary"
        assert elem.page_no == 1

    def test_default_element_id_and_parent_id(self) -> None:
        from docmeld.bronze.element_types import TitleElement

        elem = TitleElement(type="title", level=0, content="Title", page_no=1)
        assert elem.element_id == ""
        assert elem.parent_id == ""

    def test_custom_element_id_and_parent_id(self) -> None:
        from docmeld.bronze.element_types import TitleElement

        elem = TitleElement(
            type="title", level=1, content="Sub", page_no=1,
            element_id="e_002", parent_id="e_001",
        )
        assert elem.element_id == "e_002"
        assert elem.parent_id == "e_001"

    def test_level_range(self) -> None:
        from docmeld.bronze.element_types import TitleElement

        for level in range(6):
            elem = TitleElement(type="title", level=level, content="Title", page_no=1)
            assert elem.level == level

    def test_level_too_high(self) -> None:
        from docmeld.bronze.element_types import TitleElement

        with pytest.raises(ValidationError):
            TitleElement(type="title", level=6, content="Title", page_no=1)

    def test_level_negative(self) -> None:
        from docmeld.bronze.element_types import TitleElement

        with pytest.raises(ValidationError):
            TitleElement(type="title", level=-1, content="Title", page_no=1)

    def test_empty_content_rejected(self) -> None:
        from docmeld.bronze.element_types import TitleElement

        with pytest.raises(ValidationError):
            TitleElement(type="title", level=0, content="", page_no=1)

    def test_page_no_zero_rejected(self) -> None:
        from docmeld.bronze.element_types import TitleElement

        with pytest.raises(ValidationError):
            TitleElement(type="title", level=0, content="Title", page_no=0)


class TestTextElement:
    def test_valid_text(self) -> None:
        from docmeld.bronze.element_types import TextElement

        elem = TextElement(type="text", content="Some paragraph text.", page_no=2)
        assert elem.type == "text"
        assert elem.content == "Some paragraph text."
        assert elem.page_no == 2

    def test_default_element_id_and_parent_id(self) -> None:
        from docmeld.bronze.element_types import TextElement

        elem = TextElement(type="text", content="Hello", page_no=1)
        assert elem.element_id == ""
        assert elem.parent_id == ""

    def test_empty_content_rejected(self) -> None:
        from docmeld.bronze.element_types import TextElement

        with pytest.raises(ValidationError):
            TextElement(type="text", content="", page_no=1)


class TestTableElement:
    def test_valid_table(self) -> None:
        from docmeld.bronze.element_types import TableElement

        elem = TableElement(
            type="table",
            content="| A | B |\n|---|---|\n| 1 | 2 |",
            summary="Items: A, B",
            page_no=3,
        )
        assert elem.type == "table"
        assert elem.summary == "Items: A, B"

    def test_default_table_data_is_none(self) -> None:
        from docmeld.bronze.element_types import TableElement

        elem = TableElement(
            type="table", content="| A |\n|---|\n| 1 |", summary="", page_no=1
        )
        assert elem.table_data is None

    def test_table_data_with_value(self) -> None:
        from docmeld.bronze.element_types import TableElement

        td = {"headers": ["A", "B"], "rows": [["1", "2"]], "num_rows": 1, "num_cols": 2}
        elem = TableElement(
            type="table", content="| A | B |\n|---|---|\n| 1 | 2 |",
            summary="", page_no=1, table_data=td,
        )
        assert elem.table_data == td

    def test_default_element_id_and_parent_id(self) -> None:
        from docmeld.bronze.element_types import TableElement

        elem = TableElement(
            type="table", content="| A |\n|---|\n| 1 |", summary="", page_no=1
        )
        assert elem.element_id == ""
        assert elem.parent_id == ""

    def test_empty_summary_allowed(self) -> None:
        from docmeld.bronze.element_types import TableElement

        elem = TableElement(
            type="table", content="| A |\n|---|\n| 1 |", summary="", page_no=1
        )
        assert elem.summary == ""

    def test_empty_content_rejected(self) -> None:
        from docmeld.bronze.element_types import TableElement

        with pytest.raises(ValidationError):
            TableElement(type="table", content="", summary="", page_no=1)


class TestImageElement:
    def test_valid_image(self) -> None:
        from docmeld.bronze.element_types import ImageElement

        elem = ImageElement(
            type="image",
            image_name="page001_image_001.png",
            content="A chart",
            image="aGVsbG8=",
            image_id="page001_image_001",
            bbox=(0.0, 0.0, 100.0, 100.0),
            page_no=1,
        )
        assert elem.type == "image"
        assert elem.image_name == "page001_image_001.png"
        assert elem.bbox == (0.0, 0.0, 100.0, 100.0)

    def test_default_element_id_and_parent_id(self) -> None:
        from docmeld.bronze.element_types import ImageElement

        elem = ImageElement(
            type="image", image_name="img.png", content="", image="aGVsbG8=",
            image_id="img", bbox=(0.0, 0.0, 0.0, 0.0), page_no=1,
        )
        assert elem.element_id == ""
        assert elem.parent_id == ""

    def test_empty_content_allowed(self) -> None:
        from docmeld.bronze.element_types import ImageElement

        elem = ImageElement(
            type="image",
            image_name="img.png",
            content="",
            image="aGVsbG8=",
            image_id="img",
            bbox=(0.0, 0.0, 0.0, 0.0),
            page_no=1,
        )
        assert elem.content == ""


class TestParseElement:
    def test_parse_title_dict(self) -> None:
        from docmeld.bronze.element_types import parse_element

        data = {"type": "title", "level": 1, "content": "Section", "page_no": 2}
        elem = parse_element(data)
        assert elem.type == "title"

    def test_parse_text_dict(self) -> None:
        from docmeld.bronze.element_types import parse_element

        data = {"type": "text", "content": "Hello", "page_no": 1}
        elem = parse_element(data)
        assert elem.type == "text"

    def test_parse_unknown_type_raises(self) -> None:
        from docmeld.bronze.element_types import parse_element

        with pytest.raises(ValueError, match="Unknown element type"):
            parse_element({"type": "unknown", "page_no": 1})
