"""Executive AI Portfolio Renewal Excel download: formulas, dropdowns and access CTA."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from briefing_renewal_excel import (
    build_decision_advisor_xlsx, SLUG, MIME, FILE_NAME,
)
from briefing_renewal_worksheet import decision_record_cta_html

NS="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


class RenewalExcelAdvisorTests(unittest.TestCase):
    def test_five_sheets_recalculate_and_have_working_formulas(self):
        data=build_decision_advisor_xlsx()
        self.assertTrue(data.startswith(b"PK"))
        self.assertLess(len(data),900000)
        self.assertGreater(len(data),5000)
        with ZipFile(BytesIO(data)) as z:
            self.assertIsNone(z.testzip())
            names=z.namelist()
            self.assertFalse(any("vbaProject" in p or "externalLink" in p for p in names))
            self.assertEqual(len([n for n in names if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]),5)
            wb=ET.fromstring(z.read("xl/workbook.xml"))
            sheetnames=[x.get("name") for x in wb.find(NS+"sheets")]
            self.assertEqual(sheetnames,["START HERE","INPUTS","DECISION","EXAMPLE","METHOD"])
            calc=wb.find(NS+"calcPr")
            self.assertEqual(calc.get("fullCalcOnLoad"),"1")
            self.assertEqual(calc.get("calcMode"),"auto")
            inputs=ET.fromstring(z.read("xl/worksheets/sheet2.xml"))
            valid=inputs.find(NS+"dataValidations")
            self.assertGreaterEqual(len(list(valid)),12)
            formulas={x.get("r"):x.find(NS+"f").text for x in inputs.iter(NS+"c") if x.find(NS+"f") is not None}
            self.assertIn("D33",formulas)
            self.assertIn("F37",formulas)
            self.assertIn("ABS",formulas["F35"])
            decision=ET.fromstring(z.read("xl/worksheets/sheet3.xml"))
            decisionformulas={x.get("r"):x.find(NS+"f").text for x in decision.iter(NS+"c") if x.find(NS+"f") is not None}
            self.assertIn("D7",decisionformulas)
            self.assertIn("D10",decisionformulas)
            for word in ("RENEW","REPLACE","TEST","STOP","HOLD"):
                self.assertIn(word,decisionformulas["D7"])
            self.assertIn('INPUTS!D18',decisionformulas["D7"])

    def test_authenticated_only_cta_is_excel_not_pdf(self):
        self.assertEqual(MIME,"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.assertTrue(FILE_NAME.endswith(".xlsx"))
        html=decision_record_cta_html()
        self.assertIn("worksheet=1",html)
        self.assertIn("article="+SLUG,html)
        self.assertIn("Download Excel Decision Advisor (.xlsx)",html)
        self.assertIn("five worksheets",html.lower())
        self.assertNotIn(".pdf",html.lower())
        self.assertNotIn("raw.githubusercontent.com",html)
        self.assertNotIn("data:application/",html)

if __name__=="__main__":
    unittest.main()
