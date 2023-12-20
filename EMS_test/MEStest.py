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
    def __init__(self, number, target_SOC, now_SOC, power_limit, charge_end_time):
        # 電動車參數
        self.number = number
        self.battery_max_capacity = 300 * 1000  # 假設單位是 kWh
        self.target_SOC = target_SOC
        self.now_SOC = now_SOC
        self.power_limit = power_limit
        self.charge_end_time = charge_end_time
        self.charge_already_time = 0
        self.charge_pi = 0  # 倍分配充電係數

    def calculate_charge_power(self):
        # 計算每小時所需充電功率
        return (self.target_SOC - self.now_SOC) / self.charge_end_time * self.battery_max_capacity

    def calculate_power_and_soc(self, time_interval):
        # 計算充電功率
        elapsed_time = self.charge_already_time + time_interval
        remaining_time = max(0, self.charge_end_time - elapsed_time)

        if remaining_time > 0:
            charge_soc_per_second = (self.target_SOC - self.now_SOC) / remaining_time
            charge_power_per_second = charge_soc_per_second * self.battery_max_capacity
            self.charge_already_time = elapsed_time
            return min(charge_power_per_second, self.power_limit)
        else:
            return 0

    def update_charge_status(self, time_interval):
        # 模擬每秒更新一次電量和當前 SOC
        charge_power = self.calculate_power_and_soc(time_interval)
        self.now_SOC += charge_power / self.battery_max_capacity

        # 提供當前 SOC 和充電功率給充電站
        evcs_1.receive_ev_status(self.number, self.now_SOC, charge_power)

        # 顯示當前狀態（可以根據需要進行調整）
        print(f"EV {self.number} - SOC: {self.now_SOC:.2f} - Charge Power: {charge_power:.2f}")

# 創建儲能系統、充電站、和電動車
ess = ESS()
evcs_1 = EVCS("1-1", ess)

ev1 = EV(1, 0.8, 0.2, 50, 4)
evcs_1.add_ev(ev1)

# 模擬充電過程
for elapsed_time in range(ev1.charge_end_time):
    time.sleep(1)
    ev1.update_charge_status(1)
