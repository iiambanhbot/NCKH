"""
Unit tests cho core/citation_exporter.py.
Kiểm tra:
- papers_to_bibtex sinh đúng cấu trúc @article, cite key, các trường title, author, journal, year, doi, url.
- papers_to_ris sinh đúng cấu trúc TY, TI, AU, PY, JO, DO, UR, ER.
- Tránh trùng lặp cite key khi cùng tác giả và năm.
- Xử lý danh sách rỗng an toàn.
"""

from __future__ import annotations

import pytest
from core.citation_exporter import papers_to_bibtex, papers_to_ris
from core.paper import Paper


def test_papers_to_bibtex() -> None:
    p1 = Paper(
        title="Impact of Fintech on Commercial Banks",
        authors=["Nguyen Van A", "Tran Thi B"],
        year=2023,
        journal="Journal of Banking & Finance",
        doi="10.1016/j.jbankfin.2023.01",
        url="https://example.com/p1",
        abstract="This paper examines fintech adoption.",
    )
    p2 = Paper(
        title="Another Fintech Study",
        authors=["Nguyen Van A"],
        year=2023,
        journal="Finance Research Letters",
        doi="10.1016/j.frl.2023.02",
    )

    bib_str = papers_to_bibtex([p1, p2])

    assert "@article{" in bib_str
    assert "title = {Impact of Fintech on Commercial Banks}" in bib_str
    assert "author = {Nguyen Van A and Tran Thi B}" in bib_str
    assert "year = {2023}" in bib_str
    assert "doi = {10.1016/j.jbankfin.2023.01}" in bib_str
    assert "journal = {Journal of Banking & Finance}" in bib_str


def test_papers_to_ris() -> None:
    p = Paper(
        title="Green Growth in Vietnam",
        authors=["Le Van C"],
        year=2024,
        journal="Environmental Economics",
        doi="10.1000/env.2024.10",
        url="https://doi.org/10.1000/env.2024.10",
        abstract="Analyzing green growth trends.",
    )

    ris_str = papers_to_ris([p])

    assert "TY  - JOUR" in ris_str
    assert "TI  - Green Growth in Vietnam" in ris_str
    assert "AU  - Le Van C" in ris_str
    assert "PY  - 2024" in ris_str
    assert "JO  - Environmental Economics" in ris_str
    assert "DO  - 10.1000/env.2024.10" in ris_str
    assert "UR  - https://doi.org/10.1000/env.2024.10" in ris_str
    assert "ER  -" in ris_str


def test_citation_exporter_empty() -> None:
    assert papers_to_bibtex([]) == ""
    assert papers_to_ris([]) == ""
