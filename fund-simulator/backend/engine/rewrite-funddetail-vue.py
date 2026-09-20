# -*- coding: utf-8 -*-
import io

p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\FundDetail.vue'
c = io.open(p, encoding='utf-8').read()

# 1. 加载详情：单只接口（funds/universe 兜底）+ tracked 标记
old = """    // 基金基本信息
    const fundRes = await axios.get('/api/funds', { params: { limit: 100 } })
    const fund = (fundRes.data && fundRes.data.data || []).find(f => f.fund_code === fundCode.value) || null
    // 净值历史（真实）
    const navRes = await axios.get(`/api/funds/${fundCode.value}/nav`, { params: { limit: 120 } })
    const navRows = Array.isArray(navRes.data) ? navRes.data : []
    // 区间涨跌幅（支付宝式）
    let returnsData = []
    try {
      const retRes = await axios.get(`/api/funds/${fundCode.value}/returns`)
      if (retRes.data && Array.isArray(retRes.data.periods)) returnsData = retRes.data.periods
    } catch (e) { console.warn('加载区间涨跌幅失败:', e.message) }
    fundReturns.value = returnsData

    fundInfo.value = {
      fund_code: fund?.fund_code || fundCode.value,
      fund_name: fund?.fund_name || fundCode.value,
      fund_type: fund?.fund_type || '—',
      manager: fund?.manager || '—',
      inception_date: fund?.inception_date || '—',
      benchmark: fund?.benchmark || '—',
      nav_history: navRows.map(n => ({
        date: n.nav_date,
        unit_nav: n.unit_nav,
        acc_nav: n.acc_nav,
        daily_return: n.daily_return
      }))
    }"""
new = """    // 基金基本信息（优先系统跟踪库；未跟踪时由全市场基金库兜底）
    const fundRes = await axios.get(`/api/funds/${fundCode.value}`)
    const fund = fundRes.data || {}
    const tracked = fund.tracked !== false
    // 净值历史（真实，仅已跟踪基金有）
    const navRes = await axios.get(`/api/funds/${fundCode.value}/nav`, { params: { limit: 120 } })
    const navRows = Array.isArray(navRes.data) ? navRes.data : []
    // 区间涨跌幅（支付宝式）
    let returnsData = []
    try {
      const retRes = await axios.get(`/api/funds/${fundCode.value}/returns`)
      if (retRes.data && Array.isArray(retRes.data.periods)) returnsData = retRes.data.periods
    } catch (e) { console.warn('加载区间涨跌幅失败:', e.message) }
    fundReturns.value = returnsData

    fundInfo.value = {
      fund_code: fund.fund_code || fundCode.value,
      fund_name: fund.fund_name || fundCode.value,
      fund_type: fund.fund_type || '—',
      manager: fund.manager || '—',
      inception_date: fund.inception_date || '—',
      benchmark: fund.benchmark || '—',
      tracked,
      latest_nav: fund.latest_nav != null ? fund.latest_nav : null,
      latest_nav_date: fund.latest_nav_date || '',
      recent_return: fund.recent_return != null ? fund.recent_return : null,
      scale: fund.scale != null ? fund.scale : null,
      nav_history: navRows.map(n => ({
        date: n.nav_date,
        unit_nav: n.unit_nav,
        acc_nav: n.acc_nav,
        daily_return: n.daily_return
      }))
    }"""
assert c.count(old) == 1, 'load %d' % c.count(old)
c = c.replace(old, new, 1)

# 2. 模板：净值走势卡片加未跟踪提示 + 信息卡加规模/最新净值
old2 = """          <a-card :bordered="false" class="chart-card">
            <div class="block-title">净值走势</div>
            <div id="navChart" class="chart-container"></div>
          </a-card>"""
new2 = """          <a-card :bordered="false" class="chart-card">
            <div class="block-title">净值走势</div>
            <a-alert
              v-if="fundInfo && !fundInfo.tracked"
              type="info"
              show-icon
              message="该基金暂未纳入 AI 跟踪，暂无历史净值；可在基金库点击 ☆ 观察 自动拉取净值后查看走势与信号"
              style="margin-bottom: 12px; border-radius: 8px"
            />
            <div id="navChart" class="chart-container"></div>
          </a-card>"""
assert c.count(old2) == 1, 'chart card %d' % c.count(old2)
c = c.replace(old2, new2, 1)

old3 = """              <div class="info-item">
                <span class="label">成立日期</span>
                <span class="value">{{ fundInfo.inception_date }}</span>
              </div>"""
new3 = """              <div class="info-item">
                <span class="label">成立日期</span>
                <span class="value">{{ fundInfo.inception_date }}</span>
              </div>
              <div class="info-item" v-if="fundInfo.scale != null">
                <span class="label">基金规模</span>
                <span class="value">{{ fundInfo.scale.toLocaleString() }} 亿</span>
              </div>
              <div class="info-item" v-if="fundInfo.latest_nav != null">
                <span class="label">最新净值</span>
                <span class="value">¥{{ fundInfo.latest_nav }}<span class="nav-date" v-if="fundInfo.latest_nav_date">（{{ fundInfo.latest_nav_date }}）</span></span>
              </div>"""
assert c.count(old3) == 1, 'info item %d' % c.count(old3)
c = c.replace(old3, new3, 1)

io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK')
