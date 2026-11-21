"""Command-line helpers: python -m gestureplaykit [--version|download-models]."""
from __future__ import annotations

import argparse
from . import __version__, download_models


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="gestureplaykit", description="GesturePlayKit utilities")
    parser.add_argument("--version", action="version", version=f"GesturePlayKit {__version__}")
    command = parser.add_subparsers(dest="command")
    download = command.add_parser("download-models", help="Download MediaPipe model files once")
    download.add_argument("--dir", default="models", help="Output folder (default: models)")
    download.add_argument("--overwrite", action="store_true", help="Replace existing model files")
    group = download.add_mutually_exclusive_group()
    group.add_argument("--hands-only", action="store_true", help="Only download the hand model")
    group.add_argument("--faces-only", action="store_true", help="Only download the face model")
    group.add_argument("--poses-only", action="store_true", help="Only download the pose model")
    download.add_argument("--poses", action="store_true", help="Also download the optional body pose model")
    args = parser.parse_args(argv)
    if args.command == "download-models":
        options = dict(overwrite=args.overwrite,
                       hands=not (args.faces_only or args.poses_only),
                       faces=not (args.hands_only or args.poses_only))
        if args.poses or args.poses_only:
            options["poses"] = True
        paths = download_models(args.dir, **options)
        for path in paths:
            print(f"Ready: {path}")
    else:
        parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
