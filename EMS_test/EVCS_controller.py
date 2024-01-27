from datetime import datetime, timedelta
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

kWh = 1000  # 1kWh = 1000度電
time_cycle = 3600/4  # 時間間隔為1小時

class TOU:
    def __init__(self, current_time=None):
        # TOU參數
        self.summer_peak_price = 9.34
        self.summer_off_peak_price = 2.29
        self.non_summer_peak_price = 9.10
        self.non_summer_off_peak_price = 2.18

        self.summer_peak_time_start = 16
        self.summer_peak_time_end = 22
        self.non_summer_peak_time_start = 15
        self.non_summer_peak_time_end = 21

        # 使用者提供時間，如果沒有提供就使用當前時間
        self.current_time = current_time if current_time is not None else datetime.now()

    def if_summer(self):  # 判斷是否為夏季
        if 6 <= self.current_time.month <= 9:
            return True
        else:
            return False

    def get_tou(self):  # 取得當前時間電價
        summer_month = 6 <= self.current_time.month <= 9
        weekday = 1 <= (self.current_time.weekday() + 1) <= 5

        if summer_month:
            if weekday and self.summer_peak_time_start <= self.current_time.hour < self.summer_peak_time_end:
                return "尖峰", self.summer_peak_price
            elif weekday and (0 <= self.current_time.hour < self.summer_peak_time_start or self.summer_peak_time_end <= self.current_time.hour <= 24):
                return "離峰", self.summer_off_peak_price
            else:
                return "離峰", self.summer_off_peak_price
        else:
            if weekday and (self.non_summer_peak_time_start <= self.current_time.hour < self.non_summer_peak_time_end):
                return "尖峰", self.non_summer_peak_price
            elif not weekday and (0 <= self.current_time.hour < self.non_summer_peak_time_start or self.non_summer_peak_time_end <= self.current_time.hour <= 24):
                return "離峰", self.non_summer_off_peak_price
            else:
                return "離峰", self.non_summer_off_peak_price  # 非夏月離峰時間


class EVCS:
    def __init__(self):
        self.pile_power_limit = 100 * 1000
        self.connected_evs = []
        self.ev_list = []
        piles_amount = 5
        self.charging_piles = []
        self.gun1_empty = True
        self.gun2_empty = True

        self.excel_mark = ['', '']

        for group in range(1, piles_amount + 1):
            charging_pile = {
                "pile_number": str(group),
                "gun": []
            }

            for sub_group in range(1, 3):  # 這裡使用 1 和 2 作為子組的標識
                gun_info = {
                    "gun_number": f"{group}-{sub_group}",
                    "ev_number": 0,
                    "charging_power": 0,
                    "start_time": 0,
                    "end_time": 0,
                    "already_time": 0
                }
                charging_pile["gun"].append(gun_info)

            self.charging_piles.append(charging_pile)


    def add_to_ev_list(self, ev):
        self.ev_list.append(ev)
    
    def delete_from_ev_list(self, ev):
        self.ev_list.remove(ev)

    # 照順序1-1, 1-2找空的槍
    def add_ev0(self, ev):   
        self.excel_mark[0] = '照順序1-1, 1-2找空的槍'
        # 逐一搜尋 charging_piles 集合中的每一個 charging_pile
        for charging_pile in self.charging_piles:
            guns = charging_pile.get('gun', [])

            # 逐一檢查每個 gun 的 ev_number
            for gun in guns:
                if gun['ev_number'] == 0:
                    # 如果 ev_number 為空，則填入要添加的 EV 資料
                    gun['ev_number'] = ev.number
                    gun['charging_power'] = 0  # 預設充電功率
                    gun['start_time'] = ev.charge_start_time
                    gun['end_time'] = ev.charge_end_time
                    gun['check_charging'] = False  # 預設未充電
                    self.connected_evs.append(ev)
                    return  # 結束函式，已找到並填入 EV 資料

                elif gun['ev_number'] == ev.number:
                    print('該車編號已存在，請確認是否有誤')
                    return  # 結束函式，已找到重複的 EV 資料

        print('找不到可用的充電槍，請檢查充電樁狀態')

    # 先找空的樁，若沒有才共用槍
    def add_ev1(self, ev):
        self.excel_mark[0] = '先找空的樁，若沒有才共用槍'
        # 逐一搜尋 charging_piles 集合中的每一個 charging_pile
        for num in range(2):
            for charging_pile in self.charging_piles:
                guns = charging_pile.get('gun', [])

                if guns[num]['ev_number'] == 0:
                    # 如果 ev_number 為空，則填入要添加的 EV 資料
                    guns[num]['ev_number'] = ev.number
                    guns[num]['charging_power'] = 0  # 預設充電功率
                    guns[num]['start_time'] = ev.charge_start_time
                    guns[num]['end_time'] = ev.charge_end_time
                    guns[num]['check_charging'] = False  # 預設未充電
                    self.connected_evs.append(ev)
                    return  # 結束函式，已找到並填入 EV 資料
                
                elif guns[num]['ev_number'] == ev.number:
                    print('該車編號已存在，請確認是否有誤')
                    return
                
                else:
                    continue
            
            print('找不到可用的充電槍，請檢查充電樁狀態')            

    def delete_ev(self, ev):
        # 逐一搜尋 charging_piles 集合中的每一個 charging_pile
        for charging_pile in self.charging_piles:
            guns = charging_pile.get('gun', [])

            # 逐一檢查每個 gun 的 ev_number
            for gun in guns:
                if gun['ev_number'] == ev.number:
                    # 如果 ev_number 不為空，則填入要添加的 EV 資料
                    gun['ev_number'] = 0
                    gun['charging_power'] = 0  # 預設充電功率
                    gun['start_time'] = 0
                    gun['end_time'] = 0
                    gun['check_charging'] = False  # 預設未充電
                    self.connected_evs.remove(ev)
                    return
                
                else:
                    # 如果 ev_number 為空，則檢查下一個 gun
                    continue

        print('找不到可用的充電槍，請檢查充電樁狀態')
    
    # *現況*
    def update_ev_state_situation0(self, time_step):
        self.excel_mark[1] = '滿功率充電'
        for charging_pile in self.charging_piles:
            guns = charging_pile.get('gun', [])
            check_ev_number1, check_ev_number2 = False, False
            # total_charging_power = 0  # 用於累計兩槍的總充電功率

            if len(guns) >= 2:
                # 直接存取兩個gun
                gun1, gun2 = guns[0], guns[1]
                ev_number1, ev_number2 = gun1['ev_number'], gun2['ev_number']
                charge_power1, charge_power2, charge_soc1, charge_soc2 = 0, 0, 0, 0

                if ev_number1 != 0:
                    self.gun1_empty = False
                    ev1 = self.find_ev_by_number(ev_number1)
                    if ev1:
                        if (ev1.now_SOC == ev1.target_SOC) or (gun1['check_charging'] and ev1.charge_end_time <= time_step):
                            # 充完電就離開
                            self.delete_ev(ev1)
                            check_ev_number1 = False
                            charge_power1, charge_soc1 = 0, 0
                            self.gun1_empty = True

                        if (ev1.charge_start_time <= time_step < ev1.charge_end_time):
                                gun1['check_charging'] = True
                                check_ev_number1 = True
                                # charge_power1, charge_soc1 = ev1.calculate_charge_power(time_step)
                                charge_power1 = min(self.pile_power_limit, (ev1.target_SOC - ev1.now_SOC) * ev1.battery_max_capacity)
                                charge_soc1 = charge_power1 / ev1.battery_max_capacity

                else:
                    self.gun1_empty = True

                if ev_number2 != 0:
                    self.gun2_empty = False
                    ev2 = self.find_ev_by_number(ev_number2)
                    if ev2:
                        if (ev2.now_SOC == ev2.target_SOC) or (gun2['check_charging'] and ev2.charge_end_time <= time_step):
                            # 充完電就離開
                            self.delete_ev(ev2)
                            check_ev_number2 = False
                            charge_power2, charge_soc2 = 0, 0
                            self.gun2_empty = True

                        if (ev2.charge_start_time <= time_step < ev2.charge_end_time):
                                gun2['check_charging'] = True
                                check_ev_number2 = True
                                # charge_power2, charge_soc2 = ev2.calculate_charge_power(time_step)
                                charge_power2 = min(self.pile_power_limit, (ev2.target_SOC - ev2.now_SOC) * ev2.battery_max_capacity)
                                charge_soc2 = charge_power2 / ev2.battery_max_capacity

                else:
                    self.gun2_empty = True

                if (charge_power1 + charge_power2) > self.pile_power_limit:
                    # 如果兩槍的充電功率總和超過充電樁功率上限
                    new_charge_power1 = min(charge_power1, (self.pile_power_limit / 2))
                    new_charge_power2 = min(charge_power2, (self.pile_power_limit / 2))
                    charge_soc1 = new_charge_power1 / ev1.battery_max_capacity
                    charge_soc2 = new_charge_power2 / ev2.battery_max_capacity

                    # 更新槍1的充電狀態
                    ev1.now_SOC += charge_soc1
                    ev1.now_power = ev1.now_SOC * ev1.battery_max_capacity
                    gun1['charging_power'] = round(new_charge_power1, 2)

                    # 更新槍2的充電狀態
                    ev2.now_SOC += charge_soc2
                    ev2.now_power = ev2.now_SOC * ev2.battery_max_capacity
                    gun2['charging_power'] = round(new_charge_power2, 2)

                else:
                    # 如果兩槍的充電功率總和沒有超過充電樁功率上限，則直接更新充電功率
                    if check_ev_number1:
                        # 更新槍1的充電狀態
                        ev1.now_SOC += charge_soc1
                        ev1.now_power = ev1.now_SOC * ev1.battery_max_capacity
                        gun1['charging_power'] = round(charge_power1, 2)
                    else:
                        gun1['charging_power'] = 0

                    if check_ev_number2:
                        # 更新槍2的充電狀態
                        ev2.now_SOC += charge_soc2
                        ev2.now_power = ev2.now_SOC * ev2.battery_max_capacity
                        gun2['charging_power'] = round(charge_power2, 2)
                    else:
                        gun2['charging_power'] = 0

        return self.charging_piles
    
    # *兩槍充電功率均分充電樁最大輸出功率*
    def update_ev_state_situation1(self, time_step):
        self.excel_mark[1] = '兩槍充電功率均分充電樁最大輸出功率'
        for charging_pile in self.charging_piles:
            guns = charging_pile.get('gun', [])
            check_ev_number1, check_ev_number2 = False, False
            # total_charging_power = 0  # 用於累計兩槍的總充電功率

            if len(guns) >= 2:
                # 直接存取兩個gun
                gun1, gun2 = guns[0], guns[1]
                ev_number1, ev_number2 = gun1['ev_number'], gun2['ev_number']
                charge_power1, charge_power2, charge_soc1, charge_soc2 = 0, 0, 0, 0

                if ev_number1 != 0:
                    self.gun1_empty = False
                    ev1 = self.find_ev_by_number(ev_number1)
                    if ev1:
                        if (ev1.now_SOC == ev1.target_SOC) or (gun1['check_charging'] and ev1.charge_end_time <= time_step):
                            # 充完電就離開
                            self.delete_ev(ev1)
                            check_ev_number1 = False
                            charge_power1, charge_soc1 = 0, 0
                            self.gun1_empty = True

                        if (ev1.charge_start_time <= time_step < ev1.charge_end_time):
                                gun1['check_charging'] = True
                                check_ev_number1 = True
                                charge_power1, charge_soc1 = ev1.calculate_charge_power(time_step)
                                charge_power1 = min(charge_power1, self.pile_power_limit)
                                charge_soc1 = charge_power1 / ev1.battery_max_capacity

                else:
                    self.gun1_empty = True

                if ev_number2 != 0:
                    self.gun2_empty = False
                    ev2 = self.find_ev_by_number(ev_number2)
                    if ev2:
                        if (ev2.now_SOC == ev2.target_SOC) or (gun2['check_charging'] and ev2.charge_end_time <= time_step):
                            # 充完電就離開
                            self.delete_ev(ev2)
                            check_ev_number2 = False
                            charge_power2, charge_soc2 = 0, 0
                            self.gun2_empty = True

                        if (ev2.charge_start_time <= time_step < ev2.charge_end_time):
                                gun2['check_charging'] = True
                                check_ev_number2 = True
                                charge_power2, charge_soc2 = ev2.calculate_charge_power(time_step)
                                charge_power2 = min(charge_power2, self.pile_power_limit)
                                charge_soc2 = charge_power2 / ev2.battery_max_capacity

                else:
                    self.gun2_empty = True

                if (charge_power1 + charge_power2) > self.pile_power_limit:
                    # 如果兩槍的充電功率總和超過充電樁功率上限
                    new_charge_power1 = min(charge_power1, (self.pile_power_limit / 2))
                    new_charge_power2 = min(charge_power2, (self.pile_power_limit / 2))
                    charge_soc1 = new_charge_power1 / ev1.battery_max_capacity
                    charge_soc2 = new_charge_power2 / ev2.battery_max_capacity

                    # 更新槍1的充電狀態
                    ev1.now_SOC += charge_soc1
                    ev1.now_power = ev1.now_SOC * ev1.battery_max_capacity
                    gun1['charging_power'] = round(new_charge_power1, 2)

                    # 更新槍2的充電狀態
                    ev2.now_SOC += charge_soc2
                    ev2.now_power = ev2.now_SOC * ev2.battery_max_capacity
                    gun2['charging_power'] = round(new_charge_power2, 2)

                else:
                    # 如果兩槍的充電功率總和沒有超過充電樁功率上限，則直接更新充電功率
                    if check_ev_number1:
                        # 更新槍1的充電狀態
                        ev1.now_SOC += charge_soc1
                        ev1.now_power = ev1.now_SOC * ev1.battery_max_capacity
                        gun1['charging_power'] = round(charge_power1, 2)
                    else:
                        gun1['charging_power'] = 0

                    if check_ev_number2:
                        # 更新槍2的充電狀態
                        ev2.now_SOC += charge_soc2
                        ev2.now_power = ev2.now_SOC * ev2.battery_max_capacity
                        gun2['charging_power'] = round(charge_power2, 2)
                    else:
                        gun2['charging_power'] = 0

            # elif len(guns) == 1:
            #     # 只有一個gun的處理方式
            #     gun = guns[0]
            #     ev_number = gun['ev_number']

            #     if ev_number != 0:
            #         ev = self.find_ev_by_number(ev_number)
            #         if ev and ev.charge_start_time <= time_step < ev.charge_end_time:
            #             charge_power, charge_soc = ev.calculate_charge_power(gun['already_time'])
            #             charging_power_limit = min(charge_power, self.pile_power_limit - total_charging_power)
            #             # 更新槍的充電狀態
            #             ev.now_SOC += charge_soc
            #             ev.now_power = ev.now_SOC * ev.battery_max_capacity
            #             gun['charging_power'] = round(charging_power_limit, 2)
            #             gun['already_time'] += 1
            #             total_charging_power += charging_power_limit

        return self.charging_piles

    def find_ev_by_number(self, ev_number):
        for ev in self.connected_evs:
            if ev.number == ev_number:
                return ev
        return None
    
    def get_ev_summary(self):
        # 取得車輛充電當下SOC及power
        summary_soc = {ev.number: round(ev.now_SOC, 2) for ev in self.connected_evs}
        summary_power = {ev.number: round(ev.now_power, 2) for ev in self.connected_evs}
        return summary_soc, summary_power
    
    def get_pile_summary(self):
        # 取得充電樁充電當下功率
        summary_power = {}
        for charging_pile in self.charging_piles:
            guns = charging_pile.get('gun', [])
            for gun in guns:
                summary_power[gun['gun_number']] = gun['charging_power']
                total_power = sum(summary_power.values())
        return summary_power, total_power

    def check_pile_if_empty(self):
        # 檢查充電樁是否有空位
        for charging_pile in self.charging_piles:
            guns = charging_pile.get('gun', [])
            for gun in guns:
                if gun['ev_number'] == 0:
                    return True
        return False


class EV:
    def __init__(self, number, target_SOC, now_SOC, power_limit, charge_start_time, charge_end_time):
        # 電動車參數
        self.battery_max_capacity = 300 * 1000  # 假設單位是kWh

        self.number = number
        self.target_SOC = target_SOC
        self.now_SOC = now_SOC
        self.power_limit = power_limit
        self.charge_start_time = charge_start_time + timedelta(seconds=time_cycle)
        self.charge_end_time = charge_end_time + timedelta(seconds=time_cycle)
        
        self.now_power = now_SOC * self.battery_max_capacity
        self.pile_number = None  # 車輛連接的充電樁編號

        self.charge_already_time = 0
        self.charge_pi = 0  # 倍分配充電係數

    def calculate_charge_power(self, time):
        # 計算每小時所需充電功率
        if self.charge_start_time <= time < self.charge_end_time:
            charge_soc = (self.target_SOC - self.now_SOC) / ((self.charge_end_time - time).total_seconds() / time_cycle)
            charge_power = charge_soc * self.battery_max_capacity
        else:
            charge_power = 0
            charge_soc = 0
        
        return charge_power, charge_soc
    

tou = TOU()
evcs = EVCS()

# 讀取包含 EV 初始資料的 Excel 文件
excel_file_path = r"C:\Users\WYC\Desktop\電動大巴\EMS\EMS\資料生成\生成數據\generated_data.xlsx"  
ev_data_df = pd.read_excel(excel_file_path, sheet_name='Sheet1')

# 創建一個空的列表，用於存儲所有 EV 對象
ev_list = []
# 創建一個字典，用於存儲不同 EV 對象的 SOC 數據
ev_soc_data_dict = {}

# 將 EV 初始資料從 DataFrame 中讀取
for _, ev_row in ev_data_df.iterrows():

    # 直接使用 to_datetime 將 Timestamp 轉換為 datetime 對象
    start_charge_time = pd.to_datetime(ev_row['開始充電時間'])
    end_charge_time = pd.to_datetime(ev_row['結束充電時間'])

    # 使用轉換後的時間數據創建 EV 對象
    ev = EV(
        ev_row['卡片名稱'],
        ev_row['SoC(結束)']/100,
        ev_row['SoC(開始)']/100,
        100,
        start_charge_time,
        end_charge_time
    )
    ev_list.append(ev)
    evcs.add_to_ev_list(ev)
    # 添加 EV 對象的 SOC 數據到字典中
    ev_soc_data_dict[ev.number] = []

time = datetime(2024, 1, 26, 0, 0)

# while time < datetime(2023, 12, 16, 23, 0):
#     tou.current_time = time
#     for ev in evcs.ev_list:
#         if ev.charge_start_time <= time:
#             evcs.add_ev(ev)
#             evcs.delete_from_ev_list(ev)
#     evcs.update_ev_state_situation0(time)

#     print(f"Hour {time.hour} Charging Pile Status:")
#     for charging_pile in evcs.charging_piles:
#         pile_number = charging_pile["pile_number"]
#         gun_1 = charging_pile["gun"][0]
#         gun_2 = charging_pile["gun"][1]

#         print(f"Pile {pile_number} Gun 1: {gun_1}")
#         print(f"Pile {pile_number} Gun 2: {gun_2}")

#     ev_soc_summary, ev_power_summary = evcs.get_ev_summary()
#     print(f"EV SOC Summary: {ev_soc_summary}  /  EV Power Summary: {ev_power_summary}")
#     pile_summary, pile_total_power = evcs.get_pile_summary()
#     print(f"Pile Summary: {pile_summary}  /  Pile Total Power: {pile_total_power}")

#     # print(f"ESS Provide Power: {ess_provide}  /  Grid Provide Power: {grid_provide}")

#     print("\n")

#     time += timedelta(hours=1)


# =============================================================================
# 提取充電樁狀態
charging_pile_status = evcs.charging_piles

# 建立一個字典來存儲每小時每個充電樁的充電功率
charging_power_data = {}

time_list = []
piles_total_power = []
ess_charge_discharge = []
ess_soc = []
grid = []

for pile in charging_pile_status:
    pile_number = pile['pile_number']
    charging_power_data[f"Pile {pile_number} Gun 1"] = []
    charging_power_data[f"Pile {pile_number} Gun 2"] = []

while time < datetime(2024, 2, 3, 0, 0):
    tou.current_time = time
    for ev in evcs.ev_list:
        if ev.charge_start_time <= time:
            evcs.add_ev1(ev)
            evcs.delete_from_ev_list(ev)
    evcs.update_ev_state_situation1(time)

    print(f"Time {time}")
    for idx, charging_pile in enumerate(charging_pile_status):
        gun_1_power = charging_pile["gun"][0]["charging_power"]
        gun_2_power = charging_pile["gun"][1]["charging_power"]

        pile_number = charging_pile["pile_number"]
        charging_power_data[f"Pile {pile_number} Gun 1"].append(gun_1_power)
        charging_power_data[f"Pile {pile_number} Gun 2"].append(gun_2_power)

    ev_soc_summary, ev_power_summary = evcs.get_ev_summary()
    print(f"EV SOC Summary: {ev_soc_summary}  /  EV Power Summary: {ev_power_summary}")
    pile_summary, pile_total_power = evcs.get_pile_summary()
    print(f"Pile Summary: {pile_summary}  /  Pile Total Power: {pile_total_power}")
    
    time_list.append(time)
    piles_total_power.append(pile_total_power)
    for ev in ev_list:
        ev_soc_data_dict[ev.number].append(ev.now_SOC)
    
    print("\n")

    time += timedelta(seconds=time_cycle)

# =============================================================================
# 將數據保存到Excel文件
# 將充電功率和SOC數據轉換為pandas DataFrame
charging_power_df = pd.DataFrame(charging_power_data)
pile_total_power_df = pd.DataFrame({'Pile Total Power': piles_total_power})
illustrate_df = pd.DataFrame({'說明': evcs.excel_mark})

# 將時間信息添加到 DataFrame 的第一行
charging_power_df.insert(0, 'Time', time_list)
pile_total_power_df.insert(0, 'Time', time_list)

# 添加描述性的標題行
pile_total_power_df.columns = ['Time', 'Pile Total Power']

# 獲取腳本所在目錄的絕對路徑
script_directory = os.path.dirname(os.path.abspath(__file__))

# 獲取當前日期和時間
current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")

# 構建Excel文件的完整路徑，以日期和時間命名
excel_file_path = os.path.join(script_directory, "pile_output_result_data", f"pile_data_{current_datetime}.xlsx")

# 如果 "pile_output_result_data" 資料夾不存在，則創建它
output_folder = os.path.join(script_directory, "pile_output_result_data")
os.makedirs(output_folder, exist_ok=True)

# 將數據保存到Excel文件
with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:
    illustrate_df.to_excel(writer, sheet_name='說明', index=False)
    pile_total_power_df.to_excel(writer, sheet_name='Pile total Power', index=False)
    charging_power_df.to_excel(writer, sheet_name='Charging Power', index=False)
    # ev_soc_df.to_excel(writer, sheet_name='EV SOC', index=False)

print("Excel檔案已成功生成：charging_data.xlsx")

# =============================================================================
# 繪製圖表
days = 2
x_ticks_positions = np.arange(0, 24 * days, 1)
x_ticks_labels = [(hr) % 24 for hr in range(24 * days)]

# 將時間步數轉換為小時
hours = np.arange(0, len(time_list), 1)

# 創建一個 subplot
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                    subplot_titles=['EV Charging Power Over a Day', 'EV SOC Over a Day'],
                    row_heights=[1,0]) # 設定子圖的高度比例

# 添加充電功率折線圖
for idx, (pile, powers) in enumerate(charging_power_data.items()):
    fig.add_trace(go.Scatter(x=time_list, y=powers, mode='lines', name=pile, legendgroup=f"group{idx}"), row=1, col=1)

# 添加充電樁總功率折線圖
fig.add_trace(go.Scatter(x=time_list, y=piles_total_power, mode='lines', name='Piles Total Power', legendgroup=f"group{11}"), row=1, col=1)

# # 添加 SOC 折線圖
# for ev_number, soc_data in ev_soc_data_dict.items():
#     fig.add_trace(go.Scatter(x=time_list, y=soc_data, mode='lines', name=f'{ev_number} SOC', xaxis='x2'), row=2, col=1)

# 設定布局
fig.update_layout(title_text='EV Charging and SOC Over a Day',
                    xaxis_title='Time Steps (Hour)',
                    yaxis_title='Power (W)',
                    xaxis2_title='Time Steps (Hour)',
                    yaxis2_title='SOC',
                    showlegend=True,  # 顯示圖例
                    xaxis=dict(type='category', tickmode='array', tickvals=time_list, ticktext=[str(t) for t in time_list]),
                    barmode='group',  # stack：將柱狀圖疊加顯示；group：將柱狀圖並排顯示；overlay：將柱狀圖重疊顯示，並將透明度設為0.5
                    bargap=0.2)  # 控制柱狀圖之間的間距

# 顯示圖表
fig.show()