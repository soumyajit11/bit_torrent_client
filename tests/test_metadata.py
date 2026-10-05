import contextlib
import hashlib
import io
from pathlib import Path
import tempfile
import unittest

from torrent_inspector.__main__ import main
from torrent_inspector.metadata import MetadataError, inspect_torrent


PIECES = b"20:" + b"\x00\xff" * 10
SINGLE = b"d6:lengthi3e4:name5:a.txt12:piece lengthi4e6:pieces" + PIECES + b"e"
MULTI = (b"d5:filesld6:lengthi1e4:pathl1:aeed6:lengthi2e4:pathl1:beee"
         b"4:name6:bundle12:piece lengthi4e6:pieces" + PIECES + b"e")


def torrent(info=SINGLE, tracker=b"http://example.test/announce"):
    return (b"d8:announce" + str(len(tracker)).encode() + b":" + tracker
            + b"4:info" + info + b"e")


class MetadataTests(unittest.TestCase):
    def test_single_file_and_exact_info_hash(self):
        # An unknown info field must still contribute to the info hash.
        info = SINGLE[:-1] + b"7:privatei1ee"
        metadata = inspect_torrent(torrent(info))
        self.assertEqual(metadata.info_hash, hashlib.sha1(info).hexdigest())
        self.assertEqual(metadata.info_hash,
                         inspect_torrent(torrent(info, b"udp://other.test:80")).info_hash)
        self.assertEqual((metadata.name, metadata.total_size, metadata.piece_length,
                          metadata.piece_count, metadata.multi_file),
                         ("a.txt", 3, 4, 1, False))

    def test_multi_file_pieces_span_file_boundaries(self):
        metadata = inspect_torrent(torrent(MULTI))
        self.assertTrue(metadata.multi_file)
        self.assertEqual((metadata.total_size, metadata.file_count, metadata.piece_count),
                         (3, 2, 1))

    def test_zero_length_trackerless_torrent(self):
        info = SINGLE.replace(b"lengthi3e", b"lengthi0e").replace(PIECES, b"0:")
        metadata = inspect_torrent(b"d4:info" + info + b"e")
        self.assertIsNone(metadata.tracker)
        self.assertEqual(metadata.piece_count, 0)

    def test_malformed_metadata(self):
        for data in [
            b"le", b"de", b"d4:infoi1ee",
            torrent(SINGLE.replace(b"lengthi3e", b"lengthi-1e")),
            torrent(SINGLE.replace(b"lengthi4e", b"lengthi0e")),
            torrent(SINGLE.replace(PIECES, b"1:x")),
            torrent(SINGLE.replace(PIECES, b"0:")),
            torrent(SINGLE.replace(b"5:a.txt", b"1:\xff")),
            torrent(SINGLE.replace(b"6:lengthi3e", b"")),
            torrent(SINGLE.replace(b"6:length", b"5:filesle6:length")),
            torrent(MULTI.replace(b"4:pathl1:ae", b"4:pathle")),
            torrent(SINGLE.replace(b"4:name", b"12:meta versioni2e4:name")),
        ]:
            with self.subTest(data=data):
                with self.assertRaises(MetadataError):
                    inspect_torrent(data)

    def test_cli_success_and_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.torrent"
            for content, expected in [(None, "file not found"), (b"x", "invalid bencode"),
                                      (b"de", "malformed torrent metadata"),
                                      (torrent(), "Info hash (SHA-1)")]:
                if content is not None:
                    path.write_bytes(content)
                output = io.StringIO()
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                    status = main([str(path)])
                self.assertEqual(status, 0 if content == torrent() else 1)
                self.assertIn(expected, output.getvalue())
