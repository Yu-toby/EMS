from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

kWh = 1000  # 1kWh = 1000度電
time_cycle = 3600  # 時間間隔為1小時

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

    def add_ev(self, ev):
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

    # *兩槍充電功率均分充電樁最大輸出功率*
    def update_ev_state_situation0(self, time_step):
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
        self.charge_start_time = charge_start_time
        self.charge_end_time = charge_end_time
        
        self.now_power = now_SOC * self.battery_max_capacity
        self.pile_number = None  # 車輛連接的充電樁編號

        self.charge_time = (self.charge_end_time - self.charge_start_time) if \
            self.charge_end_time > self.charge_start_time else (24 - self.charge_start_time + self.charge_end_time)
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

# # 模擬夜間充電
# ev1 = EV(1, 0.9, 0.2, 60, datetime(2023, 12, 15, 22, 0), datetime(2023, 12, 16, 5, 0))
# ev2 = EV(2, 0.9, 0.25, 60, datetime(2023, 12, 15, 22, 0), datetime(2023, 12, 16, 5, 0))
# ev3 = EV(3, 0.8, 0.35, 60, datetime(2023, 12, 15, 22, 0), datetime(2023, 12, 16, 5, 0))
# ev4 = EV(4, 0.8, 0.25, 60, datetime(2023, 12, 15, 22, 0), datetime(2023, 12, 16, 5, 0))
# ev5 = EV(5, 0.9, 0.35, 60, datetime(2023, 12, 15, 22, 0), datetime(2023, 12, 16, 5, 0))
# ev6 = EV(6, 0.85, 0.25, 60, datetime(2023, 12, 15, 22, 0), datetime(2023, 12, 16, 5, 0))
# ev7 = EV(7, 0.8, 0.30, 60, datetime(2023, 12, 15, 22, 0), datetime(2023, 12, 16, 5, 0))
# ev8 = EV(8, 0.9, 0.20, 60, datetime(2023, 12, 15, 22, 0), datetime(2023, 12, 16, 5, 0))
# ev9 = EV(9, 0.9, 0.3, 60, datetime(2023, 12, 15, 22, 0), datetime(2023, 12, 16, 5, 0))
# ev10 = EV(10, 0.8, 0.4, 60, datetime(2023, 12, 15, 22, 0), datetime(2023, 12, 16, 5, 0))

# evcs.add_to_ev_list(ev1)
# evcs.add_to_ev_list(ev2)
# evcs.add_to_ev_list(ev3)
# evcs.add_to_ev_list(ev4)
# evcs.add_to_ev_list(ev5)
# evcs.add_to_ev_list(ev6)
# evcs.add_to_ev_list(ev7)
# evcs.add_to_ev_list(ev8)
# evcs.add_to_ev_list(ev9)
# evcs.add_to_ev_list(ev10)

ev1 = EV(1, 0.9, 0.2, 60, datetime(2023, 12, 15, 6, 0), datetime(2023, 12, 15, 13, 0))
ev2 = EV(2, 0.9, 0.25, 60, datetime(2023, 12, 15, 7, 0), datetime(2023, 12, 15, 13, 0))
ev3 = EV(3, 0.8, 0.35, 60, datetime(2023, 12, 15, 8, 0), datetime(2023, 12, 15, 13, 0))
ev4 = EV(4, 0.8, 0.25, 60, datetime(2023, 12, 15, 9, 0), datetime(2023, 12, 15, 13, 0))
ev5 = EV(5, 0.9, 0.35, 60, datetime(2023, 12, 15, 10, 0), datetime(2023, 12, 15, 13, 0))
ev6 = EV(6, 0.85, 0.25, 60, datetime(2023, 12, 15, 11, 0), datetime(2023, 12, 15, 13, 0))

evcs.add_to_ev_list(ev1)
evcs.add_to_ev_list(ev2)
evcs.add_to_ev_list(ev3)
evcs.add_to_ev_list(ev4)
evcs.add_to_ev_list(ev5)
evcs.add_to_ev_list(ev6)

time = datetime(2023, 12, 15, 0, 0)

# while time < datetime(2023, 12, 16, 23, 0):
#     tou.current_time = time
#     for ev in evcs.ev_list:
#         if ev.charge_start_time == time:
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
ev1_soc_data = []
ev2_soc_data = []
ev3_soc_data = []
ev4_soc_data = []
ev5_soc_data = []
ev6_soc_data = []
ev7_soc_data = []
ev8_soc_data = []
ev9_soc_data = []
ev10_soc_data = []

time_list = []
piles_total_power = []
ess_charge_discharge = []
ess_soc = []
grid = []

for pile in charging_pile_status:
    pile_number = pile['pile_number']
    charging_power_data[f"Pile {pile_number} Gun 1"] = []
    charging_power_data[f"Pile {pile_number} Gun 2"] = []

while time < datetime(2023, 12, 17, 0, 0):
    tou.current_time = time
    for ev in evcs.ev_list:
        if ev.charge_start_time == time:
            evcs.add_ev(ev)
    evcs.update_ev_state_situation0(time)

    print(f"Hour {time.hour}")
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
    ev1_soc_data.append(ev1.now_SOC)
    ev2_soc_data.append(ev2.now_SOC)
    ev3_soc_data.append(ev3.now_SOC)
    ev4_soc_data.append(ev4.now_SOC)
    # ev5_soc_data.append(ev5.now_SOC)
    # ev6_soc_data.append(ev6.now_SOC)
    # ev7_soc_data.append(ev7.now_SOC)
    # ev8_soc_data.append(ev8.now_SOC)
    # ev9_soc_data.append(ev9.now_SOC)
    # ev10_soc_data.append(ev10.now_SOC)
    
    print("\n")

    time += timedelta(hours=1)

# =============================================================================
# 將數據保存到Excel文件
# 將充電功率和SOC數據轉換為pandas DataFrame
charging_power_df = pd.DataFrame(charging_power_data)
pile_total_power_df = pd.DataFrame({'Pile Total Power': piles_total_power})
ev_soc_df = pd.DataFrame({
    'EV1 SOC': ev1_soc_data,
    'EV2 SOC': ev2_soc_data,
    'EV3 SOC': ev3_soc_data,
    'EV4 SOC': ev4_soc_data,
    # 'EV5 SOC': ev5_soc_data,
    # 'EV6 SOC': ev6_soc_data,
    # 'EV7 SOC': ev7_soc_data,
    # 'EV8 SOC': ev8_soc_data,
    # 'EV9 SOC': ev9_soc_data,
    # 'EV10 SOC': ev10_soc_data,
})

# 將時間信息添加到 DataFrame 的第一行
charging_power_df.insert(0, 'Time', time_list)
pile_total_power_df.insert(0, 'Time', time_list)
ev_soc_df.insert(0, 'Time', time_list)

# 獲取腳本所在目錄的絕對路徑
script_directory = os.path.dirname(os.path.abspath(__file__))

# 獲取當前日期和時間
current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")

# 構建Excel文件的完整路徑，以日期和時間命名
excel_file_path = os.path.join(script_directory, "output_result_data", f"data_{current_datetime}.xlsx")

# 如果 "output_result_data" 資料夾不存在，則創建它
output_folder = os.path.join(script_directory, "output_result_data")
os.makedirs(output_folder, exist_ok=True)

# 將數據保存到Excel文件
with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:
    charging_power_df.to_excel(writer, sheet_name='Charging Power', index=False)
    pile_total_power_df.to_excel(writer, sheet_name='Pile total Power', index=False)
    ev_soc_df.to_excel(writer, sheet_name='EV SOC', index=False)

print("Excel檔案已成功生成：charging_data.xlsx")

# =============================================================================
# 繪製圖表
days = 2
x_ticks_positions = np.arange(0, 24 * days, 1)
x_ticks_labels = [(hr) % 24 for hr in range(24 * days)]

# 將時間步數轉換為小時
hours = np.arange(0, len(ev1_soc_data), 1)

plt.figure(1)
# 繪製柱狀圖
plt.subplot(2, 1, 1)
# plt.figure(figsize=(12, 6))
for pile, powers in charging_power_data.items():
    plt.bar(hours, powers, label=pile, alpha=0.7)
# 添加標題與標籤
plt.title('EV Charging Power Over a Day')
plt.xlabel('Time Steps (Hour)')
plt.ylabel('EV Charging Power (kW)')
# 設定 X 軸刻度標籤
plt.xticks(x_ticks_positions, x_ticks_labels)
# 添加圖例
plt.legend()

# 繪製SOC累積折線圖
plt.subplot(2, 1, 2)
plt.plot(hours, ev1_soc_data, label='EV1 SOC')
plt.plot(hours, ev2_soc_data, label='EV2 SOC')
plt.plot(hours, ev3_soc_data, label='EV3 SOC')
plt.plot(hours, ev4_soc_data, label='EV4 SOC')
# plt.plot(hours, ev5_soc_data, label='EV5 SOC')
# plt.plot(hours, ev6_soc_data, label='EV6 SOC')
# plt.plot(hours, ev7_soc_data, label='EV7 SOC')
# plt.plot(hours, ev8_soc_data, label='EV8 SOC')
# plt.plot(hours, ev9_soc_data, label='EV9 SOC')
# plt.plot(hours, ev10_soc_data, label='EV10 SOC')
# 添加標題與標籤
plt.title('EV SOC Over a Day')
plt.xlabel('Time Steps (Hour)')
plt.ylabel('EV SOC')
# 設定 X 軸刻度標籤
plt.xticks(x_ticks_positions, x_ticks_labels)
# 添加圖例
plt.legend()

# 調整子圖之間的間距
plt.tight_layout()

# 顯示圖表
plt.show()

