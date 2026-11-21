cd "D:/Temp/claude/6a5fdc1be2cf0baf/f0b104f0-c447-4a40-a59b-216e29157d33/scratchpad/proto"
while ! grep -q END fetch_mars.log 2>/dev/null; do sleep 10; done
bash water_fetch_mars.sh data/mars; echo WATERDONE
