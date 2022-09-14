# JournalBot: Your daily dose of encouragement

JournalBot is a Slack bot that monitors a channel and encourages users to
post a daily update. The bot may remind users about posting an update if
they forget.

## Changelog

* 211027 v0.03 Moved to logging interface to reduce chatter/noise
* 211027 v0.02 Fixed some bugs and implemented (cron'able) actions
* 211026 v0.01 Initial version, as daemon

## Development and installation

```
# Create a new virtual environment for development
$ virtualenv JournalBot
$ source JournalBot/bin/activate

# Install necessary packages
$ pip3 install slack-sdk

# Adjust configuration file
$ cp config.ini.example config.ini
$ vim config.ini

# Run the bot
$ python3 JournalBot.py

# After testing, you can fire and forget
$ nohup python3 JournalBot.py -d >> bot.log &

# You can invoke JournalBot through cron
$ python3 JournalBot.py --reminder
$ python3 JournalBot.py --warning
```

The configuration file is simple and straight forward, check out `config.ini.example` for an example.


## Slack integration

Create a new slack application from scratch for your workspace on the [Slack API page](https://api.slack.com/apps) and assign basic parameters such as "JournalBot" in `Basic Information`.

Navigate to `OAuth & Permissions`. If your journal channel is public, you need the following scopes: `channels.history, channels.read, chat.write` (adjust accordingly for private channels).
In the `OAuth & Permissions` you'll also be able to copy the OAuth token to be used in the configuration. Just update the `config.ini` with the right `xoxb-XXX-XXX-XXX`.

In the `config.ini`, don't forget to add your JournalBot's UID to the `exclude_warning` list. You'll find its ID when "chatting" with the bot and clicking on its name on the top.

You should now be good to go. You may need event subscriptions for `message.channels` 
depending on the setup.


# How to contribute and attribute

This bot is a hack to motivate students to post their daily updates in a channel,
similar to scrum updates. Feel free to fork, clone, modify at your will. If you want to
contribute, reach out to the main author [Mathias Payer](https://nebelwelt.net) first.
I'm always happy about a shout out though.
