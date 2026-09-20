const s = require('sqlite3');
const db = new s.Database('C:/Users/jiancent/WorkBuddy/fund/fund-simulator/fund_simulator.db');

const funds = [
  { code: '005827', inception: '2018-09-05', manager: '张坤、杨思亮、何一铖', benchmark: '沪深300指数收益率×45%+中证港股通综合指数收益率×35%+中债总指数收益率×20%' },
  { code: '161725', inception: '2015-05-27', manager: '侯昊', benchmark: '中证白酒指数收益率×95%+金融机构人民币活期存款基准利率(税后)×5%' },
  { code: '000001', inception: '2001-12-18', manager: '郑晓辉、刘睿聪', benchmark: '中证800成长指数收益率×70%+中债-综合全价(总值)指数收益率×30%' },
  { code: '005267', inception: '2017-11-06', manager: '谭丽', benchmark: '中证800相对价值指数收益率×75%+恒生指数收益率×15%+中债-综合财富(总值)指数收益率×10%' }
];

let n = 0;
funds.forEach(f => {
  db.run('UPDATE funds SET inception_date=?, manager=?, benchmark=? WHERE fund_code=?', [f.inception, f.manager, f.benchmark, f.code], (err) => {
    if (err) console.error(f.code, err.message);
    else { console.log(f.code, '已更新:', f.manager); n++; }
  });
});
setTimeout(() => {
  db.all('SELECT fund_code, inception_date, manager, benchmark FROM funds WHERE fund_code IN (?,?,?,?)', ['005827','161725','000001','005267'], (e, r) => {
    console.log(JSON.stringify(r, null, 1));
    db.close();
  });
}, 500);
