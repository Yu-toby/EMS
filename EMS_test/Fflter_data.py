import numpy as np
import pandas as pd

# 使用Z-score方法
# 從最一開始的資料中，取SOC需求量，將資料進行過濾，去除異常值(分佈太偏的值)，並計算過濾後的最大值、平均值、最小值

# 定義 Excel 文件路徑
excel_file_path = r"C:\Users\WYC\Desktop\電動大巴\EMS\EMS\資料生成\生成數據\generated_data.xlsx"

# 從 Excel 讀取數據
ev_data_df = pd.read_excel(excel_file_path, sheet_name='Sheet3')

# 將 'SOC需求量' 列轉換為 numpy 數組
data = ev_data_df['SOC需求量'].to_numpy()

# 計算 Q1 和 Q3
Q1 = np.percentile(data, 25)
Q3 = np.percentile(data, 75)
IQR = Q3 - Q1

# 定義異常值的範圍
outlier_lower = Q1 - 1.5 * IQR
outlier_upper = Q3 + 1.5 * IQR

# 過濾掉異常值，保留正常範圍內的數據
filtered_data = data[(data >= outlier_lower) & (data <= outlier_upper)]

# 計算過濾後的數據平均值
max_value = np.max(filtered_data)
average = np.mean(filtered_data)
min_value = np.min(filtered_data)
print("過濾後的最大值：", max_value)
print("過濾後的平均值：", average)
print("過濾後的最小值：", min_value)

# 計算過濾後數據的後半部平均值
half_index = len(filtered_data) // 2  # 計算中點索引
second_half_data = filtered_data[half_index:]  # 取得後半部的數據
average_second_half = np.mean(second_half_data)  # 計算後半部數據的平均值

print("過濾後的數據後半部的平均值：", average_second_half)