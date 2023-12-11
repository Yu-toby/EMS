class EMS:
      def __init__(self):
            self.battery_max_capacity = 1000
            self.battery_min_capacity = 0
            self.current_battery = 0

            self.max_output_power = 100
            self.current_output_power = 0
            self.if_output_power = False  # 電網或儲能放電

            self.max_input_power = 100
            self.current_input_power = 0
            self.input_power_time = 0

            self.evcs_usage_amount = 0

            self.now_tou_price = 0


      def check_constraints(self, load_demand):
            # 檢查是否滿足儲能系統的限制條件
            if load_demand > self.current_battery:
                  print("需求超過儲能系統目前電量，需要充電或降低需求。")
                  return False
            else:
                  print("儲能系統滿足需求，可以供電。")
                  return True

      def charge_battery(self, amount):
            # 充電儲能系統
            if self.current_battery + amount <= self.battery_max_capacity:
                  self.current_battery += amount
                  print(f"儲能系統充電，目前電量：{self.current_battery}")
            else:
                  print("充電量超過儲能系統容量，無法完全充電。")

class EVCS:
      def __init__(self, number):
            self.number = number

            self.max_charging_power = 100
            self.current_charging_power = 0
            self.min_charging_power = 0
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


class EV:
      def __init__(self, remain_SOC, number, target_SOC, now_SOC):
            self.remain_SOC = remain_SOC
            self.number = number
            self.target_SOC = target_SOC
            self.now_SOC = now_SOC


      def drive(self, amount):
            # 電動車行駛
            print("電動車行駛。")
# 使用範例
ems = EMS()  # 假設儲能系統容量為100單位
load_demand = 50  # 假設目前需求為50單位

# 檢查限制條件
ems.check_constraints(load_demand)

# 充電
ems.charge_battery(50)

# 再次檢查限制條件
ems.check_constraints(load_demand)
