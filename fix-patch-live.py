import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\engine\patch-home-live-log.py"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()
s = s.replace("onMounted(() => {\n  loadHomeData()\n})", "onMounted(() => {\n  loadAllData()\n})")
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('patched')
