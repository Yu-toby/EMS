from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

kWh = 1000  # 1kWh = 1000度電

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

    def update_ev_state(self, time_step):
        # for charging_pile in self.charging_piles:
        #     guns = charging_pile.get('gun', [])
        #     total_charging_power = 0  # 用於累計兩槍的總充電功率

        #     for gun in guns:
        #         ev_number = gun['ev_number']

        #         if ev_number != 0:
        #             ev = self.find_ev_by_number(ev_number)

        #             if ev and ev.charge_start_time <= time_step < ev.charge_end_time:
        #                 charge_power, charge_soc = ev.calculate_charge_power(gun['already_time'])
        #                 charging_power_limit = min(charge_power, self.pile_power_limit - total_charging_power)
        #                 # 更新槍的充電狀態
        #                 charge_soc = charging_power_limit / ev.battery_max_capacity
        #                 ev.now_SOC += charge_soc
        #                 ev.now_power = ev.now_SOC * ev.battery_max_capacity
        #                 gun['charging_power'] = round(charging_power_limit, 2)
        #                 gun['already_time'] += 1
        #                 total_charging_power += charging_power_limit

        #             else:
        #                 gun['charging_power'] = 0

        # return self.charging_piles

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
        self.charge_time = self.charge_end_time - self.charge_start_time
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
    

evcs = EVCS()
ev1 = EV(1, 0.8, 0.2, 60, 7, 12)
evcs.add_ev(ev1)
ev2 = EV(2, 0.9, 0.25, 60, 8, 12)
evcs.add_ev(ev2)

# # 模擬一天的充電過程
# for hour in range(24):
#     # 假設每小時更新一次充電樁狀態
#     evcs.update_ev_state(hour)

#     # 提取充電樁狀態
#     print(f"Hour {hour + 1} Charging Pile Status:")
#     for charging_pile in evcs.charging_piles:
#         pile_number = charging_pile["pile_number"]
#         gun_1 = charging_pile["gun"][0]
#         gun_2 = charging_pile["gun"][1]

#         print(f"Pile {pile_number} Gun 1: {gun_1}")
#         print(f"Pile {pile_number} Gun 2: {gun_2}")

#     ev_soc_summary, ev_power_summary = evcs.get_ev_summary()
#     print(f"EV SOC Summary: {ev_soc_summary}  /  EV Power Summary: {ev_power_summary}")

#     print("\n")

# 提取充電樁狀態
charging_pile_status = evcs.charging_piles

# 設定時間步驟數量
hours = range(1, 25)

# 建立一個字典來存儲每小時每個充電樁的充電功率
charging_power_data = {}
for pile in charging_pile_status:
    pile_number = pile['pile_number']
    charging_power_data[f"Pile {pile_number} Gun 1"] = []
    charging_power_data[f"Pile {pile_number} Gun 2"] = []

# 逐小時提取充電功率
for hour in hours:
    evcs.update_ev_state(hour)
    for idx, charging_pile in enumerate(charging_pile_status):
        gun_1_power = charging_pile["gun"][0]["charging_power"]
        gun_2_power = charging_pile["gun"][1]["charging_power"]

        pile_number = charging_pile["pile_number"]
        charging_power_data[f"Pile {pile_number} Gun 1"].append(gun_1_power)
        charging_power_data[f"Pile {pile_number} Gun 2"].append(gun_2_power)

# 繪製柱狀圖
plt.subplot(2, 1, 1)
# plt.figure(figsize=(12, 6))
for pile, powers in charging_power_data.items():
    plt.bar(hours, powers, label=pile, alpha=0.7)

# 添加標題與標籤
plt.title('EV Charging Power Over a Day')
plt.xlabel('Time Steps (Hour)')
plt.ylabel('EV Charging Power (kW)')

# 添加圖例
plt.legend()

# 顯示圖表
plt.show()

