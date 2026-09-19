import io
p = r"C:\Users\jiancent\WorkBuddy\fund\fund-simulator\frontend\src\views\Home.vue"
with io.open(p, 'r', encoding='utf-8') as f:
    s = f.read()
s = s.replace("onMounted(() => {\n  loadHomeData()\n  startLiveStream()\n})", "onMounted(() => {\n  loadAllData()\n  startLiveStream()\n})")
with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
    f.write(s)
print('fixed')
