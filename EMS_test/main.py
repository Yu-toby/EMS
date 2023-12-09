import pymongo
import pandas as pd
from pymongo import UpdateOne
import datetime
from collections import deque
from numba import jit

client = pymongo.MongoClient("mongodb://localhost:27017/") # mongodb://xx:xx@localhost:27017/
db= client["shihlin"]

class tou:
    def __init__(self):
        tou_data = db["tou"].find_one({"name":"TOU"})
        self.peak_start = tou_data["peak_start"]
        self.peak_end = tou_data["peak_end"]
        self.peak_price = tou_data["peak_price"]
        self.off_peak_price = tou_data["off_peak_price"]
    
    def get_price(self, time):
        if time.hour >= self.peak_start and time.hour < self.peak_end:
            return self.peak_price
        else:
            return self.off_peak_price
    
class ess:
    def __init__(self):
        ess_data = db["ess"].find_one({"name":"ESS"})
        self.capacity = ess_data["capacity"]
        self.soc_max = ess_data["soc_max"]
        self.soc_min = ess_data["soc_min"]
        self.soc_now = ess_data["soc_now"]
        self.power_limit = ess_data["power_limit"]
        
        self.power = 0
        
        self.output = []
        self.info = {"receive":0, "provide":0}
        
        self.status = False
    def soc_calculate(self):
        capacity = (0.01*self.soc_now*self.capacity) + self.power*(30/3600)
        self.soc_now = (capacity / self.capacity) * 100
        
    def mongo_update(self, time):
        db.output.update_one(
                                {"time":time, "name": "ESS"}, 
                                {"$set":{"power":self.power,"soc_now":self.soc_now,}},
                                upsert=True
                            )
        
        # status = True if self.soc_now > self.soc_min else False
        db.ess.update_one(
                            {"name":"ESS"},
                            {
                                "$set":{"soc_now":self.soc_now},
                                "$inc":{ 
                                        "receive":self.power*(30/3600) if self.power > 0 else 0,
                                        "provide":self.power*(30/3600) if self.power < 0 else 0,
                                    }
                            }
                        )
    
    def update_info(self, time):
        self.info["receive"] += self.power*(30/3600) if self.power > 0 else 0
        self.info["provide"] += self.power*(30/3600) if self.power < 0 else 0
        
        self.output.append({"time":time, "power":self.power, "soc_now":self.soc_now, "name":"ESS"})

class pv:
    def __init__(self, path):
        pv_data = db["pv"].find_one({"name":"PV"})
        
        self.provide_pcs = pv_data["provide_pcs"]
        self.provide_ess = pv_data["provide_ess"]
        
        self.cost = pv_data["cost"]
        self.capacity = pv_data["capacity"]
        
        self.df = pd.read_csv(path)
        self.df["datetime"] = pd.to_datetime(self.df["datetime"])
        self.index = self.df["datetime"]
        
        self.power = 0
        
        self.power_history = deque(maxlen=30)
        
        self.ess_power = 0
        self.smoothed_power = 0
        
        self.output = []
        self.info = {"provide_pcs":0, "provide_ess":0, "price":0}
        
        self.converter_number = 3
        self.converter_number_now = 3
        
        self.converter_power = 0
        
        self.status = False
        
    def get_pv(self, time):
        self.power = self.df.loc[self.df["datetime"]==time, "p"].values[0]
        # self.power = 0
        total_power = 895.44*self.power/831.6 if self.power > 0.15 else 0
        self.converter_power = total_power/self.converter_number
        
        self.power = self.converter_power*self.converter_number_now
        
        self.power_history.append(self.power)
        
    def pv_smooth(self):
        smoothed_power = sum(self.power_history)/len(self.power_history)
        self.smoothed_power = smoothed_power

        
    def mongo_update(self, pcs_power, ess_power):
        
        provide_pcs = 0
        provide_ess = 0
        
        if self.power > 0:
            if ess_power == 0:
                provide_pcs = self.power
                provide_ess = 0
            elif ess_power > 0:
                if pcs_power == 0:
                    provide_pcs = 0
                    provide_ess = ess_power
                
                elif pcs_power > 0:
                    provide_pcs = self.power - ess_power
                    provide_ess = ess_power
            else:
                provide_pcs = self.power
                        
            db.pv.update_one(
                                {"name":"PV"}, 
                                {
                                    "$inc":{
                                            "provide_pcs":provide_pcs*(30/3600),
                                            "provide_ess":provide_ess*(30/3600),
                                            # "price":provide_grid*self.price_of_grid*(30/3600)
                                                }
                                    }
                            )
    def update_info(self, pcs_power, ess_power):
        provide_pcs = 0
        provide_ess = 0
        
        if self.power > 0:
            if ess_power == 0:
                provide_pcs = self.power
                provide_ess = 0
            elif ess_power > 0:
                if pcs_power == 0:
                    provide_pcs = 0
                    provide_ess = ess_power
                
                elif pcs_power > 0:
                    provide_pcs = self.power - ess_power
                    provide_ess = ess_power
            else:
                provide_pcs = self.power
            
            self.info["provide_pcs"] += provide_pcs*(30/3600)
            self.info["provide_ess"] += provide_ess*(30/3600)
            # self.info["price"] += provide_grid*self.price_of_grid*(30/3600)
        self.output.append({"time":time, "power":self.power, "name":"PV"})

class pcs:
    def __init__(self):        
        pcs_data = db["pcs"].find_one({"name":"PCS"})
        self.capacity = pcs_data["capacity"]
        
        self.power = 0
        self.power_history = deque(maxlen=60)
        
        self.power_avg_30min = 0
        
        self.output = []
        self.info = {"receive":0, "provide":0}
        
    def update_info(self, time):
        self.info["receive"] += self.power*(30/3600) if self.power < 0 else 0
        self.info["provide"] += self.power*(30/3600) if self.power > 0 else 0
        
        self.output.append({"time":time, "power":self.power, "name":"PCS"})

        self.power_history.append(self.power)
        
        self.power_avg_30min = sum(self.power_history)/len(self.power_history)
        
class load:
    def __init__(self, path):
        load_data = db["load"].find_one({"name":"Load"})
        
        self.df = pd.read_csv(path)
        self.df["datetime"] = pd.to_datetime(self.df["datetime"])
        self.index = self.df["datetime"]
        
        self.power = 0
        self.power_history_5min = deque(maxlen=10)
        self.power_history_15min = deque(maxlen=30)
        self.power_history_30min = deque(maxlen=60)
        
        self.power_avg_5min = 0
        self.power_avg_15min = 0
        self.power_avg_30min = 0
    
    def get_load(self, time):
        self.power = self.df.loc[self.df["datetime"]==time, "p"].values[0]
        self.power_history_5min.append(self.power)
        self.power_history_15min.append(self.power)
        self.power_history_30min.append(self.power)
        
        self.power_avg_5min = sum(self.power_history_5min)/len(self.power_history_5min)
        self.power_avg_15min = sum(self.power_history_15min)/len(self.power_history_15min)
        self.power_avg_30min = sum(self.power_history_30min)/len(self.power_history_30min)
            
class grid:
    def __init__(self):
        grid_data = db["grid"].find_one({"name":"Grid"})
        self.capacity = grid_data["capacity"]
        
        self.power = 0
        self.power_history_5min = deque(maxlen=10)
        self.power_history_15min = deque(maxlen=30)
        self.power_history_30min = deque(maxlen=60)
        
        self.power_avg_5min = 0
        self.power_avg_15min = 0
        self.power_avg_30min = 0
        
        self.output = []
        self.info = {"provide":0, "price":0}
        
    def mongo_update(self, time, tou = tou()):
        db.output.update_one(
                                {"time":time, "name": "Grid"}, 
                                {"$set":{"power":self.power}},
                                upsert=True
                            )
        
        price = self.power * tou.get_price(time) * (30/3600)
        
        db.grid.update_one(
                            {"name":"Grid"},
                            {
                                "$inc":{
                                        "provide":self.power*(30/3600) if self.power < 0 else 0,
                                        "price":-1*price if self.power < 0 else 0,
                                        }
                            }
                        )
    
    def update_info(self, time):
        self.output.append({"time":time, "power":self.power, "name":"Grid"})
        
        self.power_history_5min.append(self.power)
        self.power_history_15min.append(self.power)
        self.power_history_30min.append(self.power)
        
        self.power_avg_5min = sum(self.power_history_5min)/len(self.power_history_5min)
        self.power_avg_15min = sum(self.power_history_15min)/len(self.power_history_15min)
        self.power_avg_30min = sum(self.power_history_30min)/len(self.power_history_30min)
        
        # price = self.power * tou.get_price(time) * (30/3600)
        self.info["provide"] += self.power*(30/3600) if self.power > 0 else 0
        # self.info["price"] += -1*price if self.power < 0 else 0


        
# @jit(nopython=True)        
def control_strategy(time, load, tou, pv, grid, ess, pcs):

    SOC_PERCENTAGE_FACTOR = 0.01
    SECONDS_PER_HOUR = 3600
    SECONDS_PER_MINUTE = 60
    
    def calculate_delta_time(current_hour, current_minute, current_second, target_hour):    # 計算時間差，回傳秒數
        if current_hour >= target_hour:
            delta_hours = 24 - current_hour + target_hour - 1
        else:
            delta_hours = target_hour - current_hour - 1

        delta_minutes = 60 - current_minute
        delta_seconds = 60 - current_second
        
        return delta_hours * SECONDS_PER_HOUR + delta_minutes * SECONDS_PER_MINUTE + delta_seconds
    
    def calculate_delta_power(target_hour = 5, soc = None):
        
        if soc is None:
            soc = ess.soc_max
        delta_soc = (soc - ess.soc_now)*SOC_PERCENTAGE_FACTOR
        delta_capacity = delta_soc * ess.capacity
        delta_time = calculate_delta_time(time.hour, time.minute, time.second, target_hour)
        # print(min(delta_capacity / (delta_time/3600), ess.power_limit))
        return min(delta_capacity / (delta_time/3600), ess.power_limit)
    
    def turnoff_converter():
        pv.converter_number_now = pv.converter_number_now - 1 if pv.converter_number_now > 0 else 0
        pv.power = pv.converter_number_now*pv.power/pv.converter_number
        
        pv.power_history = deque(maxlen=30)
        pv.smoothed_power = pv.power
    
    def calculate_pcs_power(h = 80, l = 60, p = 20, load_i = 1):
        
        if ess.soc_now >= h:
            pi = 1 + (ess.soc_now - h)/p
            # pi = min(1.2, pi)
        else:
            pi = 1 - (l - ess.soc_now)/p
            # pi = max(0.8, pi)
        
        # print(pi*load_i*load_j)
        # print(pi, load_i)
        pcs.power = pv.smoothed_power * pi * load_i
        pcs.power = min(load.power_avg_5min*0.9, pcs.power)
        pcs.power = pcs.power if pcs.power > 0 else 0
    
    def smoothed_ess_power():
        ess.power = pv.power - pcs.power
            
    current_hour = time.hour
    current_minute = time.minute
    current_second = time.second
    control_step = 10
    # print("current_hour", current_hour)
    # for ev_object in evcs.ev_objects.values():
    
    if pv.power > 0: #!棄光保護
        
        if pv.power > load.power * 0.9 and ess.soc_now >= ess.soc_max:
            
            turnoff_converter()
            pcs.power = pcs.power_avg_30min
            
        elif pv.power <= load.power * 0.8 and ess.soc_now < ess.soc_max and pv.status == True:
            pv.status = False
            calculate_pcs_power()
        
        if pv.status:
            turnoff_converter()
            # print(time, "turn off converter")
            
    if pv.converter_number_now < pv.converter_number and current_minute % control_step == 0 and current_second == 0:
        pv_power = (pv.converter_number_now + 1)*pv.converter_power
        
        if pv_power < load.power*0.7 or ess.soc_now < 80:
            pv.converter_number_now += 1
    # print(current_hour, current_minute, current_minute % 5 == 0, tou.peak_start, tou.peak_end)
    
    # if load.power_avg_5min < 500:
    #     if current_minute % control_step == 0 and current_second == 0:
    #         if pv.power > load.power*0.7:
    #             pcs.power = pcs.power_avg_30min + pcs.capacity*0.1
    #             pcs.power = min(pcs.power, load.power*0.6)
                
    #         elif current_hour >= 15:
    #             ess_delta_power = 0
    #             if ess.soc_now > 20:
    #                 ess_delta_power = calculate_delta_power(target_hour= 24, soc= 20)
                    
    #             if current_minute % control_step == 0 and current_second == 0:
    #                 pcs.power = pv.smoothed_power - 2*ess_delta_power
    #                 if pcs.power > load.power_avg_5min*0.5:
    #                     pcs.power = load.power_avg_5min*0.5
    #                 if pv.smoothed_power > load.power_avg_5min*0.5:
    #                     pcs.power = pv.smoothed_power
    #             smoothed_ess_power()
            
    #         else:
    #             if pv.power > 0:
                    
    #                 pcs.power = pv.smoothed_power
    #                 grid.power = load.power- pcs.power
    #                 grid_i = grid.power/grid.power_avg_15min if grid.power_avg_5min > 0 else 1
                    
    #                 pcs.power = min(load.power*0.6, pcs.power*grid_i)
    #             elif pv.converter_number_now == 0:
    #                 pcs.power = load.power*0.6
            
    #     smoothed_ess_power()
    # else:    
    if current_hour < 7 and current_hour >= tou.peak_end:
        ess.status = False
        if current_minute % control_step == 0 and current_second == 0:
            calculate_pcs_power(90, 90, 10)
        smoothed_ess_power()
    
    elif current_hour >= 7 and current_hour < 9:
        # case1
        load_i = load.power_avg_5min/load.power_avg_15min if load.power_avg_15min > 0 else 1
        if load_i > 1.1 or ess.status == True:
            if ess.status == False:
                print(load_i, grid.power_avg_5min/grid.power_avg_15min)
            
            ess.status = True
            if current_minute % control_step == 0 and current_second == 0:
                # print(ess.soc_now)
                # print(load.power_avg, load.old_power_avg)
                # print("load_i", load_i, "grid_i", grid_i)
                
                load_i = 1.1 if load_i > 1.1 else load_i
                calculate_pcs_power(30, 20, 20, 1)
                grid.power = load.power- pcs.power
                
                grid_i = grid.power/grid.power_avg_15min if grid.power_avg_5min > 0 else 1
                # grid_i = grid.power_avg_5min/grid.power_avg_15min if grid.power_avg_15min > 0 else 1
                
                grid_i = 1.1 if grid_i > 1.1 else grid_i
                
                # print(grid_i)
                pcs.power = pcs.power*grid_i
            smoothed_ess_power()
        # case2
        else:
            ess.status = False
            if current_minute % control_step == 0 and current_second == 0:
                calculate_pcs_power(90, 90, 10)
            smoothed_ess_power()
            
    elif current_hour >= 9 and current_hour < 12:
        ess.status = False
        # case3
        if current_minute % control_step == 0 and current_second == 0:
            pcs.power = pv.smoothed_power
            
            grid.power = load.power- pcs.power
            grid_i = grid.power/grid.power_avg_15min if grid.power_avg_15min > 0 else 1
            grid_i = max(0.95, grid_i)
            
            pcs.power = pcs.power*grid_i
            
        smoothed_ess_power()
    
    elif current_hour >= 12 and current_hour < 14:
        if current_minute % control_step == 0 and current_second == 0:
            
            if ess.soc_now > 80:
                pcs.power = pv.smoothed_power*1.2
            else:
                pcs.power = pv.smoothed_power

            grid.power = load.power- pcs.power
            grid_i = grid.power/grid.power_avg_30min if grid.power_avg_15min > 0 else 1
            grid_i = min(1.5, grid_i) if grid_i > 1 else grid_i
            grid_i = max(0.4,grid_i) if grid_i < 1 else grid_i
            
            
            pcs.power = pcs.power*grid_i
                
        smoothed_ess_power()
    
    elif current_hour >= 14 and current_hour < 17 :
        
        if current_minute % control_step == 0 and current_second == 0:
            pcs.power = pcs.power_avg_30min
            
            grid.power = load.power- pcs.power
            grid_i = grid.power/grid.power_avg_30min if grid.power_avg_15min > 0 else 1
            grid_i = min(1.2, grid_i) if grid_i > 1 else grid_i
            grid_i = max(0.6, grid_i) if grid_i < 1 else grid_i
            
            pcs.power = pcs.power*grid_i
            
        smoothed_ess_power()
        # ess_delta_power = 0
        # if ess.soc_now > 20:
        #     ess_delta_power = calculate_delta_power(target_hour= 20, soc= 20)
            
        # if current_minute % control_step == 0 and current_second == 0:
        #     pcs.power = pv.smoothed_power - 2*ess_delta_power
        #     if pcs.power > 300:
        #         pcs.power = 300
        #     if pv.smoothed_power > 300:
        #         pcs.power = pv.smoothed_power
        # smoothed_ess_power()
    
    else:
        # case4
        ess_delta_power = calculate_delta_power(target_hour= 20, soc= 20)
        
        if current_minute % control_step == 0 and current_second == 0:
            pcs.power = -2*ess_delta_power + pv.smoothed_power
            
            grid.power = load.power- pcs.power
            grid_i = grid.power/grid.power_avg_15min if grid.power_avg_15min > 0 else 1
            pcs.power = pcs.power*grid_i
            
        smoothed_ess_power()
        
    grid.power = load.power- pcs.power    


def save_csv(filename, pv, pcs, ess, grid):
    
    df_pv_output = pd.DataFrame(pv.output)
    df_pcs_output = pd.DataFrame(pcs.output)
    df_ess_output = pd.DataFrame(ess.output)
    df_grid_output = pd.DataFrame(grid.output)
    
    df = pd.concat([df_pv_output, df_pcs_output, df_ess_output, df_grid_output], ignore_index=True)

    df.to_csv("./data/"+filename, index=False)
        
    # db.ess.update_one({"name":"ESS"}, {"$set": ess.info})
    # db.pv.update_one({"name":"PV"}, {"$set": pv.info})
    # db.grid.update_one({"name":"Grid"}, {"$set": grid.info})
        
    # ess = db.ess.find_one({"name": "ESS"})
    # pv = db.pv.find_one({"name": "PV"})
    # grid = db.grid.find_one({"name": "Grid"})
    # tou = db.tou.find_one({"name": "TOU"})

    # ev = list(db.equipment.find({}))

    # df_ess = pd.DataFrame(ess, index=[0]) if isinstance(ess, dict) else pd.DataFrame(ess)
    # df_pv = pd.DataFrame(pv, index=[0]) if isinstance(pv, dict) else pd.DataFrame(pv)
    # df_grid = pd.DataFrame(grid, index=[0]) if isinstance(grid, dict) else pd.DataFrame(grid)
    # df_tou = pd.DataFrame(tou, index=[0]) if isinstance(tou, dict) else pd.DataFrame(tou)
    # df_ev = [pd.DataFrame(e, index=[0]) if isinstance(e, dict) else pd.DataFrame(e) for e in ev]

    # # 確保 ess, pv, grid, ev, tou 是 DataFrame 的列表，並使用 pd.concat() 結合
    # df = pd.concat([df_ess, df_pv, df_grid] + df_ev + [df_tou], ignore_index=True)

    # df = df.drop(columns=["_id", "soc_min", "soc_max", "soc_now", "status"])
    # # print(df)

    # df.to_csv('./info/'+filename, index=False)

        
if __name__ == "__main__":
    
    pv = pv("./pv_04.csv")
    pcs = pcs()
    grid = grid()
    ess = ess()
    load = load("./load_04_30.csv")
    tou = tou()
    
    
    # pv.__init__("./pv_04.csv")
    # grid.__init__()
    # ess.__init__()

    # tou.__init__()
    
    time = datetime.datetime(2023, 4, 20, 0, 0, 0)
    
    while time < datetime.datetime(2023, 4, 22, 0, 00, 00):
        # print(time)
        pv.get_pv(time)
        pv.pv_smooth()
        
        load.get_load(time)
        
        control_strategy(time, load, tou, pv, grid, ess, pcs)
        
        ess.soc_calculate()
        
        ess.update_info(time = time)
        pcs.update_info(time = time)
        pv.update_info(pcs_power=pcs.power, ess_power=ess.power)
        grid.update_info(time = time)
        
        
        time += datetime.timedelta(seconds=30)
    
    save_csv('test.csv', pv, pcs, ess, grid)
        
    
