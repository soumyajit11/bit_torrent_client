"""A small, strict Bencode decoder. Strings and dictionary keys stay bytes."""


class BencodeError(ValueError):
    """The input is not valid Bencode."""


def decode_integer(data: bytes) -> int:
    """Decode one complete Bencoded integer such as b"i42e"."""
    if not data.startswith(b"i") or not data.endswith(b"e"):
        raise BencodeError("integer must start with 'i' and end with 'e'")

    raw = data[1:-1]
    digits = raw[1:] if raw.startswith(b"-") else raw
    if (not digits.isdigit() or raw == b"-0"
            or (len(digits) > 1 and digits.startswith(b"0"))):
        raise BencodeError("invalid integer")
    return int(raw)


def decode_byte_string(data: bytes) -> bytes:
    """Decode one complete Bencoded byte string such as b"4:spam"."""
    separator = data.find(b":")
    if separator == -1:
        raise BencodeError("byte string is missing ':'")

    raw_length = data[:separator]
    if not raw_length.isdigit() or (len(raw_length) > 1 and raw_length.startswith(b"0")):
        raise BencodeError("invalid byte-string length")
    value = data[separator + 1:]
    if len(value) != int(raw_length):
        raise BencodeError("byte string length does not match its data")
    return value


class Decoder:
    def __init__(self, data: bytes):
        self.data = data
        self.position = 0
        self.info_bytes = None

    def fail(self, message):
        raise BencodeError(f"{message} at byte {self.position}")

    def decode(self):
        value = self.read_value()
        if self.position != len(self.data):
            self.fail("trailing data")
        return value

    def read_value(self, depth=0):
        if depth > 100:
            self.fail("nesting exceeds the supported limit of 100")
        if self.position >= len(self.data):
            self.fail("unexpected end of input")
        token = self.data[self.position:self.position + 1]
        if token == b"i":
            self.position += 1
            end = self.data.find(b"e", self.position)
            if end == -1:
                self.fail("unterminated integer")
            raw = self.data[self.position:end]
            digits = raw[1:] if raw.startswith(b"-") else raw
            if (not digits.isdigit() or raw == b"-0"
                    or (len(digits) > 1 and digits.startswith(b"0"))):
                self.fail("invalid integer")
            try:
                value = int(raw)
            except ValueError:
                self.fail("integer exceeds Python's supported digit limit")
            self.position = end + 1
            return value
        if token.isdigit():
            return self.read_string()
        if token in (b"l", b"d"):
            self.position += 1
            result = [] if token == b"l" else {}
            previous_key = None
            while True:
                if self.position >= len(self.data):
                    self.fail("unterminated container")
                if self.data[self.position:self.position + 1] == b"e":
                    self.position += 1
                    return result
                if token == b"l":
                    result.append(self.read_value(depth + 1))
                else:
                    key = self.read_string()
                    if previous_key is not None and key <= previous_key:
                        self.fail("dictionary keys must be unique and sorted")
                    previous_key = key
                    start = self.position
                    result[key] = self.read_value(depth + 1)
                    # Hash the original top-level info value, never a re-encoding.
                    if depth == 0 and key == b"info":
                        self.info_bytes = self.data[start:self.position]
            
        self.fail("unknown value marker")

    def read_string(self):
        colon = self.data.find(b":", self.position)
        if colon == -1:
            self.fail("missing byte-string length separator")
        raw = self.data[self.position:colon]
        if not raw.isdigit() or (len(raw) > 1 and raw.startswith(b"0")):
            self.fail("invalid byte-string length")
        try:
            length = int(raw)
        except ValueError:
            self.fail("byte-string length exceeds Python's supported digit limit")
        start = colon + 1
        end = start + length
        if end > len(self.data):
            self.fail("truncated byte string")
        self.position = end
        return self.data[start:end]


def decode(data: bytes):
    """Decode exactly one Bencode value, rejecting trailing bytes."""
    return Decoder(data).decode()
