"""Run with: python -m torrent_inspector path/to/file.torrent."""

import argparse
from pathlib import Path
import sys

from .bencode import BencodeError
from .metadata import MetadataError, inspect_torrent


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspect a BitTorrent v1 .torrent file offline.")
    parser.add_argument("torrent", type=Path, help="path to a .torrent file")
    args = parser.parse_args(argv)
    try:
        metadata = inspect_torrent(args.torrent.read_bytes())
    except FileNotFoundError:
        print(f"Error: file not found: {args.torrent}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Error: cannot read file: {exc}", file=sys.stderr)
        return 1
    except BencodeError as exc:
        print(f"Error: invalid bencode: {exc}", file=sys.stderr)
        return 1
    except MetadataError as exc:
        print(f"Error: malformed torrent metadata: {exc}", file=sys.stderr)
        return 1

    print(f"Tracker URL: {ascii(metadata.tracker) if metadata.tracker else 'not provided'}")
    print(f"Torrent name: {ascii(metadata.name)}")
    print(f"Torrent type: {'multi-file' if metadata.multi_file else 'single-file'}")
    print(f"File count: {metadata.file_count}")
    print(f"Total file size: {metadata.total_size:,} bytes")
    print(f"Piece length: {metadata.piece_length:,} bytes")
    print(f"Number of pieces: {metadata.piece_count}")
    print(f"Info hash (SHA-1): {metadata.info_hash}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
