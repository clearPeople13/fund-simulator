import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\backend\routes\ai.js"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()

# 默认 mode='ai'（不是 'rule'）
old = "const analysisMode = mode || 'rule';"
new = "const analysisMode = mode || 'ai';  // 默认走 AI，失败自动降级到规则"
assert s.count(old) == 1
s = s.replace(old, new)

# AI 失败降级到规则时，日志要明确
old2 = '''        } else {
          // 规则模式：原来的 getFundSignal（保留不动）
          sig = await getFundSignal(code);
        }'''
new2 = '''        } else {
          // 规则模式：原来的 getFundSignal（保留不动）
          console.log(`[分析] ${code} 走规则引擎`);
          sig = await getFundSignal(code);
        }'''
assert s.count(old2) == 1
s = s.replace(old2, new2)

# AI 分析日志
old3 = '''          } catch (aiErr) {
            console.error('[AI] 分析失败: ' + aiErr.message);
            sig = await getFundSignal(code); // 降级到规则引擎
          }'''
new3 = '''          } catch (aiErr) {
            console.error(`[AI] ${code} 分析失败: ${aiErr.message}，降级到规则引擎`);
            sig = await getFundSignal(code); // 降级到规则引擎
          }'''
assert s.count(old3) == 1
s = s.replace(old3, new3)

with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('default AI mode + logs added')
