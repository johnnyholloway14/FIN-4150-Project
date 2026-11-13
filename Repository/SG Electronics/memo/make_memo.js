// Builds the one-page memo to Mr. Hosfeld. Run: node memo/make_memo.js
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, WidthType, ShadingType, BorderStyle, LevelFormat,
} = require("docx");

const FONT = "Calibri";
const SZ = 19; // 9.5 pt body
const NAVY = "1F3864";
const ORANGE = "C0504D";

const run = (text, o = {}) => new TextRun({ text, font: FONT, size: SZ, ...o });
const b = (text, o = {}) => run(text, { bold: true, ...o });
const para = (children, o = {}) =>
  new Paragraph({ children, spacing: { before: 0, after: 60, line: 252 }, ...o });
const heading = (text) =>
  new Paragraph({
    children: [new TextRun({ text, font: FONT, size: 21, bold: true, color: NAVY })],
    spacing: { before: 90, after: 30 }, keepNext: true,
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF", space: 1 } },
  });
const bullet = (children) =>
  new Paragraph({ children, numbering: { reference: "dots", level: 0 },
    spacing: { before: 0, after: 30, line: 247 } });

// ---- Covenant table: metrics down, periods across -------------------------
const periods = ["Q1 x1", "Q2 x1", "Q3 x1", "Q4 x1", "20x2", "20x3", "20x4", "20x5"];
const rows = [
  ["Bank loan (line $150,000)", ["92,710", "141,479", "66,068", "30,433", "70,752", "106,711", "108,430", "128,111"], []],
  ["Current ratio (min 1.50)", ["2.10", "1.55", "1.74", "1.72", "1.56", "2.05", "1.52", "1.50"], []],
  ["Liabilities / equity (max 0.60)", ["0.52", "0.81", "0.65", "0.59", "0.46", "0.34", "0.52", "0.40"], [1, 2]],
  ["Loan paid to zero this year?", ["", "", "", "No", "No", "No", "No", "No"], [3, 4, 5, 6, 7]],
];
const W0 = 2300, WC = 1000, TW = W0 + WC * 8; // 10,300 DXA
const border = { style: BorderStyle.SINGLE, size: 2, color: "D9D9D9" };
const borders = { top: border, bottom: border, left: border, right: border };
const cell = (text, width, o = {}) =>
  new TableCell({
    width: { size: width, type: WidthType.DXA }, borders,
    margins: { top: 25, bottom: 25, left: 70, right: 70 },
    shading: o.fill ? { fill: o.fill, type: ShadingType.CLEAR, color: "auto" } : undefined,
    children: [new Paragraph({
      alignment: o.left ? AlignmentType.LEFT : AlignmentType.CENTER,
      spacing: { before: 0, after: 0 },
      children: [new TextRun({ text, font: FONT, size: 17, bold: !!o.bold, color: o.color })],
    })],
  });
const table = new Table({
  width: { size: TW, type: WidthType.DXA },
  columnWidths: [W0, ...Array(8).fill(WC)],
  rows: [
    new TableRow({ tableHeader: true, children: [
      cell("Covenant test", W0, { left: true, bold: true, fill: "DCE6F1" }),
      ...periods.map((p) => cell(p, WC, { bold: true, fill: "DCE6F1" })),
    ] }),
    ...rows.map(([label, vals, bad]) => new TableRow({ children: [
      cell(label, W0, { left: true }),
      ...vals.map((v, i) => bad.includes(i)
        ? cell(v, WC, { bold: true, color: ORANGE, fill: "FBE9E7" })
        : cell(v, WC)),
    ] })),
  ],
});

const chart = new ImageRun({
  type: "png",
  data: fs.readFileSync(path.join(__dirname, "loan_chart.png")),
  transformation: { width: 660, height: 215 },
  altText: { title: "Quarterly bank loan", description: "Quarterly bank loan 20x1 to 20x5 against the $150,000 line; Q2 peaks reach $197K, $252K, $278K and $321K.", name: "loan chart" },
});

const doc = new Document({
  numbering: { config: [{ reference: "dots", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
    alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 260, hanging: 180 } } } }] }] },
  styles: { default: { document: { run: { font: FONT, size: SZ } } } },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 },
      margin: { top: 720, bottom: 600, left: 970, right: 970 } } },
    children: [
      new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: "MEMORANDUM", font: FONT, size: 28, bold: true, color: NAVY })] }),
      para([b("To: "), run("Bob Hosfeld, Chief Financial Officer\t"), b("From: "), run("Johnny Holloway\t"), b("Date: "), run("January 20x1")],
        { tabStops: [{ type: "left", position: 4300 }, { type: "left", position: 7200 }], spacing: { after: 20 } }),
      para([b("Re: "), run("Five-year loan needs and the Pioneer National Bank covenants")],
        { spacing: { after: 60 }, border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: NAVY, space: 2 } } }),

      para([b("Recommendation. "), run("SG is profitable, but its plan does not fit the current $150,000 line. We will break the debt covenant in the second quarter, we never meet the clean-up clause, and our spring borrowing outgrows the line from 20x2 on. I recommend we meet Mr. Weaver before April and ask for three changes: a $350,000 seasonal line, a waiver of the debt-to-equity test for 20x1, and a clean-up clause we can meet. We should also hold the dividend at $110,000 until the loan is under control.")]),

      heading("1. The 20x1 quarterly forecast"),
      para([run("With cash held at $70,000 and the bank loan as the plug, borrowing climbs from $31,000 to "), b("$141,479 in Q2"), run(". Receivables and inventory build ahead of peak sales, and the $250,000 equipment comes on line. The loan then falls to $30,433 by December as customers pay. Net income for the year is $160,292. The balance sheet balances and the cash delta is zero in every quarter.")]),

      heading("2. The five-year forecast"),
      para([run("Sales grow 8% a year, from $1.51 million to $2.05 million in 20x5, and net income rises to $211,809. Even so, the year-end loan climbs to "), b("$128,111"), run(". Our sustainable growth rate is only 4% to 6%, so 8% growth must be funded with debt. Dividends rising 10% a year make the gap wider.")]),

      heading("3. Covenant tests"),
      new Paragraph({ spacing: { after: 40 }, children: [] }),
      table,
      new Paragraph({ spacing: { after: 30 }, children: [] }),
      bullet([b("Debt to equity fails in Q2 and Q3 20x1 (0.81 and 0.65). "), run("The $250,000 equipment loan counts as debt. The breach lasts two quarters, longer than the one-quarter cure period, so Pioneer could call the loan.")]),
      bullet([b("The clean-up clause is never met. "), run("The lowest balance is $30,433, in December 20x1.")]),
      bullet([b("The current ratio is thin. "), run("It passes, but only at 1.50 to 1.52 in 20x4 and 20x5.")]),
      bullet([b("Year-end figures hide the real peak. "), run("When I ran 20x2 to 20x5 quarter by quarter, the Q2 loan tops the line every year and reaches $321,000 in 20x5 (chart below). Sales could also miss plan by 15%; in that case the 20x5 loan is $293,000 and both ratios fail.")]),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 30, after: 20 }, children: [chart] }),
      para([b("What fixes it. "), run("Holding the dividend at $110,000 cuts the 20x5 year-end loan from $128,111 to zero and the 20x5 peak from $321,000 to $217,000. That still exceeds $150,000, so a larger line is needed either way. A waiver is the cheapest cure for 20x1, because the breach comes from interest-free vendor financing, not from losses.")]),

      heading("4. Inflation"),
      para([run("This forecast is in real terms. Inflation would raise prices, so receivables and inventory, which the bank funds, would rise with them. It would also raise fixed costs, the price of the 20x4 expansion, and likely the prime rate. Depreciation stays at historical cost, so taxes would rise faster than real profit. At 3% inflation, the 20x5 Q2 peak rises to $329,000 even though year-end debt falls. I would forecast in nominal dollars, test a range of rates, and plan for a floating loan rate.")]),
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(__dirname, "SG Electronics Memo - Johnny Holloway.docx");
  fs.writeFileSync(out, buf);
  console.log(out);
});
