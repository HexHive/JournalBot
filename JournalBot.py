from configparser import ConfigParser
import datetime
import time
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def get_channel_id(client, channel_name):
	""" Get the channel id from a channel name """
	try:
		response = client.conversations_list()
		assert response["ok"] is True
		for channel in response["channels"]:
			if channel["name"] == channel_name:
				return channel["id"]
	except SlackApiError as e:
		print(f"Unable to get channel id: {e.response['error']}")
		print(e)
	print("Unable to find channel id.")
	return ""

def get_user_ids(client, channel_id):
	""" Get the list of user_ids for all channel members """
	try:
		response = client.conversations_members(channel=channel_id)
		assert response["ok"] is True
	except SlackApiError as e:
		print(f"Unable to get user ids: {e.response['error']}")
		print(e)
		return []
	return response["members"]

def send_message(client, channel_id, message):
	""" Send a message to a channel """
	try:
		response = client.chat_postMessage(channel=channel_id, text=message)
		assert response["message"]["text"] == message
	except SlackApiError as e:
		print(f"Could not send message: {e.response['error']}")

def get_messages(client, channel_id, last_check):
	""" Get all messages from a timestamp up to now """
	try:
		ts = time.mktime(last_check.timetuple())
		response = client.conversations_history(channel=channel_id, oldest=ts)
		return response["messages"]
	except SlackApiError as e:
		print(f"Could not get channel messages: {e.response['error']}")


def get_next_time(hour_second):
	""" Calculate when it is next time 17:30 (hour:second in 24hr format) """
	now = datetime.datetime.now()
	hs = datetime.datetime.strptime(hour_second, "%H:%M")
	#target = datetime.date.today() + datetime.timedelta(hours=hs.hour, minutes=hs.minute)
	target = now.replace(hour=hs.hour, minute=hs.minute, second=0, microsecond=0)
	if (now >= target):
		print("Next slot is tomorrow!")
		target = target + datetime.timedelta(days=1)
	while target.weekday() > 4:
		print("Not working on weekends, advancing!")
		target = target + datetime.timedelta(days=1)
	return target

def sleep_until(target):
	""" Sleep until a given time """
	now = datetime.datetime.now()
	duration = (target-now).total_seconds()
	print("Sleeping for {} seconds".format(duration))
	time.sleep(duration)


if __name__ == "__main__":
	# Initialize configuration and slack connection
	config = ConfigParser()
	config.read("config.ini")
	client = WebClient(token=config.get("JournalBot", "authtoken"))
	channel_id = get_channel_id(client, config.get("JournalBot", "channel"))

	last_check = datetime.date.today()
	#last_check = datetime.datetime.now()
	while True:
		# For each cycle: get list of user_ids
		user_ids = get_user_ids(client, channel_id)

		print("Target users: " + str(user_ids))
		
		# wait until we need to post the reminder
		print("Send out the reminder at "+config.get("JournalBot", "reminder_time"))
		reminder_at = get_next_time(config.get("JournalBot", "reminder_time"))
		#sleep_until(reminder_at)
		#send_message(client, channel_id, config.get("JournalBot", "reminder"))

		time.sleep(5)
		# wait until we need to check who responded
		print("Send out the warning at "+config.get("JournalBot", "warning_time"))
		warning_at = get_next_time(config.get("JournalBot", "warning_time"))
		sleep_until(warning_at)

		# get all messages and tick off user_ids
		messages = get_messages(client, channel_id, last_check)
		for message in messages:
			if message["user"] in user_ids:
				user_ids.remove(message["user"])

		# notify stragglers
		if len(user_ids) != 0:
			notify_list = ""
			for uid in user_ids:
				notify_list += "<@" + uid + ">, "
			notify_list = notify_list[:-2]
			warning = config.get("JournalBot", "warning").replace("{}", notify_list)
			send_message(client, channel_id, warning)

		# set new timestamp
		last_check = datetime.datetime.now()
