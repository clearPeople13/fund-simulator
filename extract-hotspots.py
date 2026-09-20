import io

p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 1) 在第1行后加 require hotspots
old_line = "const express = require('express');"
new_line = """const express = require('express');
const { buildHotspots: buildHotspotsRaw } = require('./services/hotspots');"""
assert s.count(old_line) == 1
s = s.replace(old_line, new_line, 1)

# 2) 包一层
old_wrap = "const { buildHotspots: buildHotspotsRaw } = require('./services/hotspots');"
new_wrap = """const { buildHotspots: buildHotspotsRaw } = require('./services/hotspots');
// 包一层：routes 调用 buildHotspots(userId)，内部传 ctx
function buildHotspots(userId) {
  return buildHotspotsRaw({ db, userConfigs }, userId);
}"""
assert s.count(old_wrap) == 1
s = s.replace(old_wrap, new_wrap)

# 3) 删 HOTSPOT_THEMES + buildHotspots 块
start = s.find("const HOTSPOT_THEMES = [")
end = s.find("// 市场行情概览：基准指数走势", start)
assert start != -1 and end != -1
s = s[:start] + "// HOTSPOT_THEMES + buildHotspots 已抽到 services/hotspots.js\n" + s[end:]

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('buildHotspots extracted to services/')
