# -*- coding: utf-8 -*-
"""删除 server.js 516-527 旧版 isTradingDay（读 data/holidays.json，文件不存在时仅按周末判断）；
统一使用 1565 行新版（engine/holidays.json 2026 节假日表）。"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """// 交易日历：周一至周五，法定节假日（data/holidays.json，无文件时仅按周末判断）
function isTradingDay(date) {
  const d = date || new Date();
  const day = d.getDay();
  if (day === 0 || day === 6) return false;
  try {
    const list = JSON.parse(fs.readFileSync(path.join(__dirname, 'data', 'holidays.json'), 'utf8'));
    const ds = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    return !(list.holidays || []).includes(ds);
  } catch (e) {
    return true;
  }
}

"""
assert s.count(old) == 1, 'old isTradingDay block not found'
s = s.replace(old, '')

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('removed legacy isTradingDay (data/holidays.json)')
