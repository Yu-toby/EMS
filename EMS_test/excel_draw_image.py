import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd



excel_file_path = r"C:\Users\WYC\Desktop\電動大巴\EMS\EMS\EMS_test\pile_output_result_data\pile_data_20240129_163433.xlsx"  
ev_data_df = pd.read_excel(excel_file_path, sheet_name='Pile total Power')
excel_file_path2 = r"C:\Users\WYC\Desktop\電動大巴\EMS\EMS\EMS_test\pile_output_result_data\pile_data_20240129_163453.xlsx"  
ev_data_df2 = pd.read_excel(excel_file_path2, sheet_name='Pile total Power')  # 注意這裡修改了檔案路徑和讀取的工作表

# 建立折線圖1
trace1 = go.Scatter(x=ev_data_df['Time'], y=ev_data_df['Pile Total Power'], mode='lines', name='未導入功率控制', legendgroup='group1')

# 建立折線圖2
trace2 = go.Scatter(x=ev_data_df2['Time'], y=ev_data_df2['Pile Total Power'], mode='lines', name='導入功率控制', legendgroup='group2')

# 建立佈局
layout = go.Layout(title='電動大巴總功率變化', xaxis=dict(title='日期時間'), yaxis=dict(title='功率'))

# 建立圖表
fig = go.Figure(data=[trace1, trace2], layout=layout)

# 顯示圖表
fig.show()
