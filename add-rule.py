import io
p = r"C:\Users\jiancent\WorkBuddy\fund\docs\CODING_STANDARDS.md"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

old = '''## 一、总则

1. **功能优先，重构不破坏现有行为**：每次改动必须可运行、可验证，不允许"重构中跑不起来"。
2. **小步提交**：一个职责一次 commit，commit message 用 `type: 描述`（feat/fix/refactor/style/chore）。
3. **不过度设计**：三个相似片段再抽象；两个就复制。抽象成本高于复制成本时不抽象。'''
new = '''## 一、总则

1. **功能优先，重构不破坏现有行为**：每次改动必须可运行、可验证，不允许"重构中跑不起来"。
2. **小步提交**：一个职责一次 commit，commit message 用 `type: 描述`（feat/fix/refactor/style/chore）。
3. **不过度设计**：三个相似片段再抽象；两个就复制。抽象成本高于复制成本时不抽象。
4. **思考先行，不盲目编码**：收到需求后先想清楚——
   - 这个问题的根因是什么？（不是表面症状）
   - 真实业务规则是什么？（如：基金净值 21:30 才公布，不是 15:00）
   - 改了这个地方，其他地方会不会受影响？
   - 有没有更优解？（不是第一个想到的方案就直接写）
   - **想清楚了再动手**，不要"先改了再说，用户不满意再改"。'''
assert s.count(old) == 1
s = s.replace(old, new)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('thinking-first rule added')
