from datetime import datetime

class TOU:
      def __init__(self):
            # TOU參數
            self.summer_peak_price = 4.71
            self.summer_off_peak_price = 1.85
            self.non_summer_peak_price = 4.48
            self.non_summer_off_peak_price = 1.78

      def get_tou(self, month, day, hour):  # 取得當前時間電價
            summer_month = 6 <= month <= 9
            weekday = 1 <= day <= 5

            if summer_month:
                  if weekday and 9 <= hour <= 24:
                        return "尖峰", self.summer_peak_price
                  elif not weekday and (6 <= hour <= 11 or 14 <= hour <= 24):
                        return "尖峰", self.non_summer_peak_price
                  else:
                        return "離峰", self.non_summer_off_peak_price  # 非夏月離峰時間
            else:
                  if weekday and (6 <= hour <= 11 or 14 <= hour <= 24):
                        return "尖峰", self.non_summer_peak_price
                  elif not weekday and (0 <= hour <= 6 or 11 <= hour <= 14):
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
            self.battery_max_capacity = 200*1000  
            self.battery_min_capacity = 0
            self.current_battery = 0

            self.now_soc = 0
            self.target_soc = 0

            self.max_output_power = 100   # 儲能系統最大輸出功率
            self.current_output_power = 0
            self.output_power_time = 0

            self.max_input_power = 100    # 儲能系統最大輸入功率  
            self.current_input_power = 0
            self.input_power_time = 0

            self.start_charge_time = 0
            self.end_charge_time = 0

            self.ess_state = 0  # 0:不動作 1:充電 2:放電


      def charge_battery(self, amount):      # 儲能系統充電
            if self.current_battery + amount <= self.battery_max_capacity:
                  self.ess_state = 1
                  if amount / (self.end_charge_time - self.start_charge_time) > self.max_input_power:
                        charge_power = self.max_input_power
                  else:
                        charge_power = amount / (self.end_charge_time - self.start_charge_time)
                  self.current_battery += charge_power
                  print(f"儲能系統充電，目前電量：{self.current_battery}")
                  return (self.current_battery, charge_power)
            else:
                  self.ess_state = 0
                  print("充電量超過儲能系統容量，無法完全充電。")
                  return (self.current_battery)
      
      def provide_power(self, load_demand):   # 儲能放電
            if load_demand > self.current_battery:
                  self.ess_state = 2
                  print("需求超過儲能系統目前電量，只能提供：", self.current_battery)
                  return self.current_battery
            else:
                  self.ess_state = 2
                  print("儲能系統滿足需求，目前電量為：" , self.current_battery, "，提供電量為：", load_demand)
                  return load_demand

      def get_current_battery(self):
            return self.current_battery
      
      def get_ess_state(self):
            return self.ess_state
      
class GC:
      def __init__(self):
            # GC參數
            self.now_tou_price = 0

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

            if self.ess_state == 0:
                  print("儲能系統不動作。")
                  self.ess_provide_power = 0
                  self.if_ess_provide_power = False
            elif self.ess_state == 1:
                  print("儲能系統充電。")
                  self.ess_provide_power = self.ess.charge_battery(load_demand)
                  self.if_ess_provide_power = False
            elif self.ess_state == 2:
                  print("儲能系統放電。")
                  self.ess_provide_power = self.ess.provide_power(load_demand)
                  self.if_ess_provide_power = True

            if self.if_ess_provide_power == True:
                  self.grid_provide_power = self.grid.provide_power(load_demand - self.ess_provide_power)
            else:
                  self.grid_provide_power = self.grid.provide_power(load_demand)

            print("電網提供電量：", self.grid_provide_power)
            print("儲能系統提供電量：", self.ess_provide_power)
            return (self.grid_provide_power, self.ess_provide_power)




class EVCS:
      def __init__(self):
            self.number = 0

            self.max_output_power = 100
            self.current_output_power = 0
            self.min_output_power = 0
            self.suitable_charging_power = 50

            self.charge_start_time = 0
            self.charge_end_time = 0
            self.charge_already_time = 0

            self.gun_usage_amount = 0
            
            self.target_SOC = 0
            self.start_SOC = 0
            self.now_SOC = 0

      def charge(self):
            if self.gun_usage_amount == 1:
                  print("目前是一支槍在使用。")
                  self.max_charging_power = self.max_charging_power / 2
                  return 1
            elif self.gun_usage_amount == 2:
                  print("目前是兩支槍在使用。")
                  return 2
            else:
                  print("目前沒有槍在使用。")
                  return False
            
      def connect_to_ess(self, ess):
            self.ess = ess


class EV:
      def __init__(self, number, msx_capacity, target_SOC, now_SOC, power_limit, charge_end_time):
            # 電動車參數
            self.number = number

            self.battery_max_capacity = msx_capacity

            self.target_SOC = target_SOC
            self.now_SOC = now_SOC

            self.power_limit = power_limit

            self.charge_start_time = 0
            self.charge_end_time = charge_end_time
            self.charge_already_time = 0

            self.charge_pi = 0      # 倍分配充電係數


      def calculate_power_and_soc(self):
            # 計算充電功率
            self.charge_soc = (self.target_SOC - self.now_SOC) / (self.charge_end_time - self.charge_already_time)
            self.charge_power = self.charge_soc * self.battery_max_capacity
            # 計算當前SOC
            self.now_SOC = self.now_SOC + self.charge_soc
            
            print(f"電動車{self.number}充電功率：{self.charge_power}，當前SOC：{self.now_SOC}")


# 取得當前的日期和時間
current_time = datetime.now()
tou = TOU()
