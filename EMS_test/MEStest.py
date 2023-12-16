import time

class ESS:
    def __init__(self):
        # 儲能系統初始設定
        self.battery_max_capacity = 200 * 1000
        self.current_battery = 0
        self.now_soc = 0
        self.max_output_power = 100

    def provide_power(self, total_power_needed):
        # 計算儲能系統提供的功率
        if total_power_needed <= self.max_output_power:
            return total_power_needed
        else:
            return self.max_output_power

class EVCS:
    def __init__(self, number, ess):
        # 充電站初始設定
        self.number = number
        self.connected_evs = []
        self.ess = ess

    def add_ev(self, ev):
        # 新進一輛車，連接到充電站
        self.connected_evs.append(ev)

    def calculate_total_power_needed(self):
        # 計算所有連接車輛的總充電功率需求
        total_power_needed = sum(ev.calculate_charge_power() for ev in self.connected_evs)
        return total_power_needed

    def inform_ess(self):
        # 向儲能系統報告總共需要多少功率
        total_power_needed = self.calculate_total_power_needed()
        provided_power = self.ess.provide_power(total_power_needed)
        return provided_power
    
    def receive_ev_status(self, ev_number, ev_soc, charge_power):
        # 充電站接收電動車的狀態
        print(f"EVCS {self.number} - Connected EV: {ev_number} - SOC: {ev_soc:.2f} - Charge Power: {charge_power:.2f}")

class EV:
    def __init__(self, number, max_capacity, now_soc, target_soc, power_limit, charge_duration):
        # 電動車初始設定
        self.number = number
        self.max_capacity = max_capacity
        self.target_soc = target_soc
        self.now_soc = now_soc
        self.power_limit = power_limit
        self.charge_duration = charge_duration
        self.charge_pi = 0

    def calculate_charge_power(self, elapsed_time):
      # 計算充電功率（平均分散）
      if elapsed_time <= self.charge_duration:
            remaining_time = max(0, self.charge_duration - elapsed_time)
            if remaining_time > 0:
                  charge_soc_per_second = (self.target_soc - self.now_soc) / remaining_time
                  charge_power_per_second = charge_soc_per_second * self.max_capacity
                  return min(charge_power_per_second, self.power_limit)
            else:
                  return 0
      else:
            return 0

    def update_charge_status(self):
        # 模擬每秒更新一次電量和當前 SOC
        for elapsed_time in range(self.charge_duration + 1):
            time.sleep(1)
            charge_power = self.calculate_charge_power(elapsed_time)
            self.now_soc += charge_power / self.max_capacity

            # 提供當前 SOC 和充電功率給充電站
            evcs_1.receive_ev_status(self.number, self.now_soc, charge_power)

            # 顯示當前狀態（可以根據需要進行調整）
            # print(f"EV {self.number} - SOC: {self.now_soc:.2f} - Charge Power: {charge_power:.2f}")

# 創建儲能系統、充電站、和電動車
ess = ESS()
evcs_1 = EVCS("1-1", ess)
# evcs_2 = EVCS("1-2", ess)

ev1 = EV(1, 100, 0.2, 0.8, 50, 4)
# ev2 = EV(2, 120, 0.25, 0.9, 60, 3)
# print(f"車輛 {ev1.number} 的充電功率需求：{ev1.update_charge_status()}")
# print(f"車輛 {ev2.number} 的充電功率需求：{ev2.calculate_charge_power()}")
ev1.update_charge_status()

# 車輛進入充電站
evcs_1.add_ev(ev1)
# evcs_1.add_ev(ev2)

# 模擬充電過程
ev1.update_charge_status()
# ev2.update_charge_status()
