# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


def export_rows_to_files(rows: list[dict], stem: str, export_dir: Path) -> tuple[Path, Path, Path]:
    export_dir.mkdir(parents=True, exist_ok=True)
    csv_path = export_dir / f"{stem}.csv"
    xlsx_path = export_dir / f"{stem}.xlsx"
    pdf_path = export_dir / f"{stem}.pdf"

    import pandas as pd
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    df.to_excel(xlsx_path, index=False)

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [Paragraph(stem, styles["Title"]), Spacer(1, 12)]
    if df.empty:
        elements.append(Paragraph("暂无数据", styles["BodyText"]))
    else:
        for _, row in df.iterrows():
            text = " | ".join(f"{col}: {row[col]}" for col in df.columns)
            elements.append(Paragraph(str(text), styles["BodyText"]))
            elements.append(Spacer(1, 6))
    doc.build(elements)
    return csv_path, xlsx_path, pdf_path
