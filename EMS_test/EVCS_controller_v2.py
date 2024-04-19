from datetime import datetime, timedelta
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

kWh = 1000  # 1kWh = 1000度電
time_cycle = 3600/60  # 1小時秒數 / 多久一筆資料的秒數(1小時一筆：3600 ；1分鐘一筆；60)

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
        self.ev_waiting_list = []
        piles_amount = 5
        self.charging_piles = []
        self.gun1_empty = True
        self.gun2_empty = True
        self.check_ev_number1 = False
        self.check_ev_number2 = False

        self.excel_instructions = ['', '']

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
                    "charging_soc": 0,
                    "start_time": 0,
                    "end_time": 0,
                    "already_time": 0
                }
                charging_pile["gun"].append(gun_info)

            self.charging_piles.append(charging_pile)

# 增減等待的車輛===============================================================
    def add_to_ev_waiting_list(self, ev):
        self.ev_waiting_list.append(ev)
    
    def delete_from_ev_waiting_list(self, ev):
        self.ev_waiting_list.remove(ev)
# 找空位充電===================================================================
    # 照順序1-1, 1-2找空的槍
    def add_ev0(self, ev):   
        self.excel_instructions[0] = '照順序1-1, 1-2找空的槍'
        # 逐一搜尋 charging_piles 集合中的每一個 charging_pile
        for charging_pile in self.charging_piles:
            guns = charging_pile.get('gun', [])

            # 逐一檢查每個 gun 的 ev_number
            for gun in guns:
                # 如果 ev_number 為空，則填入要添加的 EV 資料
                if gun['ev_number'] == 0:
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

    # 先找兩隻槍都沒有在用的樁，若沒有才共用槍
    def add_ev1(self, ev):
        self.excel_instructions[0] = '先找兩隻槍都沒有在用的樁，若沒有才共用槍'
        # 先找有沒有空的樁
        for charging_pile in self.charging_piles:
            guns = charging_pile.get('gun', [])

            if guns[0]['ev_number'] == 0 and guns[1]['ev_number'] == 0:
                # 如果兩隻槍都沒有在用，則填入要添加的 EV 資料
                guns[0]['ev_number'] = ev.number
                guns[0]['charging_power'] = 0
                guns[0]['charging_soc'] = 0
                guns[0]['start_time'] = ev.charge_start_time
                guns[0]['end_time'] = ev.charge_end_time
                guns[0]['check_charging'] = False
                ev.gun_number = guns[0]['gun_number']
                self.connected_evs.append(ev)
                return {'state': True}  # 結束函式，已找到並填入 EV 資料
            
        # 如果沒有空的樁，則找有沒有任一隻槍沒有在用的樁
        for charging_pile in self.charging_piles:
            guns = charging_pile.get('gun', [])

            if guns[0]['ev_number'] == 0 and guns[1]['ev_number'] != 0:
                # 如果第一隻槍沒有在用，則填入要添加的 EV 資料
                guns[0]['ev_number'] = ev.number
                guns[0]['charging_power'] = 0
                guns[0]['charging_soc'] = 0
                guns[0]['start_time'] = ev.charge_start_time
                guns[0]['end_time'] = ev.charge_end_time
                guns[0]['check_charging'] = False
                ev.gun_number = guns[0]['gun_number']
                self.connected_evs.append(ev)
                return {'state': True}  # 結束函式，已找到並填入 EV 資料
            elif guns[0]['ev_number'] != 0 and guns[1]['ev_number'] == 0:
                # 如果第二隻槍沒有在用，則填入要添加的 EV 資料
                guns[1]['ev_number'] = ev.number
                guns[1]['charging_power'] = 0
                guns[1]['charging_soc'] = 0
                guns[1]['start_time'] = ev.charge_start_time
                guns[1]['end_time'] = ev.charge_end_time
                guns[1]['check_charging'] = False
                ev.gun_number = guns[1]['gun_number']
                self.connected_evs.append(ev)
                return  {'state': True}  # 結束函式，已找到並填入 EV 資料
            elif guns[0]['ev_number'] == ev.number or guns[1]['ev_number'] == ev.number:
                print(f"time:{ev.charge_start_time} / {ev.number} - 該車編號已存在，請確認是否有誤")
                return  {'state': False, 'illustrate': "資料有誤，該車編號已存在"}  # 結束函式，已找到重複的 EV 資料
            
        print(f"{ev.charge_start_time} / {ev.number}找不到可用的充電槍，請檢查充電樁狀態")
        return  {'state': False, 'illustrate': "找不到可用的充電槍，請檢查充電樁狀態"}  

    def delete_ev(self, ev):
        # 逐一搜尋 charging_piles 集合中的每一個 charging_pile
        for charging_pile in self.charging_piles:
            guns = charging_pile.get('gun', [])

            # 逐一檢查每個 gun 的 ev_number
            for gun in guns:
                if gun['ev_number'] == ev.number:
                    # 如果找到對應的充電槍，則移除該EV資料
                    gun['ev_number'] = 0
                    gun['charging_power'] = 0  # 預設充電功率
                    gun['charging_soc'] = 0
                    gun['start_time'] = 0
                    gun['end_time'] = 0
                    gun['check_charging'] = False  # 預設未充電
                    self.connected_evs.remove(ev)
                    return
                

# 需要用到的函式===============================================================
    def find_ev_by_number(self, ev_number):
        for ev in self.connected_evs:
            if ev.number == ev_number:
                return ev
        return None
    
    def get_ev_summary(self):
        # 取得車輛充電當下SOC及power
        # summary_soc = {ev.number: round(ev.now_SOC, 2) for ev in self.connected_evs}
        summary_soc = {ev.number: ev.now_SOC for ev in self.connected_evs}
        summary_power = {ev.number: (ev.now_power) for ev in self.connected_evs}
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

    # 判斷兩槍輸出功率是否超過充電樁供電上限(第一槍車輛number, 第二槍車輛number, 第一槍, 第二槍)
    def if_over_pile_power_limit(self, ev_number1, ev_number2, gun1, gun2):
            # # print(f"ev_number1: {ev_number1} / ev_number2: {ev_number2}")
            # ev1 = self.find_ev_by_number(ev_number1)
            # ev2 = self.find_ev_by_number(ev_number2)
            # # print(f"ev1: {ev1} / ev2: {ev2}")
            # # print(f"ev1_gun: {ev1.gun_number} / ev2_gun: {ev2.gun_number}")
            # gun1 = self.charging_piles[int(ev1.gun_number.split('-')[0]) - 1]['gun'][int(ev1.gun_number.split('-')[1]) - 1]
            # gun2 = self.charging_piles[int(ev2.gun_number.split('-')[0]) - 1]['gun'][int(ev2.gun_number.split('-')[1]) - 1]
            # charge_power1 = ev1.charge_power
            # charge_power2 = ev2.charge_power
            # charge_soc1 = charge_power1 / ev1.battery_max_capacity
            # charge_soc2 = charge_power2 / ev2.battery_max_capacity

            # 從EV端取得兩槍的充電功率、充電SOC及對應的充電樁編號
            if self.check_ev_number1:
                ev1 = self.find_ev_by_number(ev_number1)
                gun1 = self.charging_piles[int(ev1.gun_number.split('-')[0]) - 1]['gun'][int(ev1.gun_number.split('-')[1]) - 1]
                charge_power1 = ev1.charge_power
                charge_soc1 = charge_power1 / ev1.battery_max_capacity
            else:
                charge_power1 = 0
                charge_soc1 = 0
            
            if self.check_ev_number2:
                ev2 = self.find_ev_by_number(ev_number2)
                gun2 = self.charging_piles[int(ev2.gun_number.split('-')[0]) - 1]['gun'][int(ev2.gun_number.split('-')[1]) - 1]
                charge_power2 = ev2.charge_power
                charge_soc2 = charge_power2 / ev2.battery_max_capacity
            else:
                charge_power2 = 0
                charge_soc2 = 0

            # 開始判斷處
            if (charge_power1 + charge_power2) > self.pile_power_limit:
                # 如果兩槍的充電功率總和超過充電樁功率上限
                new_charge_power1 = min(charge_power1, (self.pile_power_limit / 2))
                new_charge_power2 = min(charge_power2, (self.pile_power_limit / 2))
                charge_soc1 = new_charge_power1 / ev1.battery_max_capacity
                charge_soc2 = new_charge_power2 / ev2.battery_max_capacity

                # 更新槍1的充電狀態
                ev1.now_SOC += charge_soc1
                ev1.now_power = ev1.now_SOC * ev1.battery_max_capacity
                gun1['charging_power'] = (new_charge_power1)
                gun1['charging_soc'] = charge_soc1

                # 更新槍2的充電狀態
                ev2.now_SOC += charge_soc2
                ev2.now_power = ev2.now_SOC * ev2.battery_max_capacity
                gun2['charging_power'] = (new_charge_power2)
                gun2['charging_soc'] = charge_soc2

            else:
                # 如果兩槍的充電功率總和沒有超過充電樁功率上限，則直接更新充電功率
                if self.check_ev_number1:
                    # 更新槍1的充電狀態
                    # ev1.now_SOC += charge_soc1
                    # ev1.now_power = ev1.now_SOC * ev1.battery_max_capacity
                    ev1.now_power += charge_power1
                    ev1.now_SOC = ev1.now_power / ev1.battery_max_capacity
                    gun1['charging_power'] = (charge_power1)
                    gun1['charging_soc'] = charge_soc1 / ev1.battery_max_capacity
                else:
                    gun1['charging_power'] = 0
                    gun1['charging_soc'] = 0

                if self.check_ev_number2:
                    # 更新槍2的充電狀態
                    # ev2.now_SOC += charge_soc2
                    # ev2.now_power = ev2.now_SOC * ev2.battery_max_capacity
                    ev2.now_power += charge_power2
                    ev2.now_SOC = ev2.now_power / ev2.battery_max_capacity
                    gun2['charging_power'] = (charge_power2)
                    gun2['charging_soc'] = charge_soc2 / ev2.battery_max_capacity
                else:
                    gun2['charging_power'] = 0
                    gun2['charging_soc'] = 0

# 充電=========================================================================
    # 最大供率充電
    def charging_method0(self, time_step):
        self.excel_instructions[1] = '最大供率充電'
        for charging_pile in self.charging_piles:
            guns = charging_pile.get('gun', [])
            check_ev_number1, check_ev_number2 = False, False
            gun1, gun2 = guns[0], guns[1]
            ev_number1, ev_number2 = gun1['ev_number'], gun2['ev_number']
            charge_power1, charge_power2, charge_soc1, charge_soc2 = 0, 0, 0, 0
            
            # 計算各槍充電功率
            if ev_number1 != 0:
                self.gun1_empty = False
                ev1 = self.find_ev_by_number(ev_number1)
                if ev1:
                    if (ev1.now_SOC >= ev1.target_SOC):
                        # 充完電就離開
                        self.delete_ev(ev1)
                        check_ev_number1 = False
                        charge_power1, charge_soc1 = 0, 0
                        self.gun1_empty = True

                    if (ev1.charge_start_time <= time_step):
                        gun1['check_charging'] = True
                        check_ev_number1 = True
                        # charge_power1, charge_soc1 = ev1.calculate_charge_power(time_step)
                        # charge_power1 = self.pile_power_limit
                        charge_power1 = min(self.pile_power_limit, (ev1.target_SOC - ev1.now_SOC) * ev1.battery_max_capacity)
                        charge_soc1 = charge_power1 / ev1.battery_max_capacity

            else:
                self.gun1_empty = True

            if ev_number2 != 0:
                self.gun2_empty = False
                ev2 = self.find_ev_by_number(ev_number2)
                if ev2:
                    if (ev2.now_SOC >= ev2.target_SOC):
                        # 充完電就離開
                        self.delete_ev(ev2)
                        check_ev_number2 = False
                        charge_power2, charge_soc2 = 0, 0
                        self.gun2_empty = True

                    if (ev2.charge_start_time <= time_step):
                        gun2['check_charging'] = True
                        check_ev_number2 = True
                        # charge_power2, charge_soc2 = ev2.calculate_charge_power(time_step)
                        # charge_power2 = self.pile_power_limit
                        charge_power2 = min(self.pile_power_limit, (ev2.target_SOC - ev2.now_SOC) * ev2.battery_max_capacity)
                        charge_soc2 = charge_power2 / ev2.battery_max_capacity

            else:
                self.gun2_empty = True

            # 判斷兩槍輸出功率是否超過充電樁供電上限
            if (charge_power1 + charge_power2) > self.pile_power_limit:
                # 如果兩槍的充電功率總和超過充電樁功率上限
                new_charge_power1 = min((self.pile_power_limit / 2), charge_power1)
                new_charge_power2 = min((self.pile_power_limit / 2), charge_power2)
                charge_soc1 = new_charge_power1 / ev1.battery_max_capacity
                charge_soc2 = new_charge_power2 / ev2.battery_max_capacity

                # 更新槍1的充電狀態
                ev1.now_SOC += charge_soc1
                ev1.now_power = ev1.now_SOC * ev1.battery_max_capacity
                gun1['charging_power'] = (new_charge_power1)

                # 更新槍2的充電狀態
                ev2.now_SOC += charge_soc2
                ev2.now_power = ev2.now_SOC * ev2.battery_max_capacity
                gun2['charging_power'] = (new_charge_power2)

            else:
                # 如果兩槍的充電功率總和沒有超過充電樁功率上限，則直接更新充電功率
                if check_ev_number1:
                    # 更新槍1的充電狀態
                    ev1.now_SOC += charge_soc1
                    ev1.now_power = ev1.now_SOC * ev1.battery_max_capacity
                    gun1['charging_power'] = (charge_power1)
                else:
                    gun1['charging_power'] = 0

                if check_ev_number2:
                    # 更新槍2的充電狀態
                    ev2.now_SOC += charge_soc2
                    ev2.now_power = ev2.now_SOC * ev2.battery_max_capacity
                    gun2['charging_power'] = (charge_power2)
                else:
                    gun2['charging_power'] = 0

        return self.charging_piles

    # 平均功率充電
    def charging_method1(self, time_step):
        self.excel_instructions[1] = '平均功率充電'
        for charging_pile in self.charging_piles:
            guns = charging_pile.get('gun', [])
            self.check_ev_number1, self.check_ev_number2 = False, False
            gun1, gun2 = guns[0], guns[1]
            ev_number1, ev_number2 = gun1['ev_number'], gun2['ev_number']
            ev_number1_gun, ev_number2_gun = gun1['gun_number'], gun2['gun_number']
            charge_power1, charge_power2, charge_soc1, charge_soc2 = 0, 0, 0, 0
            
            # 計算各槍充電功率
            if ev_number1 != 0:
                self.gun1_empty = False
                ev1 = self.find_ev_by_number(ev_number1)
                if ev1:
                    # print(f"ev1: {ev1.number} / soc: {ev1.now_SOC} / target_soc: {ev1.target_SOC} / start_time: {ev1.charge_start_time} / end_time: {ev1.charge_end_time}")
                    if (ev1.now_SOC >= ev1.target_SOC) or (gun1['check_charging'] and ev1.charge_end_time <= time_step):
                        # 充完電就離開
                        # print(f"ev1: {ev1.number} depart")
                        self.delete_ev(ev1)
                        self.check_ev_number1 = False
                        charge_power1, charge_soc1 = 0, 0
                        self.gun1_empty = True

                    else:
                            # print(f"ev1: {ev1.number} charging")
                            gun1['check_charging'] = True
                            self.check_ev_number1 = True
                            charge_power1, charge_soc1 = ev1.calculate_charge_power(time_step)
                            charge_power1 = min(charge_power1, self.pile_power_limit)
                            ev1.charge_power = charge_power1
                            # charge_soc1 = charge_power1 / ev1.battery_max_capacity

            else:
                self.gun1_empty = True

            if ev_number2 != 0:
                self.gun2_empty = False
                ev2 = self.find_ev_by_number(ev_number2)
                if ev2:
                    if (ev2.now_SOC >= ev2.target_SOC) or (gun2['check_charging'] and ev2.charge_end_time <= time_step):
                        # 充完電就離開
                        self.delete_ev(ev2)
                        self.check_ev_number2 = False
                        charge_power2, charge_soc2 = 0, 0
                        self.gun2_empty = True

                    else:
                            gun2['check_charging'] = True
                            self.check_ev_number2 = True
                            charge_power2, charge_soc2 = ev2.calculate_charge_power(time_step)
                            charge_power2 = min(charge_power2, self.pile_power_limit)
                            ev2.charge_power = charge_power2
                            # charge_soc2 = charge_power2 / ev2.battery_max_capacity

            else:
                self.gun2_empty = True

            if self.check_ev_number1 or self.check_ev_number2:
                # print(f"gun1_number: {ev_number1_gun} / gun2_number: {ev_number2_gun}")
                self.if_over_pile_power_limit(ev_number1, ev_number2, gun1, gun2)
        
        return self.charging_piles


    
# 電動車=======================================================================
class EV:
    def __init__(self, number, target_SOC, now_SOC, power_limit, charge_start_time, charge_end_time):
        # 電動車參數
        self.battery_max_capacity = 300 * 1000 * time_cycle # 假設單位是Wh
        
        # 有提供的資訊
        self.number = number
        self.target_SOC = target_SOC
        self.now_SOC = now_SOC
        # self.charge_start_time = charge_start_time + timedelta(seconds=time_cycle)
        # self.charge_end_time = charge_end_time + timedelta(seconds=time_cycle)
        self.charge_start_time = charge_start_time
        self.charge_end_time = charge_end_time
        
        # 計算的資訊
        self.now_power = now_SOC * self.battery_max_capacity
        self.gun_number = None  # 車輛連接的充電樁編號

        self.charge_power = 0
        
        self.power_limit = power_limit
        self.charge_pi = 0  # 倍分配充電係數

    def calculate_charge_power(self, current_time):
        # 計算每小時所需充電功率
        if self.charge_start_time <= current_time < self.charge_end_time:
            # 每小時/每分鐘 充多少SOC，看time_cycle決定
            # charge_soc = (((self.target_SOC - self.now_SOC)) / ((self.charge_end_time - current_time).total_seconds() / 3600)) / time_cycle
            try :
                charge_soc = ((self.target_SOC - self.now_SOC)) / int((self.charge_end_time - current_time).total_seconds() / time_cycle)
            except ZeroDivisionError:
                charge_soc = 0
            # charge_soc = (((self.target_SOC - self.now_SOC)) /((self.charge_end_time - current_time).total_seconds() / time_cycle))
            # 每個時刻充電功率(W)
            charge_power = charge_soc * self.battery_max_capacity
        else:
            charge_power = 0
            charge_soc = 0
        # if self.number == 'EAA-780':
        #     print(f"now_soc: {self.now_SOC} / target_soc: {self.target_SOC}  / charging_time: {int((self.charge_end_time - current_time).total_seconds() / time_cycle)}  /  Charge Power: {charge_power}  /  Charge SOC: {charge_soc}")
        return charge_power, charge_soc # 回傳 充電功率(W)、充多少SOC
    

# 主程式=======================================================================
tou = TOU()
evcs = EVCS()

# 讀取包含 EV 初始資料的 Excel 文件
excel_file_path = r"C:\Users\WYC\Desktop\電動大巴\EMS\EMS\資料生成\生成數據\original_end時間有改.xlsx"  
# excel_file_path = r"C:\Users\WYC\Desktop\電動大巴\EMS\EMS\資料生成\生成數據\generated_data.xlsx"  
ev_data_df = pd.read_excel(excel_file_path, sheet_name='Sheet1')

# 創建一個空的列表，用於存儲所有 EV 對象
ev_waiting_list = []
# 創建一個字典，用於存儲不同 EV 對象的 SOC 數據
ev_soc_data_dict = {}

# 將 EV 初始資料從 DataFrame 中讀取
for _, ev_row in ev_data_df.iterrows():

    # 直接使用 to_datetime 將 Timestamp 轉換為 datetime 對象
    start_charge_time = pd.to_datetime(ev_row['開始充電時間'])
    end_charge_time = pd.to_datetime(ev_row['結束充電時間'])
    # 將秒數部分設置為特定值
    start_charge_time = start_charge_time.replace(second=0)
    end_charge_time = end_charge_time.replace(second=0)    

    # 使用轉換後的時間數據創建 EV 對象
    ev = EV(
        ev_row['卡片名稱'],
        ev_row['SoC(結束)']/100,
        ev_row['SoC(開始)']/100,
        100,
        start_charge_time,
        end_charge_time
    )
    # print(f"start_charge_time: {start_charge_time}  /  end_charge_time: {end_charge_time}")
    ev_waiting_list.append(ev)
    evcs.add_to_ev_waiting_list(ev)
    # 添加 EV 對象的 SOC 數據到字典中
    if ev.number not in ev_soc_data_dict:
        ev_soc_data_dict[ev.number] = []
        ev_soc_data_dict[ev.number].append(0)

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
pile_total = 0

for pile in charging_pile_status:
    pile_number = pile['pile_number']
    charging_power_data[f"{pile_number}-1"] = []
    charging_power_data[f"{pile_number}-1-EV"] = []
    charging_power_data[f"{pile_number}-1-EV-SOC"] = []
    charging_power_data[f"{pile_number}-2"] = []
    charging_power_data[f"{pile_number}-2-EV"] = []
    charging_power_data[f"{pile_number}-2-EV-SOC"] = []

# time = datetime(2024, 1, 29, 7, 0)
# end_time = datetime(2024, 2, 5, 7, 0)   # datetime(2024, 2, 5, 10, 0)
    
# time = datetime(2023, 5, 9, 5, 35, 0)
# end_time = datetime(2023, 5, 10, 5, 35) 
time = datetime(2023, 5, 9, 4, 00, 0)
end_time = datetime(2023, 5, 15, 16, 0, 0) 

ev_to_add = []
# print(f"ev_soc_data_dict: {ev_soc_data_dict}")

while time < end_time:   
    # print(f"Time {time}")
    tou.current_time = time
    index = 0
    while index < len(evcs.ev_waiting_list):
        ev = evcs.ev_waiting_list[index]
        if ev.charge_start_time <= time:
            evcs.add_ev1(ev)
            evcs.delete_from_ev_waiting_list(ev)
            # 重設迴圈的索引，讓它從頭開始
            index = 0
        else:
            # 如果條件不成立，則遞增索引以檢查下一個 EV
            index += 1

    evcs.charging_method1(time)
    # print(f"ev_charge_start_time: {ev.charge_start_time}  /  ev_charge_end_time: {ev.charge_end_time}")
    charging_evs = []
    for idx, charging_pile in enumerate(charging_pile_status):
        gun_1_power = charging_pile["gun"][0]["charging_power"]
        gun_2_power = charging_pile["gun"][1]["charging_power"]
        ev_1_number = charging_pile["gun"][0]["ev_number"]
        ev_2_number = charging_pile["gun"][1]["ev_number"]
        ev_1_soc = evcs.find_ev_by_number(ev_1_number).now_SOC if ev_1_number != 0 else 0
        ev_2_soc = evcs.find_ev_by_number(ev_2_number).now_SOC if ev_2_number != 0 else 0
        gun_1_soc = charging_pile["gun"][0]["charging_soc"]

        pile_number = charging_pile["pile_number"]
        charging_power_data[f"{pile_number}-1-EV"].append(ev_1_number)
        charging_power_data[f"{pile_number}-1"].append(gun_1_power)
        charging_power_data[f"{pile_number}-1-EV-SOC"].append(ev_1_soc)
        charging_power_data[f"{pile_number}-2-EV"].append(ev_2_number)
        charging_power_data[f"{pile_number}-2"].append(gun_2_power)
        charging_power_data[f"{pile_number}-2-EV-SOC"].append(ev_2_soc)

        if ev_1_number != 0:
            charging_evs.append(ev_1_number)
            # ev_1_soc = evcs.find_ev_by_number(ev_1_number).now_SOC
            ev_soc_data_dict[ev_1_number].append(ev_1_soc)
        if ev_2_number != 0:
            charging_evs.append(ev_2_number)
            # ev_2_soc = evcs.find_ev_by_number(ev_2_number).now_SOC
            ev_soc_data_dict[ev_2_number].append(ev_2_soc)

    for ev in ev_soc_data_dict:
        if ev not in charging_evs:
            ev_soc_data_dict[ev].append(ev_soc_data_dict[ev][-1])

    ev_soc_summary, ev_power_summary = evcs.get_ev_summary()
    # print(f"EV SOC Summary: {ev_soc_summary}  /  EV Power Summary: {ev_power_summary}")
    pile_summary, pile_total_power = evcs.get_pile_summary()
    # print(f"Pile Summary: {pile_summary}  /  Pile Total Power: {pile_total_power}")
    
    time_list.append(time)
    piles_total_power.append(pile_total_power)
    
    pile_total += pile_total_power
    
    # print("\n")
    print("pile_total_power: ", pile_total)
    # print("\n")

    time += timedelta(seconds=time_cycle)

# 跑第二遍=============================================================================
# # 將 EV 初始資料從 DataFrame 中讀取
# for _, ev_row in ev_data_df.iterrows():

#     # 直接使用 to_datetime 將 Timestamp 轉換為 datetime 對象
#     start_charge_time = pd.to_datetime(ev_row['開始充電時間'])
#     end_charge_time = pd.to_datetime(ev_row['結束充電時間'])
#     # 將秒數部分設置為特定值
#     start_charge_time = start_charge_time.replace(second=0)
#     end_charge_time = end_charge_time.replace(second=0)    

#     # 使用轉換後的時間數據創建 EV 對象
#     ev = EV(
#         ev_row['卡片名稱'],
#         ev_row['SoC(結束)']/100,
#         ev_row['SoC(開始)']/100,
#         100,
#         start_charge_time,
#         end_charge_time
#     )
#     # print(f"start_charge_time: {start_charge_time}  /  end_charge_time: {end_charge_time}")
#     ev_waiting_list.append(ev)
#     evcs.add_to_ev_waiting_list(ev)
#     # 添加 EV 對象的 SOC 數據到字典中
#     ev_soc_data_dict[ev.number] = []

# # =============================================================================
# # 提取充電樁狀態
# charging_pile_status = evcs.charging_piles

# # 建立一個字典來存儲每小時每個充電樁的充電功率
# charging_power_data = {}

# time_list = []
# piles_total_power1 = []
# ess_charge_discharge = []
# ess_soc = []
# grid = []
# pile_total1 = 0

# for pile in charging_pile_status:
#     pile_number = pile['pile_number']
#     charging_power_data[f"{pile_number}-1"] = []
#     charging_power_data[f"{pile_number}-1-EV"] = []
#     charging_power_data[f"{pile_number}-1-EV-SOC"] = []
#     charging_power_data[f"{pile_number}-2"] = []
#     charging_power_data[f"{pile_number}-2-EV"] = []
#     charging_power_data[f"{pile_number}-2-EV-SOC"] = []

# # time = datetime(2024, 1, 29, 7, 0)
# # end_time = datetime(2024, 2, 5, 7, 0)   # datetime(2024, 2, 5, 10, 0)
    
# # time = datetime(2023, 5, 9, 5, 35, 0)
# # end_time = datetime(2023, 5, 10, 5, 35) 
# time = datetime(2023, 5, 9, 4, 00, 0)
# end_time = datetime(2023, 5, 15, 16, 0, 0) 

# ev_to_add = []

# while time < end_time:   
#     # print(f"Time {time}")
#     tou.current_time = time
#     index = 0
#     while index < len(evcs.ev_waiting_list):
#         ev = evcs.ev_waiting_list[index]
#         if ev.charge_start_time <= time:
#             evcs.add_ev1(ev)
#             evcs.delete_from_ev_waiting_list(ev)
#             # 重設迴圈的索引，讓它從頭開始
#             index = 0
#         else:
#             # 如果條件不成立，則遞增索引以檢查下一個 EV
#             index += 1

#     evcs.charging_method1(time)
#     # print(f"ev_charge_start_time: {ev.charge_start_time}  /  ev_charge_end_time: {ev.charge_end_time}")

#     for idx, charging_pile in enumerate(charging_pile_status):
#         gun_1_power = charging_pile["gun"][0]["charging_power"]
#         gun_2_power = charging_pile["gun"][1]["charging_power"]
#         ev_1_number = charging_pile["gun"][0]["ev_number"]
#         ev_2_number = charging_pile["gun"][1]["ev_number"]
#         ev_1_soc = evcs.find_ev_by_number(ev_1_number).now_SOC if ev_1_number != 0 else 0
#         ev_2_soc = evcs.find_ev_by_number(ev_2_number).now_SOC if ev_2_number != 0 else 0
#         gun_1_soc = charging_pile["gun"][0]["charging_soc"]

#         pile_number = charging_pile["pile_number"]
#         charging_power_data[f"{pile_number}-1"].append(gun_1_power)
#         charging_power_data[f"{pile_number}-1-EV"].append(ev_1_number)
#         charging_power_data[f"{pile_number}-1-EV-SOC"].append(ev_1_soc)
#         charging_power_data[f"{pile_number}-2"].append(gun_2_power)
#         charging_power_data[f"{pile_number}-2-EV"].append(ev_2_number)
#         charging_power_data[f"{pile_number}-2-EV-SOC"].append(ev_2_soc)

#         # if ev_1_number == 'EAA-780':
#         #     print(f"Time: {time}  /  EV1: {ev_1_number}  /  EV1 SOC: {ev_1_soc}  /  Charging SOC: {gun_1_soc}")

#     ev_soc_summary, ev_power_summary = evcs.get_ev_summary()
#     # print(f"EV SOC Summary: {ev_soc_summary}  /  EV Power Summary: {ev_power_summary}")
#     pile_summary, pile_total_power = evcs.get_pile_summary()
#     # print(f"Pile Summary: {pile_summary}  /  Pile Total Power: {pile_total_power}")
    
#     time_list.append(time)
#     piles_total_power1.append(pile_total_power)
    
#     pile_total1 += pile_total_power
    
#     # print("\n")
#     # print("pile_total_power: ", pile_total1)
#     # print("\n")

#     time += timedelta(seconds=time_cycle)

# 繪製圖表=====================================================================
days = 2
x_ticks_positions = np.arange(0, 24 * days, 1)
x_ticks_labels = [(hr) % 24 for hr in range(24 * days)]

# 將時間步數轉換為小時
hours = np.arange(0, len(time_list), 1)


# 創建一個 subplot
"""
fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                    subplot_titles=['EV Charging Power Over a Day', 'EV SOC Over a Day'],
                    row_heights=[1,0]) # 設定子圖的高度比例
"""

fig = make_subplots(rows=2, cols=1)

# 添加充電功率折線圖
# for idx, (pile, powers) in enumerate(charging_power_data.items()):
#     fig.add_trace(go.Scatter(x=time_list, y=powers, mode='lines', name=pile, legendgroup=f"group{idx}"), row=1, col=1)

# 添加充電樁總功率折線圖
fig.add_trace(go.Scatter(x=time_list, y=piles_total_power, mode='lines', name='未導入功率控制', legendgroup=f"group{11}"), row=1, col=1)
# fig.add_trace(go.Scatter(x=time_list, y=piles_total_power1, mode='lines', name='導入功率控制', legendgroup=f"group{12}"), row=1, col=1)

# 添加 SOC 折線圖
for ev_number, soc_data in ev_soc_data_dict.items():
    fig.add_trace(go.Scatter(x=time_list, y=soc_data, mode='lines', name=f'{ev_number} SOC', xaxis='x2'), row=2, col=1)

# 設定布局
fig.update_layout(title_text='EV Charging and SOC Over a Day',
                    xaxis_title='Time Steps (Hour)',
                    yaxis_title='Power (W)',
                    xaxis2_title='Time Steps (Hour)',
                    yaxis2_title='SOC',
                    showlegend=True,  # 顯示圖例
                    # xaxis=dict(type='category', tickmode='array', tickvals=time_list, ticktext=[t.strftime("%Y-%m-%d %H:%M") for t in time_list]),
                    barmode='group',  # stack：將柱狀圖疊加顯示；group：將柱狀圖並排顯示；overlay：將柱狀圖重疊顯示，並將透明度設為0.5
                    bargap=0.2)  # 控制柱狀圖之間的間距
fig.update_xaxes(tickvals=time_list,tickmode='auto')



# 顯示圖表
fig.show()

# =============================================================================
# 將數據保存到Excel文件
# 將充電功率和SOC數據轉換為pandas DataFrame
# charging_power_df = pd.DataFrame(charging_power_data)
# pile_total_power_df = pd.DataFrame({'Pile Total Power': piles_total_power})
# illustrate_df = pd.DataFrame({'說明': evcs.excel_instructions})
# # ev_list_df = pd.DataFrame({'EV List': [(ev.number, ev.charge_start_time) for ev in ev_waiting_list]})

# # 將時間信息添加到 DataFrame 的第一行
# charging_power_df.insert(0, 'Time', time_list)
# pile_total_power_df.insert(0, 'Time', time_list)

# # 添加描述性的標題行
# pile_total_power_df.columns = ['Time', 'Pile Total Power']

# # 獲取腳本所在目錄的絕對路徑
# script_directory = os.path.dirname(os.path.abspath(__file__))

# # 獲取當前日期和時間
# current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")

# # 構建Excel文件的完整路徑，以日期和時間命名
# excel_file_path = os.path.join(script_directory, "pile_output_result_data\\test", f"pile_data_{current_datetime}.xlsx")

# # 如果 "pile_output_result_data" 資料夾不存在，則創建它
# output_folder = os.path.join(script_directory, "pile_output_result_data")
# os.makedirs(output_folder, exist_ok=True)

# # 將數據保存到Excel文件
# with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:
#     illustrate_df.to_excel(writer, sheet_name='說明', index=False)
#     pile_total_power_df.to_excel(writer, sheet_name='Pile total Power', index=False)
#     charging_power_df.to_excel(writer, sheet_name='Charging Power', index=False)
#     # ev_list_df.to_excel(writer, sheet_name='EV List', index=False)
#     # ev_soc_df.to_excel(writer, sheet_name='EV SOC', index=False)

# print("Excel檔案已成功生成：charging_data.xlsx")
