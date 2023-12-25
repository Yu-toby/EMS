from datetime import datetime
import matplotlib.pyplot as plt

kWh = 1000  # 1kWh = 1000度電


class TOU:
    def __init__(self, current_time=None):
        # TOU參數
        self.summer_peak_price = 9.34
        self.summer_off_peak_price = 2.29
        self.non_summer_peak_price = 9.10
        self.non_summer_off_peak_price = 2.18

        # 使用者提供時間，如果沒有提供就使用當前時間
        self.current_time = current_time if current_time is not None else datetime.now()

    def if_summer(self):  # 判斷是否為夏季
        summer_month = 6 <= self.current_time.month <= 9
        return summer_month

    def get_tou(self):  # 取得當前時間電價
        summer_month = 6 <= self.current_time.month <= 9
        weekday = 1 <= (self.current_time.weekday() + 1) <= 5

        if summer_month:
            if weekday and 16 <= self.current_time.hour <= 21:
                return "尖峰", self.summer_peak_price
            elif weekday and (0 <= self.current_time.hour <= 15 or 22 <= self.current_time.hour <= 24):
                return "離峰", self.summer_off_peak_price
            else:
                return "離峰", self.summer_off_peak_price
        else:
            if weekday and (15 <= self.current_time.hour <= 20):
                return "尖峰", self.non_summer_peak_price
            elif not weekday and (0 <= self.current_time.hour <= 14 or 21 <= self.current_time.hour <= 24):
                return "離峰", self.non_summer_off_peak_price
            else:
                return "離峰", self.non_summer_off_peak_price  # 非夏月離峰時間

    # *時間有錯要改*
    # def calculate_hourly_rate(month, day, hour, total_consumption):   # 計算每小時電價
    #     summer_month = 6 <= month <= 9
    #     weekday = 1 <= day <= 5

    #     if summer_month:
    #         if weekday and 9 <= hour <= 24:
    #             rate = 4.71
    #         elif not weekday and (6 <= hour <= 11 or 14 <= hour <= 24):
    #             rate = 4.48
    #         else:
    #             rate = 1.78  # 非夏月離峰時間
    #     else:
    #         if weekday and (6 <= hour <= 11 or 14 <= hour <= 24):
    #             rate = 4.48
    #         elif not weekday and (0 <= hour <= 6 or 11 <= hour <= 14):
    #             rate = 1.78
    #         else:
    #             rate = 1.85  # 非夏月離峰時間

    #     if total_consumption > 2000:
    #         rate += 0.99

    #     return rate


class Grid:
    def __init__(self):
        # 電網參數
        # self.now_tou_price = self.get_tou()[1]

        self.max_output_power = 100 * 1000  # 電網最大輸出功率

    def provide_power(self, load_demand):
        if load_demand <= self.max_output_power:
            print("電網各別提供功率：", load_demand)
            return load_demand
        else:
            print("電網各別提供功率：", self.max_output_power)
            return self.max_output_power


class ESS:
    def __init__(self):
        # 儲能系統參數
        self.battery_max_capacity = 1000 * kWh
        self.current_battery = 800 * kWh
        self.required_charging_capacity = self.battery_max_capacity - self.current_battery

        self.now_soc = 0
        self.target_soc = 0

        self.max_output_power = 200*1000   # 儲能系統最大輸出功率
        self.current_output_power = 0
        self.output_power_time = 0

        self.max_input_power = 200*1000    # 儲能系統最大輸入功率
        self.current_input_power = 0
        self.input_power_time = 0

        self.start_charge_time = 6      # 6點開始充電
        self.end_charge_time = 0        # 尖峰時間結束充電

        self.ess_state = 0  # 0:不動作 1:充電 2:放電

        self.tou = TOU()

    def charge_battery(self):      # 儲能系統充電
        self.tou_state = self.tou.get_tou()[0]
        self.end_charge_time = 16 if self.tou.if_summer() else 15


        if self.tou_state == "尖峰":
            print("目前是尖峰時段，儲能系統不充電。")
            return (self.current_battery, 0, self.now_soc)
        else:
            calculate_input_power = (self.required_charging_capacity /
                                        (self.end_charge_time - self.start_charge_time))
            self.current_input_power = min(self.max_input_power, calculate_input_power)

        if self.current_input_power + self.current_battery <= self.battery_max_capacity:
            self.ess_state = 1
            self.current_battery += self.current_input_power
            self.now_soc = self.current_battery / self.battery_max_capacity
            # print(f"儲能系統充電，目前電量：{self.current_battery}")
            return (self.current_battery, self.current_input_power, self.now_soc)
        else:
            self.ess_state = 0
            # print("充電量超過儲能系統容量，無法完全充電。")
            return (self.current_battery, 0, self.now_soc)

    def provide_power(self, load_demand):   # 儲能放電
        if self.current_battery <= 0:
            self.ess_state = 0
            print("儲能系統電量為0，無法提供電量。")
            return 0, 0
        else:
            if load_demand > self.current_battery:
                self.ess_state = 2
                print("需求超過儲能系統目前電量，只能提供：", self.current_battery)
                self.current_battery = 0
                return self.current_battery, self.current_battery, self.now_soc
            else:
                self.ess_state = 2
                print("儲能系統滿足需求，目前電量為：", self.current_battery,
                    "，提供電量為：", load_demand)
                self.current_battery -= load_demand
                return self.current_battery, load_demand, self.now_soc

    def get_current_battery(self):
        return self.current_battery

    def get_ess_state(self):
        return self.ess_state

    def change_ess_state(self, state):
        if state == 'charge':
            self.ess_state = 1
        elif state == 'discharge':
            self.ess_state = 2
        elif state == 'idle':
            self.ess_state = 0


class GC:
    def __init__(self):
        # GC參數
        self.if_ess_provide_power = False
        self.if_PV_provide_power = False

        self.ess_provide_power = 0
        self.grid_provide_power = 0

        self.ess_charge_power = 0

        self.ess = ESS()
        self.grid = Grid()
        self.tou = TOU()
        self.evcs = EVCS()

    def provide_power(self):
        self.pile_load_demand = evcs.get_pile_power_summary()[1]
        self.ess_state = self.ess.get_ess_state()
        self.ess_current_battery = self.ess.get_current_battery()

        self.tou_price = self.tou.get_tou()[0]

        if self.tou_price == "尖峰":
            print("目前是尖峰時段，由儲能供電。")
            self.ess.change_ess_state('discharge')
            self.if_ess_provide_power = True
            self.ess_provide_power = self.ess.provide_power(self.pile_load_demand)[1]
            return (self.ess_provide_power)

        elif self.tou_price == "離峰":      
            if self.pile_load_demand > 0:
                print("目前是離峰時段，由電網供電。")
                # self.ess.change_ess_state('idle')
                self.if_ess_provide_power = False
                self.ess_provide_power = 0
                self.if_grid_provide_power = True
                self.grid_provide_power_for_pile = self.grid.provide_power(self.pile_load_demand)
                # return (self.grid_provide_power)
            # else:
            #     if self.charging_scheduler():
            #         print("目前是離峰時段，且電動車無充電需求，儲能充電。")
            #         self.ess.change_ess_state('charge')
            #         self.if_ess_provide_power = False
            #         self.ess_provide_power = 0
            #         self.if_grid_provide_power = True
            #         self.grid_provide_power = self.ess.charge_battery()
            #         return (self.grid_provide_power)
            #     else:
            #         print("目前是離峰時段，但電動車可能有充電需求，儲能不充電。")
            #         self.ess.change_ess_state('idle')
            #         self.if_ess_provide_power = False
            #         self.ess_provide_power = 0
            self.ess.change_ess_state('charge')
            self.if_ess_provide_power = False
            self.ess_provide_power = 0
            self.if_grid_provide_power = True
            self.grid_provide_power_for_ess = self.grid.provide_power(self.ess.charge_battery()[1])

        self.grid_provide_power = self.grid_provide_power_for_pile + self.grid_provide_power_for_ess
        return (self.grid_provide_power)

    def charging_scheduler(self):
        self.summer_off_peak_start_hour = 6
        self.summer_off_peak_end_hour = 9
        self.non_summer_off_peak_start_hour = 11
        self.non_summer_off_peak_end_hour = 14

        summer_month = 6 <= datetime.now().month <= 9

        if summer_month:
            if self.summer_off_peak_start_hour <= datetime.now().hour <= self.summer_off_peak_end_hour:
                return True
            else:
                return False
        else:
            if self.non_summer_off_peak_start_hour <= datetime.now().hour <= self.non_summer_off_peak_end_hour:
                return True
            else:
                return False


class EVCS:
    def __init__(self):
        self.number = 0
        self.connected_evs = []
        self.pile_number = ['1-1', '1-2', '2-1', '2-2',
                            '3-1', '3-2', '4-1', '4-2', '5-1', '5-2']

        self.max_output_power = 100 * 1000
        self.current_output_power = 0
        self.min_output_power = 0
        self.suitable_charging_power = 0

        self.charge_start_time = 0
        self.charge_end_time = 0
        self.charge_already_time = 0

        self.gun_usage_amount = 0

        self.target_SOC = 0
        self.start_SOC = 0
        self.now_SOC = 0

        self.pile_status = {pile: {'charging_power': 0, 'ev_number': None, 'already_time': 0}
                            for pile in self.pile_number}

    def add_ev(self, ev):
        # 新進一輛車，連接到充電站
        for pile, status in self.pile_status.items():
            if status['ev_number'] is None:
                ev.pile_number = pile
                status['ev_number'] = ev.number
                self.connected_evs.append(ev)
                break

    def ev_state(self):
        for ev in self.connected_evs:
            charge_power, charge_soc = ev.calculate_charge_power(
                self.pile_status[ev.pile_number]['already_time'])
            ev.now_SOC += charge_soc
            ev.now_power = ev.now_SOC * ev.battery_max_capacity
            self.pile_status[ev.pile_number]['charging_power'] = charge_power
            self.pile_status[ev.pile_number]['already_time'] += 1
        return self.connected_evs

    def get_pile_power_summary(self):
        # 取得各充電樁的狀態及總功率
        summary = {pile: {'charging_power': status['charging_power'], 'ev_number': status['ev_number']} for pile, status in
                    self.pile_status.items()}
        total_power = sum(status['charging_power']
                            for status in self.pile_status.values())
        return summary, total_power

    def get_ev_summary(self):
        # 取得車輛充電當下SOC及power
        summary_soc = {ev.number: round(ev.now_SOC, 2) for ev in self.connected_evs}
        summary_power = {ev.number: round(ev.now_power, 2) for ev in self.connected_evs}
        return summary_soc, summary_power


class EV:
    def __init__(self, number, target_SOC, now_SOC, power_limit, charge_end_time):
        # 電動車參數
        self.number = number
        self.battery_max_capacity = 300  # 假設單位是kWh
        self.target_SOC = target_SOC
        self.now_SOC = now_SOC
        self.now_power = now_SOC * self.battery_max_capacity
        self.power_limit = power_limit
        self.charge_end_time = charge_end_time
        self.charge_already_time = 0
        self.charge_pi = 0  # 倍分配充電係數
        self.pile_number = None  # 車輛連接的充電樁編號

    def calculate_charge_power(self, already_time):
        # 計算每小時所需充電功率
        self.charge_already_time = already_time
        if self.charge_already_time < self.charge_end_time:
            remaining_time = self.charge_end_time - self.charge_already_time
            charge_soc_per_second = (
                self.target_SOC - self.now_SOC) / remaining_time
            charge_power_per_second = charge_soc_per_second * self.battery_max_capacity
            return round(charge_power_per_second, 2), round(charge_soc_per_second, 2)
        else:
            return 0, 0


# 使用範例
# 使用者提供時間範例
user_provided_time = datetime(year=2023, month=12, day=15, hour=21, minute=30)
tou_instance = TOU(current_time=user_provided_time)
# 取得電價
tou_result = tou_instance.if_summer()
# print(tou_result)

gc = GC()
evcs = EVCS()
ev1 = EV(1, 0.8, 0.2, 50, 4)
evcs.add_ev(ev1)
ev2 = EV(2, 0.9, 0.25, 60, 3)
evcs.add_ev(ev2)

# # 模擬充電過程
# for _ in range(max(ev1.charge_end_time, ev2.charge_end_time)):
#     evcs.ev_state()
#     pile_summary, total_power = evcs.get_pile_power_summary()
#     ev_soc_summary, ev_power_summary = evcs.get_ev_summary()
#     print(f'電網提供功率：{gc.provide_power()}')
#     print(f"Pile Summary: {pile_summary}")
#     print(f"Total Power: {total_power}")
#     print(f"EV SOC Summary: {ev_soc_summary}  /  EV Power Summary: {ev_power_summary}")

# 模擬充電過程
time_steps = 24  # 代表一天的每個小時

# 調整充電結束時間至一天內的合理範圍
ev1.charge_end_time = min(ev1.charge_end_time, time_steps)
ev2.charge_end_time = min(ev2.charge_end_time, time_steps)

ev1_power = []
ev2_power = []
ev1_cumulative_soc = []
ev2_cumulative_soc = []

for _ in range(time_steps):
    evcs.ev_state()
    _, ev1_soc_per_second = ev1.calculate_charge_power(
        evcs.pile_status[ev1.pile_number]['already_time'])
    _, ev2_soc_per_second = ev2.calculate_charge_power(
        evcs.pile_status[ev2.pile_number]['already_time'])

    # 計算每個時間步驟的SOC累積值
    ev1_cumulative_soc.append(ev1.now_SOC)
    ev2_cumulative_soc.append(ev2.now_SOC)

    # 計算每個時間步驟的功率
    ev1_power.append(ev1_soc_per_second * ev1.battery_max_capacity)
    ev2_power.append(ev2_soc_per_second * ev2.battery_max_capacity)

# 設定柱狀圖的寬度
bar_width = 0.4

# 計算每個柱子的中心點位置
bar_positions_center = range(1, time_steps + 1)

# 產生 x 軸的位置
bar_positions_ev1 = [x - bar_width/2 for x in bar_positions_center]
bar_positions_ev2 = [x + bar_width/2 for x in bar_positions_center]

# 畫出總功率柱狀圖
plt.subplot(3, 1, 1)
plt.bar(bar_positions_center, [x + y for x, y in zip(ev1_power, ev2_power)],
        label='Total Power EV1 & EV2', width=bar_width, color='skyblue')
plt.xlabel('Time Steps (Hour)')
plt.ylabel('Total Charging Power (kW)')
plt.title('Total Charging Power Over a Day')
plt.legend()

# 畫出功率柱狀圖
plt.subplot(3, 1, 2)
plt.bar(bar_positions_ev1, ev1_power, label='EV1 Power', width=bar_width, color='orange')
plt.bar(bar_positions_ev2, ev2_power, label='EV2 Power', width=bar_width, color='green', alpha=0.7)
plt.xlabel('Time Steps (Hour)')
plt.ylabel('EV Charging Power (kW)')
plt.title('EV Charging Power Over a Day')
plt.legend()

# 畫出SOC累積折線圖
plt.subplot(3, 1, 3)
plt.plot(range(1, time_steps + 1), ev1_cumulative_soc,
        label='EV1 Cumulative SOC')
plt.plot(range(1, time_steps + 1), ev2_cumulative_soc,
        label='EV2 Cumulative SOC')
plt.xlabel('Time Steps (Hour)')
plt.ylabel('Cumulative SOC')
plt.title('EV Cumulative SOC Over a Day')
plt.legend()

# 調整子圖之間的間距
plt.tight_layout()

# 顯示圖表
plt.show()
