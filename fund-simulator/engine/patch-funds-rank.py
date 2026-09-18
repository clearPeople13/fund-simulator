# -*- coding: utf-8 -*-
"""api/routes.js /api/funds：①返回完整区间涨幅字段（r1w/r1m/r3m/r6m/r1y/r2y/r3y/ytd/since）
②排序白名单补 r1w/r2y/r3y/ytd/unit_nav/scale，支撑基金排行"""
import io, os

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\api\routes.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """  const sortMap = {
    fund_code: 'u.fund_code', fund_name: 'u.fund_name',
    day_return: 'u.day_return', r1m: 'u.r1m', r3m: 'u.r3m', r6m: 'u.r6m', r1y: 'u.r1y',
    unit_nav: 'u.unit_nav', scale: 'u.scale'
  };"""
new = """  const sortMap = {
    fund_code: 'u.fund_code', fund_name: 'u.fund_name',
    day_return: 'u.day_return', r1w: 'u.r1w', r1m: 'u.r1m', r3m: 'u.r3m', r6m: 'u.r6m',
    r1y: 'u.r1y', r2y: 'u.r2y', r3y: 'u.r3y', ytd: 'u.ytd', since: 'u.since',
    unit_nav: 'u.unit_nav', scale: 'u.scale'
  };"""
assert s.count(old) == 1, 'sortMap not found'
s = s.replace(old, new)

old2 = """  const query = `SELECT u.fund_code, u.fund_name, u.fund_type, u.unit_nav AS latest_nav, u.nav_date AS latest_nav_date,
        u.day_return, u.r6m AS recent_return, u.inception_date, u.scale
      FROM fund_universe u${whereSql}"""
new2 = """  const query = `SELECT u.fund_code, u.fund_name, u.fund_type, u.unit_nav AS latest_nav, u.nav_date AS latest_nav_date,
        u.day_return, u.r1w, u.r1m, u.r3m, u.r6m AS recent_return, u.r1y, u.r2y, u.r3y, u.ytd, u.since, u.inception_date, u.scale
      FROM fund_universe u${whereSql}"""
assert s.count(old2) == 1, 'query not found'
s = s.replace(old2, new2)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('routes.js patched')
