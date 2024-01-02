from datetime import datetime
import matplotlib.pyplot as plt

kWh = 1000  # 1kWh = 1000度電

class EVCS:
    def __init__(self):
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
        for charging_pile in self.charging_piles:
            guns = charging_pile.get('gun', [])

            for gun in guns:
                ev_number = gun['ev_number']

                if ev_number != 0:
                    ev = self.find_ev_by_number(ev_number)

                    if ev and ev.charge_start_time <= time_step < ev.charge_end_time:
                        charge_power, charge_soc = ev.calculate_charge_power(gun['already_time'])
                        ev.now_SOC += charge_soc
                        ev.now_power = ev.now_SOC * ev.battery_max_capacity
                        gun['charging_power'] = round(charge_power, 2)
                        gun['already_time'] += 1
                    else:
                        gun['charging_power'] = 0

        return self.charging_piles

    def find_ev_by_number(self, ev_number):
        for ev in self.connected_evs:
            if ev.number == ev_number:
                return ev
        return None


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
ev1 = EV(1, 0.8, 0.2, 50, 7, 11)
evcs.add_ev(ev1)
ev2 = EV(2, 0.9, 0.25, 60, 17, 20)
evcs.add_ev(ev2)

# 模擬一天的充電過程
for hour in range(24):
    # 假設每小時更新一次充電樁狀態
    evcs.update_ev_state(hour)

    # 提取充電樁狀態
    print(f"Hour {hour + 1} Charging Pile Status:")
    for charging_pile in evcs.charging_piles:
        pile_number = charging_pile["pile_number"]
        gun_1 = charging_pile["gun"][0]
        gun_2 = charging_pile["gun"][1]

        print(f"Pile {pile_number} Gun 1: {gun_1}")
        print(f"Pile {pile_number} Gun 2: {gun_2}")

    print("\n")

