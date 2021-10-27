import argparse
import datetime
import time
import logging
from configparser import ConfigParser

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


''' XXXXXXXXXXXXXXXXXXXXXX '''
''' Interaction with Slack '''
''' XXXXXXXXXXXXXXXXXXXXXX '''

def get_channel_id(client, channel_name):
	''' Get the channel id from a channel name '''
	try:
		response = client.conversations_list()
		assert response['ok'] is True
		for channel in response['channels']:
			if channel['name'] == channel_name:
				return channel['id']
	except SlackApiError as e:
		logging.error('Unable to get channel id: {}'.format(e.response['error']))
		logging.error(e)
	logging.error('Unable to find channel id.')
	return ''

def get_user_ids(client, channel_id):
	''' Get the list of user_ids for all channel members '''
	try:
		response = client.conversations_members(channel=channel_id)
		assert response['ok'] is True
	except SlackApiError as e:
		logging.error('Unable to get user ids: {}'.format(e.response['error']))
		logging.error(e)
		return []
	return response['members']

def send_message(client, channel_id, message):
	''' Send a message to a channel '''
	try:
		response = client.chat_postMessage(channel=channel_id, text=message)
		assert response['ok'] is True
		assert response['message']['text'] == message
	except SlackApiError as e:
		logging.error('Could not send message: {}'.format(e.response['error']))

def get_messages(client, channel_id, last_check):
	''' Get all messages from a timestamp up to now '''
	try:
		ts = time.mktime(last_check.timetuple())
		response = client.conversations_history(channel=channel_id, oldest=ts)
		return response['messages']
	except SlackApiError as e:
		logging.error('Could not get messages: {}'.format(e.response['error']))


''' XXXXXXXXXXXXXXXX '''
''' Helper functions '''
''' XXXXXXXXXXXXXXXX '''

def get_next_time(hour_second):
	''' Calculate when it is next time 17:30 (hour:second in 24hr format) '''
	now = datetime.datetime.now()
	hs = datetime.datetime.strptime(hour_second, '%H:%M')
	target = now.replace(hour=hs.hour, minute=hs.minute, second=0, microsecond=0)
	if (now >= target):
		logging.info('Next slot is tomorrow!')
		target = target + datetime.timedelta(days=1)
	while target.weekday() > 4:
		logging.info('Not working on weekends, advancing!')
		target = target + datetime.timedelta(days=1)
	return target

def sleep_until(target):
	''' Sleep until a given time '''
	now = datetime.datetime.now()
	duration = (target-now).total_seconds()
	logging.info('Sleeping for {} seconds'.format(duration))
	time.sleep(duration)


''' XXXXXXXXXXXXXXXXXXXXXXX '''
''' Main JournalBot actions '''
''' XXXXXXXXXXXXXXXXXXXXXXX '''

def action_reminder(client, channel_id, message):
	logging.info('Sending out reminder now.')
	send_message(client, channel_id, message)

def action_warning(client, channel_id, message, warning_at):
	# get all messages since yesterday and tick off user_ids that interacted
	logging.info('Sending out warning now.')
	user_ids = get_user_ids(client, channel_id)
	total = len(user_ids)
	previous_day = warning_at - datetime.timedelta(days=1)
	messages = get_messages(client, channel_id, previous_day)
	for message in messages:
		if message['user'] in user_ids:
			user_ids.remove(message['user'])

	# notify stragglers
	if len(user_ids) != 0:
		notify_list = ''
		for uid in user_ids:
			notify_list += '<@' + uid + '>, '
		notify_list = notify_list[:-2]
		warning = message.replace('{}', notify_list)
		send_message(client, channel_id, warning)
	logging.info('Had to warn {} of {} people'.format(len(user_ids), total))


''' XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX '''
''' Main: parse configs and dispatch '''
''' XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX '''

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-v', '--verbose', action='store_true',
		help='Be more verbose and chatty in the output.')
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument('-d', '--daemon', action='store_true',
		help='Run the JournalBot in daemon mode.')
	group.add_argument('-r', '--reminder', action='store_true',
		help='Send out the reminder and exit.')
	group.add_argument('-w', '--warning', action='store_true',
		help='Send out the warning and exit.')
	args = parser.parse_args()

	if args.verbose:
		logging.basicConfig(level=logging.INFO)

	# Initialize configuration and slack connection
	config = ConfigParser()
	config.read('config.ini')
	client = WebClient(token=config.get('JournalBot', 'authtoken'))
	channel_id = get_channel_id(client, config.get('JournalBot', 'channel'))
	reminder = config.get('JournalBot', 'reminder')
	reminder_at = config.get('JournalBot', 'reminder_time')
	warning = config.get('JournalBot', 'warning')
	warning_at = config.get('JournalBot', 'warning_time')

	# We've got an action: fire and exit
	if args.reminder or args.warning:
		# If we're in action mode, check if we need to act
		now = datetime.date.today()
		if str(now.weekday()) not in config.get('JournalBot', 'dow_active'):
			logging.info('Today is not a workday, not sending a message.')
			exit(0)

		if args.reminder:
			action_reminder(client, channel_id, reminder)

		elif args.warning:
			current_warning_at = datetime.datetime.now()
			action_warning(client, channel_id, warning, current_warning_at)

		# We're all done here
		exit(0)

	# Looks like we're running in daemon mode.
	assert args.daemon is True
	last_check = datetime.date.today()
	while True:
		# wait until we need to post the reminder
		logging.info('Send out the reminder at {}'.format(reminder_at))
		sleep_until(get_next_time(reminder_at))
		action_reminder(client, channel_id, reminder)

		# wait until we need to check who responded
		logging.info('Send out the warning at {}'.format(warning_at))
		current_warning_at = get_next_time(warning_at)
		sleep_until(current_warning_at)
		action_warning(client, channel_id, warning, current_warning_at)