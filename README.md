# BitTorrent Client — Milestone 1

A small Python project for learning networking and systems programming, one
milestone at a time. Today it is an **offline .torrent metadata inspector**.
It makes no network requests and does not download anything.

## What is BitTorrent?

BitTorrent distributes files among peers. Files are divided into pieces, and
peers can exchange those pieces with each other. A `.torrent` file describes
the content; it does not contain the downloadable files themselves.

## What this milestone does

- Reads a `.torrent` file and decodes its Bencode data.
- Validates classic v1 metadata for single-file and multi-file torrents.
- Prints the tracker URL (if present), name, total size in bytes, file count,
  piece length, number of pieces, torrent type, and hexadecimal info hash.
- Reports missing/unreadable files, invalid Bencode, and malformed metadata.

There is no tracker communication, peer discovery, TCP, handshake, peer message
handling, downloading, piece verification, or concurrency yet.

## Focused primitive-decoder progress

BitTorrent Client Learning Project

- [x] Bencode integers
- [x] Bencode byte strings
- [ ] Bencode lists
- [ ] Bencode dictionaries
- [ ] Parse .torrent metadata
- [ ] Calculate info hash
- [ ] Contact tracker
- [ ] Connect to peer
- [ ] BitTorrent handshake
- [ ] Download and verify pieces

This checklist marks the deliberately small primitive-decoder exercise. The
repository also contains earlier, broader metadata-inspector work, which is left
unchanged for preservation.

## Run it

Requires **Python 3.10+**, with no third-party packages. Run from the project root:

```powershell
python -m torrent_inspector "C:\path\to\example.torrent"
python -m torrent_inspector --help
python -m unittest discover -s tests -v
```

On Windows, `py` can replace `python` if that is how Python is installed.
Use a local v1 `.torrent` file, not a magnet link. Paths containing spaces should
be quoted. The supplied tests generate tiny synthetic metadata in temporary
files, so testing requires no torrent download or network access.

Example output for a three-byte file split into one piece:

```text
Tracker URL: 'http://example.test/announce'
Torrent name: 'a.txt'
Torrent type: single-file
File count: 1
Total file size: 3 bytes
Piece length: 4 bytes
Number of pieces: 1
Info hash (SHA-1): <40 hexadecimal characters>
```

Names and tracker strings use Python-style quoted escapes for safe terminal
display, including non-ASCII characters. A successful run exits with status 0;
file or data errors go to stderr with status 1. Argument errors use status 2.

## Bencode in a minute

Bencode has four types:

| Type | Encoding example | Python result |
| --- | --- | --- |
| Integer | `i42e` | `42` |
| Byte string | `4:spam` | `b"spam"` |
| List | `li1e4:spame` | `[1, b"spam"]` |
| Dictionary | `d4:name4:spame` | `{b"name": b"spam"}` |

String lengths count **bytes**, not characters. Dictionary keys are byte strings
in sorted byte order. The decoder preserves binary strings, including `pieces`,
and decodes only known text fields as UTF-8. It rejects duplicate/unsorted keys,
invalid numeric forms, truncated values, and trailing data.

The decoder uses a cursor and recursive calls: a container reads children until
its closing `e`. A depth limit of 100 keeps excessive nesting from exhausting
Python's call stack. Python's integer-conversion digit limit also applies.

## What the info hash represents

For v1 torrents, the info hash is the 20-byte SHA-1 digest of the **exact encoded
`info` dictionary bytes in the original file**, displayed here as 40 hexadecimal
characters. The parser records the start and end of that value instead of
decoding and re-encoding it for hashing.

It identifies the torrent's content description, including names, sizes, and
piece hashes. It is not the hash of the whole `.torrent` file or the downloaded
file. Changing only the tracker outside `info` leaves it unchanged; changing
bytes inside `info` changes the hash. SHA-1 is used because v1 specifies it.

The `pieces` string stores one 20-byte digest per piece. Its byte length divided
by 20 gives the piece count. The inspector checks that this matches
`ceil(total_size / piece_length)`. Multi-file torrents are treated as one
concatenated byte stream for this calculation, so pieces can cross file
boundaries. It does not verify the piece digests against content yet.

Protocol reference: [BEP 3 — The BitTorrent Protocol Specification](https://www.bittorrent.org/beps/bep_0003.html).

## Project structure

```text
BitTorrent_Client/
├── .gitignore
├── README.md
├── torrent_inspector/
│   ├── __init__.py
│   ├── __main__.py
│   ├── bencode.py
│   └── metadata.py
└── tests/
    ├── test_bencode.py
    └── test_metadata.py
```

- `.gitignore`: excludes Python caches and a local virtual environment.
- `README.md`: learning guide, commands, scope, and roadmap.
- `torrent_inspector/__init__.py`: marks the inspector as a Python package.
- `torrent_inspector/__main__.py`: command-line parsing, file reading, output,
  and user-facing errors.
- `torrent_inspector/bencode.py`: four-type decoder and original `info` byte capture.
- `torrent_inspector/metadata.py`: torrent field validation, summary, and info hashing.
- `tests/test_bencode.py`: valid types, binary strings, invalid encodings, nesting,
  and top-level `info` capture.
- `tests/test_metadata.py`: single/multi-file data, hash boundaries, zero-length
  content, malformed metadata, and command-line success/errors.

## Deliberate limits

This is a small learning implementation, not a production parser. It reads the
whole metadata file into memory. It supports classic v1 torrents and explicitly
rejects v2/hybrid metadata. Unknown fields are ignored for the summary but remain
included in the original `info` bytes when hashing. Only `announce` is displayed;
alternate tracker tiers are not interpreted. Missing `announce` is allowed.
File paths are checked as text metadata, never created on disk. Download-time
path validation belongs to a later milestone.

## Roadmap

- [✅] Milestone 1 - Torrent metadata parser
- [ ] Milestone 2 - Tracker communication
- [ ] Milestone 3 - Peer discovery
- [ ] Milestone 4 - TCP peer connection
- [ ] Milestone 5 - BitTorrent handshake
- [ ] Milestone 6 - Peer message protocol
- [ ] Milestone 7 - Download one piece
- [ ] Milestone 8 - Verify piece hashes
- [ ] Milestone 9 - Download complete file
- [ ] Milestone 10 - Concurrent peer downloading

## Five concepts to study next

1. Bytes versus Unicode: byte lengths, UTF-8, and binary digests.
2. Recursive descent parsing: cursors, nested containers, and delimiters.
3. Encoding validity versus application-level metadata validity.
4. Hash inputs: exact serialization, digest bytes, and hexadecimal display.
5. Piece boundaries: ceiling division and multi-file byte streams.
