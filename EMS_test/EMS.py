class EMS:
      def __init__(self, battery_max_capacity):
            self.battery_max_capacity = battery_max_capacity
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

      def charge(self, amount):
            # 充電電動車
            if self.ems.check_constraints(amount):
                  print("電動車充電。")
            else:
                  print("電動車無法充電。")

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
ems = EMS(battery_capacity=100)  # 假設儲能系統容量為100單位
load_demand = 50  # 假設目前需求為50單位

# 檢查限制條件
ems.check_constraints(load_demand)

# 充電
ems.charge_battery(50)

# 再次檢查限制條件
ems.check_constraints(load_demand)
