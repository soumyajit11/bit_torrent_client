import unittest

from torrent_inspector.bencode import BencodeError, Decoder, decode


class BencodeTests(unittest.TestCase):
    def test_four_types_and_binary_strings(self):
        for encoded, expected in [
            (b"i42e", 42), (b"i-7e", -7), (b"i0e", 0),
            (b"0:", b""), (b"3:\x00\xffe", b"\x00\xffe"),
            (b"li1e3:abce", [1, b"abc"]),
            (b"d1:ali2ee1:b0:e", {b"a": [2], b"b": b""}),
            (b"le", []), (b"de", {}),
        ]:
            with self.subTest(encoded=encoded):
                self.assertEqual(decode(encoded), expected)

    def test_invalid_encodings(self):
        for encoded in [
            b"", b"x", b"i03e", b"i-0e", b"i+1e", b"ie", b"i1",
            b"4:abc", b"03:abc", b"1", b"li1e", b"i1ei2e",
            b"di1e1:ae", b"d1:bi1e1:ai2ee", b"d1:ai1e1:ai2ee",
            b"d1:ae", b"l" * 102 + b"e" * 102,
        ]:
            with self.subTest(encoded=encoded):
                with self.assertRaises(BencodeError):
                    decode(encoded)

    def test_captures_only_top_level_info_bytes(self):
        raw_info = b"d4:infod1:xi1ee4:name1:xe"
        decoder = Decoder(b"d4:info" + raw_info + b"e")
        decoder.decode()
        self.assertEqual(decoder.info_bytes, raw_info)
