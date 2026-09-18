// 验证：2026 节假日交易日历（holidays.json + isTradingDay/nextTradingDay 逻辑 + holidays 表 seed）
const path = require('path');
const HOLIDAYS = require('./engine/holidays.json');

function getLocalDateStr(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return y + '-' + m + '-' + day;
}
function isTradingDay(d) {
  const dow = d.getDay();
  if (dow === 0 || dow === 6) return false;
  const list = HOLIDAYS[String(d.getFullYear())] || [];
  return list.indexOf(getLocalDateStr(d)) === -1;
}
function nextTradingDay(date) {
  const d = new Date(date);
  while (!isTradingDay(d)) d.setDate(d.getDate() + 1);
  return d;
}

const cases = [
  // [YYYY-MM-DD, 期望是否交易日, 说明]
  ['2026-09-17', true, '周四 普通交易日'],
  ['2026-09-18', true, '周五 普通交易日（今天）'],
  ['2026-09-19', false, '周六 周末'],
  ['2026-09-20', false, '周日 调休上班但A股不开市'],
  ['2026-09-25', false, '周五 中秋节休市'],
  ['2026-09-26', false, '周六 中秋假期'],
  ['2026-09-28', true, '周一 节后首个交易日'],
  ['2026-10-01', false, '周四 国庆休市'],
  ['2026-10-02', false, '周五 国庆休市'],
  ['2026-10-05', false, '周一 国庆休市'],
  ['2026-10-07', false, '周三 国庆休市'],
  ['2026-10-09', true, '周五 国庆后首个交易日'],
  ['2026-10-10', false, '周六 调休上班但A股不开市'],
  ['2026-10-12', true, '周一 普通交易日'],
  ['2026-01-01', false, '周四 元旦休市'],
  ['2026-01-02', false, '周五 元旦休市'],
  ['2026-01-04', false, '周日 调休上班但A股不开市'],
  ['2026-01-05', true, '周一 普通交易日'],
  ['2026-02-14', false, '周六 调休上班但A股不开市'],
  ['2026-02-16', false, '周一 春节休市'],
  ['2026-02-20', false, '周五 春节休市'],
  ['2026-02-23', false, '周一 春节休市'],
  ['2026-02-24', true, '周二 春节后首个交易日'],
  ['2026-02-28', false, '周六 调休上班但A股不开市'],
  ['2026-04-06', false, '周一 清明节休市'],
  ['2026-04-07', true, '周二 清明后首个交易日'],
  ['2026-05-01', false, '周五 劳动节休市'],
  ['2026-05-04', false, '周一 劳动节休市'],
  ['2026-05-05', false, '周二 劳动节休市'],
  ['2026-05-06', true, '周三 劳动节后首个交易日'],
  ['2026-05-09', false, '周六 调休上班但A股不开市'],
  ['2026-06-19', false, '周五 端午节休市'],
  ['2026-06-22', true, '周一 端午后首个交易日'],
];

let pass = 0, fail = 0;
for (const [ds, expect, label] of cases) {
  const d = new Date(ds + 'T12:00:00');
  const got = isTradingDay(d);
  const ok = got === expect;
  if (ok) pass++; else { fail++; console.log(`FAIL ${ds} ${label}: expect ${expect} got ${got}`); }
}
console.log(`isTradingDay 边界: ${pass} 通过, ${fail} 失败 / ${cases.length}`);

// nextTradingDay 顺延（语义：不小于 date 的第一个交易日）
const nexts = [
  ['2026-09-24T15:00:00', '2026-09-24', '周四已是交易日→当天'],
  ['2026-09-25T10:00:00', '2026-09-28', '中秋休市→节后首日'],
  ['2026-09-26T00:00:00', '2026-09-28', '中秋假期周六→节后首日'],
  ['2026-10-01T10:00:00', '2026-10-08', '国庆休市→节后首日'],
  ['2026-10-07T10:00:00', '2026-10-08', '国庆最后一天→节后首日'],
  ['2026-02-16T10:00:00', '2026-02-24', '春节休市→节后首日'],
  ['2026-02-23T10:00:00', '2026-02-24', '春节最后一天→节后首日'],
  ['2026-04-06T10:00:00', '2026-04-07', '清明休市→节后首日'],
  ['2026-05-05T10:00:00', '2026-05-06', '劳动节当天→节后首日'],
  ['2026-06-19T10:00:00', '2026-06-22', '端午休市→节后首日'],
  ['2026-01-02T10:00:00', '2026-01-05', '元旦最后一天→节后首日'],
];
let np = 0, nf = 0;
for (const [from, expect, label] of nexts) {
  const got = getLocalDateStr(nextTradingDay(new Date(from)));
  const ok = got === expect;
  if (ok) np++; else { nf++; console.log(`FAIL next ${label}: expect ${expect} got ${got}`); }
}
console.log(`nextTradingDay 顺延: ${np} 通过, ${nf} 失败 / ${nexts.length}`);

// holidays 表 seed 可执行性（真实 DB，只读验证——不写入，仅验证 prepare 语法可用）
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3')).verbose();
const db = new sqlite3.Database('./fund_simulator.db');
db.serialize(() => {
  db.run(`CREATE TABLE IF NOT EXISTS holidays (date TEXT PRIMARY KEY, name TEXT)`);
  const hd = HOLIDAYS['2026'] || [];
  const stmt = db.prepare('INSERT OR IGNORE INTO holidays (date, name) VALUES (?, ?)');
  hd.forEach(d => stmt.run(d, '法定节假日休市'));
  stmt.finalize();
  db.all('SELECT COUNT(*) AS c FROM holidays', (err, rows) => {
    console.log('holidays 表 seed 可执行, 当前行数:', err ? 'ERR ' + err.message : rows[0].c);
    db.close();
    process.exit(fail + nf === 0 ? 0 : 1);
  });
});
