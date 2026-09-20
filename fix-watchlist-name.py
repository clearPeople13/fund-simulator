import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\backend\server.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = '''      FROM watchlist w
      LEFT JOIN funds f ON w.fund_code = f.fund_code
      WHERE w.user_id = ?'''
new = '''      FROM watchlist w
      LEFT JOIN funds f ON w.fund_code = f.fund_code
      LEFT JOIN fund_universe fu ON w.fund_code = fu.fund_code
      WHERE w.user_id = ?'''
assert s.count(old) == 1
s = s.replace(old, new)

# fund_name 从 funds 或 fund_universe 拿
old2 = "          fund_name: row.fund_name,"
new2 = "          fund_name: row.fund_name || row.fu_fund_name,"
assert s.count(old2) == 1
s = s.replace(old2, new2)

# SQL 里加 fu.fund_name
old3 = '''             f.fund_name, f.fund_type,'''
new3 = '''             f.fund_name, f.fund_type,
             fu.fund_name AS fu_fund_name, fu.fund_type AS fu_fund_type,'''
assert s.count(old3) == 1
s = s.replace(old3, new3)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('watchlist join fund_universe added')
