# -*- coding: utf-8 -*-
import io

p2 = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\FundDetail.vue'
with io.open(p2, 'r', encoding='utf-8') as f:
    c2 = f.read()

new_css = """.loss {
  color: #f87171;
  font-weight: 600;
}

/* 涨跌幅（支付宝式） */
.returns-card { margin-bottom: 20px; }
.block-title-inline { display: inline-block; font-size: 15px; font-weight: 600; color: var(--text, #e8ebff); }
.returns-sub { margin-left: 10px; font-size: 12px; color: #8b92b8; }
.returns-list { display: flex; flex-direction: column; gap: 14px; padding: 4px 8px 8px; }
.ret-row { display: flex; align-items: center; gap: 14px; }
.ret-label { width: 64px; font-size: 13px; color: #a5adcf; flex-shrink: 0; }
.ret-track { position: relative; flex: 1; height: 16px; background: rgba(255,255,255,0.05); border-radius: 4px; overflow: hidden; }
.ret-zero { position: absolute; top: 0; bottom: 0; left: 50%; width: 1px; background: rgba(139,146,184,0.5); z-index: 2; }
.ret-fill { position: absolute; top: 2px; bottom: 2px; border-radius: 3px; transition: width 0.3s; }
.ret-fill.up { background: linear-gradient(90deg, rgba(52,211,153,0.5), #34d399); }
.ret-fill.down { background: linear-gradient(270deg, rgba(248,113,113,0.5), #f87171); }
.ret-value { width: 84px; text-align: right; font-size: 13px; font-weight: 600; font-variant-numeric: tabular-nums; flex-shrink: 0; }
.returns-empty { padding: 12px 0; color: #8b92b8; font-size: 13px; }
</style>"""

old_css = """.loss {
  color: #f87171;
  font-weight: 600;
}
</style>"""

assert old_css in c2, 'css anchor not found'
c2 = c2.replace(old_css, new_css, 1)
with io.open(p2, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c2)
print('OK FundDetail.vue CSS')
