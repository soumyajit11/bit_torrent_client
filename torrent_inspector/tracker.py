"""Build HTTP tracker announce URLs without sending a request."""

from dataclasses import dataclass
from urllib.parse import quote, quote_from_bytes, urlsplit, urlunsplit

from .bencode import BencodeError, decode


class TrackerRequestError(ValueError):
    """The data needed to build a tracker announce request is invalid."""


class TrackerResponseError(ValueError):
    """A tracker response cannot be used by this client."""


@dataclass(frozen=True)
class TrackerResponse:
    interval: int
    peers: bytes


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


def parse_tracker_response(data: bytes) -> TrackerResponse:
    """Parse an offline HTTP tracker response without decoding compact peers."""
    try:
        response = decode(data)
    except BencodeError as exc:
        raise TrackerResponseError("invalid tracker response Bencode") from exc

    if not isinstance(response, dict):
        raise TrackerResponseError("tracker response must be a dictionary")
    if b"failure reason" in response:
        reason = response[b"failure reason"]
        if not isinstance(reason, bytes):
            raise TrackerResponseError("tracker failure reason must be bytes")
        raise TrackerResponseError(f"tracker failure: {reason.decode('utf-8', errors='replace')}")

    interval = response.get(b"interval")
    if not isinstance(interval, int) or interval <= 0:
        raise TrackerResponseError("tracker interval must be a positive integer")
    peers = response.get(b"peers")
    if not isinstance(peers, bytes):
        raise TrackerResponseError("tracker peers must be bytes")
    return TrackerResponse(interval=interval, peers=peers)
