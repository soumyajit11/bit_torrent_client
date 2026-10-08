import unittest

from torrent_inspector.tracker import TrackerResponseError, parse_tracker_response


class TrackerResponseTests(unittest.TestCase):
    def test_extracts_interval_and_preserves_raw_peers(self):
        peers = b"\x7f\x00\x00\x01\x1a\xe1"
        data = b"d8:intervali1800e5:peers6:" + peers + b"e"

        response = parse_tracker_response(data)

        self.assertEqual(response.interval, 1800)
        self.assertEqual(response.peers, peers)

    def test_reports_tracker_failure_reason(self):
        with self.assertRaisesRegex(TrackerResponseError, "torrent not registered"):
            parse_tracker_response(b"d14:failure reason22:torrent not registerede")

    def test_rejects_missing_interval(self):
        with self.assertRaisesRegex(TrackerResponseError, "interval"):
            parse_tracker_response(b"d5:peers0:e")

    def test_rejects_zero_or_non_integer_interval(self):
        for data in (b"d8:intervali0e5:peers0:e", b"d8:interval1:x5:peers0:e"):
            with self.subTest(data=data):
                with self.assertRaisesRegex(TrackerResponseError, "interval"):
                    parse_tracker_response(data)

    def test_rejects_missing_or_non_byte_peers(self):
        for data in (b"d8:intervali1ee", b"d8:intervali1e5:peersi1ee"):
            with self.subTest(data=data):
                with self.assertRaisesRegex(TrackerResponseError, "peers"):
                    parse_tracker_response(data)

    def test_rejects_malformed_bencode(self):
        with self.assertRaisesRegex(TrackerResponseError, "invalid tracker response Bencode"):
            parse_tracker_response(b"d8:intervali1800e5:peers")
