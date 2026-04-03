import argparse
import os
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.dirname(SCRIPT_DIR)
if FRONTEND_DIR not in sys.path:
    sys.path.insert(0, FRONTEND_DIR)

from core.library import MusicLibrary


def main():
    parser = argparse.ArgumentParser(description="音乐库扫描基准测试")
    parser.add_argument("directory", nargs="?", default=".", help="待扫描目录")
    parser.add_argument("--repeat", type=int, default=3, help="重复次数")
    args = parser.parse_args()

    target = os.path.abspath(args.directory)
    if not os.path.exists(target):
        raise SystemExit(f"目录不存在: {target}")

    elapsed = []
    song_count = 0

    for _ in range(max(1, args.repeat)):
        library = MusicLibrary()
        start = time.perf_counter()
        success = library.scan_music(target)
        end = time.perf_counter()

        if not success:
            raise SystemExit("扫描失败，无法统计基线")

        song_count = len(library.songs)
        elapsed.append(end - start)

    avg = sum(elapsed) / len(elapsed)
    print("=== Scan Benchmark ===")
    print(f"directory: {target}")
    print(f"songs: {song_count}")
    print(f"repeat: {len(elapsed)}")
    print(f"avg_seconds: {avg:.3f}")
    print(f"min_seconds: {min(elapsed):.3f}")
    print(f"max_seconds: {max(elapsed):.3f}")


if __name__ == "__main__":
    main()


