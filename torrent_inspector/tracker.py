"""Build HTTP tracker announce URLs without sending a request."""

from urllib.parse import quote, quote_from_bytes, urlsplit, urlunsplit


class TrackerRequestError(ValueError):
    """The data needed to build a tracker announce request is invalid."""


def info_hash_bytes(info_hash: str) -> bytes:
    """Convert a v1 torrent's 40-character hexadecimal info hash to 20 bytes."""
    if not isinstance(info_hash, str) or len(info_hash) != 40:
        raise TrackerRequestError("info hash must be 40 hexadecimal characters")
    try:
        raw_hash = bytes.fromhex(info_hash)
    except ValueError as exc:
        raise TrackerRequestError("info hash must be 40 hexadecimal characters") from exc
    return raw_hash


def build_announce_url(tracker_url: str, info_hash: str, peer_id: bytes, port: int,
                       uploaded: int, downloaded: int, left: int) -> str:
    """Construct the URL for a future HTTP tracker announce, without sending it."""
    if not isinstance(peer_id, bytes) or len(peer_id) != 20:
        raise TrackerRequestError("peer_id must be exactly 20 bytes")

    raw_info_hash = info_hash_bytes(info_hash)
    parameters = (
        f"info_hash={quote_from_bytes(raw_info_hash, safe='')}",
        f"peer_id={quote_from_bytes(peer_id, safe='')}",
        f"port={quote(str(port), safe='')}",
        f"uploaded={quote(str(uploaded), safe='')}",
        f"downloaded={quote(str(downloaded), safe='')}",
        f"left={quote(str(left), safe='')}",
        "compact=1",
    )
    parts = urlsplit(tracker_url)
    query = "&".join(filter(None, (parts.query, "&".join(parameters))))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))
