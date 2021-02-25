from db_fns import add_pull_to_DB, get_count_from_DB, get_current_log_from_DB, get_log_from_DB, get_player_stats, new_log_in_DB
import discord
from decouple import config

BOT_TOKEN = config('RDV2_BOT_TOKEN')

usage_message = """Unknown command.
USAGE:

`!rd [ACTION] [BANNER_TYPE] [OPTIONAL_LOG_MESSAGE]`

For more details, enter: `!rd help`"""

help_actions = [
    """add, a [BANNER_TYPE] [OPTIONAL_LOG_MESSAGE]
		adds an entry to the specified banner type with an option to provide a message including what was pulled, then displays the new number of pulls
		
		EXAMPLE:

		Congrats, you pulled your eighth Barbara off of the character banner! Make sure you tell the bot by entering:

		!rd add character Barbara""",
    """bulkadd, b [BANNER_TYPE] NUMBER_OF_PULLS
		adds NUMBER_OF_PULLS blank entries to the specified banner type to quickly catch up to where you should be

		EXAMPLE:

		The new character banner came out and you pulled 5 times and got 3-star garbage. Don't bother logging them, instead enter:

		!rd bulkadd 5""",
    """current, count, c [BANNER_TYPE]
		displays the number of pulls on the specified banner

		EXAMPLE:

		!rd current character""",
    """help, h [OPTIONAL_ACTION_TYPE]
		displays this full message or the entry for the specified action""",
    """log, list, l [BANNER_TYPE]
		displays the current pull log for the specified banner

		EXAMPLE:

		!rd log standard""",
    """past, previous, p [BANNER_TYPE] LOG_NUMBER
		displays a previous pull log for the specified banner

		EXAMPLE:

		You pulled Venti when the game launched, but you want to see what you needed to pull to get there, enter:

		!rd past character 1""",
    """reset, r [BANNER_TYPE] [OPTIONAL_LOG_MESSAGE]
		adds a final entry and displays the number of pulls before starting a new log on the specified banner

		EXAMPLE:

		You finally pulled Diluc on standard banner! Log it and reset the counter to 0 by entering:

		!rd reset standard DILUC LFGGGGGG""",
    """summary, status, stats, s
		displays a summary of current pull information

		EXAMPLE:

		You want to see your total pull numbers. Enter:

		!rd summary"""
]

client = discord.Client()


# TODO:
#   - (DONE) function to reset/new log for banner
#   - (DONE) function to print usage
#   - (DONE) display previous logs on banner
#   - (DONE) function to print help
#   - (DONE) function to bulk add with number parameter
#   - (DONE) function to display user profile
#   - (DONE) refactor command parsing logic
#   - error checks for pull counts > 90
#   - set up remote server
#
#   - stretch goals
#       - embed/UI with reacts
#       - pull simulator based on current
#
def add_pull(discID: str, banner: str, log_msg=''):
    return add_pull_to_DB(discID, banner, log_msg)


def count_pull(discID: str, banner: str):
    return get_count_from_DB(discID, banner)


def log_pull(discID: str, banner: str):
    return get_current_log_from_DB(discID, banner)


def close_pull_log(discID: str, banner: str, log_msg=''):
    return new_log_in_DB(discID, banner, log_msg)


def previous_log_pull(discID: str, banner: str, log_num: int):
    return get_log_from_DB(discID, banner, log_num)


def display_help(help_action: str = ''):
    if help_action == 'a' or help_action == 'add':
        help_string = '```' + help_actions[0] + '```'
    elif help_action == 'b' or help_action == 'bulkadd':
        help_string = '```' + help_actions[1] + '```'
    elif help_action == 'c' or help_action == 'count' or help_action == 'current':
        help_string = '```' + help_actions[2] + '```'
    elif help_action == 'h' or help_action == 'help':
        help_string = '```' + help_actions[3] + '```'
    elif help_action == 'l' or help_action == 'log' or help_action == 'list':
        help_string = '```' + help_actions[4] + '```'
    elif help_action == 'p' or help_action == 'past' or help_action == 'previous':
        help_string = '```' + help_actions[5] + '```'
    elif help_action == 'r' or help_action == 'reset':
        help_string = '```' + help_actions[6] + '```'
    elif help_action == 's' or help_action == 'status' or help_action == 'summary' or help_action == 'stats':
        help_string = '```' + help_actions[7] + '```'
    else:
        help_string = '```Rice Doller Bot\n\n!rd [add|count|log|reset|...] [character|weapon|standard] [Optional message to log pull result]\n\nACTIONS:\n\n'
        for x in range(len(help_actions)):
            help_string += help_actions[x] + '\n\n'
        help_string += '```'

    return help_string


def format_log(entries, banner, log_num):
    page_limit = 30
    plimit_in_entries = int(len(entries) / page_limit) + 1
    log_strings = []
    for up_to_page_limit in range(plimit_in_entries):
        inner_range = min(page_limit, len(entries) -
                          (up_to_page_limit * page_limit))
        page_number = up_to_page_limit + 1
        if log_num == 0:
            log_string = '```Current pulls on {:s} banner: ({:d}/{:d})\n'.format(
                banner, page_number, plimit_in_entries)
        else:
            log_string = '```Pull Log#{:d} on {:s} banner: ({:d}/{:d})\n'.format(
                log_num, banner,  page_number, plimit_in_entries)
        for x in range(inner_range):
            entryindex = (up_to_page_limit * page_limit) + x
            log_string += entries[entryindex]
            log_string += '\n'
        log_string += '```'
        log_strings.append(log_string)
    return log_strings


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='!rd help'))
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):

    # do not process if message was sent by bot-self
    if message.author == client.user:
        return

    # split command to parse
    contents = message.content.split()

    # if not a bot command, return
    if not (contents[0].startswith('!rd')):
        return

    # debug purposes 
    user = str(message.author)
    command = str(message.content)
    print('{:s}:{:s}'.format(user, command))

    # get unique discord identifier
    discID = str(message.author.id)

    # if no actions are specified, display usage
    if len(contents) < 2:
        await message.channel.send(usage_message)
        return

    # first argument will always be the action argument
    action_arg = contents[1].lower()

    # if display player stats
    if action_arg == 's' or action_arg == 'status' or action_arg == 'summary' or action_arg == 'stats':
        player_stats = get_player_stats(discID)
        user_tag = str(message.author)
        user_tag = user_tag[0:len(user_tag)-5]
        stats_msg = '```Displaying stats for {:s}:\n\n'.format(user_tag)
        for statistic in player_stats:
            stats_msg += statistic
            stats_msg += '\n'
        stats_msg += '```'
        await message.channel.send(stats_msg)
        return
    # display help message
    elif action_arg == 'h' or action_arg == 'help':
        if len(contents) == 2:
            help_arg = ''
        else:
            help_arg = contents[2].lower()
        help_msg = display_help(help_arg)
        await message.channel.send(help_msg)
        return

    if len(contents) < 3:
        await message.channel.send(usage_message)
        return
    # if not a help argument, arg2 should always be the banner argument
    banner_arg = contents[2].lower()

    # banner argument should be one of the following
    if banner_arg == 'c' or banner_arg == 'character':
        banner = 'character'
    elif banner_arg == 'w' or banner_arg == 'weapon':
        banner = 'weapon'
    elif banner_arg == 's' or banner_arg == 'standard':
        banner = 'standard'
    else:
        await message.channel.send(usage_message)
        return


    # log message is anything after the banner argument, combine and strip the whitespace
    log_msg = ''
    for count in range(3, len(contents)):
        log_msg += contents[count] + ' '
    log_msg = log_msg.strip(' ')

    # add entry w/ possible log message on specific banner
    if action_arg == 'a' or action_arg == 'add':
        pull_count = add_pull(discID, banner, log_msg)
        await message.channel.send('You pulled from the {:s} banner. You are now at {:d} pulls.'.format(banner, pull_count))
        return
    # bulk add entries
    elif action_arg == 'b' or action_arg == 'bulkadd':
        if not log_msg.isnumeric():
            await message.channel.send(usage_message)
            return
        num_iterations = int(log_msg)
        if num_iterations > 90:
            await message.channel.send('Max number of entries to bulk add is 90. Please do not abuse this function.')
            return
        for x in range(num_iterations):
            pull_count = add_pull(discID, banner, '')
        await message.channel.send('You pulled {:d} times from the {:s} banner. You are now at {:d} pulls.'.format(num_iterations, banner, pull_count))
    # display current count on specific banner
    elif action_arg == 'c' or action_arg == 'count' or action_arg == 'current':
        pull_count = count_pull(discID, banner)
        await message.channel.send('You have {:d} pulls on the {:s} banner'.format(pull_count, banner))
        return
    # display current log on specific banner
    elif action_arg == 'l' or action_arg == 'log' or action_arg == 'list':
        entries = log_pull(discID, banner)
        log_strings = format_log(entries, banner, 0)
        for log_string in log_strings:
            await message.channel.send(log_string)
        return
    # display previous logs on specific banner
    elif action_arg == 'p' or action_arg == 'past' or action_arg == 'previous':
        if not log_msg.isnumeric():
            await message.channel.send(usage_message)
            return
        log_num = int(log_msg)
        entries = previous_log_pull(discID, banner, log_num)
        if entries == None:
            await message.channel.send('Log#{:d} not yet reached on {:s} banner. Try `!rd current {:s}`'.format(log_num, banner, banner))
            return
        log_strings = format_log(entries, banner, log_num)
        for log_string in log_strings:
            await message.channel.send(log_string)
        return
    # reset count on specific banner
    elif action_arg == 'r' or action_arg == 'reset':
        last_pull_count_get = close_pull_log(discID, banner, log_msg)
        if len(log_msg) > 0:
            msg = 'Congratulations, it took {:d} pulls to get {:s}! Starting a new log on the {:s} banner.'.format(
                last_pull_count_get, log_msg, banner)
        else:
            msg = 'Starting a new log on the {:s} banner.'.format(banner)
        await message.channel.send(msg)
        return
    else:
        await message.channel.send(usage_message)
        return


client.run(BOT_TOKEN)
