from __future__ import print_function

__author__ = 'bobo'
"""
Code purpose: Read in the recommended editors from each algorithm and newcomers,
 assume the study is launched, then start stream their edits to see what they
 are doing after the experiment for study evaluation.
 But this can be probably done by direct API queries as well.
"""

import json
from sseclient import SSEClient as EventSource

# API: https://wikitech.wikimedia.org/wiki/EventStreams
# https://pypi.python.org/pypi/sseclient/

class Streamer:

    def __init__(self, filenames):
        self.url = 'https://stream.wikimedia.org/v2/stream/recentchange'

        self.users_topics = []
        self.users_bonds = []
        self.users_rule = []
        self.users_cf = []

        self.newcomers = []
        self.organizers = []

        self.user_project = {}

        self.file_topics = filenames[1]
        self.file_bonds = filenames[2]
        self.file_rule = filenames[3]
        self.file_cf = filenames[4]
        self.file_newcomers = filenames[5]
        self.file_organizers = filenames[6]
        self.output = filenames[7]

        self.fout = open(self.output, "w")


    def streaming(self):

        # construct file and fout
        print("Working on a new file..")

        print("user_text,wikiproject,type,title,ns,timestamp,minor", file=self.fout)

        for event in EventSource(self.url):

            if event.event == 'message':
                try:
                    change = json.loads(event.data)
                except ValueError:
                    pass

                else:
                    if change['wiki'] != "enwiki":
                        continue

                    if change['type'] != 'edit':
                        continue

                    username = change.get('user').encode('utf-8')
                    title = change.get('title').encode('utf-8')
                    timestamp = change.get('timestamp')
                    ns = change.get('namespace')
                    minor = 1 if change.get('minor') else 0

                    if username in self.users_bonds:
                        type = 'bonds'
                    elif username in self.users_topics:
                        type = 'topics'
                    elif username in self.users_rule:
                        type = 'rule'
                    elif username in self.users_cf:
                        type = 'cf'
                    elif username in self.newcomers:
                        type = 'newcomer'
                    elif username in self.organizers:
                        type = 'organizer'
                    else:
                        # not recommended users...
                        continue

                    wikiproject = None
                    if username in self.user_project:
                        wikiproject = self.user_project[username]
                    else:
                        # TODO: something is wrong here...
                        pass

                    print("{}**{}**{}**{}**{}**{}**{}".format(username, wikiproject, type, title, ns, timestamp, minor),
                          file=self.fout)
                    print("{}**{}**{}**{}**{}**{}**{}".format(username, wikiproject, type, title, ns, timestamp, minor))

                    self.fout.flush()


    def read_files(self):

        # read topics recommendations
        for line in open(self.file_topics, "r").readlines()[1:]:
            user = line.split(",")[0]
            wp = line.split(",")[1]
            self.users_topics.append(user)
            self.user_project[user] = wp

        # read bonds recommendations
        for line in open(self.file_bonds, "r").readlines()[1:]:
            user = line.split(",")[0]
            wp = line.split(",")[1]
            self.users_bonds.append(user)
            self.user_project[user] = wp

        # read rule recommendations
        for line in open(self.file_rule, "r").readlines()[1:]:
            user = line.split(",")[0]
            wp = line.split(",")[1]
            self.users_rule.append(user)
            self.user_project[user] = wp

        # read cf recommendations
        for line in open(self.file_cf, "r").readlines()[1:]:
            user = line.split(",")[0]
            wp = line.split(",")[1]
            self.users_cf.append(user)
            self.user_project[user] = wp

        # read newcomer recommendations
        for line in open(self.file_newcomers, "r").readlines()[1:]:
            user = line.split(",")[0]
            wp = line.split(",")[1]
            self.newcomers.append(user)
            self.user_project[user] = wp

        # read project organizers
        for line in open(self.file_organizers, "r").readlines()[1:]:
            user = line.split(",")[0]
            wp = line.split(",")[1]
            self.organizers.append(user)
            self.user_project[user] = wp

def main():
    # streaming_newcomers

    from sys import argv
    if len(argv) != 8:
        print("Usage: <topic_recsys> <bonds_recsys> <rule_recsys> <cf_recsys> <newcomers> <organizers> <output_file>")
        return

    streamer = Streamer(argv)
    streamer.read_files()
    streamer.streaming()

    # python code/API_collecting_activities.py data/topic_based.csv data/bonds_based.csv data/rule_based.csv data/user_cf.csv data/newcomers.csv data/organizers.csv data/output.csv



main()

''''
event: message
id: [{"topic":"codfw.mediawiki.recentchange","partition":0,"offset":-1},
{"topic":"eqiad.mediawiki.recentchange","partition":0,"offset":285882958}]
data: {"bot":false,"comment":"moved CEO name from nonexistent infobox category to key_people; reformatted title; unwiki-linked to unredlink",
"id":961820736,"length":{"new":5988,"old":6023},
"meta":{"domain":"en.wikipedia.org","dt":"2017-07-12T01:14:53+00:00",
"id":"82a209ee-669f-11e7-9531-141877613a1c",
"request_id":"dc274846-d411-458a-8480-5168b045df03","schema_uri":"mediawiki/recentchange/1",
"topic":"eqiad.mediawiki.recentchange","uri":"https://en.wikipedia.org/wiki/Perforce_Software",
"partition":0,"offset":285882957},"minor":false,"namespace":0,"revision":{"new":790171601,"old":787502175},
"server_name":"en.wikipedia.org","server_script_path":"/w","server_url":"https://en.wikipedia.org",
"timestamp":1499822093,"title":"Perforce Software","type":"edit","user":"Timtempleton","wiki":"enwiki"}

'''