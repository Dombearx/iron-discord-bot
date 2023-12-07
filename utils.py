from datetime import datetime


def get_data_from_channel(channel):
    """Placeholder function to get data from channel"""
    day_ago = datetime.datetime.now() - datetime.timedelta(days=1)
    messages = [message async for message in channel.history(after=day_ago)]
    channel_history = ""
    for old_message in messages:
        channel_history += old_message.author.name + " at " + str(old_message.created_at) + " said: "
        channel_history += old_message.content
        channel_history += "\n"
    return channel_history