"""Deterministic matching of public Research Square metadata to an NCS DOI.

This module deliberately accepts metadata that has already been obtained and
parsed by an allowed source.  It has no network or filesystem client.  The
matching result is a flat, allow-listed record so source-specific fields do not
leak into the review corpus.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote, urlsplit, urlunsplit

from .core import normalize_doi as _core_normalize_doi
from .core import normalize_space


MATCH_STATUSES = frozenset(
    {"CONFIRMED", "PLAUSIBLE", "AMBIGUOUS", "NO_MATCH_FOUND"}
)

METADATA_FIELDS = frozenset(
    {
        "doi",
        "title",
        "authors",
        "date",
        "publisher",
        "version",
        "url",
        "source",
        "response_sha256",
    }
)

AUDIT_FIELDS = frozenset(
    {
        "status",
        "candidate_count",
        "deduplicated_candidate_count",
        "matched_candidate_count",
        "candidate_rank",
        "match_basis",
        "relation_target_doi",
        "title_exact",
        "author_overlap_count",
    }
)

OUTPUT_FIELDS = METADATA_FIELDS | AUDIT_FIELDS

_SOURCE_ALIASES = {
    "crossref": "Crossref",
    "openalex": "OpenAlex",
    "public search": "public_search",
    "public-search": "public_search",
    "public_search": "public_search",
}
_SOURCE_RANK = {"Crossref": 0, "OpenAlex": 1, "public_search": 2}
_DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
_VERSION_PATTERN = re.compile(r"(?:^|/)(v\d+)$", re.IGNORECASE)
_FULL_TEXT_PATTERN = re.compile(
    r"(?:^|[/_-])full(?:[-_]?text)(?:$|[/_.?-])", re.IGNORECASE
)
_PDF_PATTERN = re.compile(r"(?:^|[/_.-])pdf(?:$|[/_.?-])", re.IGNORECASE)


def _lookup(record: Mapping[str, Any], *names: str) -> Any:
    """Read a field with a small amount of source-key casing tolerance."""
    for name in names:
        if name in record:
            return record[name]
    lowered = {str(key).lower(): value for key, value in record.items()}
    for name in names:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return None


def _first_value(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return next((item for item in value if item not in (None, "")), None)
    return value


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return normalize_space(value)
    return normalize_space(str(value))


def _fold_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value).casefold()
    without_marks = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    folded = "".join(
        character if character.isalnum() else " " for character in without_marks
    )
    return normalize_space(folded)


def normalize_title(value: Any) -> str:
    """Return the exact-comparison title normalization used by the matcher."""
    return _fold_text(_text(_first_value(value)))


def _normalize_doi(value: Any) -> str | None:
    text = _text(value)
    if not text:
        return None
    normalized = _core_normalize_doi(text).rstrip(".,;:)]").lower()
    if not normalized.startswith("10.") or "/" not in normalized:
        return None
    return normalized


def _doi_from_value(value: Any) -> str | None:
    if isinstance(value, Mapping):
        for key in ("doi", "DOI", "id", "identifier", "url", "URL", "target"):
            candidate = _doi_from_value(_lookup(value, key))
            if candidate:
                return candidate
        return None
    if isinstance(value, (list, tuple, set)):
        for item in value:
            candidate = _doi_from_value(item)
            if candidate:
                return candidate
        return None
    text = _text(value)
    if not text:
        return None
    match = _DOI_PATTERN.search(text)
    if not match:
        return _normalize_doi(text)
    return _normalize_doi(match.group(0))


def _extract_doi(record: Mapping[str, Any]) -> str | None:
    value = _lookup(record, "doi", "DOI")
    doi = _doi_from_value(value)
    if doi:
        return doi
    for key in ("id", "identifier", "url", "URL", "landing_page_url", "landingPageUrl"):
        value = _lookup(record, key)
        text = _text(value)
        if text.startswith("10.") or "doi.org/" in text.lower():
            doi = _doi_from_value(text)
            if doi:
                return doi
    return None


def _author_display(value: Any) -> str:
    if isinstance(value, Mapping):
        display = _lookup(value, "display_name", "displayName", "name", "full_name")
        if display:
            return _text(display)
        given = _text(_lookup(value, "given", "first_name", "firstName"))
        family = _text(_lookup(value, "family", "last_name", "lastName"))
        if given and family:
            return f"{given} {family}"
        return family or given
    return _text(value)


def _extract_authors(record: Mapping[str, Any]) -> tuple[str, ...]:
    values = _lookup(record, "authors", "author", "authorships", "author_list")
    if values is None:
        return ()
    if isinstance(values, Mapping):
        values = [values]
    elif isinstance(values, str):
        values = [values]
    elif not isinstance(values, (list, tuple)):
        return ()

    authors: list[str] = []
    seen: set[str] = set()
    for value in values:
        if isinstance(value, Mapping) and _lookup(value, "author") is not None:
            value = _lookup(value, "author")
        display = _author_display(value)
        folded = _fold_text(display)
        if display and folded and folded not in seen:
            seen.add(folded)
            authors.append(display)
    return tuple(authors)


def _author_keys(value: str) -> frozenset[str]:
    folded = _fold_text(value)
    if not folded:
        return frozenset()
    keys = {folded}
    parts = folded.split()
    if "," in value and len(parts) > 1:
        keys.add(parts[0])
    elif len(parts) > 1:
        keys.add(parts[-1])
    return frozenset(keys)


def _author_overlap(target: Sequence[str], candidate: Sequence[str]) -> int:
    target_keys = [_author_keys(author) for author in target]
    candidate_keys = [_author_keys(author) for author in candidate]
    return sum(
        1
        for keys in candidate_keys
        if keys and any(keys.intersection(other) for other in target_keys)
    )


def _date_parts(value: Any) -> str | None:
    if isinstance(value, Mapping):
        parts = _lookup(value, "date-parts", "date_parts")
        if isinstance(parts, (list, tuple)) and parts:
            first = parts[0]
            if isinstance(first, (list, tuple)) and first:
                values = list(first[:3])
                try:
                    year = int(values[0])
                    if len(values) == 1:
                        return f"{year:04d}"
                    month = int(values[1])
                    if len(values) == 2:
                        return f"{year:04d}-{month:02d}"
                    return f"{year:04d}-{month:02d}-{int(values[2]):02d}"
                except (TypeError, ValueError):
                    pass
        year = _lookup(value, "year")
        if year is not None:
            month = _lookup(value, "month")
            day = _lookup(value, "day")
            try:
                if month is None:
                    return f"{int(year):04d}"
                if day is None:
                    return f"{int(year):04d}-{int(month):02d}"
                return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
            except (TypeError, ValueError):
                pass
        return None
    text = _text(_first_value(value))
    if not text:
        return None
    match = re.match(r"^(\d{4})(?:[-/]?(\d{1,2}))?(?:[-/]?(\d{1,2}))?", text)
    if match:
        year, month, day = match.groups()
        if day:
            return f"{year}-{int(month):02d}-{int(day):02d}"
        if month:
            return f"{year}-{int(month):02d}"
        return year
    return text


def _extract_date(record: Mapping[str, Any]) -> str | None:
    value = _lookup(
        record,
        "date",
        "publication_date",
        "published-online",
        "published_online",
        "published-print",
        "published_print",
        "published",
        "issued",
    )
    return _date_parts(value)


def _extract_publisher(record: Mapping[str, Any]) -> str | None:
    value = _lookup(record, "publisher")
    if value is None:
        venue = _lookup(record, "host_venue", "hostVenue")
        if isinstance(venue, Mapping):
            value = _lookup(venue, "publisher")
    if value is None:
        location = _lookup(record, "primary_location", "primaryLocation")
        if isinstance(location, Mapping):
            source = _lookup(location, "source")
            if isinstance(source, Mapping):
                value = _lookup(source, "publisher", "display_name", "displayName")
    text = _text(_first_value(value))
    return text or None


def _extract_title(record: Mapping[str, Any]) -> str | None:
    value = _first_value(_lookup(record, "title", "display_name", "displayName"))
    text = _text(value)
    return text or None


def _extract_url(record: Mapping[str, Any], doi: str | None) -> str | None:
    value = _lookup(record, "url", "URL", "landing_page_url", "landingPageUrl")
    if value is None:
        location = _lookup(record, "primary_location", "primaryLocation")
        if isinstance(location, Mapping):
            value = _lookup(location, "landing_page_url", "landingPageUrl")
    text = _text(_first_value(value))
    if not text and doi:
        text = f"https://doi.org/{doi}"
    return text or None


def _extract_version(record: Mapping[str, Any], doi: str | None, url: str | None) -> str | None:
    value = _first_value(_lookup(record, "version"))
    text = _text(value)
    if text:
        return text.lower() if re.fullmatch(r"v\d+", text, re.IGNORECASE) else text
    for source in (doi, url):
        if not source:
            continue
        path = urlsplit(source).path if "://" in source else source
        match = _VERSION_PATTERN.search(path.rstrip("/"))
        if match:
            return match.group(1).lower()
    return None


def _canonical_url(url: str) -> str:
    parsed = urlsplit(url)
    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/") or "/",
            parsed.query,
            "",
        )
    )


def validate_public_url(url: str) -> str:
    """Validate and return a public metadata URL, rejecting article resources."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("Research Square metadata requires a non-empty URL")
    normalized = normalize_space(url)
    parsed = urlsplit(normalized)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"Unsupported public metadata URL: {normalized}")

    host = parsed.hostname.lower().rstrip(".")
    if host == "researchsquare.com" or host.endswith(".researchsquare.com"):
        path = unquote(parsed.path).lower()
        query = unquote(parsed.query).lower()
        if path == "/api" or path.startswith("/api/"):
            raise ValueError("Research Square API URLs are not allowed")
        if _PDF_PATTERN.search(path) or _FULL_TEXT_PATTERN.search(path):
            raise ValueError("Research Square PDF or full-text URLs are not allowed")
        if re.search(
            r"(?:^|[&;])(?:pdf|download|fulltext|full-text|full_text)(?:=|[&;]|$)",
            query,
        ) or _PDF_PATTERN.search(query) or _FULL_TEXT_PATTERN.search(query):
            raise ValueError("Research Square PDF or full-text URLs are not allowed")
    return normalized


def response_sha256(response: bytes | bytearray | memoryview | str | Mapping[str, Any] | Sequence[Any]) -> str:
    """Hash supplied response bytes or a deterministic serialized response object."""
    if isinstance(response, (bytes, bytearray, memoryview)):
        payload = bytes(response)
    elif isinstance(response, str):
        payload = response.encode("utf-8")
    else:
        try:
            payload = json.dumps(
                response,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise TypeError("response must be bytes, text, or JSON-serializable metadata") from exc
    return hashlib.sha256(payload).hexdigest()


def _validated_hash(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", value):
        raise ValueError("response_sha256 must be a 64-character hexadecimal digest")
    return value.lower()


def _relation_dois(record: Mapping[str, Any]) -> tuple[str, ...]:
    values: list[str] = []
    relation = _lookup(record, "relation", "relations")

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            visited_key = False
            for key in (
                "id",
                "doi",
                "DOI",
                "identifier",
                "url",
                "URL",
                "target",
                "related",
            ):
                nested = _lookup(value, key)
                if nested is not None:
                    visited_key = True
                    visit(nested)
            if not visited_key:
                for nested in value.values():
                    visit(nested)
            return
        if isinstance(value, (list, tuple, set)):
            for item in value:
                visit(item)
            return
        text = _text(value)
        if not text:
            return
        matches = _DOI_PATTERN.findall(text)
        if matches:
            values.extend(
                doi for doi in (_normalize_doi(match) for match in matches) if doi
            )
        else:
            doi = _normalize_doi(text)
            if doi:
                values.append(doi)

    visit(relation)
    return tuple(sorted(set(values)))


@dataclass(frozen=True)
class _Candidate:
    identity: str
    doi: str | None
    title: str | None
    authors: tuple[str, ...]
    date: str | None
    publisher: str | None
    version: str | None
    url: str
    source: str
    response_sha256: str | None
    relation_target_doi: str | None
    relation_match: bool
    title_exact: bool
    author_overlap_count: int
    completeness: int


def _candidate_preference(candidate: _Candidate) -> tuple[Any, ...]:
    return (
        not candidate.relation_match,
        not (candidate.title_exact and candidate.author_overlap_count > 0),
        -candidate.author_overlap_count,
        -candidate.completeness,
        _SOURCE_RANK[candidate.source],
        candidate.doi or "",
        _canonical_url(candidate.url),
        normalize_title(candidate.title or ""),
        tuple(normalize_title(author) for author in candidate.authors),
        candidate.date or "",
        candidate.publisher or "",
        candidate.version or "",
        candidate.response_sha256 or "",
    )


def _unwrap_candidate(record: Mapping[str, Any]) -> dict[str, Any]:
    nested = _lookup(record, "metadata")
    if not isinstance(nested, Mapping):
        return dict(record)
    merged = dict(nested)
    for key in ("source", "response_sha256"):
        value = _lookup(record, key)
        if value is not None:
            merged[key] = value
    return merged


def _normalize_source(value: Any) -> str:
    source = _text(value).casefold()
    canonical = _SOURCE_ALIASES.get(source)
    if canonical is None:
        raise ValueError("source must be Crossref, OpenAlex, or public_search")
    return canonical


def _normalize_candidate(
    record: Mapping[str, Any],
    target_doi: str,
    target_title: str | None,
    target_authors: Sequence[str],
    default_source: str | None,
    default_response_sha256: str | None,
) -> _Candidate:
    if not isinstance(record, Mapping):
        raise TypeError("Each Research Square candidate must be parsed metadata")
    flattened = _unwrap_candidate(record)
    doi = _extract_doi(flattened)
    title = _extract_title(flattened)
    authors = _extract_authors(flattened)
    date = _extract_date(flattened)
    publisher = _extract_publisher(flattened)
    url = _extract_url(flattened, doi)
    if url is None:
        raise ValueError("Research Square candidate requires a DOI or public URL")
    url = validate_public_url(url)
    source_value = _lookup(flattened, "source") or default_source
    source = _normalize_source(source_value)
    candidate_response_sha256 = _validated_hash(
        _lookup(flattened, "response_sha256")
    ) or default_response_sha256
    relation_dois = _relation_dois(flattened)
    relation_match = target_doi in relation_dois
    title_exact = bool(
        target_title and title and normalize_title(target_title) == normalize_title(title)
    )
    author_overlap_count = _author_overlap(target_authors, authors)
    identity = f"doi:{doi}" if doi else f"url:{_canonical_url(url)}"
    version = _extract_version(flattened, doi, url)
    completeness = sum(
        bool(value)
        for value in (doi, title, authors, date, publisher, version)
    )
    return _Candidate(
        identity=identity,
        doi=doi,
        title=title,
        authors=authors,
        date=date,
        publisher=publisher,
        version=version,
        url=url,
        source=source,
        response_sha256=candidate_response_sha256,
        relation_target_doi=target_doi if relation_match else None,
        relation_match=relation_match,
        title_exact=title_exact,
        author_overlap_count=author_overlap_count,
        completeness=completeness,
    )


def _empty_result(
    status: str,
    response_hash: str | None,
    candidate_count: int,
    deduplicated_count: int,
    matched_count: int,
) -> dict[str, Any]:
    return {
        "doi": None,
        "title": None,
        "authors": [],
        "date": None,
        "publisher": None,
        "version": None,
        "url": None,
        "source": None,
        "response_sha256": response_hash,
        "status": status,
        "candidate_count": candidate_count,
        "deduplicated_candidate_count": deduplicated_count,
        "matched_candidate_count": matched_count,
        "candidate_rank": None,
        "match_basis": "NONE",
        "relation_target_doi": None,
        "title_exact": False,
        "author_overlap_count": 0,
    }


def _project_result(
    selected: _Candidate,
    status: str,
    rank: int,
    response_hash: str | None,
    candidate_count: int,
    deduplicated_count: int,
    matched_count: int,
    match_basis: str,
) -> dict[str, Any]:
    return {
        "doi": selected.doi,
        "title": selected.title,
        "authors": list(selected.authors),
        "date": selected.date,
        "publisher": selected.publisher,
        "version": selected.version,
        "url": selected.url,
        "source": selected.source,
        "response_sha256": response_hash or selected.response_sha256,
        "status": status,
        "candidate_count": candidate_count,
        "deduplicated_candidate_count": deduplicated_count,
        "matched_candidate_count": matched_count,
        "candidate_rank": rank,
        "match_basis": match_basis,
        "relation_target_doi": selected.relation_target_doi,
        "title_exact": selected.title_exact,
        "author_overlap_count": selected.author_overlap_count,
    }


def match_research_square_metadata(
    ncs_metadata: Mapping[str, Any] | str,
    candidates: Iterable[Mapping[str, Any]],
    response: bytes | bytearray | memoryview | str | Mapping[str, Any] | Sequence[Any] | None = None,
    *,
    response_sha256: str | None = None,
    response_bytes: bytes | bytearray | memoryview | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    """Match parsed Research Square metadata to one NCS metadata record.

    A relation to the target DOI is a confirmed match.  Without such a
    relation, exactly one candidate with an exactly normalized title and at
    least one overlapping author is plausible.  Multiple viable candidates
    are ambiguous; all other inputs yield no match.
    """
    if isinstance(ncs_metadata, Mapping):
        target_doi = _extract_doi(ncs_metadata)
        target_title = _extract_title(ncs_metadata)
        target_authors = _extract_authors(ncs_metadata)
    else:
        target_doi = _doi_from_value(ncs_metadata)
        target_title = None
        target_authors = ()
    if not target_doi:
        raise ValueError("NCS metadata requires a DOI")

    if response is not None and response_bytes is not None:
        raise ValueError("Pass response or response_bytes, not both")
    supplied_response = response if response is not None else response_bytes
    computed_response_sha256 = (
        response_sha256_value(supplied_response) if supplied_response is not None else None
    )
    explicit_response_sha256 = _validated_hash(response_sha256)
    if (
        computed_response_sha256 is not None
        and explicit_response_sha256 is not None
        and computed_response_sha256 != explicit_response_sha256
    ):
        raise ValueError("response_sha256 does not match supplied response")
    response_hash = explicit_response_sha256 or computed_response_sha256
    default_source = _normalize_source(source) if source is not None else None

    raw_candidates = list(candidates)
    normalized: list[_Candidate] = []
    for record in raw_candidates:
        normalized.append(
            _normalize_candidate(
                record,
                target_doi,
                target_title,
                target_authors,
                default_source,
                response_hash,
            )
        )

    deduplicated: dict[str, _Candidate] = {}
    for item in normalized:
        existing = deduplicated.get(item.identity)
        if existing is None or _candidate_preference(item) < _candidate_preference(existing):
            deduplicated[item.identity] = item
    ranked = sorted(deduplicated.values(), key=_candidate_preference)

    relation_matches = [item for item in ranked if item.relation_match]
    if relation_matches:
        matched = relation_matches
        status = "CONFIRMED" if len(relation_matches) == 1 else "AMBIGUOUS"
        match_basis = "RELATION"
    else:
        plausible_matches = [
            item
            for item in ranked
            if item.title_exact and item.author_overlap_count > 0
        ]
        matched = plausible_matches
        status = (
            "PLAUSIBLE"
            if len(plausible_matches) == 1
            else "AMBIGUOUS"
            if len(plausible_matches) > 1
            else "NO_MATCH_FOUND"
        )
        match_basis = "TITLE_AUTHOR" if plausible_matches else "NONE"

    if not matched:
        uniform_hashes = {
            item.response_sha256 for item in ranked if item.response_sha256
        }
        if response_hash is None and len(uniform_hashes) == 1:
            response_hash = next(iter(uniform_hashes))
        return _empty_result(
            status,
            response_hash,
            len(raw_candidates),
            len(ranked),
            0,
        )

    selected = matched[0]
    rank = ranked.index(selected) + 1
    return _project_result(
        selected,
        status,
        rank,
        response_hash,
        len(raw_candidates),
        len(ranked),
        len(matched),
        match_basis,
    )


def response_sha256_value(
    response: bytes | bytearray | memoryview | str | Mapping[str, Any] | Sequence[Any] | None,
) -> str | None:
    """Return a response digest while allowing the matcher to omit a response."""
    if response is None:
        return None
    return response_sha256(response)


def match_research_square(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Compatibility name for :func:`match_research_square_metadata`."""
    return match_research_square_metadata(*args, **kwargs)


def match_metadata(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Short compatibility name for :func:`match_research_square_metadata`."""
    return match_research_square_metadata(*args, **kwargs)


__all__ = [
    "AUDIT_FIELDS",
    "MATCH_STATUSES",
    "METADATA_FIELDS",
    "OUTPUT_FIELDS",
    "match_metadata",
    "match_research_square",
    "match_research_square_metadata",
    "normalize_title",
    "response_sha256",
    "validate_public_url",
]
