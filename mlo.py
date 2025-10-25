#!/usr/bin/env python3
"""
mlo.py — Search JSON for user-provided keywords ("keys")

Other capabilities retained from mlo.py:
- Works on a single JSON file OR a directory (recursively scans *.json by default).
- Reports where each match was found: file path + JSON pointer path.
- Case-insensitive by default (toggle with --case-sensitive).
- Output can be "pretty" (default) or JSON (machine-readable) via --output json.
"""
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple, Iterable, Union

JSONScalar = Union[str, int, float, bool, None]

def load_keys_from_file(path: Path) -> List[str]:
    text = path.read_text(encoding="utf-8").strip()
    # Try JSON first (e.g., ["alpha","beta"])
    try:
        data = json.loads(text)
        if isinstance(data, list) and all(isinstance(x, str) for x in data):
            return [x.strip() for x in data if x.strip()]
    except json.JSONDecodeError:
        pass
    # Fallback: newline-separated or comma-separated text
    parts = [p.strip() for p in text.replace("\r", "\n").replace(",", "\n").split("\n")]
    return [p for p in parts if p]

def normalize_terms(terms: Iterable[str], case_sensitive: bool) -> List[str]:
    cleaned = []
    for t in terms:
        t = t.strip()
        if not t:
            continue
        cleaned.append(t if case_sensitive else t.lower())
    # Preserve order but remove dupes
    seen = set()
    unique = []
    for t in cleaned:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique

def iter_json_files(root: Path, extensions: Iterable[str]) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    exts = {e.lower().lstrip(".") for e in extensions}
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower().lstrip(".") in exts:
            yield p

def scalar_to_str(value: JSONScalar) -> str:
    # For matching, stringify scalars
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)

def search_json(obj: Any,
                keys: List[str],
                case_sensitive: bool,
                keys_only: bool,
                values_only: bool,
                path: str = "") -> List[Tuple[str, str]]:
    """
    Returns list of (matched_term, json_pointer_path) for each match found in obj.
    - If keys_only: only check dict keys.
    - If values_only: only check values (scalars become strings before matching).
    - If neither flag is set: check both keys and values.
    """
    matches: List[Tuple[str, str]] = []

    def norm(s: str) -> str:
        return s if case_sensitive else s.lower()

    if isinstance(obj, dict):
        for k, v in obj.items():
            kp = f"{path}/{k}"
            if not values_only:
                nk = norm(str(k))
                for term in keys:
                    if term in nk:
                        matches.append((term, kp))
            if not keys_only:
                if isinstance(v, (dict, list)):
                    matches.extend(search_json(v, keys, case_sensitive, keys_only, values_only, kp))
                else:
                    sval = scalar_to_str(v)
                    nv = norm(sval)
                    for term in keys:
                        if term in nv:
                            matches.append((term, kp))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            ip = f"{path}/{idx}"
            if isinstance(item, (dict, list)):
                matches.extend(search_json(item, keys, case_sensitive, keys_only, values_only, ip))
            else:
                if not keys_only:
                    sval = scalar_to_str(item)
                    nv = norm(sval)
                    for term in keys:
                        if term in nv:
                            matches.append((term, ip))
    else:
        # scalar at root
        if not keys_only:
            sval = scalar_to_str(obj)
            nv = norm(sval)
            for term in keys:
                if term in nv:
                    matches.append((term, path or "/"))
    return matches

def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Search JSON files for user-provided keywords ('keys')."
    )
    p.add_argument("path", help="Path to a JSON file or a directory to scan recursively.")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--keys", help="Comma-separated list of terms (e.g., 'name,email,token').")
    g.add_argument("--keys-file", help="Path to file containing terms (JSON array or newline-separated).")
    p.add_argument("--key", action="append", default=[], help="Repeatable single term (e.g., --key token --key email).")
    p.add_argument("--case-sensitive", action="store_true", help="Enable case-sensitive matching (default: case-insensitive).")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--keys-only", action="store_true", help="Match only on keys.")
    mode.add_argument("--values-only", action="store_true", help="Match only on values.")
    p.add_argument("--extensions", default="json", help="File extensions to scan in directories (comma-separated). Default: json")
    p.add_argument("--output", choices=["pretty", "json"], default="pretty", help="Output format. Default: pretty")
    return p

def main():
    ap = build_argparser()
    args = ap.parse_args()

    root = Path(args.path).expanduser().resolve()
    if not root.exists():
        ap.error(f"Path not found: {root}")

    terms: List[str] = []
    if args.keys:
        terms.extend([t.strip() for t in args.keys.split(",") if t.strip()])
    if args.key:
        terms.extend([t.strip() for t in args.key if t.strip()])
    if args.keys_file:
        terms.extend(load_keys_from_file(Path(args.keys_file).expanduser().resolve()))

    # Interactive fallback if no terms supplied
    if not terms:
        try:
            raw = input("Enter comma-separated search keys: ").strip()
        except EOFError:
            raw = ""
        if raw:
            terms.extend([t.strip() for t in raw.split(",") if t.strip()])

    if not terms:
        ap.error("No search keys provided. Use --keys, --key, --keys-file, or provide keys interactively.")

    keys = normalize_terms(terms, args.case_sensitive)
    exts = [e.strip() for e in args.extensions.split(",") if e.strip()]

    results: Dict[str, Dict[str, List[str]]] = {}  # file -> term -> [paths]

    for fp in iter_json_files(root, exts):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            # Skip unreadable/invalid JSON files
            continue
        hits = search_json(data, keys, args.case_sensitive, args.keys_only, args.values_only, path="")
        if not hits:
            continue
        by_term: Dict[str, List[str]] = {}
        for term, jptr in hits:
            by_term.setdefault(term, []).append(jptr or "/")
        results[str(fp)] = by_term

    # Prepare found/missing
    found_terms = set()
    for _file, term_map in results.items():
        for t in term_map:
            found_terms.add(t)
    missing_terms = [t for t in keys if t not in found_terms]

    if args.output == "json":
        out = {
            "searched_root": str(root),
            "keys": keys,
            "case_sensitive": args.case_sensitive,
            "keys_only": args.keys_only,
            "values_only": args.values_only,
            "results": results,
            "missing_keys": missing_terms,
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    # Pretty output
    print(f"\nSearched: {root}")
    print(f"Keys ({'case-sensitive' if args.case_sensitive else 'case-insensitive'}): {', '.join(keys)}")
    if args.keys_only:
        print("Mode: keys-only")
    elif args.values_only:
        print("Mode: values-only")
    else:
        print("Mode: keys + values")
    print("")

    if not results:
        print("No matches found in provided files.\n")
    else:
        for fpath, term_map in sorted(results.items()):
            print(f"File: {fpath}")
            for term in keys:
                paths = term_map.get(term, [])
                if paths:
                    print(f"  {term} ✅  ({len(paths)} matches)")
                    for pth in paths:
                        print(f"    - {pth}")
                else:
                    print(f"  {term} —")
            print("")

    if missing_terms:
        print("Missing keys (not found anywhere):")
        for t in missing_terms:
            print(f"  {t} ❌")
    else:
        print("All keys were found at least once. 🎉")

if __name__ == "__main__":
    main()
