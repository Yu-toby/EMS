from datetime import datetime
import matplotlib.pyplot as plt

from pymongo import MongoClient

kWh = 1000  # 1kWh = 1000度電

# 連接 MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['E_Bus']
evcs_collection = db['EVCS']
ev_collection = db['EV']
ess_collection = db['ESS']
grid_collection = db['Grid']
tou_collection = db['TOU']


class EVCS:
    def __init__(self):    
        self.pile_number = evcs_collection.distinct('pile_number')

    def add_ev(self, ev):
        # 逐一搜尋 MongoDB 集合中的每一個 gun
        for pile_num in self.pile_number:
            pile_query = {'pile_number': pile_num}
            pile_data = evcs_collection.find_one(pile_query)

            if pile_data:
                guns = pile_data.get('gun', [])

                # 逐一檢查每個 gun 的 ev_number
                for gun in guns:
                    if gun['ev_number'] == 0:
                        # 如果 ev_number 為空，則填入要添加的 EV 資料
                        gun['ev_number'] = ev.number
                        gun['charging_power'] = 0  # 預設充電功率
                        gun['start_time'] = ev.charge_start_time
                        gun['already_time'] = 0  # 預設已充電時間

                        # 更新 MongoDB 集合中的資料
                        evcs_collection.update_one(pile_query, {'$set': {'gun': guns}})
                        return  # 結束函式，已找到並填入 EV 資料
                    
                    elif gun['ev_number'] == ev.number:
                        print('該車編號已存在，請確認是否有誤')
                        return  # 結束函式，已找到並填入 EV 資料
                    
                    else:
                        # 如果 ev_number 不為空，則檢查下一個 gun
                        continue
    
    def delete_ev(self, ev):
        # 逐一搜尋 MongoDB 集合中的每一個 gun
        for pile_num in self.pile_number:
            pile_query = {'pile_number': pile_num}
            pile_data = evcs_collection.find_one(pile_query)

            if pile_data:
                guns = pile_data.get('gun', [])

                # 逐一檢查每個 gun 的 ev_number
                for gun in guns:
                    if gun['ev_number'] == ev.number:
                        # 如果 ev_number 為要刪除的 EV 資料，則清空 gun 資料
                        gun['ev_number'] = 0    
                        gun['charging_power'] = 0  
                        gun['start_time'] = 0
                        gun['already_time'] = 0  

                        # 更新 MongoDB 集合中的資料
                        evcs_collection.update_one(pile_query, {'$set': {'gun': guns}})
                        return  # 結束函式，已找到並刪除 EV 資料
                    
                    else:
                        # 如果 ev_number 不為要刪除的 EV 資料，則檢查下一個 gun
                        continue
    
    def update_ev(self, ev):
        # 逐一搜尋 MongoDB 集合中的每一個 gun
        for pile_num in self.pile_number:
            pile_query = {'pile_number': pile_num}
            pile_data = evcs_collection.find_one(pile_query)

            if pile_data:
                guns = pile_data.get('gun', [])

                # 逐一檢查每個 gun 的 ev_number
                for gun in guns:
                    if gun['ev_number'] == ev.number:
                        # 如果 ev_number 為要更新的 EV 資料，則更新 gun 資料
                        gun['charging_power'] = ev.now_power
                        gun['start_time'] = ev.charge_start_time
                        gun['already_time'] = ev.charge_already_time

                        # 更新 MongoDB 集合中的資料
                        evcs_collection.update_one(pile_query, {'$set': {'gun': guns}})
                        return  # 結束函式，已找到並更新 EV 資料


class EV:
    def __init__(self, number, target_SOC, now_SOC, power_limit, charge_start_time, charge_end_time):
        # 電動車參數
        self.number = number
        self.battery_max_capacity = 300 * 1000  # 假設單位是kWh
        self.target_SOC = target_SOC
        self.now_SOC = now_SOC
        self.now_power = now_SOC * self.battery_max_capacity
        self.power_limit = power_limit
        self.charge_start_time = charge_start_time
        self.charge_end_time = charge_end_time
        self.charge_time = self.charge_end_time - self.charge_start_time
        self.charge_already_time = 0
        self.charge_pi = 0  # 倍分配充電係數
        self.pile_number = None  # 車輛連接的充電樁編號

    def calculate_charge_power(self, already_time):
        # 計算每小時所需充電功率
        self.charge_already_time = already_time
        if self.charge_already_time < self.charge_time:
            remaining_time = self.charge_time - self.charge_already_time
            charge_soc_per_second = (
                self.target_SOC - self.now_SOC) / remaining_time
            charge_power_per_second = charge_soc_per_second * self.battery_max_capacity
        else:
            charge_power_per_second = 0
            charge_soc_per_second = 0
        
        return charge_power_per_second, charge_soc_per_second
    
    def save_to_mongodb(self):
        ev_data = {
            'number': self.number,
            'battery_max_capacity': self.battery_max_capacity,
            'target_SOC': self.target_SOC,
            'now_SOC': self.now_SOC,
            'now_power': self.now_power,
            'power_limit': self.power_limit,
            'charge_start_time': self.charge_start_time,
            'charge_end_time': self.charge_end_time,
            'charge_already_time': self.charge_already_time,
            'charge_pi': self.charge_pi,
            'pile_number': self.pile_number
        }
        ev_collection.insert_one(ev_data)


evcs = EVCS()
ev1 = EV(1, 0.8, 0.2, 50, 7, 11)
ev1.save_to_mongodb()
evcs.add_ev(ev1)
# ev2 = EV(2, 0.9, 0.25, 60, 17, 20)
# ev2.save_to_mongodb()