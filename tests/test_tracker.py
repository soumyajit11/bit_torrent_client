import unittest
from urllib.parse import unquote_to_bytes

from torrent_inspector.tracker import (
    TrackerRequestError,
    build_announce_url,
    info_hash_bytes,
)


INFO_HASH = "00ff102030405060708090a0b0c0d0e0f0010203"
PEER_ID = b"-PY0001-123456789012"


class TrackerRequestTests(unittest.TestCase):
    def test_builds_announce_url_with_standard_parameters(self):
        url = build_announce_url(
            "https://tracker.example/announce", INFO_HASH, PEER_ID,
            port=6881, uploaded=12, downloaded=34, left=56,
        )

        self.assertIn("port=6881", url)
        self.assertIn("uploaded=12", url)
        self.assertIn("downloaded=34", url)
        self.assertIn("left=56", url)
        self.assertIn("compact=1", url)
        self.assertIn("info_hash=%00%FF", url)
        self.assertEqual(unquote_to_bytes(url.split("peer_id=", 1)[1].split("&", 1)[0]), PEER_ID)

    def test_accepts_exactly_twenty_byte_peer_id(self):
        url = build_announce_url(
            "https://tracker.example/announce", INFO_HASH, PEER_ID,
            port=6881, uploaded=0, downloaded=0, left=1,
        )
        self.assertIn("peer_id=", url)

    def test_rejects_invalid_peer_id(self):
        with self.assertRaises(TrackerRequestError):
            build_announce_url(
                "https://tracker.example/announce", INFO_HASH, b"too short",
                port=6881, uploaded=0, downloaded=0, left=1,
            )

    def test_converts_hex_info_hash_to_twenty_raw_bytes(self):
        raw_hash = info_hash_bytes(INFO_HASH)
        self.assertEqual(len(raw_hash), 20)
        self.assertEqual(raw_hash, bytes.fromhex(INFO_HASH))

    def test_preserves_an_existing_tracker_query(self):
        url = build_announce_url(
            "https://tracker.example/announce?token=abc", INFO_HASH, PEER_ID,
            port=6881, uploaded=0, downloaded=0, left=1,
        )
        self.assertIn("token=abc&info_hash=", url)

