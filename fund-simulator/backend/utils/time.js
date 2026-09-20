/**
 * 时间与交易日工具（纯函数，无副作用）
 * 唯一出处：所有日期/交易时段判断都从这里导出
 */
const path = require('path');

// A 股节假日表：engine/holidays.json（国务院公布，每年 11 月补）
let HOLIDAYS = {};
try { HOLIDAYS = require(path.join(__dirname, '..', 'engine', 'holidays.json')); } catch { /* 无文件则全工作日 */ }

/** 本地日期串 YYYY-MM-DD */
function getLocalDateStr(d = new Date()) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

/** 是否交易日（周一~周五且不在节假日表） */
function isTradingDay(d = new Date()) {
  const dow = d.getDay();
  if (dow === 0 || dow === 6) return false;
  const year = String(d.getFullYear());
  const list = HOLIDAYS[year] || [];
  return list.indexOf(getLocalDateStr(d)) === -1;
}

/** 是否正在连续竞价时段（交易日 9:30-11:30 / 13:00-15:00） */
function isMarketOpenNow(d = new Date()) {
  if (!isTradingDay(d)) return false;
  const mins = d.getHours() * 60 + d.getMinutes();
  return (mins >= 570 && mins <= 690) || (mins >= 780 && mins <= 900);
}

/** 找到不小于 date 的第一个交易日 0 点 */
function nextTradingDay(date) {
  const d = new Date(date);
  while (!isTradingDay(d)) d.setDate(d.getDate() + 1);
  return d;
}

module.exports = { HOLIDAYS, getLocalDateStr, isTradingDay, isMarketOpenNow, nextTradingDay };
