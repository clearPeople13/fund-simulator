const sqlite3 = require('sqlite3');
const db = new sqlite3.Database('fund_simulator.db');
const codes = ['007340','501205','010033','014472','009715','519005','165528','017878','007490','005844','013840'];
db.all("SELECT fund_code, fund_name, fund_type, unit_nav, day_return, r1y, r3m, r6m, inception_date, scale FROM fund_universe WHERE fund_code IN ('" + codes.join("','") + "')", (e, rows) => {
  if (e) { console.log('ERR', e.message); return; }
  for (const r of rows) {
    const theme = /新能源|光伏|锂电|储能|风电|白酒|食品饮料|能源|石油|煤炭|钢铁|有色|化工|农业|养殖|消费|医药|医疗|生物|创新药|军工|国防|半导体|芯片|集成电路|电子|计算机|软件|信创|通信|5G|传媒|游戏|互联网|人工智能|AI|机器人|汽车|智能汽车|科创|创业板|专精特新|数字经济|云计算|大数据|数字|高端装备|高端制造|制造|改革|央企|国企|红利|环保|碳中和|基建|地产|银行|券商|保险|黄金|贵金属|原油|材料|设备|主题/.test(r.fund_name || '');
    console.log(r.fund_code, r.fund_name, '[' + r.fund_type + ']', 'theme=' + theme, 'r1y=' + r.r1y, 'r6m=' + r.r6m, 'scale=' + (r.scale == null ? '-' : r.scale));
  }
});
