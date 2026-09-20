# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\FundDetail.vue'
c = io.open(p, encoding='utf-8').read()

# 1. 删除规模行（rankhandler 规模字段不可靠，避免展示错误数据）
old = """              <div class="info-item" v-if="fundInfo.scale != null">
                <span class="label">基金规模</span>
                <span class="value">{{ fundInfo.scale.toLocaleString() }} 亿</span>
              </div>
"""
assert c.count(old) == 1, 'scale row %d' % c.count(old)
c = c.replace(old, "", 1)

# 2. 未跟踪提示文案（查看详情会自动拉净值，改为说明 AI 跟踪概念）
old2 = """              message="该基金暂未纳入 AI 跟踪，暂无历史净值；可在基金库点击 ☆ 观察 自动拉取净值后查看走势与信号\""""
new2 = """              message="该基金暂未纳入 AI 跟踪：无 AI 信号与操作记录。可在基金库点击 ☆ 观察 纳入跟踪后查看入场建议与信号\""""
assert c.count(old2) == 1, 'alert text %d' % c.count(old2)
c = c.replace(old2, new2, 1)

io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK')
