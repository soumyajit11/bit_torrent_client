"""Validate the fields needed to inspect a classic BitTorrent v1 torrent."""

from dataclasses import dataclass
import hashlib

from .bencode import Decoder


class MetadataError(ValueError):
    """Bencode decoded successfully, but the torrent metadata is malformed."""


@dataclass(frozen=True)
class TorrentMetadata:
    tracker: str | None
    name: str
    total_size: int
    piece_length: int
    piece_count: int
    multi_file: bool
    file_count: int
    info_hash: str


def text_field(value, label):
    if not isinstance(value, bytes) or not value:
        raise MetadataError(f"{label} must be a nonempty byte string")
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MetadataError(f"{label} must contain valid UTF-8 text") from exc


def integer_field(value, label, minimum=0):
    if not isinstance(value, int) or value < minimum:
        raise MetadataError(f"{label} must be an integer >= {minimum}")
    return value


def inspect_torrent(data: bytes) -> TorrentMetadata:
    decoder = Decoder(data)
    root = decoder.decode()
    if not isinstance(root, dict):
        raise MetadataError("torrent root must be a dictionary")
    info = root.get(b"info")
    if not isinstance(info, dict):
        raise MetadataError("info must be a dictionary")
    if b"meta version" in info:
        raise MetadataError("v2 and hybrid torrents are not supported in Milestone 1")

    tracker = None
    if b"announce" in root:
        tracker = text_field(root[b"announce"], "announce")
    name = text_field(info.get(b"name"), "info.name")
    piece_length = integer_field(info.get(b"piece length"), "info.piece length", 1)
    pieces = info.get(b"pieces")
    if not isinstance(pieces, bytes) or len(pieces) % 20:
        raise MetadataError("info.pieces must be bytes with length divisible by 20")

    if (b"length" in info) == (b"files" in info):
        raise MetadataError("info must contain exactly one of length or files")
    multi_file = b"files" in info
    file_count = 1
    if multi_file:
        files = info[b"files"]
        if not isinstance(files, list) or not files:
            raise MetadataError("info.files must be a nonempty list")
        total_size = 0
        file_count = len(files)
        for index, file in enumerate(files):
            label = f"info.files[{index}]"
            if not isinstance(file, dict):
                raise MetadataError(f"{label} must be a dictionary")
            total_size += integer_field(file.get(b"length"), f"{label}.length")
            path = file.get(b"path")
            if not isinstance(path, list) or not path:
                raise MetadataError(f"{label}.path must be a nonempty list")
            for part in path:
                text_field(part, f"{label}.path component")
    else:
        total_size = integer_field(info[b"length"], "info.length")

    # A v1 pieces string contains one 20-byte SHA-1 digest per piece.
    piece_count = len(pieces) // 20
    expected_count = (total_size + piece_length - 1) // piece_length
    if piece_count != expected_count:
        raise MetadataError(
            f"pieces contains {piece_count} hashes; size and piece length require {expected_count}"
        )
    info_hash = hashlib.sha1(decoder.info_bytes).hexdigest()
    return TorrentMetadata(tracker, name, total_size, piece_length,
                           piece_count, multi_file, file_count, info_hash)
