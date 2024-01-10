from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

kWh = 1000  # 1kWh = 1000度電
time_cycle = 3600  # 時間間隔為1小時

class TOU:
    def __init__(self, current_time=None):
        # TOU參數
        self.summer_peak_price = 9.34
        self.summer_off_peak_price = 2.29
        self.non_summer_peak_price = 9.10
        self.non_summer_off_peak_price = 2.18

        self.summer_peak_time_start = 16
        self.summer_peak_time_end = 22
        self.non_summer_peak_time_start = 15
        self.non_summer_peak_time_end = 21

        # 使用者提供時間，如果沒有提供就使用當前時間
        self.current_time = current_time if current_time is not None else datetime.now()

    def if_summer(self):  # 判斷是否為夏季
        if 6 <= self.current_time.month <= 9:
            return True
        else:
            return False

    def get_tou(self):  # 取得當前時間電價
        summer_month = 6 <= self.current_time.month <= 9
        weekday = 1 <= (self.current_time.weekday() + 1) <= 5

        if summer_month:
            if weekday and self.summer_peak_time_start <= self.current_time.hour < self.summer_peak_time_end:
                return "尖峰", self.summer_peak_price
            elif weekday and (0 <= self.current_time.hour < self.summer_peak_time_start or self.summer_peak_time_end <= self.current_time.hour <= 24):
                return "離峰", self.summer_off_peak_price
            else:
                return "離峰", self.summer_off_peak_price
        else:
            if weekday and (self.non_summer_peak_time_start <= self.current_time.hour < self.non_summer_peak_time_end):
                return "尖峰", self.non_summer_peak_price
            elif not weekday and (0 <= self.current_time.hour < self.non_summer_peak_time_start or self.non_summer_peak_time_end <= self.current_time.hour <= 24):
                return "離峰", self.non_summer_off_peak_price
            else:
                return "離峰", self.non_summer_off_peak_price  # 非夏月離峰時間


class Grid:
    def __init__(self):
        # 電網參數
        # self.now_tou_price = self.get_tou()[1]

        self.max_output_power = 250 * 1000  # 電網最大輸出功率

    def provide_power(self, load_demand):
        if load_demand <= self.max_output_power:
            # print(f"電網提供功率：{load_demand}")
            return load_demand
        else:
            # print(f"電網提供功率：{self.max_output_power}")
            return self.max_output_power


class ESS:
    def __init__(self, tou):
        self.battery_max_capacity = 1500 * kWh
        self.battery_charge_limit = 0.9 * self.battery_max_capacity
        self.battery_discharge_limit = 0.1 * self.battery_max_capacity
        self.current_battery = 800 * kWh
        self.required_charging_capacity = self.battery_charge_limit - self.current_battery

        self.current_soc = self.current_battery / self.battery_max_capacity
        self.target_soc = self.battery_charge_limit / self.battery_max_capacity

        self.charging_limit = 250 * 1000  # 儲能系統最大充電功率
        self.discharging_limit = 250 * 1000  # 儲能系統最大放電功率

        self.charging_capacity = 0
        self.discharging_capacity = 0
        self.discharging_time = 7

        self.tou = tou
        
        self.start_charge_time = datetime(self.tou.current_time.year, 
                                            self.tou.current_time.month, 
                                            self.tou.current_time.day, 6, 0, 0)      # 6點開始充電
        self.end_charge_time = datetime(self.tou.current_time.year, 
                                            self.tou.current_time.month, 
                                            self.tou.current_time.day, 16, 0, 0) if self.tou.if_summer() else \
                                datetime(self.tou.current_time.year, 
                                            self.tou.current_time.month, 
                                            self.tou.current_time.day, 15, 0, 0)       # 尖峰開始時間

        # self.start_discharge_time = datetime(self.tou.current_time.year, 
        #                                     self.tou.current_time.month, 
        #                                     self.tou.current_time.day, 22, 0, 0)  # 22點開始放電
        self.end_discharge_time = datetime(self.tou.current_time.year, 
                                    self.tou.current_time.month, 
                                    self.tou.current_time.day, 5, 0, 0) + relativedelta(days=1) 

        self.ess_state = 0  # 0:不動作 1:充電 2:放電

    def update_ess_end_time(self):
        self.end_charge_time = datetime(self.tou.current_time.year, 
                                            self.tou.current_time.month, 
                                            self.tou.current_time.day, 16, 0, 0) if self.tou.if_summer() else \
                                datetime(self.tou.current_time.year, 
                                            self.tou.current_time.month, 
                                            self.tou.current_time.day, 15, 0, 0)       # 尖峰開始時間
        self.end_discharge_time = datetime(self.tou.current_time.year,
                                            self.tou.current_time.month,
                                            self.tou.current_time.day, 5, 0, 0) + relativedelta(days=1)

    def calculate_charge_power(self):
        charge_duration = (self.end_charge_time - self.tou.current_time).total_seconds() 
        print(f"當前電量：{self.current_battery}，目標電量：{self.battery_charge_limit}，充電時間：{charge_duration / time_cycle}小時")
        self.charging_capacity = (self.battery_charge_limit - self.current_battery) / (charge_duration / time_cycle)
        return self.charging_capacity
        
    def charging_battery(self, charging_power):
        # self.tou = TOU(current_time)
        self.tou_state = self.tou.get_tou()[0]

        # 判斷電池是否可以充電
        if self.tou_state == "尖峰":
            #  尖峰時段不充電
            print("目前是尖峰時段，儲能系統不充電。")
            return (self.current_battery, self.current_soc)
        
        elif self.tou_state == "離峰" and self.start_charge_time <= self.tou.current_time < self.end_charge_time:
            # 離峰時段且為充電時間
            if self.current_battery < self.battery_charge_limit:
                # 電池未充飽
                self.current_battery = min(self.current_battery + charging_power, self.battery_charge_limit)
                self.current_soc = self.current_battery / self.battery_max_capacity
                print(f"儲能系統充電中，目前電量：{round(self.current_battery, 2)}，目前SOC：{self.current_soc}")
                return (self.current_battery, self.current_soc)
            else:
                # 電池已充飽
                print("儲能系統已充飽，不再充電。")
                return (self.current_battery, self.current_soc)
        else:
            # 非充電時段
            print("非充電時段，儲能系統不充電。")
            return (self.current_battery, self.current_soc)

    def calculate_discharge_power(self):
        discharge_duration = (self.end_discharge_time - self.tou.current_time).total_seconds() 
        print(f"當前電量：{self.current_battery}，目標電量：{self.battery_discharge_limit}，放電時間：{discharge_duration / time_cycle}小時")
        self.discharging_capacity = (self.current_battery - self.battery_discharge_limit) / (discharge_duration / time_cycle)
        return self.discharging_capacity
    
    def discharging_battery(self, discharging_power):
        if self.current_battery <= self.battery_discharge_limit:
            print("電池電量不足，無法提供電力。")
            print(f"儲能系統當前SOC：{self.current_soc}")
            return 0, 0, 0
        else:
            if discharging_power <= (self.current_battery - self.battery_discharge_limit):
                provided_power = min(discharging_power, self.discharging_limit)
                print(f"儲能系統提供電力：{provided_power}")
                self.current_battery -= provided_power
                self.current_soc = self.current_battery / self.battery_max_capacity
                return self.current_battery, self.current_soc, provided_power
            else:
                print(f"儲能系統提供電力：{self.current_battery - self.battery_discharge_limit}")
                self.current_battery = self.battery_discharge_limit
                self.current_soc = self.current_battery / self.battery_max_capacity
                return self.current_battery, self.current_soc, (self.current_battery - self.battery_discharge_limit)

tou = TOU(datetime(2023, 5, 31, 22, 0, 0))
grid = Grid()
ess = ESS(tou)

time = datetime(2023, 5, 31, 22, 0, 0)

while time < datetime(2023, 6, 1, 16, 0, 0):
    tou.current_time = time
    ess.update_ess_end_time()

    print(f"當前時間：{time}")
    print(f"結束充電時間：{ess.end_charge_time}")
    # charge_power = ess.calculate_charge_power()
    # ess.charging_battery(charge_power)
    # discharge_power = ess.calculate_discharge_power()
    # ess.discharging_battery(discharge_power)

    time += timedelta(seconds=time_cycle)