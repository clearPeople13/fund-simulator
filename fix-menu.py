import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\App.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()
old = '''          <a-menu
            v-model:selectedKeys="selectedKeys"
            mode="horizontal"
            class="header-menu"
            @click="handleSelect"
          >'''
new = '''          <a-menu
            v-model:selectedKeys="selectedKeys"
            mode="horizontal"
            class="header-menu"
            :overflowed-indicator="null"
            @click="handleSelect"
          >'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('added overflowed-indicator=null')
