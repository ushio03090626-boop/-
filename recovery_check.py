#!/usr/bin/env python3
"""復旧データチェックツール - 外付けHDD/USBメモリの復旧状態をHTMLレポートで出力"""

import os
import sys
import argparse
import datetime
import html
from pathlib import Path


def format_size(size_bytes):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def is_readable(filepath):
    try:
        with open(filepath, "rb") as f:
            f.read(1)
        return True
    except (IOError, OSError, PermissionError):
        return False


def scan_directory(root_path):
    stats = {
        "total_folders": 0,
        "total_files": 0,
        "total_size": 0,
        "normal_files": [],
        "corrupted_files": [],
    }

    for dirpath, dirnames, filenames in os.walk(root_path):
        stats["total_folders"] += len(dirnames)

        for filename in filenames:
            filepath = Path(dirpath) / filename
            stats["total_files"] += 1

            try:
                file_size = filepath.stat().st_size
                stats["total_size"] += file_size

                if file_size == 0:
                    stats["corrupted_files"].append(
                        {"path": str(filepath), "size": 0, "reason": "0バイト"}
                    )
                elif not is_readable(filepath):
                    stats["corrupted_files"].append(
                        {"path": str(filepath), "size": file_size, "reason": "読み取り不可"}
                    )
                else:
                    stats["normal_files"].append(str(filepath))

            except (OSError, PermissionError) as e:
                stats["corrupted_files"].append(
                    {"path": str(filepath), "size": 0, "reason": f"アクセス不可: {e}"}
                )

    return stats


def generate_html(stats, target_path, output_path):
    total = stats["total_files"]
    normal = len(stats["normal_files"])
    corrupted = len(stats["corrupted_files"])
    rate = (normal / total * 100) if total > 0 else 0

    if rate >= 90:
        color = "#27ae60"
        status = "良好"
    elif rate >= 70:
        color = "#f39c12"
        status = "注意"
    else:
        color = "#e74c3c"
        status = "要確認"

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    corrupted_rows = ""
    if corrupted == 0:
        corrupted_rows = '<tr><td colspan="3" style="text-align:center;color:#aaa;padding:20px;">破損ファイルはありません</td></tr>'
    else:
        for item in stats["corrupted_files"]:
            badge_bg = "#fff3cd" if item["reason"] == "0バイト" else "#f8d7da"
            badge_color = "#856404" if item["reason"] == "0バイト" else "#842029"
            corrupted_rows += f"""<tr>
  <td style="word-break:break-all;padding:6px 10px;color:#555;">{html.escape(item['path'])}</td>
  <td style="padding:6px 10px;white-space:nowrap;">
    <span style="background:{badge_bg};color:{badge_color};padding:2px 8px;border-radius:12px;font-size:0.8em;font-weight:bold;">{html.escape(item['reason'])}</span>
  </td>
  <td style="padding:6px 10px;text-align:right;color:#888;">{format_size(item['size'])}</td>
</tr>"""

    content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>データ復旧チェックレポート</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'Helvetica Neue',Arial,sans-serif;background:#f0f2f5;color:#333;padding:24px}}
    h1{{text-align:center;color:#2c3e50;font-size:1.7rem;margin-bottom:28px}}
    .wrap{{max-width:900px;margin:0 auto}}
    .card{{background:#fff;border-radius:12px;padding:22px;margin-bottom:20px;box-shadow:0 2px 10px rgba(0,0,0,.07)}}
    .card h2{{font-size:1rem;color:#2c3e50;border-bottom:2px solid #eee;padding-bottom:8px;margin-bottom:16px}}
    .meta{{color:#888;font-size:.85rem;margin-bottom:4px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px}}
    .stat{{text-align:center;background:#f8f9fa;border-radius:8px;padding:14px}}
    .stat .val{{font-size:1.9rem;font-weight:700}}
    .stat .lbl{{font-size:.8rem;color:#666;margin-top:4px}}
    .rate-big{{font-size:3.5rem;font-weight:700;text-align:center}}
    .bar-bg{{background:#e9ecef;border-radius:50px;height:18px;overflow:hidden;margin:14px 0}}
    .bar-fill{{height:100%;border-radius:50px}}
    .rate-sub{{text-align:center;font-size:.9rem;color:#555}}
    table{{width:100%;border-collapse:collapse;font-size:.83rem}}
    th{{background:#f8f9fa;padding:8px 10px;text-align:left;font-weight:600;color:#555;border-bottom:2px solid #eee}}
    tr:hover td{{background:#fafafa}}
    td{{border-bottom:1px solid #f0f0f0}}
    .scroll{{max-height:320px;overflow-y:auto}}
  </style>
</head>
<body>
<div class="wrap">
  <h1>データ復旧チェックレポート</h1>

  <div class="card">
    <p class="meta">対象パス: {html.escape(str(target_path))}</p>
    <p class="meta">チェック日時: {now}</p>
  </div>

  <div class="card">
    <h2>サマリー</h2>
    <div class="grid">
      <div class="stat"><div class="val">{stats['total_folders']:,}</div><div class="lbl">総フォルダー数</div></div>
      <div class="stat"><div class="val">{total:,}</div><div class="lbl">総ファイル数</div></div>
      <div class="stat"><div class="val">{format_size(stats['total_size'])}</div><div class="lbl">総容量</div></div>
      <div class="stat"><div class="val" style="color:#27ae60">{normal:,}</div><div class="lbl">正常ファイル数</div></div>
      <div class="stat"><div class="val" style="color:#e74c3c">{corrupted:,}</div><div class="lbl">破損ファイル数</div></div>
    </div>
  </div>

  <div class="card">
    <h2>復旧率</h2>
    <div class="rate-big" style="color:{color}">{rate:.1f}%</div>
    <div class="bar-bg"><div class="bar-fill" style="width:{rate:.1f}%;background:{color}"></div></div>
    <p class="rate-sub">ステータス: <strong>{status}</strong> &nbsp;|&nbsp; 正常 {normal:,} / 総ファイル {total:,}</p>
  </div>

  <div class="card">
    <h2>破損ファイル一覧（{corrupted:,} 件）</h2>
    <div class="scroll">
      <table>
        <thead><tr><th>ファイルパス</th><th>原因</th><th style="text-align:right">サイズ</th></tr></thead>
        <tbody>{corrupted_rows}</tbody>
      </table>
    </div>
  </div>
</div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(
        description="復旧データチェックツール（外付けHDD/USBメモリ対応）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""使用例:
  python recovery_check.py /Volumes/MyHDD
  python recovery_check.py D:\\recovered -o report.html
""",
    )
    parser.add_argument("path", help="チェック対象のディレクトリパス")
    parser.add_argument(
        "-o", "--output", default=None, help="出力HTMLファイル名（省略時は自動生成）"
    )
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f"エラー: パスが存在しません: {args.path}", file=sys.stderr)
        sys.exit(1)
    if not target.is_dir():
        print(f"エラー: ディレクトリを指定してください: {args.path}", file=sys.stderr)
        sys.exit(1)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output = Path(args.output) if args.output else Path(f"recovery_report_{timestamp}.html")

    print(f"スキャン開始: {target}")
    print("しばらくお待ちください...")

    stats = scan_directory(target)

    total = stats["total_files"]
    normal = len(stats["normal_files"])
    corrupted = len(stats["corrupted_files"])
    rate = (normal / total * 100) if total > 0 else 0

    print()
    print(f"  総フォルダー数 : {stats['total_folders']:,}")
    print(f"  総ファイル数   : {total:,}")
    print(f"  総容量         : {format_size(stats['total_size'])}")
    print(f"  正常ファイル   : {normal:,}")
    print(f"  破損ファイル   : {corrupted:,}")
    print(f"  復旧率         : {rate:.1f}%")
    print()

    generate_html(stats, target, output)
    print(f"HTMLレポート生成完了: {output}")


if __name__ == "__main__":
    main()
