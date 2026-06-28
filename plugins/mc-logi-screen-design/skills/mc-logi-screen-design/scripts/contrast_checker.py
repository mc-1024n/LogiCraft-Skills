#!/usr/bin/env python3
"""
WCAG Contrast Checker (vendored — self-contained, no external deps)

mc-logi-screen-design 에 동봉된 자립 스크립트. 외부 스킬(ui-design-system 등) 설치 없이
Phase 3 D5(WCAG 대비 게이트)가 어느 사용자 환경에서도 동작하도록 표준 라이브러리만 사용한다.
WCAG 2.1 상대휘도/대비비 공식은 W3C 공개 표준(https://www.w3.org/TR/WCAG21/#dfn-relative-luminance)이다.

출력은 ASCII only — Windows 콘솔(cp949)에서도 인코딩 에러 없이 동작한다.

Usage:
    python contrast_checker.py <fg> <bg>
    python contrast_checker.py "#111827" "#FFFFFF"

    # Palette mode: DS 토큰 hex 들을 {"name":"#hex", ...} JSON 으로 저장 후 모든 조합 검사
    python contrast_checker.py --palette tokens.json

WCAG 2.1 thresholds:
    AA  normal text:  4.5:1
    AA  large text:   3.0:1   (>= 18pt or 14pt bold)
    AAA normal text:  7.0:1
    AAA large text:   4.5:1
    Non-text UI:      3.0:1
"""

import json
import sys
from typing import Dict, List, Tuple

THRESHOLDS = {
    "AA_normal": 4.5,
    "AA_large": 3.0,
    "AAA_normal": 7.0,
    "AAA_large": 4.5,
    "non_text": 3.0,
}


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Parse #RRGGBB or #RGB into an (R, G, B) tuple."""
    h = hex_color.lstrip("#").strip()
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError("Invalid hex color: %r" % hex_color)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore


def relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """WCAG relative luminance."""
    def channel(c: int) -> float:
        s = c / 255
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: str, bg: str) -> float:
    """WCAG contrast ratio (1.0 to 21.0). Order-independent."""
    l1 = relative_luminance(hex_to_rgb(fg))
    l2 = relative_luminance(hex_to_rgb(bg))
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def grade(ratio: float) -> Dict[str, bool]:
    return {
        "AA_normal": ratio >= THRESHOLDS["AA_normal"],
        "AA_large": ratio >= THRESHOLDS["AA_large"],
        "AAA_normal": ratio >= THRESHOLDS["AAA_normal"],
        "AAA_large": ratio >= THRESHOLDS["AAA_large"],
        "non_text_ui": ratio >= THRESHOLDS["non_text"],
    }


def _verdict(ratio: float) -> str:
    if ratio >= THRESHOLDS["AAA_normal"]:
        return "AAA (best - passes everywhere)"
    if ratio >= THRESHOLDS["AA_normal"]:
        return "AA (safe for body text)"
    if ratio >= THRESHOLDS["AA_large"]:
        return "AA Large only (>=18pt or 14pt bold; not safe for body text)"
    return "FAIL (do not use for text)"


def check_pair(fg: str, bg: str) -> Dict:
    ratio = contrast_ratio(fg, bg)
    return {"fg": fg, "bg": bg, "ratio": round(ratio, 2),
            "passes": grade(ratio), "verdict": _verdict(ratio)}


def render_text_report(result: Dict) -> str:
    p = result["passes"]
    mark = lambda b: "PASS" if b else "FAIL"
    return (
        "\n%s  on  %s\n"
        "  Contrast ratio : %s:1\n"
        "  Verdict        : %s\n"
        "  AA  normal text: %s    (>= 4.5:1)\n"
        "  AA  large text : %s    (>= 3.0:1)\n"
        "  AAA normal text: %s    (>= 7.0:1)\n"
        "  AAA large text : %s    (>= 4.5:1)\n"
        "  Non-text UI    : %s    (>= 3.0:1)\n"
        % (result["fg"], result["bg"], result["ratio"], result["verdict"],
           mark(p["AA_normal"]), mark(p["AA_large"]), mark(p["AAA_normal"]),
           mark(p["AAA_large"]), mark(p["non_text_ui"]))
    )


def check_palette(palette: Dict) -> List[Dict]:
    """Flatten a palette dict and check every fg/bg combination."""
    flat: List[Tuple[str, str]] = []

    def walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(v, ("%s.%s" % (path, k)) if path else str(k))
        elif isinstance(obj, str) and obj.startswith("#"):
            try:
                hex_to_rgb(obj)
                flat.append((path, obj))
            except ValueError:
                pass

    walk(palette)
    results = []
    for fg_path, fg in flat:
        for bg_path, bg in flat:
            if fg == bg:
                continue
            results.append({"fg_token": fg_path, "bg_token": bg_path, **check_pair(fg, bg)})
    return results


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    if args[0] == "--palette":
        with open(args[1]) as f:
            palette = json.load(f)
        results = check_palette(palette)
        viable = [r for r in results if r["passes"]["AA_normal"]]
        print("Checked %d combinations, %d pass AA normal text:" % (len(results), len(viable)))
        print(json.dumps(viable[:50], indent=2))
        if len(viable) > 50:
            print("... (%d more)" % (len(viable) - 50))
        return

    if len(args) < 2:
        print("Usage: contrast_checker.py <fg> <bg>", file=sys.stderr)
        sys.exit(1)

    print(render_text_report(check_pair(args[0], args[1])))


if __name__ == "__main__":
    main()
