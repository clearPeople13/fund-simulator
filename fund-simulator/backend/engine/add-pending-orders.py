# -*- coding: utf-8 -*-
"""后端 /api/ai/transactions 附加 pending（该用户 SUBMITTED 订单 + fund_name），供前端展示待确认状态"""
import io, os

BASE = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator"
p = os.path.join(BASE, 'server.js')
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = """      enriched.push({ ...tx, fund_name: fund ? fund.fund_name : tx.fund_code });
    }
    res.json(enriched);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});"""
new = """      enriched.push({ ...tx, fund_name: fund ? fund.fund_name : tx.fund_code });
    }
    // 待确认订单（T+1：SUBMITTED，20:00 按 trade_date 官方净值落账）
    const pendingRows = await new Promise((resolve, reject) => {
      db.all("SELECT id, fund_code, order_type, amount, shares, price, fee, status, order_date, trade_date, reason FROM orders WHERE user_id = ? AND status = 'SUBMITTED' ORDER BY id DESC", [userId], (err, rows) => err ? reject(err) : resolve(rows || []));
    });
    const pending = [];
    for (const p of pendingRows) {
      const fund = await new Promise((resolve) => {
        db.get('SELECT fund_name FROM funds WHERE fund_code = ?', [p.fund_code], (err, row) => resolve(err ? null : row));
      });
      pending.push({ ...p, fund_name: fund ? fund.fund_name : p.fund_code });
    }
    res.json(Object.assign(enriched, { pending }));
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});"""
assert s.count(old) == 1, 'backend block not found'
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('server.js patched')
