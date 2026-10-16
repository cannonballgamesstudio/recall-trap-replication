from __future__ import annotations

import argparse
import sys

from ragfusion.eval.index_register import index_and_register


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m ragfusion.eval",
        description="Build + register one static srclight index for the A/B eval.",
    )
    parser.add_argument("--repo", required=True, help="repo id the client sends, e.g. django/django")
    parser.add_argument("--ref", required=True, help="ref name to register under (query branch resolves to this)")
    parser.add_argument("--sha", required=True, help="head sha recorded for the staleness check")
    parser.add_argument("--checkout", required=True, help="path to the checked-out worktree (also the registered worktree)")
    parser.add_argument("--registry", required=True, help="path to the registry sqlite file retrievald reads")
    parser.add_argument(
        "--embed-model",
        default=None,
        help="srclight provider string, e.g. openai:Qwen/Qwen3-Embedding-8B; omit for keyword-only",
    )
    parser.add_argument("--dims", type=int, default=None, help="embedding dimensions, if pinning a non-default width")
    args = parser.parse_args(argv)

    result = index_and_register(
        repo=args.repo,
        ref=args.ref,
        sha=args.sha,
        checkout=args.checkout,
        registry_db=args.registry,
        embed_model=args.embed_model,
        dims=args.dims,
    )
    print(
        f"indexed {result.files_indexed} files, {result.symbols} symbols, "
        f"{result.edges} edges -> {result.index_dir}",
        file=sys.stderr,
    )
    print(
        f"registered {args.repo}@{args.ref} (sha {args.sha[:12]}) status=ready in {args.registry}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
