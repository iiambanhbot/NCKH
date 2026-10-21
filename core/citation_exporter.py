"""
Xuất danh sách bài báo sang các định dạng quản lý trích dẫn tiêu chuẩn quốc tế:
- BibTeX (.bib): Tương thích hoàn hảo với Zotero, Mendeley, Overleaf, LaTeX.
- RIS (.ris): Tương thích hoàn hảo với EndNote, Zotero, Mendeley, RefWorks.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Sequence

from core.paper import Paper


def _slugify_author(author_str: str) -> str:
    """Chuẩn hóa họ tên tác giả thành họ/tên viết liền không dấu cho citekey."""
    if not author_str:
        return "anonymous"
    # Bỏ dấu tiếng Việt / ký tự đặc biệt
    clean = unicodedata.normalize("NFKD", author_str).encode("ascii", "ignore").decode("ascii")
    # Lấy từ cuối cùng (họ hoặc tên tùy cách viết)
    parts = re.findall(r"\b[A-Za-z0-9]+\b", clean)
    if parts:
        return parts[-1].lower()
    return "author"


def _make_cite_key(paper: Paper, index: int) -> str:
    """Tạo khóa định danh trích dẫn duy nhất (cite key) dạng author_year_title."""
    first_author = paper.authors[0] if paper.authors else "paper"
    author_tag = _slugify_author(first_author)
    year_tag = str(paper.year) if paper.year else "nodate"

    # 1 từ khóa đầu tiên từ tiêu đề
    clean_title = unicodedata.normalize("NFKD", paper.title or "").encode("ascii", "ignore").decode("ascii")
    title_words = re.findall(r"\b[A-Za-z0-9]+\b", clean_title.lower())
    title_tag = title_words[0] if title_words else f"p{index}"

    return f"{author_tag}{year_tag}_{title_tag}"


def papers_to_bibtex(papers: Sequence[Paper]) -> str:
    """
    Chuyển đổi danh sách đối tượng Paper thành chuỗi định dạng BibTeX (.bib).

    Đầu vào:
        papers: Danh sách các bài báo nghiên cứu.

    Đầu ra:
        Chuỗi văn bản mã hóa UTF-8 định dạng .bib.
    """
    if not papers:
        return ""

    entries: list[str] = []
    seen_keys: set[str] = set()

    for idx, paper in enumerate(papers, 1):
        base_key = _make_cite_key(paper, idx)
        key = base_key
        suffix_counter = 1
        while key in seen_keys:
            key = f"{base_key}_{suffix_counter}"
            suffix_counter += 1
        seen_keys.add(key)

        authors_str = " and ".join(paper.authors) if paper.authors else ""
        year_str = str(paper.year) if paper.year else ""
        venue = paper.journal or getattr(paper, "venue", "") or ""
        url = paper.url or (f"https://doi.org/{paper.doi}" if paper.doi else "")

        fields: list[str] = []
        if paper.title:
            fields.append(f"  title = {{{paper.title}}}")
        if authors_str:
            fields.append(f"  author = {{{authors_str}}}")
        if venue:
            fields.append(f"  journal = {{{venue}}}")
        if year_str:
            fields.append(f"  year = {{{year_str}}}")
        if paper.doi:
            fields.append(f"  doi = {{{paper.doi}}}")
        if url:
            fields.append(f"  url = {{{url}}}")
        if paper.abstract:
            # Escape ký tự ngoặc nhọn nếu có trong abstract
            clean_abs = paper.abstract.replace("{", "\\{").replace("}", "\\}")
            fields.append(f"  abstract = {{{clean_abs}}}")

        entry_body = ",\n".join(fields)
        entries.append(f"@article{{{key},\n{entry_body}\n}}")

    return "\n\n".join(entries) + "\n"


def papers_to_ris(papers: Sequence[Paper]) -> str:
    """
    Chuyển đổi danh sách đối tượng Paper thành chuỗi định dạng RIS (.ris).

    Đầu vào:
        papers: Danh sách các bài báo nghiên cứu.

    Đầu ra:
        Chuỗi văn bản mã hóa UTF-8 định dạng .ris.
    """
    if not papers:
        return ""

    records: list[str] = []

    for paper in papers:
        lines: list[str] = ["TY  - JOUR"]

        if paper.title:
            lines.append(f"TI  - {paper.title}")

        if paper.authors:
            for author in paper.authors:
                if author.strip():
                    lines.append(f"AU  - {author.strip()}")

        if paper.year:
            lines.append(f"PY  - {paper.year}")

        venue = paper.journal or getattr(paper, "venue", "") or ""
        if venue:
            lines.append(f"JO  - {venue}")

        if paper.doi:
            lines.append(f"DO  - {paper.doi}")

        url = paper.url or (f"https://doi.org/{paper.doi}" if paper.doi else "")
        if url:
            lines.append(f"UR  - {url}")

        if paper.abstract:
            lines.append(f"AB  - {paper.abstract.strip()}")

        lines.append("ER  - ")
        records.append("\n".join(lines))

    return "\n\n".join(records) + "\n"
