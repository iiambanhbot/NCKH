"""
Khuôn dữ liệu chung của một bài báo, mọi module chỉ trao đổi dữ liệu thông qua khuôn này.
Đầu vào: Dữ liệu thô của bài báo từ các nguồn học thuật khác nhau hoặc từ kết quả phân tích AI.
Đầu ra: Đối tượng dữ liệu bài báo chuẩn hóa phục vụ các tiến trình xử lý tiếp theo.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional


@dataclass
class Paper:
    """Đối tượng lưu trữ thông tin chuẩn hóa của một bài báo nghiên cứu kinh tế."""

    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: Optional[int] = None
    journal: str = ""
    doi: str = ""
    url: str = ""
    citations: int = 0
    abstract: str = ""
    source: str = ""
    relevance_score: int = 0
    relevance_reason: str = ""
    summary: str = ""
    methodology: str = ""
    data_source: str = ""
    key_findings: str = ""
    limitations: str = ""
    policy_implications: str = ""
    notes: str = ""
    analyzed: bool = False

    def __hash__(self) -> int:
        """Hàm băm cho Paper dựa trên DOI hoặc kết hợp (title, year) để hỗ trợ set/dict."""
        clean_doi = (self.doi or "").strip().lower()
        if clean_doi:
            return hash(clean_doi)
        clean_title = (self.title or "").strip().lower()
        return hash((clean_title, self.year))

    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển đổi đối tượng Paper thành dictionary đầy đủ các trường.

        Đầu ra:
            dict chứa toàn bộ thông tin của Paper bao gồm trường analyzed.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Paper:
        """
        Tạo đối tượng Paper từ dictionary dữ liệu.

        Đầu vào:
            data: dict chứa thông tin bài báo.

        Đầu ra:
            Đối tượng Paper đã được chuẩn hóa.
        """
        authors_raw = data.get("authors", [])
        if isinstance(authors_raw, str):
            authors = [a.strip() for a in authors_raw.split(",") if a.strip()]
        elif isinstance(authors_raw, list):
            authors = [str(a) for a in authors_raw]
        else:
            authors = []

        year_raw = data.get("year")
        year = int(year_raw) if year_raw is not None and str(year_raw).isdigit() else None

        citations_raw = data.get("citations", 0)
        try:
            citations = int(citations_raw)
        except (ValueError, TypeError):
            citations = 0

        score_raw = data.get("relevance_score", 0)
        try:
            relevance_score = int(score_raw)
        except (ValueError, TypeError):
            relevance_score = 0

        return cls(
            title=str(data.get("title", "") or ""),
            authors=authors,
            year=year,
            journal=str(data.get("journal", "") or ""),
            doi=str(data.get("doi", "") or ""),
            url=str(data.get("url", "") or ""),
            citations=citations,
            abstract=str(data.get("abstract", "") or ""),
            source=str(data.get("source", "") or ""),
            relevance_score=relevance_score,
            relevance_reason=str(data.get("relevance_reason", "") or ""),
            summary=str(data.get("summary", "") or ""),
            methodology=str(data.get("methodology", "") or ""),
            data_source=str(data.get("data_source", "") or ""),
            key_findings=str(data.get("key_findings", "") or ""),
            limitations=str(data.get("limitations", "") or ""),
            policy_implications=str(data.get("policy_implications", "") or ""),
            notes=str(data.get("notes", "") or ""),
            analyzed=bool(data.get("analyzed", False)),
        )

    def to_excel_row(self) -> dict[str, Any]:
        """
        Chuyển đổi thông tin bài báo thành một dòng dữ liệu gồm đúng 18 cột phục vụ xuất file Excel.

        Đầu ra:
            dict ánh xạ 18 tên cột tiếng Việt với giá trị tương ứng (không bao gồm cờ analyzed).
        """
        authors_str = ", ".join(self.authors) if isinstance(self.authors, list) else str(self.authors)
        return {
            "Tiêu đề": self.title,
            "Tác giả": authors_str,
            "Năm xuất bản": self.year if self.year is not None else "",
            "Tạp chí / Nơi xuất bản": self.journal,
            "DOI": self.doi,
            "URL": self.url,
            "Số trích dẫn": self.citations,
            "Nguồn": self.source,
            "Abstract": self.abstract,
            "Điểm phù hợp": self.relevance_score,
            "Lý do phù hợp": self.relevance_reason,
            "Tóm tắt": self.summary,
            "Phương pháp": self.methodology,
            "Dữ liệu nghiên cứu": self.data_source,
            "Kết quả chính": self.key_findings,
            "Hạn chế": self.limitations,
            "Hàm ý chính sách": self.policy_implications,
            "Ghi chú": self.notes,
        }

    @property
    def dedupe_key(self) -> str:
        """Khóa định danh duy nhất của bài báo."""
        return get_dedupe_key(self)


def normalize_doi(doi: Optional[str]) -> str:
    """Chuẩn hóa chuỗi DOI về định dạng tiêu chuẩn (bỏ tiền tố url/doi: và viết thường)."""
    if not doi:
        return ""
    doi_clean = str(doi).strip()
    for prefix in (
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
        "doi:",
    ):
        if doi_clean.lower().startswith(prefix):
            doi_clean = doi_clean[len(prefix):]
    return doi_clean.strip().lower()


if not hasattr(Paper, "normalize_doi"):
    Paper.normalize_doi = staticmethod(normalize_doi)


def get_dedupe_key(paper: Paper) -> str:
    """Tạo khóa định danh duy nhất để khử trùng bài báo."""
    raw_doi = getattr(paper, "doi", None)
    if raw_doi:
        normalized_doi = normalize_doi(raw_doi)
        if normalized_doi:
            return f"doi:{normalized_doi}"

    title = (getattr(paper, "title", "") or "").strip().lower()
    title_clean = "".join(c for c in title if c.isalnum() or c.isspace())
    title_slug = "_".join(title_clean.split())
    year = str(getattr(paper, "year", "") or "")
    return f"title_year:{title_slug}_{year}"


def rank(papers: list[Paper]) -> list[Paper]:
    """
    Sắp xếp danh sách bài báo:
    - Các bài đã có relevance_score (> 0) xếp trước theo relevance_score giảm dần.
    - Các bài chưa có điểm (hoặc điểm = 0) xếp sau, sắp xếp theo citation_count / citations giảm dần.
    """
    if not papers:
        return []

    def sort_key(p: Paper) -> tuple[int, int, int, int]:
        score = p.relevance_score or 0
        has_score = 1 if score > 0 else 0
        cit = getattr(p, "citation_count", p.citations) or 0
        year = p.year or 0
        return (-has_score, -score, -cit, -year)

    return sorted(papers, key=sort_key)
