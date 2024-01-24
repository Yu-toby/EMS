import os
import sys
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import time, timedelta, datetime
import random

# Generate the StartTime, EndTime, StartSoC, EndSoC, CardNumber
# Each bus will appear up to 2 times
# The same bus will not appear in the morning and night

# Function to round time to the nearest quarter hour
def round_time_to_nearest_quarter_hour(t):
    """
    Rounds a datetime.time object to the nearest quarter hour.
    """
    full_datetime = pd.Timestamp.combine(pd.Timestamp.today().date(), t)
    rounded_datetime = full_datetime - timedelta(minutes=full_datetime.minute % 15, seconds=full_datetime.second, microseconds=full_datetime.microsecond)
    return rounded_datetime.time()

# Function to build SoC distribution models for each time slot based on historical data
def build_soc_distribution_models(original_data):
    """
    Build SoC distribution models for each time slot based on historical data.
    """
    time_slots = original_data.groupby(original_data['開始充電時間'].dt.hour)
    distribution_models = {}
    for hour, group in time_slots:
        distribution = group['SoC(開始)'].value_counts(normalize=True)
        distribution_models[hour] = distribution
    return distribution_models

# Function to sample a SoC value based on the given distribution model
def sample_soc_from_distribution(distribution_model):
    """
    Sample a SoC value based on the given distribution model.
    """
    return np.random.choice(distribution_model.index, p=distribution_model.values)

# Function to build time slot distribution model based on historical data
def build_time_slot_distribution_model(original_data):
    """
    Build a model for the distribution of records across different time slots.
    """
    time_slot_distribution = original_data['開始充電時間'].dt.hour.value_counts(normalize=True)
    return time_slot_distribution

# Modified function to generate synthetic charging data
def generate_charging_data(days, original_data, min_records_per_day, max_records_per_day, soc_end_inf, soc_end_sup):
    soc_distribution_models = build_soc_distribution_models(original_data)
    time_slot_distribution_model = build_time_slot_distribution_model(original_data)
    generated_dates = pd.date_range(start=pd.Timestamp.today().date(), periods=days)
    generated_charging_times_start = []
    generated_soc_start = []
    generated_soc_end = []
    generated_charging_times_end = []
    generated_card_names = []

    if max_records_per_day > 30:
        print("Error: max_records cannot exceed 30")
        sys.exit(0)

    for date in generated_dates:
        num_records_today = np.random.randint(min_records_per_day, max_records_per_day + 1)
        records_generated = 0
        number_of_morning = 0
        nuumber_of_night = 0

        number_of_bus = len(original_data['卡片名稱'].unique().tolist())
        cards_before_3pm = original_data['卡片名稱'].unique().tolist()  # Convert to Python list
        cards_after_3pm = original_data['卡片名稱'].unique().tolist()   # Convert to Python list

        while records_generated < num_records_today:
            time_slot = np.random.choice(range(96))
            hour = time_slot // 4
            quarter = (time_slot % 4) * 15
            minute_offset = random.randint(0, 14)  # Add random offset within the time slot

            if hour in soc_distribution_models and np.random.rand() < time_slot_distribution_model.get(hour, 0):
                soc_value = sample_soc_from_distribution(soc_distribution_models[hour])
                soc_random_offset = random.uniform(-5, 5)  # Add random offset to SoC
                soc_value = round(max(0, min(95, soc_value + soc_random_offset)))  # Ensure SoC is within 0-95% and round to the nearest integer

                rounded_time = round_time_to_nearest_quarter_hour(time(hour, quarter + minute_offset))

                if rounded_time <= time(15, 0):
                    if number_of_morning < number_of_bus:
                        generated_charging_times_start.append(pd.Timestamp.combine(date, rounded_time))
                        generated_soc_start.append(soc_value)

                        # Determine end charging time based on start charging time
                        if rounded_time <= time(15, 0):  # If before 15:00
                            start_datetime = datetime(date.year, date.month, date.day, rounded_time.hour, rounded_time.minute)
                            end_time = random.choice(pd.date_range(start_datetime, datetime(date.year, date.month, date.day, 15, 0), freq='15T').tolist())
                        else:  # If after 15:00
                            end_time = random.choice(pd.date_range(datetime(date.year, date.month, date.day, 5, 0), datetime(date.year, date.month, date.day, 5, 30), freq='15T'))

                        # Check if it needs to span to the next day
                        if end_time < pd.Timestamp.combine(date, rounded_time):
                            end_time += timedelta(days=1)
                        generated_charging_times_end.append(end_time)

                        # Depending on the start charging time zone, choose a card
                        if rounded_time < time(15, 0):  # If before 15:00
                            if cards_before_3pm:
                                card_number = random.choice(cards_before_3pm)
                                cards_before_3pm.remove(card_number)
                        else:  # If after 15:00
                            if cards_after_3pm:
                                card_number = random.choice(cards_after_3pm)
                                cards_after_3pm.remove(card_number)
                        generated_card_names.append(card_number)

                        generated_soc_end.append(np.random.randint(soc_end_inf, soc_end_sup + 1))
                        number_of_morning += 1
                        records_generated += 1
                else:
                    if nuumber_of_night < number_of_bus:
                        generated_charging_times_start.append(pd.Timestamp.combine(date, rounded_time))
                        generated_soc_start.append(soc_value)

                        # Determine end charging time based on start charging time
                        if rounded_time <= time(15, 0):  # If before 15:00
                            start_datetime = datetime(date.year, date.month, date.day, rounded_time.hour, rounded_time.minute)
                            end_time = random.choice(pd.date_range(start_datetime, datetime(date.year, date.month, date.day, 15, 0), freq='15T'))
                        else:  # If after 15:00
                            end_time = random.choice(pd.date_range(datetime(date.year, date.month, date.day, 5, 0), datetime(date.year, date.month, date.day, 5, 30), freq='15T').tolist())

                        # Check if it needs to span to the next day
                        if end_time < pd.Timestamp.combine(date, rounded_time):
                            end_time += timedelta(days=1)
                        generated_charging_times_end.append(end_time)

                        # Depending on the start charging time zone, choose a card
                        if rounded_time < time(15, 0):  # If before 15:00
                            if cards_before_3pm:
                                card_number = random.choice(cards_before_3pm)
                                cards_before_3pm.remove(card_number)
                        else:  # If after 15:00
                            if cards_after_3pm:
                                card_number = random.choice(cards_after_3pm)
                                cards_after_3pm.remove(card_number)
                        generated_card_names.append(card_number)

                        generated_soc_end.append(95)
                        nuumber_of_night += 1
                        records_generated += 1

    generated_data = pd.DataFrame({
        '卡片名稱': generated_card_names,
        '開始充電時間': generated_charging_times_start,
        '結束充電時間': generated_charging_times_end,
        'SoC(開始)': generated_soc_start,
        'SoC(結束)': generated_soc_end
    })

    return generated_data

# Function to plot scatter graph of SoC over time with vertical lines every 15 minutes
def plot_scatter(data):
    """
    Plots a scatter graph of SoC over time with vertical lines every 15 minutes.
    """
    plt.figure(figsize=(15, 8))
    unique_dates = data['開始充電時間'].dt.date.unique()
    colors = sns.color_palette("hsv", len(unique_dates))

    for i, date in enumerate(unique_dates):
        daily_data = data[data['開始充電時間'].dt.date == date]
        times = daily_data['開始充電時間'].dt.hour + daily_data['開始充電時間'].dt.minute / 60
        plt.scatter(times, daily_data['SoC(開始)'], color=colors[i], label=f"{date.strftime('%Y-%m-%d')} ({len(daily_data)} points)", alpha=0.6)

    for hour in range(24):
        for quarter in range(0, 60, 15):
            plt.axvline(x=hour + quarter/60, color='grey', linestyle='--', linewidth=0.5)

    plt.title('SoC Scatter Plot Over Time (0-24 Hours)')
    plt.xlabel('Time of Day (Hours)')
    plt.ylabel('Start SoC (%)')
    plt.xlim(0, 24)
    plt.ylim(0, 100)
    plt.xticks(np.arange(0, 25, 1))
    plt.grid(True)
    plt.legend(title='Date', loc='upper left')
    plt.tight_layout()
    plt.show()

def plot_kdeplot(data, original_data):
    data['相對時間'] = data['開始充電時間'].apply(lambda x: x.hour * 60 + x.minute)
    original_data['相對時間'] = original_data['開始充電時間'].apply(lambda x: x.hour * 60 + x.minute)
    plt.figure(figsize=(15, 8))
    sns.kdeplot(original_data, x='相對時間', y='SoC(開始)', cmap="Oranges", fill=True, levels=20, alpha=1, label='Original Data')
    sns.kdeplot(data, x='相對時間', y='SoC(開始)', cmap="bone", fill=True, levels=20, alpha=0.1, label='Simulated Data')
    plt.scatter(data['相對時間'], data['SoC(開始)'])
    plt.title('SoC Scatter Plot Over Time (0-24 Hours)')
    plt.xlabel('Time of Day (Hours)')
    plt.ylabel('Start SoC (%)')
    plt.xlim(0, 24)
    plt.ylim(0, 100)
    plt.xticks(np.arange(0, 25, 1))
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.xticks(range(0, 24*60+15, 15), [f'{i//60:02d}:{i%60:02d}' for i in range(0, 24*60+15, 15)], rotation=90)
    plt.yticks(np.arange(0, 101, 10))
    plt.show()

# Clear terminal
os.system("cls")

# Parameter setting
number_of_generation = 14   #數據生成天數
min_records = 10    # 一天最少充電次數
max_records = 25    # 一天最多充電次數 maximun = 30
soc_end_inf = 90    # 結束SoC下限
soc_end_sup = 95    # 結束SoC上限

# Read data and reset index
charging_data = pd.read_excel('C:\\Users\\WYC\\Desktop\\電動大巴\\EMS\\EMS\\資料生成\\2305-府城客運_充電樁充電列表.xlsx', sheet_name="充電樁充電列表")
charging_data = charging_data[charging_data['充電樁名稱'] != '頂東站1']
charging_data.reset_index(drop=True, inplace=True)

charging_data['相對時間'] = charging_data['開始充電時間'].apply(lambda x: x.hour * 60 + x.minute)
generated_data = generate_charging_data(number_of_generation, charging_data, min_records, max_records, soc_end_inf, soc_end_sup)
print(generated_data)

# Plot scatter graph
plot_scatter(generated_data)
plot_kdeplot(generated_data, charging_data)

# Optionally save generated data to Excel
output_file_path = 'C:\\Users\\WYC\\Desktop\\電動大巴\\EMS\\EMS\\資料生成\\生成數據\\generated_data.xlsx'
generated_data.drop(columns=['相對時間'], inplace=True)
generated_data.to_excel(output_file_path, index=False)