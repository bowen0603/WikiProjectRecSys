from __future__ import print_function
import socketIO_client

"""""
NOTICE: THIS API IS OUTDATED. NO LONGER SUPPORTED BY WIKI
"""""

"""
Reference:
RCStream: https://wikitech.wikimedia.org/wiki/RCStream
change object: https://www.mediawiki.org/wiki/Manual:Recentchanges_table
"""

NEW_USERS = {}
fout_newcomers = open("streaming_newcomers/newcomers_text.csv", "w", 0)
fout_newreg = open("streaming_newcomers/new_registered_text.csv", "w", 0)
print("user_name,title,timestamp", file=fout_newreg)
print("user_name,title,timestamp", file=fout_newcomers)

user_cnt = 0
register_cnt = 0

class WikiNamespace(socketIO_client.BaseNamespace):
    def on_change(self, change):
        if (change['type'] == "log" and
            change['log_type'] == "newusers" and
            change['log_action'] == "create" and
            'user' in change and
            change['user'] is not None):

            NEW_USERS[change['user']] = 0

            global register_cnt
            register_cnt += 1

            print("{} registered {}.".format(change.get('user'), register_cnt))
            print("{},{},{}".format(register_cnt, change['user'], change['timestamp']), file=fout_newreg)
            # fout_newreg.write(str(register_cnt)+","+ change['user'] +","+ str(change['timestamp']))


        elif change['type'] in ('edit', 'new'):
            username = change.get('user')
            if username in NEW_USERS:

                if NEW_USERS[username] == 0 and change['namespace'] == 0:
                    NEW_USERS[username] += 1

                    global user_cnt
                    user_cnt += 1
                    print("{},{},{}".format(username, change['title'], change['timestamp']), file=fout_newcomers)
                    # fout_newreg.write(username+","+ change['title'] +","+ str(change['timestamp']))
                    print("{}. {} edited {}.".format(user_cnt, username, change['title']))


                    # store and look up the dictionary for the article

                # if NEW_USERS[username] >= 1:
                    #print("** {0} saved their second {1} edit".format(username, NEW_USERS[username]))
                    #del NEW_USERS[username]


    def on_connect(self):
        self.emit('subscribe', 'en.wikipedia.org')


socketIO = socketIO_client.SocketIO('https://stream.wikimedia.org')
socketIO.define(WikiNamespace, '/rc')

socketIO.wait(99999999999999)


'''
{"comment":"/*Kick*/",
 "wiki":"plwiki",
 "server_name":"pl.wikipedia.org",
 "title":"Kick",
 "timestamp":1493910444,
 "server_script_path":"/w",
 "namespace":0,
 "server_url":"https://pl.wikipedia.org",
 "length":{"new":350,"old":350},
 "user":"91.242.58.59","bot":false,
 "type":"edit","id":78429929,"minor":false,"revision":{"new":49237300,"old":49237297}}

{"comment":"",
 "wiki":"enwiki",
 "server_name":"en.wikipedia.org",
 "server_url":"https://en.wikipedia.org",
 "title":"User:Waterdropstudios",
 "log_id":82664638,
 "timestamp":1493910812,
 "server_script_path":"/w",
 "namespace":2,
 "log_params":{"userid":31006639},
 "log_type":"newusers",
 "user":"Waterdropstudios",
 "bot":false,
 "log_action_comment":"New user account",
 "type":"log",
 "id":938806714,
 "log_action":"create"}
'''
