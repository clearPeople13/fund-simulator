# -*- coding: utf-8 -*-
import io
p = r'C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue'
c = io.open(p, encoding='utf-8').read()
old = """  } catch (err) {
    console.warn('加载预估涨幅失败:', err.message)
  }"""
new = """  } catch (err: any) {
    console.warn('加载预估涨幅失败:', err.message)
  }"""
assert c.count(old) == 1, 'anchor'
c = c.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('OK')
