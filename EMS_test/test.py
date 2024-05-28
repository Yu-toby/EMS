def get_corresponding_power(pile_summary, gun_number):
    # 將 gun_number 的格式拆分成樁組編號和樁號
    group, number = gun_number.split('-')
    
    # 根據樁號選擇對應的另一個樁號
    if number == '1':
        corresponding_number = group + '-2'
    else:
        corresponding_number = group + '-1'
    
    # 從字典中獲取對應樁號的功率
    corresponding_power = pile_summary[corresponding_number]
    return corresponding_power

# 示例數據
pile_summary = {
    '1-1': 44144.116282665156,
    '1-2': 29859.590289421827,
    '2-1': 60255.31914893604,
    '2-2': 26947.9672869505,
    '3-1': 61326.043648030005,
    '3-2': 38673.956351969995,
    '4-1': 35962.21808134679,
    '4-2': 47178.423236514514,
    '5-1': 74413.111014241,
    '5-2': 25586.888985758986
}

# 示範呼叫
gun_number = '1-1'
result = get_corresponding_power(pile_summary, gun_number)
print(f'The corresponding power for {gun_number} is {result}')
