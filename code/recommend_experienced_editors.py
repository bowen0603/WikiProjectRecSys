from __future__ import print_function

__author__ = 'bobo'

"""
Related APIs for different methods
1. identify_experienced_editor(): https://www.mediawiki.org/w/api.php?action=help&modules=query%2Busers
TODO: need to handle maximum request threshold and sleeping...
"""
import requests


class RecommendExperienced():
    def __init__(self, argv):
        self.active_editor_file = argv[1]

        self.list_active_editors = []
        self.list_bots = []
        self.dict_editor_text_id = {}
        self.dict_editor_text_editcount = {}

        self.exp_editor_thr = 100

        self.url_userinfo = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=users"
        self.url_usercontb = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=usercontribs&"

        self.debug = True
        # self.list_bots = self.read_bot_list(argv[2])

    def read_active_editors(self):
        # each line only contain an editor name
        for line in open(self.active_editor_file, "r").readlines()[1:]:
            self.list_active_editors.append(line.replace("\n", ""))

    # query the active editors to obtain their total edits in Wikipedia
    def identify_experienced_editor(self):
        cnt_editor, str_editors = 0, ""
        for editor_text in self.list_active_editors:

            # create a list of editors to request at the same time (50 maximum)
            if cnt_editor < 50:
                cnt_editor += 1
                str_editors += editor_text + "%7C"
            else:
                query = self.url_userinfo + "&usprop=editcount&ususers=" + str_editors
                # TODO: check query limit
                for editor_info in requests.get(query).json()['query']['users']:
                    editor_text = editor_info['name']
                    editor_id = editor_info['userid']
                    editor_editcount = editor_info['editcount']

                    if editor_editcount < self.exp_editor_thr or editor_text in self.list_bots:
                        continue

                    self.dict_editor_text_id[editor_text] = editor_id
                    self.dict_editor_text_editcount[editor_text] = editor_editcount
                    print("{},{},{}".format(editor_text, editor_id, editor_editcount))

                cnt_editor, str_editors = 0, ""
                if self.debug:
                    break
        print("Number of active editors: {}; experienced editors: {}".format(len(self.list_active_editors),
                                                                             len(self.dict_editor_text_id)))

    def constr_cont_url(self, editor_text, wpcont):
        query = self.url_usercontb + "uclimit=5&ucnamespace=0%7C3%7C4%7C5&" \
                                     "ucprop=title%7Ctimestamp%7Cparsedcomment%7Csizediff&ucuser=" + editor_text
        query += "&uccontinue=" + wpcont
        return query


    def constr_original_url(self, editor_text):
        query = self.url_usercontb + "uclimit=5&ucnamespace=0%7C3%7C4%7C5&" \
                                     "ucprop=title%7Ctimestamp%7Cparsedcomment%7Csizediff&ucuser=" + editor_text
        return query

    def fetch_edit_history(self):

        uccontinue = ''

        for editor_text in self.dict_editor_text_id.keys():
            first = True
            cnt_page = 0
            while True:
                try:
                    cnt_page += 1
                    if cnt_page == 3:
                        break
                    if first:
                        query = self.constr_original_url(editor_text)
                        first=False
                    else:
                        query = self.constr_cont_url(editor_text, uccontinue)

                    # query = self.url_usercontb + "ucnamespace=0%7C3%7C4%7C5&" \
                    #                              "ucprop=title%7Ctimestamp%7Cparsedcomment%7Csizediff&" \
                    #                              "ucuser=" + editor_text + "&uccontinue=" + uccontinue
                    response = requests.get(query).json()
                    uccontinue = response['continue']['uccontinue']

                    for usercontrib in response['query']['usercontribs']:
                        title = usercontrib['title']
                        ns = usercontrib['ns']
                        userid = usercontrib['userid']
                        user = usercontrib['user']
                        # TODO: check with userid to make sure same editor

                        # TODO: handle different pages
                        print("{},{},{},{}".format(user, userid, title, ns))

                except KeyError:

                    if "error" in response:
                        print("Code: {}; Info{}".format(response['error']['code'],
                                                        response['error']['info']))
                    print("Error here...")

                    if "error" in response and response['error']['code'] == 'maxlag':
                        ptime = max(5, int(response.headers['Retry-After']))
                        print('WD API is lagged, waiting {} seconds to try again'.format(ptime))
                        from time import sleep

                        sleep(ptime)
                        continue



    def parse_revision_page(self):
        # parse the single page
        pass

    def identify_project_members(self):
        pass

    @staticmethod
    def read_bot_list(bot_file):
        # TODO: update the bot file
        # each line only contain an editor name
        list_bot = []
        for line in open(bot_file, "r").readlines()[1:]:
            list_bot.append(line.replace("\n", ""))
        return list_bot

    def run(self):
        self.read_active_editors()
        self.identify_experienced_editor()
        self.fetch_edit_history()


def main():
    from sys import argv
    # if len(argv) != 2:
    # print("Usage: <active_editors> <bot_list>")
    #     return

    rec_exp = RecommendExperienced(argv)
    rec_exp.run()


main()