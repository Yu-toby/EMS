import matplotlib.pyplot as plt

# 設置時間和充電功率的列表
time = [0, 15, 30, 45, 60]
charging_power = [25, 25, 25, 25, 0]  # 最後一個時間點為 0，表示充滿

# 繪製折線圖
plt.plot(time, charging_power, marker='o')

# 添加標籤和標題
plt.xlabel('時間 (分鐘)')
plt.ylabel('充電功率 (kW)')
plt.title('充電功率隨時間變化')

# 顯示圖表
plt.grid(True)
plt.show()
