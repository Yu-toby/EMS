from datetime import datetime, timedelta
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import math
from collections import Counter

kWh = 1000  # 1kWh = 1000度電
time_cycle = 3600/60  # 1小時秒數 / 多久一筆資料的秒數(1小時一筆：3600 ；1分鐘一筆；60)

# 一般判斷副程式===============================================================
def if_Spinning_Reserve(time):
    if datetime(2023, 5, 8, 3, 0, 0) <= time < datetime(2023, 5, 8, 4, 0, 0):   # 這裡的datetime要改成投標後的輔助服務時間
    # if datetime(2023, 5, 15, 13, 0, 0) <= time < datetime(2023, 5, 15, 14, 0, 0):
        return True
    else:
        return False

def if_Start_Charge(time, evcs, Spinning_Reserve):
    pile_still_vacancies = {'state': True}
    # if not Spinning_Reserve:
    if True:
        index = 0
        while index < len(evcs.ev_waiting_list):
            ev = evcs.ev_waiting_list[index]
            if ev.charge_start_time <= time:
                pile_still_vacancies = evcs.add_ev1(ev)
                # print(f"{time} - {ev.number} - {pile_still_vacancies}")
                # evcs.add_ev1(ev)
                if pile_still_vacancies['state']:
                # 充電樁有空位可充電，刪除等待的 EV
                    evcs.delete_from_ev_waiting_list(ev)
                    # 重設迴圈的索引，讓它從頭開始
                    index = 0
                else:
                    if pile_still_vacancies['type'] == 0:
                    # 充電樁沒空位可充電
                        evcs.add_to_ev_overtime_waiting_list(ev)
                        # print(f"{time} - {ev.number} - {pile_still_vacancies['illustrate']}")
                    elif pile_still_vacancies['type'] == 1:
                    # 資料有誤，該車編號已存在
                        print(f"{time} - {ev.number} - {pile_still_vacancies['illustrate']}")

                    index += 1

            else:
                # 如果條件不成立，則遞增索引以檢查下一個 EV
                index += 1
    #     return pile_still_vacancies
    return pile_still_vacancies
    
    # else:
    #     print(f"{time} - Spinning_Reserve: {Spinning_Reserve}")

# 去除包含"秒"以後的單位=======================================================
def truncate_seconds(dt):
    return datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute)

# 充電樁=======================================================================
class EVCS:
    def __init__(self):
        self.pile_power_limit = 100 * 1000
        self.connected_evs = []
        self.ev_waiting_list = []
        self.ev_overtime_waiting_list = []
        piles_amount = 5
        self.charging_piles = []
        self.original_pile_power_data = []   # 紀錄沒有任何更動下的充電樁功率
        self.gun1_empty = True
        self.gun2_empty = True
        self.check_ev_number1 = False
        self.check_ev_number2 = False

        # ------------------------------------------------------
        self.set_time = False
        self.waiting_start_charge_time = 0
        self.field_end_charge_time = 0

        self.half_power_start_charge_time = 0
        self.full_power_start_charge_time = 0

        self.half_power_end_charge_time = 0
        self.full_power_end_charge_time = 0
        self.update_ev_amount = 0
        self.ev_waiting_length = 0
        self.pile_more_then_bus = False
        self.end_charge_time_range = 0     # 結束充電時間範圍

        self.SR_charge_power1 = 0
        self.SR_charge_power2 = 0

        self.customize_power_end_charge_time = 0
        self.pile_power = {}
        self.gun_power = {}

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
                    "already_time": 0,
                    "check_charging": False
                }
                charging_pile["gun"].append(gun_info)

            self.charging_piles.append(charging_pile)

        for group in range(1, piles_amount + 1):
            charging_pile = {
                "pile_number": str(group),
                "gun": []
            }

            for sub_group in range(1, 3):  # 這裡使用 1 和 2 作為子組的標識
                gun_info = {
                    "gun_number": f"{group}-{sub_group}",
                    "charging_power": 0,
                }
                charging_pile["gun"].append(gun_info)

            self.original_pile_power_data.append(charging_pile)

# 增減等待的車輛===============================================================
    def add_to_ev_waiting_list(self, ev):
        self.ev_waiting_list.append(ev)
    
    def delete_from_ev_waiting_list(self, ev):
        self.ev_waiting_list.remove(ev)

# 增減等待(超時還沒充電)的車輛========================================================= 
    def add_to_ev_overtime_waiting_list(self, ev):
        self.ev_overtime_waiting_list.append(ev)

    def delete_from_ev_overtime_waiting_list(self, ev):
        self.ev_overtime_waiting_list.remove(ev)

# 找空位充電===================================================================

    # 先找兩隻槍都沒有在用的樁，若沒有才共用槍
    def add_ev1(self, ev):
        self.excel_instructions[0] = '先找兩隻槍都沒有在用的樁，若沒有才共用槍'
        # 先找有沒有空的樁
        if ev.gun_number == None:
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
                    return  {'state': False, 'type': 1, 'illustrate': "資料有誤，該車編號已存在"}  # 結束函式，已找到重複的 EV 資料
                
            # print(f"{ev.charge_start_time} / {ev.number}找不到可用的充電槍，請檢查充電樁狀態")
        else:
            for charging_pile in self.charging_piles:
                guns = charging_pile.get('gun', [])

                # 逐一檢查每個 gun 的 gun_number
                for gun in guns:
                    if (ev.gun_number == gun['gun_number']) and (gun['ev_number'] == 0):
                        gun['ev_number'] = ev.number
                        gun['charging_power'] = 0
                        gun['charging_soc'] = 0
                        gun['start_time'] = ev.charge_start_time
                        gun['end_time'] = ev.charge_end_time
                        gun['check_charging'] = False
                        ev.gun_number = gun['gun_number']
                        self.connected_evs.append(ev)
                        return {'state': True}
        return  {'state': False, 'type': 0, 'illustrate': "找不到可用的充電槍，請檢查充電樁狀態"}  

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
    
    def get_pile_power(self):
        # 取得充電樁充電當下功率
        summary_power = {}
        for pile in self.charging_piles:
            pile_number = pile['pile_number']
            guns = pile.get('gun', [])
            gun1, gun2 = guns[0], guns[1]
            summary_power[pile_number] = gun1['charging_power'] + gun2['charging_power']
        return summary_power
    
    def get_gun_power(self):
        # 取得充電槍充電當下功率
        summary = []
        for pile in self.charging_piles:
            pile_summary = {
                'pile_number': pile['pile_number'],  # 假設每個pile字典中都有'pile_number'鍵
                'gun': []
            }
            guns = pile.get('gun', [])
            for gun in guns:
                gun_info = {
                    'gun_number': gun['gun_number'],
                    'ev_number': gun['ev_number'],
                    'charging_power': gun['charging_power']
                }
                pile_summary['gun'].append(gun_info)
            summary.append(pile_summary)
        return summary

    def charge_time(self, start_soc, target_soc, battery_max_capacity, charge_power):
        # 計算充電時間
        minute = (target_soc - start_soc) * battery_max_capacity / charge_power
        charge_time = timedelta(minutes=minute)
        # print(f"charge_time: {charge_time}")
        return charge_time

    def get_corresponding_power(self, pile_summary, gun_number):
        # 將 gun_number 的格式拆分成樁組編號和樁號
        group, number = gun_number.split('-')
        
        # 根據樁號選擇對應的另一個樁號
        if number == '1':
            corresponding_number = group + '-2'
        else:
            corresponding_number = group + '-1'
        
        # 從字典中獲取對應樁號的功率
        corresponding_power = pile_summary[corresponding_number]
        return corresponding_power

    # 紀錄充電功率沒有因任何條件更動時(計算出來是什麼就是什麼)，最原始的充電樁總功率
    def original_pile_power(self, gun_number, ev_power):
        for pile in self.original_pile_power_data:
            guns = pile.get('gun', [])
            for gun in guns:
                if gun['gun_number'] == gun_number:
                    gun['charging_power'] = ev_power
        # print(f"original_pile_power_data: {self.original_pile_power_data}")
        # 計算充電樁總功率
        total_power = sum([sum([gun['charging_power'] for gun in pile['gun']]) for pile in self.original_pile_power_data])
        return total_power

    # 車多樁少、依照離開時間調配充電功率、較少換車次數
    def charging_method5(self, time_step, Spinning_Reserve, average_latest_five_pile_total_power, if_pile_still_vacancies):
        # print(f"if_pile_still_vacancies: {if_pile_still_vacancies}")
        if not if_pile_still_vacancies:
            # 更改場域內車輛結束充電時間================================================================
            # print(f"{time_step} - charging - {if_pile_still_vacancies}")
            # --------------------------------------------------------------------------------------------
            overtime_waiting_ev_amount = 0  # 超時車輛數
            # 找出等待區內充電時間已到，但因為沒空槍而無法充電的車輛中，若用最大功率充電，最晚要開始充電的時間
            for ev in self.ev_waiting_list:
                if ev.charge_start_time <= time_step:
                    # print(f"time1: {time_step}")
                    overtime_waiting_ev_amount += 1
                    if self.update_ev_amount < overtime_waiting_ev_amount:
                        self.pile_more_then_bus = True
                        self.update_ev_amount = overtime_waiting_ev_amount
                        if self.update_ev_amount == 1:  # 找出換車前的場內數據
                            self.pile_power = self.get_pile_power()
                            self.gun_power = self.get_gun_power()
                        sorted_pile_power = sorted(self.pile_power.items(), key=lambda item: item[1])   # 依照充電樁功率小到大排序
                        keys_string = ', '.join(key for key, _ in sorted_pile_power)
                        pile_key_number = keys_string.split(', ')[(overtime_waiting_ev_amount-1)%5] # 找出充電樁功率第X小的充電樁編號，X為等待區第幾個進入的車輛
                        guns = self.gun_power[int(pile_key_number)-1].get('gun', [])   # 取出該充電樁中的兩槍
                        sorted_guns = sorted(guns, key=lambda x: x['charging_power'])   # 依照充電槍功率小到大排序
                        gun_key_number = sorted_guns[int((overtime_waiting_ev_amount-1)/5)]['gun_number']    # 找出充電槍功率第1or2小的充電槍編號，前五輛車分配給第一小的充電槍，第六到十輛車分配給第二小的充電槍
                        ev.gun_number = gun_key_number
                        for file in self.connected_evs:
                            if file.number == sorted_guns[int((overtime_waiting_ev_amount-1)/5)]['ev_number']:
                                if file.charge_end_time >= ev.charge_end_time:
                                    file.charge_end_time = truncate_seconds(ev.charge_end_time)
                                file_ev_charging_power = file.calculate_charge_power(time_step, Spinning_Reserve)[0]
                                waiting_ev_charging_power = ev.calculate_charge_power(time_step, Spinning_Reserve)[0]
                                self.customize_power_end_charge_time = time_step + self.charge_time(file.now_SOC, file.target_SOC, file.battery_max_capacity, (file_ev_charging_power + waiting_ev_charging_power))
                                file.charge_end_time = truncate_seconds(self.customize_power_end_charge_time)

                            for file1 in self.connected_evs:
                                if truncate_seconds(file.charge_end_time) <= truncate_seconds(file1.charge_end_time) <= truncate_seconds(file.charge_end_time + timedelta(minutes=self.end_charge_time_range)):
                                    file1_original_end_time = truncate_seconds(file1.charge_end_time)
                                    file1.charge_end_time = truncate_seconds(file.charge_end_time)

                                    file1_ev_charging_power = file1.calculate_charge_power(time_step, Spinning_Reserve)[0]
                                    another_gun_power = self.get_corresponding_power(self.get_pile_summary()[0], file1.gun_number)
                                    if (file1_ev_charging_power + another_gun_power) > self.pile_power_limit:
                                        file1.charge_end_time = truncate_seconds(file1_original_end_time)

        if self.pile_more_then_bus and (len(self.ev_waiting_list) != self.ev_waiting_length):
                        self.ev_waiting_length = len(self.ev_waiting_list)
                        # print(f"time: {time_step}")
                        # print(f"connected_evs_end_time: [{[(ev.number, ev.charge_end_time) for ev in self.connected_evs]}]")
                        for file in self.connected_evs:
                            for file1 in self.connected_evs:
                                for wetting_ev in self.ev_waiting_list:
                                    if file1.gun_number == wetting_ev.gun_number:

                                        if truncate_seconds(file.charge_end_time) <= truncate_seconds(file1.charge_end_time) <= truncate_seconds(file.charge_end_time + timedelta(minutes=self.end_charge_time_range)):
                                            file1_original_end_time = truncate_seconds(file1.charge_end_time)
                                            file1.charge_end_time = truncate_seconds(file.charge_end_time)

                                            file1_ev_charging_power = file1.calculate_charge_power(time_step, Spinning_Reserve)[0]
                                            another_gun_power = self.get_corresponding_power(self.get_pile_summary()[0], file1.gun_number)
                                            if (file1_ev_charging_power + another_gun_power) > self.pile_power_limit:
                                                file1.charge_end_time = truncate_seconds(file1_original_end_time)
                                        
        
        self.calculate_gun_charge_power(time_step, Spinning_Reserve, average_latest_five_pile_total_power)

    def calculate_gun_charge_power(self, time_step, Spinning_Reserve, average_latest_five_pile_total_power):
        # self.set_time = False
        self.excel_instructions[1] = '依比例分配功率充電'
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
                    if (ev1.now_SOC >= ev1.target_SOC) or (gun1['check_charging'] and truncate_seconds(ev1.charge_end_time) <= time_step):
                        # 充完電就離開
                        # print(f"ev1: {ev1.number} depart")
                        self.delete_ev(ev1)
                        self.check_ev_number1 = False
                        charge_power1, charge_soc1 = 0, 0
                        self.gun1_empty = True

                    else:
                        gun1['check_charging'] = True
                        self.check_ev_number1 = True
                        charge_power1, charge_soc1 = ev1.calculate_charge_power(time_step, Spinning_Reserve)
                        original_total_pile_power = self.original_pile_power(ev1.gun_number, charge_power1)
                        # print(f"original_total_pile_power: {original_total_pile_power}")
                        # 依據當下是否為即時備轉服務時間，計算充電功率。若為即時備轉服務時間，則充電功率會乘上[(充電樁前五分鐘總功率平均 - 100k) / 服務時間內充電樁最大總功率]。(100k 為投標量)                            
                        charge_power1 = min(charge_power1, self.pile_power_limit) if not Spinning_Reserve else (min(charge_power1, self.pile_power_limit)) * ((average_latest_five_pile_total_power - 100000) / (original_total_pile_power))
                        ev1.charge_power = charge_power1
                        # charge_soc1 = charge_power1 / ev1.battery_max_capacity

            else:
                self.gun1_empty = True

            if ev_number2 != 0:
                self.gun2_empty = False
                ev2 = self.find_ev_by_number(ev_number2)
                if ev2:
                    if (ev2.now_SOC >= ev2.target_SOC) or (gun2['check_charging'] and truncate_seconds(ev2.charge_end_time) <= time_step):
                        # 充完電就離開
                        self.delete_ev(ev2)
                        self.check_ev_number2 = False
                        charge_power2, charge_soc2 = 0, 0
                        self.gun2_empty = True

                    else:
                            gun2['check_charging'] = True
                            self.check_ev_number2 = True
                            charge_power2, charge_soc2 = ev2.calculate_charge_power(time_step, Spinning_Reserve)
                            original_total_pile_power = self.original_pile_power(ev2.gun_number, charge_power2)
                            # 依據當下是否為即時備轉服務時間，計算充電功率。若為即時備轉服務時間，則充電功率會乘上[(充電樁總功率 - 100k) / 充電樁總功率]。(100k 為投標量)
                            charge_power2 = min(charge_power2, self.pile_power_limit) if not Spinning_Reserve else (min(charge_power2, self.pile_power_limit)) * ((average_latest_five_pile_total_power - 100000) / (original_total_pile_power))
                            ev2.charge_power = charge_power2
                            # charge_soc2 = charge_power2 / ev2.battery_max_capacity

            else:
                self.gun2_empty = True

            if self.check_ev_number1 or self.check_ev_number2:
                # print(f"gun1_number: {ev_number1_gun} / gun2_number: {ev_number2_gun}")
                # 依照離開時間調配充電功率
                self.if_over_pile_power_limit2(ev_number1, ev_number2, gun1, gun2, Spinning_Reserve, average_latest_five_pile_total_power, time_step)
        
        return self.charging_piles
    
    def if_over_pile_power_limit2(self, ev_number1, ev_number2, gun1, gun2, Spinning_Reserve, average_latest_five_pile_total_power, current_time):
        # 從EV端取得兩槍的充電功率、充電SOC及對應的充電樁編號=======================================
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

        if (charge_power1 + charge_power2) > self.pile_power_limit:
            if ev1.charge_end_time < ev2.charge_end_time:
                # 如果槍1的充電結束時間比較早，則槍1的充電功率不變，槍2的充電功率為充電樁功率上限減去槍1的充電功率
                ev1.now_power += min(charge_power1, (self.pile_power_limit-1))
                ev1.now_SOC = ev1.now_power / ev1.battery_max_capacity
                gun1['charging_power'] = (charge_power1)
                gun1['charging_soc'] = charge_soc1

                charge_power2 = self.pile_power_limit - charge_power1
                charge_soc2 = charge_power2 / ev2.battery_max_capacity
                ev2.now_power += charge_power2
                ev2.now_SOC = ev2.now_power / ev2.battery_max_capacity
                gun2['charging_power'] = (charge_power2)
                gun2['charging_soc'] = charge_soc2

            elif ev1.charge_end_time > ev2.charge_end_time:
                # 如果槍2的充電結束時間比較早，則槍2的充電功率不變，槍1的充電功率為充電樁功率上限減去槍2的充電功率
                ev2.now_power += min(charge_power2, (self.pile_power_limit-1))
                ev2.now_SOC = ev2.now_power / ev2.battery_max_capacity
                gun2['charging_power'] = (charge_power2)
                gun2['charging_soc'] = charge_soc2

                charge_power1 = self.pile_power_limit - charge_power2
                charge_soc1 = charge_power1 / ev1.battery_max_capacity
                ev1.now_power += charge_power1
                ev1.now_SOC = ev1.now_power / ev1.battery_max_capacity
                gun1['charging_power'] = (charge_power1)
                gun1['charging_soc'] = charge_soc1

            else:
                # 如果兩槍的充電結束時間一樣，且用當前功率充電可能不會在結束時達到目標SOC
                remaining_available_SOC = (((ev1.charge_end_time - current_time).total_seconds() / 3600) * 100 * 1000 * time_cycle) / ev1.battery_max_capacity
                new_target_SOC = (ev1.now_SOC + ev2.now_SOC + remaining_available_SOC) / 2

                ev1.target_SOC = new_target_SOC
                ev2.target_SOC = new_target_SOC
                charge_power1, charge_soc1 = ev1.calculate_charge_power(current_time, Spinning_Reserve) 
                charge_power2, charge_soc2 = ev2.calculate_charge_power(current_time, Spinning_Reserve)

                if (charge_power1 + charge_power2) > self.pile_power_limit:
                    new_charge_power1 = charge_power1 / ((charge_power1 + charge_power2) / self.pile_power_limit)
                    new_charge_power2 = charge_power2 / ((charge_power1 + charge_power2) / self.pile_power_limit)
                    charge_power1 = new_charge_power1
                    charge_power2 = new_charge_power2
                    charge_soc1 = new_charge_power1 / ev1.battery_max_capacity
                    charge_soc2 = new_charge_power2 / ev2.battery_max_capacity

                ev1.now_power += charge_power1
                ev1.now_SOC = ev1.now_power / ev1.battery_max_capacity
                gun1['charging_power'] = (charge_power1)
                gun1['charging_soc'] = charge_soc1

                ev2.now_power += charge_power2
                ev2.now_SOC = ev2.now_power / ev2.battery_max_capacity
                gun2['charging_power'] = (charge_power2)
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
                gun1['charging_soc'] = charge_soc1
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
                gun2['charging_soc'] = charge_soc2
            else:
                gun2['charging_power'] = 0
                gun2['charging_soc'] = 0

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
        self.spinning_reserve_charge_power = 0
        
        self.power_limit = power_limit
        self.charge_pi = 0  # 倍分配充電係數

        self.charging_ramp_rate = 0.07  # 充電功率上升、下降變動率

        self.count = 0

        # --------------------------------------
        self.total_energy = self.battery_max_capacity * (self.target_SOC - self.now_SOC)
        self.total_time = int((self.charge_end_time - (self.charge_start_time - timedelta(minutes=1))).total_seconds() / time_cycle)
        self.T_ramp_max = int(self.total_time - (self.total_energy / 100000))
        self.T_ramp = min((math.ceil(1 / self.charging_ramp_rate)), self.T_ramp_max, self.total_time // 4)  # 確保上升和下降階段總和不超過總時間的一半，且平穩階段功率不超過100kW
        self.T_stable = self.total_time - 2 * self.T_ramp
        self.ramp_multiplier = (self.total_time / (self.total_time - self.T_ramp)) / self.T_ramp
        self.stable_multiplier = (self.total_time / (self.total_time - self.T_ramp))
        self.last_charging_power = 0

    def calculate_charge_power(self, current_time, Spinning_Reserve):
        self.count += 1
        
        # 計算每小時所需充電功率
        if self.charge_start_time <= current_time < self.charge_end_time:
            # 每小時/每分鐘 充多少SOC，看time_cycle決定
            # charge_soc = (((self.target_SOC - self.now_SOC)) / ((self.charge_end_time - current_time).total_seconds() / 3600)) / time_cycle
            try :
                charge_soc = ((self.target_SOC - self.now_SOC)) / int((self.charge_end_time - current_time).total_seconds() / time_cycle)
            except ZeroDivisionError:
                charge_soc = 0
            # 每個時刻充電功率(W)
            charge_power = charge_soc * self.battery_max_capacity
        else:
            charge_power = 0
            charge_soc = 0

        if not Spinning_Reserve:    # 非即時備轉服務時間，充電功率會一直計算
            self.spinning_reserve_charge_power = charge_power
            return charge_power, charge_soc # 回傳 充電功率(W)、充多少SOC
        else:   # 即時備轉服務時間，充電功率會直接以最後一筆計算值輸出
            if self.count == 2:
                self.spinning_reserve_charge_power = charge_power
            return self.spinning_reserve_charge_power, charge_soc # 回傳 充電功率(W)、充多少SOC
        

# 初始資料建構=======================================================================
evcs = EVCS()

# Excel 讀取 EV 初始資料=======================================================
excel_file_path = r"C:\Users\WYC\Desktop\電動大巴\EMS\EMS\資料生成\生成數據\generated_data.xlsx"  
# excel_file_path = r"C:\Users\WYC\Desktop\電動大巴\EMS\EMS\資料生成\生成數據\generated_data.xlsx"  
# ev_data_df = pd.read_excel(excel_file_path, sheet_name='Sheet1')
ev_data_df = pd.read_excel(excel_file_path, sheet_name='Sheet4')

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
    start_charge_time = start_charge_time.replace(second=0, microsecond=0)
    end_charge_time = end_charge_time.replace(second=0, microsecond=0)    

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

# 提取充電樁狀態=============================================================================
charging_pile_status = evcs.charging_piles

# 建立一個字典來存儲每小時每個充電樁的充電功率
charging_power_data = {}
each_pile_power = {}

Draw_time_list = []
Export_file_time_list = []
piles_total_power = []
ess_charge_discharge = []
ess_soc = []
grid = []
pile_total = 0

for pile in charging_pile_status:
    pile_number = pile['pile_number']
    charging_power_data[f"{pile_number}-1-EV"] = []
    charging_power_data[f"{pile_number}-1-P"] = []
    charging_power_data[f"{pile_number}-1-SOC"] = []
    # charging_power_data[f"{pile_number}-1-pile-SOC"] = []
    charging_power_data[f"{pile_number}-2-EV"] = []
    charging_power_data[f"{pile_number}-2-P"] = []
    charging_power_data[f"{pile_number}-2-SOC"] = []

for pile in charging_pile_status:
    pile_number = pile['pile_number']
    each_pile_power[pile_number] = []
each_pile_power['piles_total_power'] = []

# 主程式=============================================================================

Draw = False
# Draw = True
Export_file = False
# Export_file = True

time = datetime(2023, 5, 5, 8, 30, 0)
# end_time = datetime(2023, 5, 12, 5, 35) 
end_time = datetime(2023, 5, 6, 6, 00) 
# end_time = datetime(2023, 5, 5, 15, 00) 

# time = datetime(2023, 5, 9, 4, 0, 0)
# end_time = datetime(2023, 5, 15, 16, 0, 0) 

Spinning_Reserve = False    # 是否為即時備轉服務時間
pile_total_power = 0
latest_five_pile_total_power = []

while time < end_time:   
    # print(f"Time {time}")

    # 判斷是否為即時備轉服務時間
    Spinning_Reserve = if_Spinning_Reserve(time)
    # print(f"Spinning_Reserve: {Spinning_Reserve}")
    if not Spinning_Reserve:
        # 更新 pile_total_power_rate，確保只保留最新的五筆資料
        if len(latest_five_pile_total_power) >= 5:
            # 如果列表已有五個元素，移除最舊的元素
            latest_five_pile_total_power.pop(0)
        # 加入最新的 pile_total_power
        latest_five_pile_total_power.append(pile_total_power)
        average_last_five_power = sum(latest_five_pile_total_power) / len(latest_five_pile_total_power)
    # print(f"latest 5 power: {latest_five_pile_total_power}  /  average: {average_last_five_power}")

    # 判斷等待區車輛充電時間是否到達，若到達則加入充電樁
    if_pile_still_vacancies = if_Start_Charge(time, evcs, Spinning_Reserve)

    # evcs.charging_method0(time)
    
    evcs.charging_method5(time, Spinning_Reserve, average_last_five_power, if_pile_still_vacancies['state'])
    
    # 紀錄充電時，各槍的資訊=============================================================================
    charging_evs = []
    for idx, charging_pile in enumerate(charging_pile_status):
        gun_1_power = charging_pile["gun"][0]["charging_power"]
        gun_2_power = charging_pile["gun"][1]["charging_power"]
        ev_1_number = charging_pile["gun"][0]["ev_number"]
        ev_2_number = charging_pile["gun"][1]["ev_number"]
        ev_1_soc = evcs.find_ev_by_number(ev_1_number).now_SOC if ev_1_number != 0 else 0
        ev_2_soc = evcs.find_ev_by_number(ev_2_number).now_SOC if ev_2_number != 0 else 0
        # gun_1_soc = charging_pile["gun"][0]["charging_soc"]

        pile_number = charging_pile["pile_number"]
        charging_power_data[f"{pile_number}-1-EV"].append(ev_1_number)
        charging_power_data[f"{pile_number}-1-P"].append(gun_1_power)
        charging_power_data[f"{pile_number}-1-SOC"].append(ev_1_soc)
        # charging_power_data[f"{pile_number}-1-pile-SOC"].append(gun_1_soc)
        charging_power_data[f"{pile_number}-2-EV"].append(ev_2_number)
        charging_power_data[f"{pile_number}-2-P"].append(gun_2_power)
        charging_power_data[f"{pile_number}-2-SOC"].append(ev_2_soc)

    for idx, charging_pile in enumerate(charging_pile_status):
        pile_power = charging_pile["gun"][0]["charging_power"] + charging_pile["gun"][1]["charging_power"]

        pile_number = charging_pile["pile_number"]
        each_pile_power[pile_number].append(pile_power)

        # 紀錄車輛充電時的SOC
        if ev_1_number != 0:
            charging_evs.append(ev_1_number)
            # ev_1_soc = evcs.find_ev_by_number(ev_1_number).now_SOC
            ev_soc_data_dict[ev_1_number].append(ev_1_soc)
        if ev_2_number != 0:
            charging_evs.append(ev_2_number)
            # ev_2_soc = evcs.find_ev_by_number(ev_2_number).now_SOC
            ev_soc_data_dict[ev_2_number].append(ev_2_soc)

    # 紀錄車輛從時間開始到結束的SOC======================================================================
    for ev in ev_soc_data_dict:
        if ev not in charging_evs:
            ev_soc_data_dict[ev].append(ev_soc_data_dict[ev][-1])
    
    ev_soc_summary, ev_power_summary = evcs.get_ev_summary()
    # print(f"EV SOC Summary: {ev_soc_summary}  /  EV Power Summary: {ev_power_summary}")
    pile_summary, pile_total_power = evcs.get_pile_summary()
    # print(f"Pile Summary: {pile_summary}  /  Pile Total Power: {pile_total_power}")
    pile_summary = evcs.get_pile_power()
    # print(f"Pile Summary: {pile_summary}")
    # min_key = min(pile_summary, key=pile_summary.get)
    # print(f"min_key: {min_key}  /  min_value: {pile_summary[min_key]}")
    # sorted_data = sorted(pile_summary.items(), key=lambda item: item[1])
    # # 打印排序后的结果
    # for key, value in sorted_data:
    #     print(f"Key: {key}, Value: {value}")
    if Export_file:
        Export_file_time_list.append(time.strftime('%m/%d %H:%M'))
    if Draw:
        Draw_time_list.append(time)
    each_pile_power['piles_total_power'].append(pile_total_power)
    
    pile_total += pile_total_power
    
    # print("\n")
    print("pile_total_power: ", pile_total)
    # print("\n")

    time += timedelta(seconds=time_cycle)

    if Draw:
        days = 2
        x_ticks_positions = np.arange(0, 24 * days, 1)
        x_ticks_labels = [(hr) % 24 for hr in range(24 * days)]

        # 將時間步數轉換為小時
        hours = np.arange(0, len(Draw_time_list), 1)


        # 創建一個 subplot
        """
        fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                            subplot_titles=['EV Charging Power Over a Day', 'EV SOC Over a Day'],
                            row_heights=[1,0]) # 設定子圖的高度比例
        """

        fig = make_subplots(rows=1, cols=1)
        # fig = make_subplots(rows=2, cols=1)

        # 添加充電功率折線圖
        # for idx, (pile, powers) in enumerate(charging_power_data.items()):
        #     fig.add_trace(go.Scatter(x=time_list, y=powers, mode='lines', name=pile, legendgroup=f"group{idx}"), row=1, col=1)

        # 添加充電樁總功率折線圖
        fig.add_trace(go.Scatter(x=Draw_time_list, y=each_pile_power['piles_total_power'], mode='lines', name='總功率', legendgroup=f"group{11}"), row=1, col=1)
        # fig.add_trace(go.Scatter(x=time_list, y=piles_total_power1, mode='lines', name='原始總功率', legendgroup=f"group{12}"), row=1, col=1)

        # 添加 SOC 折線圖
        # for ev_number, soc_data in ev_soc_data_dict.items():
        #     fig.add_trace(go.Scatter(x=Draw_time_list, y=soc_data, mode='lines', name=f'{ev_number} SOC', xaxis='x2'), row=2, col=1)

        # 設定布局
        fig.update_layout(title_text='EV Charging and SOC Over a Day',
                            xaxis_title='Time Steps (Hour)',
                            yaxis_title='Power (W)',
                            # xaxis2_title='Time Steps (Hour)',
                            # yaxis2_title='SOC',
                            showlegend=True,  # 顯示圖例
                            # xaxis=dict(type='category', tickmode='array', tickvals=time_list, ticktext=[t.strftime("%Y-%m-%d %H:%M") for t in time_list]),
                            barmode='group',  # stack：將柱狀圖疊加顯示；group：將柱狀圖並排顯示；overlay：將柱狀圖重疊顯示，並將透明度設為0.5
                            bargap=0.2)  # 控制柱狀圖之間的間距
        fig.update_xaxes(tickvals=Draw_time_list,tickmode='auto')



        # 顯示圖表
        fig.show()
