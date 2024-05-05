# 初始狀態
ev1_initial_soc = 70.1
ev2_initial_soc = 32.3
target_soc = 100
charging_duration = 155  # 充電時長 (分鐘)
max_charging_power = 100 * 1000 * 60  # 最大充電功率 (kW)
battery_capacity = 300 *1000 *60  # 電池容量 (kWh)


# 計算兩輛車的充電需求
ev1_charging_demand = target_soc - ev1_initial_soc
ev2_charging_demand = target_soc - ev2_initial_soc

# 找到兩輛車充電需求中的最大值，作為共同充電需求
common_charging_demand = max(ev1_charging_demand, ev2_charging_demand)

# 計算初始充電功率（根據共同充電需求）
initial_charging_power = common_charging_demand / charging_duration

# 使用共同充電需求來計算最終充電功率，並確保不超過最大充電功率
ev1_final_charging_power = min(ev1_charging_demand / charging_duration, max_charging_power)
ev2_final_charging_power = min(ev2_charging_demand / charging_duration, max_charging_power)
print(f"ev1_final_charging_power: {ev1_final_charging_power}")
print(f"ev2_final_charging_power: {ev2_final_charging_power}")

# 使用最終充電功率計算最終SOC
ev1_final_soc = ev1_initial_soc + ev1_final_charging_power * charging_duration
ev2_final_soc = ev2_initial_soc + ev2_final_charging_power * charging_duration

print(f"ev1_final_charge_soc: {ev1_final_charging_power * charging_duration}")
print(f"ev2_final_charge_soc: {ev2_final_charging_power * charging_duration}")
print("Final SOC for EV1:", ev1_final_soc)
print("Final SOC for EV2:", ev2_final_soc)
