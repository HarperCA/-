"""Run iterative random strategy search and save the champion report."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.random_strategy_search import (  # noqa: E402
    load_default_datasets,
    run_random_strategy_search,
    save_search_report,
)


def pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def main() -> int:
    parser = argparse.ArgumentParser(description="Iterative random strategy search")
    parser.add_argument("--rounds", type=int, default=20, help="Number of champion-selection rounds")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--data-dir", default="data/cleaned", help="Directory containing cleaned CSV files")
    parser.add_argument("--output", default="", help="JSON report output path")
    args = parser.parse_args()

    datasets = load_default_datasets(args.data_dir)
    report = run_random_strategy_search(datasets, rounds=args.rounds, seed=args.seed)

    if args.output:
        output_path = Path(args.output)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path("reports") / f"random_strategy_search_{stamp}.json"
    save_search_report(report, output_path)

    champion = report["champion"]
    print(f"Datasets: {report['dataset_count']} | Rounds: {report['rounds']} | Seed: {report['seed']}")
    print(
        "Champion: "
        f"{champion['key']} | score={champion['score']:.4f} | "
        f"avg_cagr={pct(champion['avg_cagr'])} | "
        f"avg_mdd={pct(champion['avg_max_drawdown'])} | "
        f"avg_sharpe={champion['avg_sharpe']:.2f} | "
        f"positive_assets={champion['positive_assets']}/{report['dataset_count']} | "
        f"trades={champion['total_trades']}"
    )
    print("Entry:")
    for condition in champion["spec"]["entry"]:
        print(f"  {condition['feature']} {condition['op']} {condition['value']}")
    print("Exit:")
    for condition in champion["spec"]["exit"]:
        print(f"  {condition['feature']} {condition['op']} {condition['value']}")
    print(
        f"Holding: min_hold_days={champion['spec']['min_hold_days']} "
        f"cooldown_days={champion['spec']['cooldown_days']}"
    )
    print("Per asset:")
    for row in champion["asset_results"]:
        print(
            f"  {row['label']}: total={pct(row['total_return'])}, "
            f"cagr={pct(row['cagr'])}, mdd={pct(row['max_drawdown'])}, "
            f"sharpe={row['sharpe_ratio']:.2f}, trades={row['trade_count']}"
        )
    print(f"Report: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
