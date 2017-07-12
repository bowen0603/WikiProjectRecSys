from __future__ import print_function

__author__ = 'bobo'

import json
from sseclient import SSEClient as EventSource

# API: https://wikitech.wikimedia.org/wiki/EventStreams
# https://pypi.python.org/pypi/sseclient/

class Streamer:

    def __init__(self, output_dir):
        self.url = 'https://stream.wikimedia.org/v2/stream/recentchange'
        self.NEW_USERS = {}

        self.newcomers_file = "newcomers"
        self.new_registered_file = "new_registered"
        self.output_dir = output_dir
        self.fout_newcomers = None
        self.fout_newreg = None

        self.time_gap = 60 * 60  # in seconds
        self.days_limit = 10


    def stream(self, start_date):

        # construct file and fout
        print("Working on a new file..")
        user_cnt = 0
        register_cnt = 0

        unit = 0
        if self.time_gap >= 60 * 60 * 24:
            unit = start_date.day
        elif self.time_gap >= 60 * 60:
            unit = start_date.hour
        elif self.time_gap >= 60:
            unit = start_date.minute

        self.fout_newcomers = open(self.output_dir + "/" + self.newcomers_file + str(unit) + ".csv", "w")
        self.fout_newreg = open(self.output_dir + "/" + self.new_registered_file + str(unit) + ".csv", "w")
        print("user_cnt**user_text**article**timestamp", file=self.fout_newcomers)
        print("user_cnt**user_text**timestamp", file=self.fout_newreg)

        for event in EventSource(self.url):

            # check if times up for the next file (over a day)
            if self.times_up(start_date):
                break

            if event.event == 'message':
                try:
                    change = json.loads(event.data)
                except ValueError:
                    pass

                else:
                    if change['wiki'] != "enwiki":
                        continue

                    if (change['type'] == "log" and
                                change['log_type'] == "newusers" and
                                change['log_action'] == "create" and
                                'user' in change and
                                change['user'] is not None):

                        self.NEW_USERS[change['user']] = 0

                        # TODO: add on edit hour, day, and month
                        register_cnt += 1
                        print("Registered {}. {}".format(register_cnt, change.get('user').encode('utf8')))
                        print("{}**{}**{}".format(register_cnt, change['user'], change['timestamp']),
                              file=self.fout_newreg)
                        self.fout_newreg.flush()


                    elif change['type'] in ('edit', 'new'):
                        username = change.get('user')
                        if username in self.NEW_USERS:

                            if self.NEW_USERS[username] == 0 and change['namespace'] == 0:
                                self.NEW_USERS[username] += 1

                                # TODO: add on edit hour, day, and month
                                user_cnt += 1
                                print("Edited {}. {} edited {}.".format(user_cnt, username.encode('utf8'), change['title'].encode('utf8')))
                                print("{}**{}**{}".format(username, change['title'], change['timestamp']),
                                      file=self.fout_newcomers)
                                self.fout_newcomers.flush()

                    # TODO: create a separated file for following edits made by newcomers


    def times_up(self, start_date):
        from datetime import datetime
        delta = datetime.now() - start_date
        if delta.seconds >= self.time_gap:
            return True
        else:
            return False


    def run(self):
        # define file name

        days_cnt = 0
        while True:
            if days_cnt >= self.days_limit:
                break
            days_cnt += 1

            from datetime import datetime
            self.stream(datetime.now())


def main():
    # streaming_newcomers

    from sys import argv
    if len(argv) != 2:
        print("Usage: <output_dir>")
        return

    streamer = Streamer(argv[1])
    streamer.run()


main()


''''
 read in recommendation files, four files for four algorithms
  '''
