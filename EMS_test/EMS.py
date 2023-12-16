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

            # GC參數
            self.now_tou_price = 0

            self.if_ess_provide_power = False
            self.if_PV_provide_power = False

            self.ess_provide_power = 0
            self.PV_provide_power = 0


      def check_remaining_power(self, load_demand):   # 檢查儲能系統剩餘電量是否足夠供電
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

