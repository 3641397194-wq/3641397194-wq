# -*- coding: utf-8 -*-
"""Generate a looping contribution-snake SVG for the GitHub profile README."""
from __future__ import annotations

import datetime as dt
import json
import urllib.request
from pathlib import Path

USER = "3641397194-wq"
SIZE = 12
GAP = 3
STRIDE = SIZE + GAP
PAD_X = 24
PAD_Y = 28
WEEKS = 53
DUR_STEP = 0.16
SNAKE_LEN = 5

LIGHT = {
    "name": "light",
    "empty": "#ebedf0",
    "levels": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
    "snake": ["#C45C14", "#E08A3C", "#F0B27A", "#F3D5B0", "#FFF8F0"],
    "label": "#7A6554",
    "stroke": "#1b1f230a",
}
DARK = {
    "name": "dark",
    "empty": "#161b22",
    "levels": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
    "snake": ["#E08A3C", "#C45C14", "#8A3D0C", "#5C2A08", "#2A1810"],
    "label": "#c9d1d9",
    "stroke": "#00000020",
}


FALLBACK_COUNTS = {
    "2026-07-23": 1,
    "2026-08-17": 1,
    "2026-08-18": 87,
    "2026-08-19": 1,
    "2026-08-20": 1,
    "2026-08-23": 2,
    "2026-08-24": 5,
    "2026-08-25": 5,
}


def fetch_counts() -> dict[str, int]:
    local = Path(__file__).with_name("contributions.json")
    if local.exists():
        data = json.loads(local.read_text(encoding="utf-8"))
        return {row["date"]: int(row.get("count") or 0) for row in data.get("contributions", [])}
    url = f"https://github-contributions-api.jogruber.de/v4/{USER}"
    req = urllib.request.Request(url, headers={"User-Agent": "coldbrew-snake"})
    try:
        with urllib.request.urlopen(req, timeout=8) as res:
            data = json.loads(res.read().decode("utf-8"))
        return {row["date"]: int(row.get("count") or 0) for row in data.get("contributions", [])}
    except Exception:
        return dict(FALLBACK_COUNTS)


def window_start(today: dt.date) -> dt.date:
    # Monday-first grid, 53 columns ending this week. Matches the CN GitHub 周一 row.
    monday = today - dt.timedelta(days=today.weekday())
    return monday - dt.timedelta(weeks=WEEKS - 1)


def level_of(count: int) -> int:
    if count <= 0:
        return 0
    if count <= 2:
        return 1
    if count <= 5:
        return 2
    if count <= 10:
        return 3
    return 4


def build_grid(counts: dict[str, int], start: dt.date):
    cells = []
    for w in range(WEEKS):
        col = []
        for d in range(7):
            day = start + dt.timedelta(days=w * 7 + d)
            n = counts.get(day.isoformat(), 0)
            col.append({"date": day, "count": n, "level": level_of(n), "w": w, "d": d})
        cells.append(col)
    return cells


def snake_path():
    path = []
    for w in range(WEEKS):
        days = range(7) if w % 2 == 0 else range(6, -1, -1)
        for d in days:
            path.append((w, d))
    return path


def xy(w: int, d: int) -> tuple[int, int]:
    return PAD_X + w * STRIDE, PAD_Y + d * STRIDE


def month_labels(start: dt.date) -> list[tuple[int, str]]:
    labels = []
    last = None
    months = "一二三四五六七八九十十一十二"
    names = {
        1: "1月",
        2: "2月",
        3: "3月",
        4: "4月",
        5: "5月",
        6: "6月",
        7: "7月",
        8: "8月",
        9: "9月",
        10: "10月",
        11: "11月",
        12: "12月",
    }
    for w in range(WEEKS):
        day = start + dt.timedelta(days=w * 7)
        if day.month != last:
            labels.append((w, names[day.month]))
            last = day.month
    return labels


def render(theme: dict, cells, path, start: dt.date) -> str:
    n = len(path)
    dur = f"{n * DUR_STEP:.2f}s"
    width = PAD_X + WEEKS * STRIDE + 8
    height = PAD_Y + 7 * STRIDE + 18
    index_of = {(w, d): i for i, (w, d) in enumerate(path)}

    css = [
        f".c{{shape-rendering:geometricPrecision;fill:{theme['empty']};stroke:{theme['stroke']};stroke-width:1px;width:{SIZE}px;height:{SIZE}px}}",
        f".s{{fill:{theme['snake'][0]}}}",
    ]
    eaten = []
    for col in cells:
        for cell in col:
            if cell["level"] == 0:
                continue
            i = index_of[(cell["w"], cell["d"])]
            pct = 100.0 * i / n
            cls = f"e{cell['w']}d{cell['d']}"
            color = theme["levels"][cell["level"]]
            css.append(
                f"@keyframes {cls}{{0%,{pct:.2f}%{{fill:{color}}}{min(pct + 0.2, 99.9):.2f}%,100%{{fill:{theme['empty']}}}}}"
                f".{cls}{{fill:{color};animation:{cls} {dur} linear infinite}}"
            )
            eaten.append(cell)

    rects = []
    for col in cells:
        for cell in col:
            x, y = xy(cell["w"], cell["d"])
            cls = "c"
            if cell["level"]:
                cls += f" e{cell['w']}d{cell['d']}"
            rects.append(f'<rect class="{cls}" x="{x}" y="{y}" rx="2"/>')

    xs = [str(xy(w, d)[0]) for w, d in path]
    ys = [str(xy(w, d)[1]) for w, d in path]
    snake = []
    for k in range(SNAKE_LEN):
        begin = f"{k * DUR_STEP:.2f}s"
        fill = theme["snake"][min(k, len(theme["snake"]) - 1)]
        snake.append(
            f'<rect class="s" width="{SIZE}" height="{SIZE}" rx="2" fill="{fill}">'
            f'<animate attributeName="x" values="{";".join(xs)}" dur="{dur}" begin="{begin}" repeatCount="indefinite" calcMode="discrete"/>'
            f'<animate attributeName="y" values="{";".join(ys)}" dur="{dur}" begin="{begin}" repeatCount="indefinite" calcMode="discrete"/>'
            f"</rect>"
        )

    months = []
    for w, name in month_labels(start):
        x, _ = xy(w, 0)
        months.append(
            f'<text x="{x}" y="16" fill="{theme["label"]}" font-size="10" font-family="Segoe UI,PingFang SC,Microsoft YaHei,sans-serif">{name}</text>'
        )
    wd = ["一", "三", "五"]
    wd_rows = [0, 2, 4]
    weekdays = []
    for label, row in zip(wd, wd_rows):
        _, y = xy(0, row)
        weekdays.append(
            f'<text x="2" y="{y + 10}" fill="{theme["label"]}" font-size="9" font-family="Segoe UI,PingFang SC,Microsoft YaHei,sans-serif">{label}</text>'
        )

    style = "".join(css)
    return (
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="contribution snake">'
        f"<desc>冷咖啡贡献蛇 · {USER}</desc>"
        f"<style>{style}</style>"
        f"{''.join(months)}{''.join(weekdays)}{''.join(rects)}{''.join(snake)}</svg>\n"
    )


def main() -> None:
    here = Path(__file__).resolve().parent.parent / "assets"
    here.mkdir(parents=True, exist_ok=True)
    counts = fetch_counts()
    today = dt.date.today()
    start = window_start(today)
    cells = build_grid(counts, start)
    path = snake_path()
    (here / "github-contribution-grid-snake.svg").write_text(
        render(LIGHT, cells, path, start), encoding="utf-8"
    )
    (here / "github-contribution-grid-snake-dark.svg").write_text(
        render(DARK, cells, path, start), encoding="utf-8"
    )
    print("wrote", here / "github-contribution-grid-snake.svg")
    print("wrote", here / "github-contribution-grid-snake-dark.svg")
    print("start", start.isoformat(), "nonzero", sum(1 for col in cells for c in col if c["count"]))


if __name__ == "__main__":
    main()
