"""
Gộp kết quả từ các nguồn khác nhau, loại bỏ bài trùng lặp và xếp hạng danh sách bài báo.
Đầu vào: Danh sách các danh sách Paper thu thập từ nhiều nguồn, tập các khóa cần loại trừ.
Đầu ra: Danh sách bài báo duy nhất đã được loại trùng, gộp dữ liệu đầy đủ và xếp hạng.
"""

from __future__ import annotations

import copy
from typing import Optional

from core.paper import Paper, get_dedupe_key, normalize_doi, rank


def _completeness_score(paper: Paper) -> int:
    """Tính điểm độ đầy đủ dữ liệu của một bài báo để ưu tiên giữ làm bản gốc."""
    score = 0
    if getattr(paper, "doi", None):
        score += 100
    abstract = getattr(paper, "abstract", "") or ""
    if abstract:
        score += len(abstract)
    if getattr(paper, "authors", None):
        score += len(paper.authors) * 10
    if getattr(paper, "journal", "") or getattr(paper, "venue", ""):
        score += 20
    if getattr(paper, "citations", 0) or getattr(paper, "citation_count", 0):
        score += 10
    if getattr(paper, "url", ""):
        score += 10
    return score


def _combine_papers(paper_a: Paper, paper_b: Paper) -> Paper:
    """
    Kết hợp hai bài báo trùng lặp: chọn bản đầy đủ hơn làm gốc và bổ sung các trường còn thiếu từ bản kia.
    """
    score_a = _completeness_score(paper_a)
    score_b = _completeness_score(paper_b)

    base = copy.deepcopy(paper_a if score_a >= score_b else paper_b)
    other = paper_b if score_a >= score_b else paper_a

    # Bổ sung các trường còn thiếu
    if not base.title and other.title:
        base.title = other.title

    if not base.doi and other.doi:
        base.doi = normalize_doi(other.doi)

    if not base.authors and other.authors:
        base.authors = copy.deepcopy(other.authors)

    if base.year is None and other.year is not None:
        base.year = other.year

    venue_other = getattr(other, "venue", other.journal)
    if not getattr(base, "journal", "") and venue_other:
        base.journal = venue_other
        setattr(base, "venue", venue_other)

    if not base.url and other.url:
        base.url = other.url

    citations_base = getattr(base, "citation_count", base.citations)
    citations_other = getattr(other, "citation_count", other.citations)
    max_citations = max(citations_base or 0, citations_other or 0)
    base.citations = max_citations
    setattr(base, "citation_count", max_citations)

    if not base.abstract and other.abstract:
        base.abstract = other.abstract

    is_oa = getattr(base, "is_open_access", False) or getattr(other, "is_open_access", False)
    setattr(base, "is_open_access", is_oa)

    other_oa_url = getattr(other, "open_access_url", "")
    if other_oa_url and not getattr(base, "open_access_url", ""):
        setattr(base, "open_access_url", other_oa_url)

    other_lang = getattr(other, "language", "")
    if other_lang and not getattr(base, "language", ""):
        setattr(base, "language", other_lang)

    # Các trường AI và ghi chú
    for field in (
        "relevance_score", "relevance_reason", "summary", "methodology",
        "data_source", "key_findings", "limitations", "policy_implications", "notes",
    ):
        if not getattr(base, field, None) and getattr(other, field, None):
            setattr(base, field, getattr(other, field))
    base.analyzed = base.analyzed or other.analyzed

    return base


def merge(lists: list[list[Paper]], exclude_keys: set[str]) -> list[Paper]:
    """
    Gộp các danh sách bài báo, loại trùng theo Paper.dedupe_key và loại bỏ các bài thuộc exclude_keys.
    Khi phát hiện trùng, giữ bản đầy đủ hơn (có abstract, có DOI) và bổ sung các trường còn thiếu từ bản kia.

    Đầu vào:
        lists: Danh sách các danh sách bài báo từ các nguồn khác nhau.
        exclude_keys: Tập hợp các khóa định danh cần loại trừ (ví dụ bài đã hiển thị/đã lưu).

    Đầu ra:
        Danh sách các đối tượng Paper duy nhất đã được chuẩn hóa và bổ sung dữ liệu.
    """
    merged_dict: dict[str, Paper] = {}
    ordered_keys: list[str] = []

    for paper_list in lists:
        if not paper_list:
            continue
        for paper in paper_list:
            if not isinstance(paper, Paper):
                continue

            key = paper.dedupe_key if hasattr(paper, "dedupe_key") else get_dedupe_key(paper)
            if not key or key in exclude_keys:
                continue

            if key not in merged_dict:
                merged_dict[key] = copy.deepcopy(paper)
                ordered_keys.append(key)
            else:
                existing_paper = merged_dict[key]
                merged_dict[key] = _combine_papers(existing_paper, paper)

    return [merged_dict[k] for k in ordered_keys]
