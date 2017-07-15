from __future__ import print_function

__author__ = 'bobo'

"""
Related APIs for different methods
1. identify_experienced_editor(): https://www.mediawiki.org/w/api.php?action=help&modules=query%2Busers
TODO: need to handle maximum request threshold and sleeping...
"""
import requests

# todo: print out decode/encode problem...

class RecommendExperienced():
    def __init__(self, argv):

        self.list_active_editors = []
        self.list_bots = []
        self.list_sample_projects = []
        self.dict_editor_text_id = {}
        self.dict_editor_text_editcount = {}
        self.project_members = {}

        self.exp_editor_thr = 100

        self.url_userinfo = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=users"
        self.url_usercontb = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=usercontribs&"
        self.url_propages = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=prefixsearch&"
        self.url_contributors = "https://en.wikipedia.org/w/api.php?action=query&format=json&prop=contributors&"

        self.debug = True
        self.list_active_editors = self.read_active_editors(argv[1])
        self.list_sample_projects = self.read_sample_projects(argv[2])
        # self.list_bots = self.read_bot_list(argv[3])


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
                        if ns == 0:
                            # todo: get the user talk page
                            pass
                        elif ns == 3:
                            # which identify project member
                            pass
                        else:
                            # project it belongs to
                            pass
                        # TODO: get the page
                        print("{},{},{},{}".format(user, userid, title, ns))

                except KeyError:

                    if "error" in response:
                        print("Code: {}; Info{}".format(response['error']['code'],
                                                        response['error']['info']))

                    if "error" in response and response['error']['code'] == 'maxlag':
                        ptime = max(5, int(response.headers['Retry-After']))
                        print('WD API is lagged, waiting {} seconds to try again'.format(ptime))
                        from time import sleep
                        sleep(ptime)
                        continue

                    break



    def parse_revision_page(self):
        # parse the single page
        pass


    def identify_project_members(self):
        for project in self.list_sample_projects:
            # search project talk pages
            # search project pages

            # pssearch=Wikipedia%3AWikiProject+Women+in+Red

            contr_project_pages = self.search_project_pages(project)
            contr_project_talk_pages = self.search_project_talk_pages(project)
            self.project_members[project] = contr_project_pages + contr_project_talk_pages


    def constr_original_page(self, page):
        query = self.url_contributors + "pclimit=5&titles=" + page
        return query

    def constr_next_page(self, page, cont):
        query = self.url_contributors + "pclimit=5&pccontinue=" + cont + "&titles=" + page
        return query

    def search_page_contributors(self, page_id, page_title):
        first = True
        pccontinue = ""
        contributors = []

        while True:
            try:
                if first:
                    query = self.constr_original_page(page_title)
                    first = False
                else:
                    query = self.constr_next_page(page_title, pccontinue)

                # todo: change page_title limit
                # query = self.url_contributors + "pclimit=5&pccontinue=&titles=" + page_title
                response = requests.get(query).json()
                pccontinue = response['continue']['pccontinue']

                for editor in response['query']['pages'][str(page_id)]['contributors']:
                    editor_text = editor['name']
                    editor_id = editor['userid']
                    contributors.append(editor_text)

            except KeyError:
                if "error" in response:
                    print("Code: {}; Info{}".format(response['error']['code'],
                                                    response['error']['info']))

                if "error" in response and response['error']['code'] == 'maxlag':
                    ptime = max(5, int(response.headers['Retry-After']))
                    print('WD API is lagged, waiting {} seconds to try again'.format(ptime))
                    from time import sleep
                    sleep(ptime)
                    continue

                break

        return contributors


    def search_project_pages(self, project):
        contributors = set()
        search_name = "Wikipedia:WikiProject " + project
        psoffset = "0"

        while True:
            try:
                # todo: change page limit
                query = self.url_propages + "pslimit=5&psnamespace=4%7C5&psoffset=" + str(psoffset) + "&pssearch=" + search_name
                response = requests.get(query).json()

                psoffset = response['continue']['psoffset']

                for page in response['query']['prefixsearch']:
                    page_id = page['pageid']
                    page_ns = page['ns']
                    page_title = page['title']

                    values = self.search_page_contributors(page_id, page_title)
                    set_value = set(values)
                    contributors = contributors.union(set_value)

            except KeyError:
                if "error" in response:
                    print("Code: {}; Info{}".format(response['error']['code'],
                                                    response['error']['info']))

                if "error" in response and response['error']['code'] == 'maxlag':
                    ptime = max(5, int(response.headers['Retry-After']))
                    print('WD API is lagged, waiting {} seconds to try again'.format(ptime))
                    from time import sleep
                    sleep(ptime)
                    continue

                break

        return contributors

    def search_project_talk_pages(self, project):
        contributors = []
        return



    @staticmethod
    def read_active_editors(file_editors):
        list_editors = []
        # each line only contain an editor name
        for line in open(file_editors, "r").readlines()[1:]:
            list_editors.append(line.replace("\n", ""))
        return list_editors

    @staticmethod
    def read_sample_projects(file_project):
        # each line only contain an editor name
        list_projects = []
        for line in open(file_project, "r").readlines()[1:]:
            project = line.split(",")[0].replace("WikiProject_", "").replace("_", " ")
            list_projects.append(project)
        return list_projects

    @staticmethod
    def read_bot_list(bot_file):
        # TODO: update the bot file
        # each line only contain an editor name
        list_bot = []
        for line in open(bot_file, "r").readlines()[1:]:
            list_bot.append(line.replace("\n", ""))
        return list_bot

    def run(self):
        # self.identify_experienced_editor()
        # self.fetch_edit_history()
        self.identify_project_members()


def main():
    from sys import argv
    # if len(argv) != 2:
    # print("Usage: <active_editors> <bot_list>")
    #     return

    rec_exp = RecommendExperienced(argv)
    rec_exp.run()


main()