"""Read-only PNG / GLB / video audit. Does not assess artistic quality."""
import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import zlib
from pathlib import Path


def inspect_file(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    result = {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    if path.suffix.lower() == '.png':
        if data[:8] != b'\x89PNG\r\n\x1a\n':
            raise ValueError('Invalid PNG signature')
        offset, payload, ended, ihdr = 8, bytearray(), False, None
        while offset < len(data):
            length = struct.unpack_from('>I', data, offset)[0]
            kind = data[offset+4:offset+8]
            chunk = data[offset+8:offset+8+length]
            crc = struct.unpack_from('>I', data, offset+8+length)[0]
            if zlib.crc32(kind + chunk) & 0xffffffff != crc:
                raise ValueError('PNG CRC mismatch')
            if kind == b'IHDR':
                ihdr = struct.unpack('>IIBBBBB', chunk)
            if kind == b'IDAT':
                payload.extend(chunk)
            if kind == b'IEND':
                ended = True
                break
            offset += length + 12
        if not ended or not ihdr or not payload:
            raise ValueError('Incomplete PNG')
        decompressed = zlib.decompress(payload)
        result.update(format='PNG', width=ihdr[0], height=ihdr[1], bit_depth=ihdr[2],
                      color_type=ihdr[3], alpha_channel=ihdr[3] in (4, 6),
                      decompressed_bytes=len(decompressed), integrity='pass')
    elif path.suffix.lower() == '.glb':
        magic, version, total = struct.unpack_from('<4sII', data)
        if magic != b'glTF' or version != 2 or total != len(data):
            raise ValueError('Invalid GLB header')
        offset, document = 12, None
        while offset < len(data):
            length, kind = struct.unpack_from('<II', data, offset)
            if offset + 8 + length > len(data):
                raise ValueError('Truncated GLB chunk')
            if kind == 0x4e4f534a:
                document = json.loads(data[offset+8:offset+8+length])
            offset += 8 + length
        if document is None:
            raise ValueError('Missing GLB JSON')
        nodes = document.get('nodes', [])
        skins = document.get('skins', [])
        joints = [joint for skin in skins for joint in skin['joints']]
        if any(j < 0 or j >= len(nodes) for j in joints):
            raise ValueError('Skin references invalid joint')
        result.update(format='GLB2', meshes=len(document.get('meshes', [])),
                      skins=len(skins), joint_references=len(joints),
                      animations=[a.get('name', '<unnamed>') for a in document.get('animations', [])],
                      materials=[m.get('name', '<unnamed>') for m in document.get('materials', [])],
                      integrity='pass', limits='Header, chunks and joint references only; not full glTF validation or visual acceptance')
    elif path.suffix.lower() in ('.mp4', '.avi', '.webm'):
        probe = shutil.which('ffprobe')
        if not probe:
            raise RuntimeError('ffprobe unavailable; video check not executed')
        process = subprocess.run([probe, '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)],
                                 check=True, capture_output=True, text=True)
        metadata = json.loads(process.stdout)
        result.update(format='video', streams=metadata['streams'],
                      duration=metadata.get('format', {}).get('duration'), integrity='metadata-pass',
                      limits='ffprobe metadata; full playback and temporal visual review still required')
    else:
        result.update(format='other', integrity='hash-only')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='+', help='Existing files; no mutation')
    parser.add_argument('--output', required=True, help='JSON report path')
    args = parser.parse_args()
    rows, failures = [], []
    for path in args.paths:
        try:
            rows.append(inspect_file(path))
        except (ValueError, OSError, RuntimeError, struct.error, zlib.error,
                subprocess.CalledProcessError, json.JSONDecodeError) as error:
            failures.append({'path': path, 'error': str(error)})
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({'files': rows, 'failures': failures,
                                 'visual_acceptance': 'requires actual image/motion inspection'}, indent=2), encoding='utf-8')
    print(json.dumps({'checked': len(rows), 'failures': len(failures), 'report': str(target)}))
    raise SystemExit(1 if failures else 0)


if __name__ == '__main__':
    main()
