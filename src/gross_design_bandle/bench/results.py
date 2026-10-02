"""Append-only checksummed JSONL chunks with resume deduplication."""
import fcntl
import hashlib
import json
import os
from pathlib import Path


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def chunk_key(row):
    return tuple(row[k] for k in ('run_hash', 'series', 'mode', 'point_index', 'chunk_index'))


def read_chunks(path):
    path = Path(path)
    if not path.exists():
        return {}
    result = {}
    with path.open('rb') as f:
        for line in f:
            try:
                record = json.loads(line)
                payload = record['payload']
                if hashlib.sha256(_canonical(payload).encode()).hexdigest() != record['sha256']:
                    raise ValueError('chunk checksum mismatch')
                key = chunk_key(payload)
                if key in result:
                    raise ValueError('duplicate stored chunk')
                result[key] = payload
            except (KeyError, json.JSONDecodeError) as exc:
                raise ValueError('incomplete result chunk') from exc
    return result


def append_chunk(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    key = chunk_key(payload)
    encoded = (_canonical({'payload': payload, 'sha256': hashlib.sha256(_canonical(payload).encode()).hexdigest()}) + '\n').encode()
    with path.open('a+b') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        existing = read_chunks(path)
        if key in existing:
            if _canonical(existing[key]) != _canonical(payload):
                raise ValueError('resume chunk identity conflicts with stored data')
            return False
        f.write(encoded); f.flush(); os.fsync(f.fileno())
        return True
