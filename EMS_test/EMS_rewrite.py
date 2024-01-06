from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

kWh = 1000  # 1kWh = 1000度電

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


class Grid:
    def __init__(self):
        # 電網參數
        # self.now_tou_price = self.get_tou()[1]

        self.max_output_power = 250 * 1000  # 電網最大輸出功率

    def provide_power(self, load_demand):
        if load_demand <= self.max_output_power:
            # print(f"電網提供功率：{load_demand}")
            return load_demand
        else:
            # print(f"電網提供功率：{self.max_output_power}")
            return self.max_output_power


class ESS:
    def __init__(self, tou):
        self.battery_max_capacity = 1500 * kWh
        self.battery_charge_limit = 0.9 * self.battery_max_capacity
        self.battery_discharge_limit = 0.1 * self.battery_max_capacity
        self.current_battery = 800 * kWh
        self.required_charging_capacity = self.battery_charge_limit - self.current_battery

        self.current_soc = self.current_battery / self.battery_max_capacity
        self.target_soc = self.battery_charge_limit / self.battery_max_capacity

        self.charging_capacity_per_hour = 0
        self.discharging_capacity_per_hour = 0
        self.discharging_time = 7

        self.tou = tou
        
        self.start_charge_time = 6      # 6點開始充電
        self.end_charge_time = 0       # 尖峰開始時間

        self.start_discharge_time = 22  # 22點開始放電
        self.end_discharge_time = 5    

        self.ess_state = 0  # 0:不動作 1:充電 2:放電


    def charging_battery(self, charging_power):
        # self.tou = TOU(current_time)
        self.tou_state = self.tou.get_tou()[0]
        current_hour = self.tou.current_time.hour
        self.end_charge_time = 16 if self.tou.if_summer() else 15

        # 判斷電池是否可以充電
        if self.tou_state == "尖峰":
            #  尖峰時段不充電
            print("目前是尖峰時段，儲能系統不充電。")
            return (self.current_battery, self.current_soc)
        
        elif self.tou_state == "離峰" and self.start_charge_time <= current_hour < self.end_charge_time:
            # 離峰時段且為充電時間
            if self.current_battery < self.battery_charge_limit:
                # 電池未充飽
                self.current_battery = min(self.current_battery + charging_power, self.battery_charge_limit)
                self.current_soc = self.current_battery / self.battery_max_capacity
                print(f"儲能系統充電中，目前電量：{round(self.current_battery, 2)}，目前SOC：{self.current_soc}")
                return (self.current_battery, self.current_soc)
            else:
                # 電池已充飽
                print("儲能系統已充飽，不再充電。")
                return (self.current_battery, self.current_soc)
        else:
            # 非充電時段
            print("非充電時段，儲能系統不充電。")
            return (self.current_battery, self.current_soc)
        
    def calculate_charge_power(self):
        current_hour = self.tou.current_time.hour
        print(f"當前電量：{self.current_battery}，目標電量：{self.battery_charge_limit}，充電時間：{self.end_charge_time - current_hour}小時")
        self.charging_capacity_per_hour = (self.battery_charge_limit - self.current_battery) / (self.end_charge_time - current_hour)
        return self.charging_capacity_per_hour
    
    def provide_power(self, load_demand):
        if self.current_battery <= self.battery_discharge_limit:
            print("電池電量不足，無法提供電力。")
            return 0, 0, 0
        else:
            if load_demand <= (self.current_battery - self.battery_discharge_limit):
                print(f"儲能系統提供電力：{load_demand}")
                self.current_battery -= load_demand
                self.current_soc = self.current_battery / self.battery_max_capacity
                return self.current_battery, self.current_soc, load_demand
            else:
                print(f"儲能系統提供電力：{self.current_battery - self.battery_discharge_limit}")
                self.current_battery = self.battery_discharge_limit
                self.current_soc = self.current_battery / self.battery_max_capacity
                return self.current_battery, self.current_soc, (self.current_battery - self.battery_discharge_limit)

    def calculate_discharge_power(self):
        current_hour = self.tou.current_time.hour
        self.discharging_time = (self.end_discharge_time - current_hour) if self.end_discharge_time > current_hour else (24 - current_hour + self.end_discharge_time)
        self.discharging_capacity_per_hour = (self.current_battery - self.battery_discharge_limit) / (self.discharging_time)
        return self.discharging_capacity_per_hour

    def change_ess_state(self, state):
        if state == 'charge':
            self.ess_state = 1
        elif state == 'discharge':
            self.ess_state = 2
        elif state == 'idle':
            self.ess_state = 0

    def get_ess_inform(self):
        return self.current_battery, self.current_soc, self.ess_state



class GC:
    def __init__(self, ess, grid, evcs, tou):
        self.if_ess_provide_power = False
        self.if_PV_provide_power = False

        self.ess_provide_power = 0
        self.grid_provide_power = 0

        self.ess_charge_power = 0

        self.grid_provide_power_for_pile = 0
        self.grid_provide_power_for_ess = 0

        self.ess = ess
        self.grid = grid
        self.evcs = evcs
        self.tou = tou

    def power_control_strategy(self):
        evcs.update_ev_state_situation0(self.tou.current_time.hour)
        self.pile_load_demand = evcs.get_pile_summary()[1]
        self.tou_peak_hr = self.tou.get_tou()[0]

        if self.tou_peak_hr == "尖峰":
            print("目前是尖峰時段，由除能供電。")
            self.ess.change_ess_state('discharge')
            self.if_ess_provide_power = True
            self.ess_provide_power = self.ess.provide_power(
                self.pile_load_demand)[2]
            self.if_grid_provide_power = False
            self.grid_provide_power = 0
            return self.ess_provide_power, self.grid_provide_power

        elif self.tou_peak_hr == "離峰":
            if self.ess_charging_schedule():    # 儲能充電時間，由電網供儲能及充電樁
                print("目前是白天離峰時段，儲能充電時間，儲能系統充電中。")
                self.ess.change_ess_state('charge')
                self.if_ess_provide_power = False
                self.ess_provide_power = 0
                self.if_grid_provide_power = True
                print(f"儲能系統充電功率：{self.ess.calculate_charge_power()}")
                ess_charge_power = min((self.ess.calculate_charge_power()), (self.grid.max_output_power - self.pile_load_demand))
                self.ess.charging_battery(ess_charge_power)
                self.grid_provide_power = self.grid.provide_power((ess_charge_power + self.pile_load_demand))
                self.ess_provide_power = - ess_charge_power
                return  self.ess_provide_power, self.grid_provide_power
            
            else:   # 非儲能充電時間，由電網及儲能供充電樁
                print("目前是晚上離峰時段，儲能與電網共同放電。")
                self.ess.change_ess_state('discharge')
                self.if_ess_provide_power = True
                self.ess_provide_power = self.ess.calculate_discharge_power() if self.pile_load_demand > 0 else 0
                self.ess.provide_power(self.ess_provide_power)
                self.if_grid_provide_power = True
                self.grid_provide_power = self.grid.provide_power(
                    self.pile_load_demand - self.ess_provide_power)
                return  self.ess_provide_power, self.grid_provide_power
    
    def ess_charging_schedule(self):
        self.ess.end_charge_time = 16 if self.tou.if_summer() else 15
        if self.ess.start_charge_time <= self.tou.current_time.hour < self.ess.end_charge_time:
            return True
        else:
            return False



class EVCS:
    def __init__(self):
        self.pile_power_limit = 100 * 1000
        self.connected_evs = []
        piles_amount = 5
        self.charging_piles = []

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


    def add_ev(self, ev):
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
                    gun['already_time'] = 0  # 預設已充電時間
                    self.connected_evs.append(ev)
                    return  # 結束函式，已找到並填入 EV 資料

                elif gun['ev_number'] == ev.number:
                    print('該車編號已存在，請確認是否有誤')
                    return  # 結束函式，已找到重複的 EV 資料

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
                    gun['already_time'] = 0
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
                    ev1 = self.find_ev_by_number(ev_number1)
                    if ev1:
                        if ev1.charge_start_time <= ev1.charge_end_time:
                            # 沒有跨夜充電的情況
                            if ev1.charge_start_time <= time_step < ev1.charge_end_time:
                                check_ev_number1 = True
                                charge_power1, charge_soc1 = ev1.calculate_charge_power(gun1['already_time'])
                                charge_power1 = min(charge_power1, self.pile_power_limit)
                                charge_soc1 = charge_power1 / ev1.battery_max_capacity
                        
                        else:
                            # 有跨夜充電的情況
                            if ev1.charge_start_time <= time_step < 24 or 0 <= time_step < ev1.charge_end_time:
                                check_ev_number1 = True
                                charge_power1, charge_soc1 = ev1.calculate_charge_power(gun1['already_time'])
                                charge_power1 = min(charge_power1, self.pile_power_limit)
                                charge_soc1 = charge_power1 / ev1.battery_max_capacity

                if ev_number2 != 0:
                    ev2 = self.find_ev_by_number(ev_number2)
                    if ev2:
                        if ev2.charge_start_time <= ev2.charge_end_time:
                            # 沒有跨夜充電的情況
                            if ev2.charge_start_time <= time_step < ev2.charge_end_time:
                                check_ev_number2 = True
                                charge_power2, charge_soc2 = ev2.calculate_charge_power(gun2['already_time'])
                                charge_power2 = min(charge_power2, self.pile_power_limit)
                                charge_soc2 = charge_power2 / ev2.battery_max_capacity
                        
                        else:
                            # 有跨夜充電的情況
                            if ev2.charge_start_time <= time_step < 24 or 0 <= time_step < ev2.charge_end_time:
                                check_ev_number2 = True
                                charge_power2, charge_soc2 = ev2.calculate_charge_power(gun2['already_time'])
                                charge_power2 = min(charge_power2, self.pile_power_limit)
                                charge_soc2 = charge_power2 / ev2.battery_max_capacity

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
                    gun1['already_time'] += 1

                    # 更新槍2的充電狀態
                    ev2.now_SOC += charge_soc2
                    ev2.now_power = ev2.now_SOC * ev2.battery_max_capacity
                    gun2['charging_power'] = round(new_charge_power2, 2)
                    gun2['already_time'] += 1

                else:
                    # 如果兩槍的充電功率總和沒有超過充電樁功率上限，則直接更新充電功率
                    if check_ev_number1:
                        # 更新槍1的充電狀態
                        ev1.now_SOC += charge_soc1
                        ev1.now_power = ev1.now_SOC * ev1.battery_max_capacity
                        gun1['charging_power'] = round(charge_power1, 2)
                        gun1['already_time'] += 1
                    else:
                        gun1['charging_power'] = 0

                    if check_ev_number2:
                        # 更新槍2的充電狀態
                        ev2.now_SOC += charge_soc2
                        ev2.now_power = ev2.now_SOC * ev2.battery_max_capacity
                        gun2['charging_power'] = round(charge_power2, 2)
                        gun2['already_time'] += 1
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

    # *兩槍充電功率依三種情況彈性分配*
    def update_ev_state_situation1(self, time_step):
        
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
                    ev1 = self.find_ev_by_number(ev_number1)
                    if ev1 and ev1.charge_start_time <= time_step < ev1.charge_end_time:
                        check_ev_number1 = True
                        charge_power1, charge_soc1 = ev1.calculate_charge_power(gun1['already_time'])
                        # charging_power_limit1 = min(charge_power1, self.pile_power_limit - total_charging_power)
                        
                        # total_charging_power += charging_power_limit1

                if ev_number2 != 0:
                    ev2 = self.find_ev_by_number(ev_number2)
                    if ev2 and ev2.charge_start_time <= time_step < ev2.charge_end_time:
                        check_ev_number2 = True
                        charge_power2, charge_soc2 = ev2.calculate_charge_power(gun2['already_time'])
                        # charging_power_limit2 = min(charge_power2, self.pile_power_limit - total_charging_power)
                        
                        # total_charging_power += charging_power_limit2

                if (charge_power1 + charge_power2) > self.pile_power_limit:
                    # 如果兩槍的充電功率總和超過充電樁功率上限
                    if ev1.charge_end_time < ev2.charge_end_time:
                        # 如果槍1的充電結束時間比較早，則槍1的充電功率不變，槍2的充電功率為充電樁功率上限減去槍1的充電功率
                        ev1.now_SOC += charge_soc1
                        ev1.now_power = ev1.now_SOC * ev1.battery_max_capacity
                        gun1['charging_power'] = round(charge_power1, 2)
                        gun1['already_time'] += 1

                        charge_power2 = self.pile_power_limit - charge_power1
                        charge_soc2 = charge_power2 / ev2.battery_max_capacity
                        ev2.now_SOC += charge_soc2
                        ev2.now_power = ev2.now_SOC * ev2.battery_max_capacity
                        gun2['charging_power'] = round(charge_power2, 2)
                        gun2['already_time'] += 1

                    elif ev1.charge_end_time > ev2.charge_end_time:
                        # 如果槍2的充電結束時間比較早，則槍2的充電功率不變，槍1的充電功率為充電樁功率上限減去槍2的充電功率
                        ev2.now_SOC += charge_soc2
                        ev2.now_power = ev2.now_SOC * ev2.battery_max_capacity
                        gun2['charging_power'] = round(charge_power2, 2)
                        gun2['already_time'] += 1

                        charge_power1 = self.pile_power_limit - charge_power2
                        charge_soc1 = charge_power1 / ev1.battery_max_capacity
                        ev1.now_SOC += charge_soc1
                        ev1.now_power = ev1.now_SOC * ev1.battery_max_capacity
                        gun1['charging_power'] = round(charge_power1, 2)
                        gun1['already_time'] += 1

                    else:
                        new_charge_power1 = charge_power1 / ((charge_power1 + charge_power2) / self.pile_power_limit)
                        new_charge_power2 = charge_power2 / ((charge_power1 + charge_power2) / self.pile_power_limit)
                        charge_soc1 = new_charge_power1 / ev1.battery_max_capacity
                        charge_soc2 = new_charge_power2 / ev2.battery_max_capacity

                        # 更新槍1的充電狀態
                        ev1.now_SOC += charge_soc1
                        ev1.now_power = ev1.now_SOC * ev1.battery_max_capacity
                        gun1['charging_power'] = round(new_charge_power1, 2)
                        gun1['already_time'] += 1

                        # 更新槍2的充電狀態
                        ev2.now_SOC += charge_soc2
                        ev2.now_power = ev2.now_SOC * ev2.battery_max_capacity
                        gun2['charging_power'] = round(new_charge_power2, 2)
                        gun2['already_time'] += 1

                else:
                    # print("charge_power1 + charge_power2 <= self.pile_power_limit")
                    # 如果兩槍的充電功率總和沒有超過充電樁功率上限，則直接更新充電功率
                    if check_ev_number1:
                        # 更新槍1的充電狀態
                        ev1.now_SOC += charge_soc1
                        ev1.now_power = ev1.now_SOC * ev1.battery_max_capacity
                        gun1['charging_power'] = round(charge_power1, 2)
                        gun1['already_time'] += 1
                    else:
                        gun1['charging_power'] = 0

                    if check_ev_number2:
                        # 更新槍2的充電狀態
                        ev2.now_SOC += charge_soc2
                        ev2.now_power = ev2.now_SOC * ev2.battery_max_capacity
                        gun2['charging_power'] = round(charge_power2, 2)
                        gun2['already_time'] += 1
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


class EV:
    def __init__(self, number, target_SOC, now_SOC, power_limit, charge_start_time, charge_end_time):
        # 電動車參數
        self.number = number
        self.battery_max_capacity = 300 * 1000  # 假設單位是kWh
        self.target_SOC = target_SOC
        self.now_SOC = now_SOC
        self.now_power = now_SOC * self.battery_max_capacity
        self.power_limit = power_limit
        self.charge_start_time = charge_start_time
        self.charge_end_time = charge_end_time
        self.charge_time = (self.charge_end_time - self.charge_start_time) if \
            self.charge_end_time > self.charge_start_time else (24 - self.charge_start_time + self.charge_end_time)
        self.charge_already_time = 0
        self.charge_pi = 0  # 倍分配充電係數
        self.pile_number = None  # 車輛連接的充電樁編號

    def calculate_charge_power(self, already_time):
        # 計算每小時所需充電功率
        self.charge_already_time = already_time
        if self.charge_already_time < self.charge_time:
            remaining_time = self.charge_time - self.charge_already_time
            charge_soc_per_second = (
                self.target_SOC - self.now_SOC) / remaining_time
            charge_power_per_second = charge_soc_per_second * self.battery_max_capacity
        else:
            charge_power_per_second = 0
            charge_soc_per_second = 0
        
        return charge_power_per_second, charge_soc_per_second
    


# user_provided_time = datetime(year=2023, month=12, day=15, hour=21, minute=30)
tou = TOU()
ess = ESS(tou)
grid = Grid()
evcs = EVCS()
grid_control = GC(ess, grid, evcs, tou)

ev1 = EV(1, 0.9, 0.2, 60, 22, 5)
evcs.add_ev(ev1)
ev2 = EV(2, 0.9, 0.25, 60, 22, 5)
evcs.add_ev(ev2)
ev3 = EV(3, 0.8, 0.35, 60, 22, 5)
evcs.add_ev(ev3)
ev4 = EV(4, 0.8, 0.25, 60, 22, 5)
evcs.add_ev(ev4)
ev5 = EV(5, 0.9, 0.35, 60, 22, 5)
evcs.add_ev(ev5)
ev6 = EV(6, 0.85, 0.25, 60, 22, 5)
evcs.add_ev(ev6)
ev7 = EV(7, 0.8, 0.30, 60, 22, 5)
evcs.add_ev(ev7)
ev8 = EV(8, 0.9, 0.20, 60, 22, 5)
evcs.add_ev(ev8)
ev9 = EV(9, 0.88, 0.35, 60, 22, 5)
evcs.add_ev(ev9)
ev10 = EV(10, 0.9, 0.2, 60, 22, 5)
evcs.add_ev(ev10)

# for hr in range(0, 24):
#     print(f"Hour {hr}")
#     tou.current_time = datetime(year=2023, month=9, day=15, hour=hr, minute=30)
#     grid_control.ess_charging_schedule()

# # 模擬一天的充電過程
# for hr in range(0, 24):
#     # 假設每小時更新一次充電樁狀態
#     tou.current_time = datetime(year=2023, month=12, day=15, hour=hr, minute=30)
#     ess_provide, grid_provide = grid_control.power_control_strategy()

#     # 提取充電樁狀態
#     print(f"Hour {hr} Charging Pile Status:")
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

#     print(f"ESS Provide Power: {ess_provide}  /  Grid Provide Power: {grid_provide}")

#     print("\n")

# 提取充電樁狀態
charging_pile_status = evcs.charging_piles

# 設定時間步驟數量
start_hours = 6
hours = range(start_hours, start_hours + 24)

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
ess_charge_discharge = []
ess_soc = []
grid = []

for pile in charging_pile_status:
    pile_number = pile['pile_number']
    charging_power_data[f"Pile {pile_number} Gun 1"] = []
    charging_power_data[f"Pile {pile_number} Gun 2"] = []

# 逐小時提取充電功率
for hr1 in hours:
    hr = hr1 % 24
    tou.current_time = datetime(year=2023, month=12, day=15, hour=hr, minute=30)
    ess_provide, grid_provide = grid_control.power_control_strategy()
    print(f"Hour {hr}")
    for idx, charging_pile in enumerate(charging_pile_status):
        gun_1_power = charging_pile["gun"][0]["charging_power"]
        gun_2_power = charging_pile["gun"][1]["charging_power"]

        pile_number = charging_pile["pile_number"]
        charging_power_data[f"Pile {pile_number} Gun 1"].append(gun_1_power)
        charging_power_data[f"Pile {pile_number} Gun 2"].append(gun_2_power)

    pile_summary, pile_total_power = evcs.get_pile_summary()
    print(f"Pile Summary: {pile_summary}  /  Pile Total Power: {pile_total_power}")
    
    ev1_soc_data.append(ev1.now_SOC)
    ev2_soc_data.append(ev2.now_SOC)
    ev3_soc_data.append(ev3.now_SOC)
    ev4_soc_data.append(ev4.now_SOC)
    ev5_soc_data.append(ev5.now_SOC)
    ev6_soc_data.append(ev6.now_SOC)
    ev7_soc_data.append(ev7.now_SOC)
    ev8_soc_data.append(ev8.now_SOC)
    ev9_soc_data.append(ev9.now_SOC)
    ev10_soc_data.append(ev10.now_SOC)

    ess_charge_discharge.append(ess_provide)
    ess_soc.append(ess.current_soc)
    grid.append(grid_provide)

    print(f"ESS Provide Power: {ess_provide}  /  Grid Provide Power: {grid_provide}")
    print("\n")

time_steps = list(range(6, 24)) + list(range(0, 6))

plt.figure(1)
# 繪製柱狀圖
plt.subplot(2, 1, 1)
# plt.figure(figsize=(12, 6))
for pile, powers in charging_power_data.items():
    plt.bar(time_steps, powers, label=pile, alpha=0.7)
# 添加標題與標籤
plt.title('EV Charging Power Over a Day')
plt.xlabel('Time Steps (Hour)')
plt.ylabel('EV Charging Power (kW)')
# 添加圖例
plt.legend()

# 繪製SOC累積折線圖
plt.subplot(2, 1, 2)
plt.plot(hours, ev1_soc_data, label='EV1 SOC')
plt.plot(hours, ev2_soc_data, label='EV2 SOC')
plt.plot(hours, ev3_soc_data, label='EV3 SOC')
plt.plot(hours, ev4_soc_data, label='EV4 SOC')
plt.plot(hours, ev5_soc_data, label='EV5 SOC')
plt.plot(hours, ev6_soc_data, label='EV6 SOC')
plt.plot(hours, ev7_soc_data, label='EV7 SOC')
plt.plot(hours, ev8_soc_data, label='EV8 SOC')
plt.plot(hours, ev9_soc_data, label='EV9 SOC')
plt.plot(hours, ev10_soc_data, label='EV10 SOC')
# 添加標題與標籤
plt.title('EV SOC Over a Day')
plt.xlabel('Time Steps (Hour)')
plt.ylabel('EV SOC')
# 添加圖例
plt.legend()

# 調整子圖之間的間距
plt.tight_layout()
# =============================================================================
plt.figure(2)
# 繪製儲能每小時充放電功率柱狀圖
plt.subplot(3, 1, 1)
plt.bar(hours, ess_charge_discharge, label='ESS Charge/Discharge Power', alpha=0.7)
plt.title('ESS Charge/Discharge Power Over a Day')
plt.xlabel('Time Steps (Hour)')
plt.ylabel('ESS Charge/Discharge Power (kW)')
plt.legend()

# 繪製儲能SOC累積折線圖
plt.subplot(3, 1, 2)
plt.plot(hours, ess_soc, label='ESS SOC')
plt.title('ESS SOC Over a Day')
plt.xlabel('Time Steps (Hour)')
plt.ylabel('ESS SOC')
plt.legend()

# 繪製電網每小時供電功率柱狀圖
plt.subplot(3, 1, 3)
plt.bar(hours, grid, label='Grid Provide Power', alpha=0.7)
plt.title('Grid Provide Power Over a Day')
plt.xlabel('Time Steps (Hour)')
plt.ylabel('Grid Provide Power (kW)')
plt.legend()

# 調整子圖之間的間距
plt.tight_layout()

# 顯示圖表
plt.show()

