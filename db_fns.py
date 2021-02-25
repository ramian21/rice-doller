from datetime import datetime
from pymongo import MongoClient
# connect to MongoDB
client = MongoClient('localhost')
db = client.gi_db
players = db.players
logs = db.pull_logs


def add_pull_to_DB(discID: str, banner: str, result: str = ''):
    player_result = players.find_one({'discID': discID})
    if player_result == None:
        player_result = create_player_record(discID)
    time_stamp = datetime.now()
    banner_log_count = str(banner + 'LogCount')
    banner_pull_count = str(banner + 'PullCount')
    log_num = player_result[banner_log_count]
    pull_num = player_result[banner_pull_count] + 1
    logs.insert_one({
        'discID': discID,
        'timeStamp': time_stamp,
        'banner': banner,
        'logNum': log_num,
        'pullNum': pull_num,
        'result': result
    })
    players.find_one_and_update(
        {'discID': discID},
        {'$inc': {banner_pull_count: 1, 'totalPulls': 1}}
    )
    return int(pull_num)


def get_count_from_DB(discID: str, banner: str):
    player_result = players.find_one({'discID': discID})
    if player_result == None:
        player_result = create_player_record(discID)
    banner_pull_count = str(banner + 'PullCount')
    pull_num = player_result[banner_pull_count]
    return int(pull_num)


def get_current_log_from_DB(discID: str, banner: str):
    player_result = players.find_one({'discID': discID})
    if player_result == None:
        player_result = create_player_record(discID)
    banner_log_count = str(banner + 'LogCount')
    log_num = int(player_result[banner_log_count]) + 1
    return get_log_from_DB(discID, banner, log_num)


def get_log_from_DB(discID: str, banner: str, log_num: int):
    player_result = players.find_one({'discID': discID})
    if player_result == None:
        player_result = create_player_record(discID)
    banner_pull_count = str(banner + 'PullCount')
    banner_log_count = str(banner + 'LogCount')
    banner_pull_count_total = str(banner + 'PullCountTotal')
    log_num -= 1  # zero based indexing
    current_log_count = int(player_result[banner_log_count])
    if log_num == current_log_count:
        pull_count = int(player_result[banner_pull_count])
    elif log_num < current_log_count and log_num >= 0:
        pull_count = int(player_result[banner_pull_count_total][log_num])
    else:
        return None
    results = logs.find({'discID': discID, 'logNum': log_num, 'banner': banner}).sort('pullNum', 1)
    entries = []
    for index in range(pull_count):
        pull_num = results[index]['pullNum']
        tmp = results[index]['timeStamp']
        time_stamp: str = tmp.strftime('%x') + ' ' + tmp.strftime('%X')
        result = results[index]['result']
        if len(result) > 16:
            result = result[0:13] + '...'
        entry = '{:2d} {:16s}     {:s}'.format(
            int(pull_num), result, time_stamp)
        entries.append(entry)
    return entries


def new_log_in_DB(discID: str, banner: str, logMsg: str = ''):
    player_result = players.find_one({'discID': discID})
    if player_result == None:
        player_result = create_player_record(discID)
    pull_count_get = add_pull_to_DB(discID, banner, logMsg)
    banner_log_count = str(banner + 'LogCount')
    banner_pull_count = str(banner + 'PullCount')
    banner_pull_count_total = str(banner + 'PullCountTotal')
    players.find_one_and_update(
        {'discID': discID},
        {'$inc': {banner_log_count: 1, banner_pull_count: -pull_count_get},
         '$push': {banner_pull_count_total: pull_count_get}
         }
    )
    return int(pull_count_get)


def get_player_stats(discID: str):
    player_result = players.find_one({'discID': discID})
    if player_result == None:
        player_result = create_player_record(discID)
    current_char_pulls = int(player_result['characterPullCount'])
    total_char_pulls = int(
        player_result['characterPullCount']) + sum(player_result['characterPullCountTotal'])
    num_prev_char_logs = player_result['characterLogCount']
    try:
        get_rate_char = num_prev_char_logs * 100 / total_char_pulls
    except ZeroDivisionError:
        get_rate_char = 0
    current_weapon_pulls = int(player_result['weaponPullCount'])
    total_weapon_pulls = int(
        player_result['weaponPullCount']) + sum(player_result['weaponPullCountTotal'])
    num_prev_weapon_logs = player_result['weaponLogCount']
    try:
        get_rate_weapon = num_prev_weapon_logs * 100 / total_weapon_pulls
    except ZeroDivisionError:
        get_rate_weapon = 0
    current_standard_pulls = int(player_result['standardPullCount'])
    total_standard_pulls = int(
        player_result['standardPullCount']) + sum(player_result['standardPullCountTotal'])
    num_prev_standard_logs = player_result['standardLogCount']
    try:
        get_rate_standard = num_prev_standard_logs * 100 / total_standard_pulls
    except ZeroDivisionError:
        get_rate_standard = 0
    totalPulls = total_char_pulls + total_weapon_pulls + total_standard_pulls
    try:
        get_rate_total = ((num_prev_char_logs + num_prev_weapon_logs +
                           num_prev_standard_logs) * 100) / (totalPulls)
    except ZeroDivisionError:
        get_rate_total = 0

    player_stats = [
        'Current pulls on character banner:             {:d}'.format(
            current_char_pulls),
        'Number of previous character banner pull logs: {:d}'.format(
            num_prev_char_logs),
        'Total number of pulls on character banner:     {:d}'.format(
            total_char_pulls),
        '5-Star pull rate on character banner:          {:.2f}%\n'.format(
            get_rate_char),
        'Current pulls on weapon banner:                {:d}'.format(
            current_weapon_pulls),
        'Number of previous weapon banner pull logs:    {:d}'.format(
            num_prev_weapon_logs),
        'Total number of pulls on weapon banner:        {:d}'.format(
            total_weapon_pulls),
        '5-Star pull rate on weapon banner:             {:.2f}%\n'.format(
            get_rate_weapon),
        'Current pulls on standard banner:              {:d}'.format(
            current_standard_pulls),
        'Number of previous standard banner pull logs:  {:d}'.format(
            num_prev_standard_logs),
        'Total number of pulls on standard banner:      {:d}'.format(
            total_standard_pulls),
        '5-Star pull rate on standard banner:           {:.2f}%\n'.format(
            get_rate_standard),
        'Total number of pulls across all banners:      {:d}'.format(
            totalPulls),
        '5-Star pull rate across all banners:           {:.2f}%'.format(
            get_rate_total)
    ]
    return player_stats


def create_player_record(discID: str):
    receipt = players.insert_one({
        'discID': discID,
        'characterPullCount': 0,
        'characterLogCount': 0,
        'characterPullCountTotal': [],
        'weaponPullCount': 0,
        'weaponLogCount': 0,
        'weaponPullCountTotal': [],
        'standardPullCount': 0,
        'standardLogCount': 0,
        'standardPullCountTotal': [],
        'totalPulls': 0
    })
    return players.find_one({'_id': receipt.inserted_id})
