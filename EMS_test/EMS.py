class EnergyManagementSystem:
      def __init__(self, battery_capacity):
            self.battery_capacity = battery_capacity
            self.current_battery_level = 0

      def check_constraints(self, load_demand):
            # 檢查是否滿足儲能系統的限制條件
            if load_demand > self.current_battery_level:
                  print("需求超過儲能系統目前電量，需要充電或降低需求。")
                  return False
            else:
                  print("儲能系統滿足需求，可以供電。")
                  return True

      def charge_battery(self, amount):
            # 充電儲能系統
            if self.current_battery_level + amount <= self.battery_capacity:
                  self.current_battery_level += amount
                  print(f"儲能系統充電，目前電量：{self.current_battery_level}")
            else:
                  print("充電量超過儲能系統容量，無法完全充電。")


# 使用範例
ems = EnergyManagementSystem(battery_capacity=100)  # 假設儲能系統容量為100單位
load_demand = 50  # 假設目前需求為50單位

# 檢查限制條件
ems.check_constraints(load_demand)

# 充電
ems.charge_battery(50)

# 再次檢查限制條件
ems.check_constraints(load_demand)
