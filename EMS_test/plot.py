

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import plotly.figure_factory as ff

def load_data(filename):
    df = pd.read_csv(filename)
    # df_pv = pd.read_csv("./pv_04.csv")
    
    df.index = pd.to_datetime(df["datetime"])
    # df_pv.index = pd.to_datetime(df_pv["datetime"])
    
    # df_pv['p'] = 895.44*df_pv['p']/831.6
    # df_pv['pv_2'] = 1605.32*df_pv['p']/895.44
    
    # print(df["p"].max())
    # print(df_pv["p"].max())
    
    fig = make_subplots( rows=1, cols=1,shared_xaxes=True, vertical_spacing=0.02)
    
    
    fig.add_trace(go.Scatter(x=df.index, y = df["p"], name= "power"),row=1,col=1)
    # fig.add_trace(go.Scatter(x=df_pv.index, y = df_pv["p"], name= "pv_power"),row=1,col=1)
    # fig.add_trace(go.Scatter(x=df_pv.index, y = df_pv["pv_2"], name= "pv_power"),row=1,col=1)
    
    fig.add_shape(
        type="line",
        x0=min(fig.data[0].x),
        y0=1500,
        x1=max(fig.data[0].x),
        y1=1500,
        line=dict(
            color="Red",
            width=2,
            dash="dashdot",
        ),
    )
    
    fig.show()

def system_info(filename):
    
    start_time = "2023-04-20 00:00:00"
    end_time = "2023-04-22 00:00:00"
    
    df_pv = pd.read_csv("./pv_04.csv")
    df_pv.index = pd.to_datetime(df_pv["datetime"])
    df_pv = df_pv[(df_pv.index > start_time) & (df_pv.index < end_time)]
    df_pv['p'] = 895.44*df_pv['p']/831.6
    # df_pv = df_pv[(df_pv.index > "2023-01-21 00:00:00") & (df_pv.index < "2023-01-28 00:00:00")]
    print(df_pv.head())
    
    df_load = pd.read_csv("./load_04_30.csv")
    df_load.index = pd.to_datetime(df_load["datetime"])
    df_load = df_load[(df_load.index > start_time) & (df_load.index < end_time)]
    
    df_sys = pd.read_csv('./data/' + filename)
    df_sys.index = pd.to_datetime(df_sys["time"])
    
    df_sys = df_sys[(df_sys.index > start_time) & (df_sys.index < end_time)]
    
    df_pv_control = df_sys[(df_sys["name"]=="PV")]
    df_ess = df_sys[(df_sys["name"]=="ESS")]
    df_grid = df_sys[(df_sys["name"]=="Grid")]
    df_pcs = df_sys[(df_sys["name"]=="PCS")]
            
    fig = make_subplots(
                        rows=2, cols=1,shared_xaxes=True,
                        vertical_spacing=0.02, row_heights=[0.8, 0.2]
                        )
    
    fig.add_trace(go.Scatter(x=df_pv.index, y = df_pv["p"], name= "PV_power"),row=1,col=1)
    fig.add_trace(go.Scatter(x=df_load.index, y = df_pv_control["power"], name= "PV_CTRL"),row=1,col=1)
    
    fig.add_trace(go.Scatter(x=df_pv.index, y = df_ess["power"],name="ESS_power"),row=1,col=1)
    
    fig.add_trace(go.Scatter(x=df_pv.index, y = df_pcs["power"], name="PCS_power"),row=1,col=1)
    
    fig.add_trace(go.Scatter(x=df_pv.index, y = df_grid["power"], name="Grid_power"),row=1,col=1)
    
    fig.add_trace(go.Scatter(x=df_pv.index, y = df_load["p"], name="Load_power"),row=1,col=1)
    
    fig.add_trace(go.Scatter(x=df_pv.index, y = df_ess["soc_now"], name="ESS_SOC"),row=2,col=1)

    # fig.add_trace(go.Scatter(x=df_pv.index, y=df_ess["soc_now"], name="ESS_SOC"), row=5, col=1)
    #fig.add_trace(go.Scatter(x=df["time"], y=df["SOC"],mode="markers"), row=3, col=1)
    #fig.add_trace(go.Scatter(x=df["time"], y=df["power"]), row=2, col=1)
    #fig.add_trace(go.Scatter(x=df["time"], y=df["case"]), row=1, col=1)
    
    fig.update_yaxes(title_text="power", row=1, col=1)
    fig.update_yaxes(title_text="SOC", row=2, col=1)
    # fig.update_yaxes(title_text="ESS_SOC", row=5, col=1)
    #set title
    fig.update_layout(title_text="控制策略優化", title_x=0.5)
    
    fig.add_shape(
        type="line",
        x0=min(fig.data[0].x),
        y0=1500,
        x1=max(fig.data[0].x),
        y1=1500,
        line=dict(
            color="Red",
            width=2,
            dash="dashdot",
        ),
    )
    
    fig.show()

def system_info_evcs():

    fig = make_subplots(
                        rows=1, cols=1,shared_xaxes=True,
                        vertical_spacing=0.02
                        )
    
    # df_sys = pd.read_csv("./data/沒改善尖離峰1.csv")
    # df_sys.index = pd.to_datetime(df_sys["datetime"])
    # df_sys = df_sys[(df_sys.index > "2022-07-02 00:00:00") & (df_sys.index < "2022-07-03 00:00:00")] 
    # fig.add_trace(go.Scatter(x=[i for i in range(len(df_sys))], y = df_sys["EVCS_power"], name="沒改善尖離峰", line=dict(width = 4)),row=1,col=1)
    
    
    # df_sys = pd.read_csv('./data/summer_499.csv')
    # df_sys.index = pd.to_datetime(df_sys["time"])
    # # df_sys = df_sys[(df_sys.index > "2023-01-02 00:00:00") & (df_sys.index < "2023-01-03 00:00:00")] 
    # df_sys = df_sys[(df_sys.index > "2022-07-02 00:00:00") & (df_sys.index < "2022-07-03 00:00:00")]
    # df_evcs = df_sys[(df_sys["name"]=="EVCS")]
    # fig.add_trace(go.Scatter(x=[i for i in range(len(df_evcs))], y = df_evcs["power"], name="本文能源管理策略 夏月",line=dict(width = 4, color = "red")),row=1,col=1)

    df_sys = pd.read_csv('./data/winter_499_000.csv')
    df_sys.index = pd.to_datetime(df_sys["time"])
    df_sys = df_sys[(df_sys.index > "2023-01-02 00:00:00") & (df_sys.index < "2023-01-03 00:00:00")] 
    # df_sys = df_sys[(df_sys.index > "2022-07-02 00:00:00") & (df_sys.index < "2022-07-03 00:00:00")]
    df_evcs = df_sys[(df_sys["name"]=="EVCS")]
    fig.add_trace(go.Scatter(x=[i for i in range(len(df_evcs))], y = df_evcs["power"], name="本文能源管理策略 非夏月",line=dict(width = 4)),row=1,col=1)
    
    
    df_sys = pd.read_csv('./data/winter_499.csv')
    df_sys.index = pd.to_datetime(df_sys["time"])
    df_sys = df_sys[(df_sys.index > "2023-01-02 00:00:00") & (df_sys.index < "2023-01-03 00:00:00")] 
    # df_sys = df_sys[(df_sys.index > "2022-07-02 00:00:00") & (df_sys.index < "2022-07-03 00:00:00")]
    df_evcs = df_sys[(df_sys["name"]=="EVCS")]
    fig.add_trace(go.Scatter(x=[i for i in range(len(df_evcs))], y = df_evcs["power"], name="本文能源管理策略 非夏月",line=dict(width = 4, color = "green")),row=1,col=1)
    # # fig.add_trace(go.Scatter(x=df_sys.index, y = df_sys["Grid_power"], name="Grid_power"),row=1,col=1)
    

    #fig.add_trace(go.Scatter(x=df["time"], y=df["SOC"],mode="markers"), row=3, col=1)
    #fig.add_trace(go.Scatter(x=df["time"], y=df["power"]), row=2, col=1)
    #fig.add_trace(go.Scatter(x=df["time"], y=df["case"]), row=1, col=1)
    
    # fig.update_yaxes(title_text="Grid", row=1, col=1)
    fig.update_yaxes(title_text="EVCS", row=1, col=1)
    
    fig.update_layout(title_text="沒改善尖離峰", title_x=0.5)

    fig.show()

def evcs_compare():
    df_1 = pd.read_csv("./data/only_evcs.csv")
    df_2 = pd.read_csv("./data/test.csv")
    
    df_1 = df_1[:5760]
    df_2 = df_2[:5760]
    
    df_2 = df_2[(df_2["name"]=="EVCS")]
    
    fig = make_subplots(
                        rows=1, cols=1,shared_xaxes=True,
    )
    
    fig.add_trace(go.Scatter(x=[i for i in range(5760)], y = df_1["EVCS_power"], name="EVCS"),row=1,col=1)
    # fig.add_trace(go.Scatter(x=[i for i in range(5760)], y = df_2["power"], name="EVCS"),row=2,col=1)
    
    fig.show()
    
def EV_info():
    fig_total = make_subplots(
                        rows=2, cols=1,shared_xaxes=True,
                        vertical_spacing=0.02
                        )
    df = pd.read_csv("./evcs_1.csv")
    for i in range(1,9):
        fig = make_subplots(
                        rows=2, cols=1,shared_xaxes=True,
                        vertical_spacing=0.02
                        )
        df_1 = df[df["ev"] == "EV"+str(i)]
        # print(df_1.head())
        fig.add_trace(go.Scatter(x=df_1["time"], y = df_1["power"], name="EV"+str(i)+"_power"),row=1,col=1)
        fig.add_trace(go.Scatter(x=df_1["time"], y = df_1["soc_now"],name="EV"+str(i)+"_SOC"),row=2,col=1)
        
        fig_total.add_trace(go.Scatter(x=df_1["time"], y = df_1["power"], name="EV"+str(i)+"_power"),row=1,col=1)
        fig_total.add_trace(go.Scatter(x=df_1["time"], y = df_1["soc_now"],name="EV"+str(i)+"_SOC"),row=2,col=1)
        
        fig.show()
    fig_total.show()
    """fig = make_subplots(
                        rows=10, cols=1,shared_xaxes=True,
                        vertical_spacing=0.02
                        )
    for i in range(1,11):
        df = pd.read_csv(path+"EV"+str(i)+".csv")
        fig.add_trace(go.Scatter(x=df_1["time"], y = df["case"],name="EV"+str(i)+"_case"),row=i,col=1)
    fig.show()"""
    
# "capacity":831.6
def pv_info():
    df_pv = pd.read_csv("./pv_04.csv")
    fig = make_subplots(
                        rows=1, cols=1,shared_xaxes=True,
                        vertical_spacing=0.02
                        )
    fig.add_trace(go.Scatter(x=df_pv["datetime"], y = df_pv["p"], name= "power"),row=1,col=1)
    fig.show()
    

def capacity_price():
    capacity = ["250kW", "300kW", "400kW", "499kW", "499kW_充電站"]
    price = [227133.33, 225447.41, 221989.43, 218564.03, 181111.1]
    
    colors = ["rgb(127, 196, 245)"] * 5
    colors[4] = "rgb(255, 207, 77)"
    colors[0] = "rgb(252, 71, 80)"
    
    fig = make_subplots( rows=1, cols=1,shared_xaxes=True, vertical_spacing=0.02)
    fig.add_trace(go.Bar(x=capacity, y=price, text=price, marker = dict(color = colors),name="收入"),row=1,col=1)
    
    fig.update_xaxes(title_text="契約容量", row=1, col=1)
    fig.update_yaxes(title_text="淨收入", row=1, col=1)
    fig.update_layout(title_text="非夏月各契約容量淨收入關係圖 2023/01", title_x=0.5)
    
    fig.show()

def grid_compare():
    
    start_time = "2023-04-10 00:00:00"
    end_time = "2023-04-12 00:00:00"
    
    df_1 = pd.read_csv("./data/test.csv")
    df_2 = pd.read_csv("./data/test_0710.csv")
    
    df_1.index = pd.to_datetime(df_1["time"])
    df_1 = df_1[(df_1.index > start_time) & (df_1.index < end_time)]
    
    df_2.index = pd.to_datetime(df_2["time"])
    df_2 = df_2[(df_2.index > start_time) & (df_2.index < end_time)]
    
    fig = make_subplots(
                        rows=1, cols=1,shared_xaxes=True,
                        vertical_spacing=0.02
                        )
    fig.add_trace(go.Scatter(x=df_1.index, y = df_1[(df_1["name"]=="Grid")]["power"], name= "能源管理策略優化", line=dict(color="orange")),row=1,col=1)
    fig.add_trace(go.Scatter(x=df_2.index, y = df_2[(df_2["name"]=="Grid")]["power"], name= "0710_能源管理", line=dict(color='#6DC0FF')),row=1,col=1)

    fig.update_yaxes(title_text="台電端輸入", row=1, col=1)
    
    fig.show()

# grid_compare()
# capacity_list = [499, 450, 400]#, 350, 300, 250]
capacity_list = [ 200]
#季節
# season_name = "summer"

# for capacity in capacity_list:
#     filename = season_name+"_"+str(capacity)+".csv"
# # # pv_info()

# filename = "summer_250.csv"


system_info('/test.csv')


# system_info_evcs()
# capacity_price()
# EV_info()
# evcs_compare()
# load_data('./load_04_30.csv')
# pv_info()