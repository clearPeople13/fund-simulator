const path = require('path');
const sqlite3 = require(path.join(__dirname, 'node_modules', 'sqlite3'));
const db = new sqlite3.Database(path.join(__dirname, 'fund_simulator.db'));

function getLocalDateStr(d) {
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
}
function utcToLocalStr(utcStr) {
  const d = new Date(String(utcStr).replace(' ', 'T') + 'Z');
  if (isNaN(d.getTime())) return utcStr;
  const p = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

const users = { default: 5, aggressive: 3 };
const codes = { default: ['000001', '005827'], aggressive: ['161725', '005267'] };

(async () => {
  for (const [uid, cooldown] of Object.entries(users)) {
    for (const code of codes[uid]) {
      const md = await new Promise(res => db.get("SELECT MAX(transaction_date) md FROM transactions WHERE user_id=? AND fund_code=? AND transaction_type='BUY'", [uid, code], (e, r) => res(e ? null : r)));
      let daysSince = 9999;
      if (md && md.md) {
        const lastD = new Date(utcToLocalStr(md.md).slice(0, 10) + 'T00:00:00');
        const todayD = new Date(getLocalDateStr(new Date()) + 'T00:00:00');
        daysSince = Math.round((todayD.getTime() - lastD.getTime()) / 86400000);
      }
      const blocked = daysSince < cooldown;
      console.log(`${uid} ${code}: lastBuy=${md ? md.md : 'none'} (本地 ${md ? utcToLocalStr(md.md) : 'none'}), daysSince=${daysSince}, cooldown=${cooldown} => ${blocked ? '拦截(冷却期)' : '允许加仓'}`);
    }
  }
  db.close();
})();
