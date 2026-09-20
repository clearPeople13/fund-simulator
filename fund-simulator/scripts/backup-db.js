/**
 * 基金模拟系统 - 数据库每日自动备份脚本
 * 使用 sqlite3 的 backup API（step(-1) 全量拷贝）生成一致性快照，可在服务运行中安全备份。
 * 保留最近 30 份，日志写入 backups/backup.log。
 * 由 Windows 计划任务 FundSimulator-DB-Backup 每日调用；也可手动执行: node backup-db.js
 */
const path = require('path');
const fs = require('fs');
const sqlite3 = require('sqlite3').verbose();

const SRC = path.join(__dirname, 'fund_simulator.db');
const DIR = path.join(__dirname, 'backups');
const KEEP = 30; // 保留份数

if (!fs.existsSync(SRC)) {
  console.error('未找到数据库文件: ' + SRC);
  process.exit(1);
}
fs.mkdirSync(DIR, { recursive: true });

// 时间戳文件名: fund_simulator_YYYYMMDD_HHMMSS.db
const ts = new Date();
const p = n => String(n).padStart(2, '0');
const stamp = `${ts.getFullYear()}${p(ts.getMonth() + 1)}${p(ts.getDate())}_${p(ts.getHours())}${p(ts.getMinutes())}${p(ts.getSeconds())}`;
const DEST = path.join(DIR, `fund_simulator_${stamp}.db`);

const db = new sqlite3.Database(SRC, sqlite3.OPEN_READONLY);
const backup = db.backup(DEST);

backup.step(-1, (err) => {
  if (err) {
    console.error('备份失败: ' + err.message);
    try { db.close(); } catch (e) {}
    process.exit(1);
  }

  // 轮转：只保留最近 KEEP 份
  const files = fs.readdirSync(DIR)
    .filter(f => /^fund_simulator_\d{8}_\d{6}\.db$/.test(f))
    .sort();
  while (files.length > KEEP) {
    fs.unlinkSync(path.join(DIR, files.shift()));
  }

  const size = fs.statSync(DEST).size;
  const line = `[${ts.toLocaleString('zh-CN', { hour12: false })}] 备份完成: ${path.basename(DEST)} (${(size / 1024).toFixed(1)} KB), 当前保留 ${files.length} 份`;
  fs.appendFileSync(path.join(DIR, 'backup.log'), line + '\n');
  console.log(line);
  db.close();
});
