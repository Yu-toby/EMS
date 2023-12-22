from datetime import datetime

kWh = 1000  # 1kWh = 1000度電


class TOU:
      def __init__(self):
            # TOU參數
            self.summer_peak_price = 4.71
            self.summer_off_peak_price = 1.85
            self.non_summer_peak_price = 4.48
            self.non_summer_off_peak_price = 1.78

      def get_tou(self):  # 取得當前時間電價
            current_time = datetime.now()
            summer_month = 6 <= current_time.month <= 9
            weekday = 1 <= (current_time.weekday() + 1) <= 5

            if summer_month:
                  if weekday and 9 <= current_time.hour <= 24:
                        return "尖峰", self.summer_peak_price
                  elif not weekday and (6 <= current_time.hour <= 11 or 14 <= current_time.hour <= 24):
                        return "尖峰", self.non_summer_peak_price
                  else:
                        return "離峰", self.non_summer_off_peak_price  # 非夏月離峰時間
            else:
                  if weekday and (6 <= current_time.hour <= 11 or 14 <= current_time.hour <= 24):
                        return "尖峰", self.non_summer_peak_price
                  elif not weekday and (0 <= current_time.hour <= 6 or 11 <= current_time.hour <= 14):
                        return "離峰", self.non_summer_off_peak_price
                  else:
                        return "離峰", self.summer_off_peak_price  # 非夏月離峰時間

      def calculate_hourly_rate(month, day, hour, total_consumption):   # 計算每小時電價
            summer_month = 6 <= month <= 9
            weekday = 1 <= day <= 5

            if summer_month:
                  if weekday and 9 <= hour <= 24:
                        rate = 4.71
                  elif not weekday and (6 <= hour <= 11 or 14 <= hour <= 24):
                        rate = 4.48
                  else:
                        rate = 1.78  # 非夏月離峰時間
            else:
                  if weekday and (6 <= hour <= 11 or 14 <= hour <= 24):
                        rate = 4.48
                  elif not weekday and (0 <= hour <= 6 or 11 <= hour <= 14):
                        rate = 1.78
                  else:
                        rate = 1.85  # 非夏月離峰時間

            if total_consumption > 2000:
                  rate += 0.99

            return rate


class Grid:
      def __init__(self):
            # 電網參數
            self.now_tou_price = 0

            self.max_output_power = 1000

      def provide_power(self, load_demand):
            if load_demand <= self.max_output_power:
                  print("電網提供電量：", load_demand)
                  return load_demand
            else:
                  print("電網提供電量：", self.max_output_power)
                  return self.max_output_power


class ESS:
      def __init__(self):
            # 儲能系統參數
            self.battery_max_capacity = 1000 * kWh
            self.battery_min_capacity = 0
            self.current_battery = 0

            self.now_soc = 0
            self.target_soc = 0

            self.max_output_power = 200*1000   # 儲能系統最大輸出功率
            self.current_output_power = 0
            self.output_power_time = 0

            self.max_input_power = 200*1000    # 儲能系統最大輸入功率
            self.current_input_power = 0
            self.input_power_time = 0

            self.start_charge_time = 0
            self.end_charge_time = 0

            self.ess_state = 0  # 0:不動作 1:充電 2:放電

      def charge_battery(self):      # 儲能系統充電
            if self.current_battery + self.max_input_power <= self.battery_max_capacity:
                  self.ess_state = 1
                  if self.max_input_power / (self.end_charge_time - self.start_charge_time) > self.max_input_power:
                        charge_power = self.max_input_power
                  else:
                        charge_power = self.max_input_power / \
                              (self.end_charge_time - self.start_charge_time)
                        self.current_battery += charge_power
                        print(f"儲能系統充電，目前電量：{self.current_battery}")
                        return (self.current_battery, charge_power)
            else:
                  self.ess_state = 0
                  print("充電量超過儲能系統容量，無法完全充電。")
                  return (self.current_battery)

      def provide_power(self, load_demand):   # 儲能放電
            if self.current_battery == 0:
                  self.ess_state = 0
                  print("儲能系統電量為0，無法提供電量。")
                  return 0
            else:
                  if load_demand > self.current_battery:
                        self.ess_state = 2
                        print("需求超過儲能系統目前電量，只能提供：", self.current_battery)
                        self.current_battery -= load_demand
                        return self.current_battery
                  else:
                        self.ess_state = 2
                        print("儲能系統滿足需求，目前電量為：", self.current_battery,
                              "，提供電量為：", load_demand)
                        self.current_battery -= load_demand
                        return load_demand

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

      def provide_power(self, load_demand):
            self.ess_state = self.ess.get_ess_state()
            self.ess_current_battery = self.ess.get_current_battery()

            self.tou_price = self.tou.get_tou()[0]

            if self.tou_price == "尖峰":
                  print("目前是尖峰時段，由儲能供電。")
                  self.ess.change_ess_state('discharge')
                  self.if_ess_provide_power = True
                  self.ess_provide_power = self.ess.provide_power(load_demand)
                  return (self.ess_provide_power)

            elif self.tou_price == "離峰":
                  if load_demand > 0:
                        print("目前是離峰時段，由電網供電。")
                        self.ess.change_ess_state('idle')
                        self.if_ess_provide_power = False
                        self.ess_provide_power = 0
                        self.if_grid_provide_power = True
                        self.grid_provide_power = self.grid.provide_power(load_demand)
                        return (self.grid_provide_power)
                  else:
                        if self.charging_scheduler():
                              print("目前是離峰時段，且電動車無充電需求，儲能充電。")
                              self.ess.change_ess_state('charge')
                              self.if_ess_provide_power = False
                              self.ess_provide_power = 0
                              self.if_grid_provide_power = True
                              self.grid_provide_power = self.ess.charge_battery()
                              return (self.grid_provide_power)
                        else:
                              print("目前是離峰時段，但電動車可能有充電需求，儲能不充電。")
                              self.ess.change_ess_state('idle')
                              self.if_ess_provide_power = False
                              self.ess_provide_power = 0

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

            self.pile_status = {pile: {'power': 0, 'ev_number': None, 'already_time': 0}
                              for pile in self.pile_number}
            

      def add_ev(self, ev):
            # 新進一輛車，連接到充電站
            for pile, status in self.pile_status.items():
                  if status['ev_number'] is None:
                        ev.pile_number = pile
                        status['ev_number'] = ev.number
                        # status['power'] = ev.calculate_charge_power()[0]
                        self.connected_evs.append(ev)
                        break

      def ev_state(self):
            for ev in self.connected_evs:
                  # print(f"already_time: {self.pile_status[ev.pile_number]['already_time']}")
                  charge_power, charge_soc = ev.calculate_charge_power(self.pile_status[ev.pile_number]['already_time'])
                  ev.now_SOC += charge_soc
                  self.pile_status[ev.pile_number]['power'] = charge_power
                  # print(f"EVCS {ev.pile_number} - Connected EV: {ev.number} - SOC: {ev.now_SOC:.2f} - Charge Power: {charge_power:.2f}")
                  # print(f"time: {ev.charge_already_time}")
                  self.pile_status[ev.pile_number]['already_time'] += 1
            return self.connected_evs

      def get_pile_power_summary(self):
            # 取得各充電樁的狀態及總功率
            summary = {pile: {'power': status['power'], 'ev_number': status['ev_number']} for pile, status in
                        self.pile_status.items()}
            total_power = sum(status['power']
                              for status in self.pile_status.values())
            return summary, total_power
      
      def get_ev_current_soc(self):
            # 取得車輛充電當下SOC
            summary = {ev.number: ev.now_SOC for ev in self.connected_evs}
            return round(summary[1], 2), round(summary[2], 2)


class EV:
      def __init__(self, number, target_SOC, now_SOC, power_limit, charge_end_time):
            # 電動車參數
            self.number = number
            self.battery_max_capacity = 300  # 假設單位是kWh
            self.target_SOC = target_SOC
            self.now_SOC = now_SOC
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
                  charge_soc_per_second = (self.target_SOC - self.now_SOC) / remaining_time
                  charge_power_per_second = charge_soc_per_second * self.battery_max_capacity
                  # self.charge_already_time += 1
                  return round(charge_power_per_second, 2), round(charge_soc_per_second, 2)
            else:
                  return 0, 0


# 使用範例
evcs = EVCS()
ev1 = EV(1, 0.8, 0.2, 50, 4)
# for _ in range(ev1.charge_end_time):
#       print(ev1.calculate_charge_power())
evcs.add_ev(ev1)
ev2 = EV(2, 0.9, 0.25, 60, 3)
evcs.add_ev(ev2)

# 模擬充電過程
for _ in range(max(ev1.charge_end_time, ev2.charge_end_time)):
      # evcs.calculate_total_power_needed()
      evcs.ev_state()
      # print(f"ev1 power: {ev1.calculate_charge_power()}", f"ev2 power: {ev2.calculate_charge_power()}")
      pile_summary, total_power = evcs.get_pile_power_summary()
      ev_summary = evcs.get_ev_current_soc()
      print(f"Pile Summary: {pile_summary}")
      print(f"Total Power: {total_power}")
      print(f"EV Summary: {ev_summary}")
