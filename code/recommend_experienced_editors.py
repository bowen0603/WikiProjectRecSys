from __future__ import print_function
from page_parser import PageParser
from datetime import datetime
import os.path

__author__ = 'bobo'

"""
Related APIs for different methods
1. identify_newcomers_and_experienced_editors(): https://www.mediawiki.org/w/api.php?action=help&modules=query%2Busers
TODO: need to handle maximum request threshold and sleeping...
"""
import requests
from time import sleep

# todo: print out decode/encode problem...

class RecommendExperienced():
    def __init__(self, argv):

        # TODO to chagne
        self.const_recommendation_nbr = 20 # 20
        self.const_max_requests = 500 # 500
        self.constr_newcomer_days = 3

        self.list_active_editors = []
        self.list_bots = []
        self.list_sample_projects = []

        self.dict_editor_text_id = {}
        self.dict_editor_text_editcount = {}
        self.dict_editor_last_edit_datetime = {}
        # computed by the contributors of project related pages
        # self.dict_project_members = {}
        self.dict_project_sub_pages = {}
        self.dict_project_sub_talkpages = {}
        self.dict_page_title_id = {}
        self.dict_project_contributors = {}

        self.dict_newcomer_text_id = {}
        self.dict_editor_regstr_time = {}
        self.dict_newcomer_editcount = {}

        self.exp_editor_thr = 100

        self.url_userinfo = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=users"
        self.url_usercontb = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=usercontribs&"
        self.url_propages = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=prefixsearch&"
        self.url_contributors = "https://en.wikipedia.org/w/api.php?action=query&format=json&prop=contributors&"

        self.debug = True
        self.list_active_editors = self.read_active_editors(argv[1])
        self.list_sample_projects, self.dict_project_rule_based_recommendation, self.dict_project_newcomer_edits = self.read_sample_projects(argv[2])
        self.list_bots = self.read_bot_list(argv[3])

        self.parser_cat = PageParser()

        # the projects an article within the scope of - parsed from article talk pages
        # self.dict_article_projects = self.read_article_projects(argv[4])
        # self.fout_art_proj = open(argv[4], 'a')
        self.dict_article_projects = self.read_article_projects(argv[4])


    # query the active editors to obtain their total edits in Wikipedia
    def identify_newcomers_and_experienced_editors(self):
        print("### Identifying newcomers and active experienced editors to recommend ###")

        cnt_total_editor, cnt_editor, str_editors = 0, 0, ""
        for editor_text in self.list_active_editors:

            if self.debug:
                if cnt_total_editor > 100:
                    break
                cnt_total_editor += 1


            # create a list of editors to request at the same time (50 maximum)
            if cnt_editor < 45:
                cnt_editor += 1
                str_editors += editor_text + "|"
            else:
                query = self.url_userinfo + "&usprop=editcount|registration&ususers=" + str_editors
                for editor_info in requests.get(query).json()['query']['users']:
                    if 'userid' not in editor_info:
                        continue

                    editor_text = editor_info['name']
                    editor_id = editor_info['userid']
                    editor_editcount = editor_info['editcount']
                    editor_regstr_ts = editor_info['registration']

                    if editor_regstr_ts is None:
                        delta_days = self.constr_newcomer_days + 1
                    else:
                        regstr_datetime = datetime.strptime(editor_regstr_ts, "%Y-%m-%dT%H:%M:%SZ")
                        delta_days = (datetime.now() - regstr_datetime).days

                    # collect data for newcomers
                    if delta_days <= self.constr_newcomer_days and editor_text not in self.list_bots:
                        self.dict_newcomer_text_id[editor_text] = editor_id
                        self.dict_newcomer_editcount[editor_text] = editor_editcount

                        self.dict_editor_regstr_time[editor_text] = editor_regstr_ts

                    # collect data for experienced editors
                    if editor_editcount >= self.exp_editor_thr and editor_text not in self.list_bots:
                        self.dict_editor_text_id[editor_text] = editor_id
                        self.dict_editor_text_editcount[editor_text] = editor_editcount

                        self.dict_editor_regstr_time[editor_text] = editor_regstr_ts

                    # print("{},{},{}".format(editor_text, editor_id, editor_editcount))

                cnt_editor, str_editors = 0, ""
        print("Number of active editors: {}; experienced editors: {}; newcomers: {}".format(len(self.list_active_editors),
                                                                                          len(self.dict_editor_text_id),
                                                                                          len(self.dict_newcomer_text_id)))

    def fetch_newcomers_and_experienced_editors_history(self):
        print("#### Working on newcomers... ####")
        self.fetch_history(self.dict_newcomer_text_id.keys(), True)
        self.write_newcomer_recommendations()

        print("#### Working on experienced editors... ####")
        self.fetch_history(self.dict_editor_text_id.keys(), False)
        self.write_rule_recommendations()



    def fetch_history(self, editor_list, is_newcomers):

        # TODO: write members that are done fetching into a file with the latest timestamp
        # TODO: write the articles editor edited into files to fasten the process
        editor_cnt = 0

        for editor_text in editor_list:
            print("#{}. Retrieving and analyzing edits of editor: {}.".format(editor_cnt, editor_text))
            editor_cnt += 1
            latest_datetime = datetime.fromordinal(1)

            edits_ns0_artiles = {}
            edits_ns3_users = {}
            edits_ns45_projects = {}

            # todo: extract projects from userboxes
            # projects_userbox = self.parser_cat.extract_user_projects(editor_text)

            # Just fetch 500 edits using one query for each editor
            try:
                query = self.url_usercontb + "uclimit="+str(self.const_max_requests)+"&ucnamespace=0|3|4|5&" \
                                     "ucprop=title|timestamp|parsedcomment|sizediff|ids&ucuser=" + editor_text
                response = requests.get(query).json()

                for usercontrib in response['query']['usercontribs']:
                    page_title = usercontrib['title']
                    page_id = usercontrib['pageid']
                    ns = usercontrib['ns']
                    userid = usercontrib['userid']
                    user_text = usercontrib['user']

                    edit_datetime = datetime.strptime(usercontrib['timestamp'], "%Y-%m-%dT%H:%M:%SZ")
                    latest_datetime = max(edit_datetime, latest_datetime)
                    self.dict_editor_last_edit_datetime[user_text] = latest_datetime

                    # print("{},{},{},{}".format(user_text, userid, page_title, ns))
                    if ns == 0:
                        edits_ns0_artiles[page_title] = 1 if page_title not in edits_ns0_artiles \
                            else edits_ns0_artiles[page_title] + 1

                    elif ns == 3:
                        # todo: create a list of editors talked to
                        # todo: connect with project members(contributors)
                        if not is_newcomers:
                            edits_ns3_users[page_title] = 1 if page_title not in edits_ns3_users \
                            else edits_ns3_users[page_title] + 1
                    else:
                        # todo: check and considered as project contributors
                        if not is_newcomers:
                            edits_ns45_projects[page_title] = 1 if page_title not in edits_ns45_projects \
                            else edits_ns45_projects[page_title] + 1
                        # TODO: get the page

            except KeyError:
                if self.catch_error_to_sleep(response):
                    continue
                else:
                    break
            except requests.exceptions.ConnectionError:
                print("Max retries exceeded with url.")
                sleep(5)
                continue
            except:
                print("Throwing except: {}".format(response))
                continue

            if is_newcomers:
                stats_edits_projects_articles = self.compute_project_article_edits(edits_ns0_artiles)
                self.add_project_newcomer_lists(user_text, stats_edits_projects_articles)
            else:
                # end of fetching revisions of an editor
                stats_edits_projects_articles = self.compute_project_article_edits(edits_ns0_artiles)
                self.maintain_project_rule_based_recommendation_lists(user_text, stats_edits_projects_articles)

                #TODO: insert sort to get topic editors who edited project related pages
                # stats_edits_projects_users = self.compute_project_user_edits(edits_ns3_users)
                # editor - project - talk
                # TODO: bonds-based recommendations
                # projects_editor_communicated_with = self.get_project_member_talks(stats_edits_projects_users)

                # editor - project - edits
                # TODO: identify himself as project contributor
                # stats_edits_projects_pages = self.compute_project_page_edits(edits_ns45_projects)


    # maintain the list in sorted order by editors who made top N edits on artiles within the scope of the project
    def maintain_project_rule_based_recommendation_lists(self, user_text, stats_edits_projects_articles):
        for project in self.dict_project_contributors.keys():

            # skip if is project member TODO: or has userbox
            if project in self.dict_project_contributors and user_text in self.dict_project_contributors[project]:
                continue

            if project not in stats_edits_projects_articles:
                continue

            # insert the new editor
            dict_recommended_editors = self.dict_project_rule_based_recommendation[project]
            dict_recommended_editors[user_text] = stats_edits_projects_articles[project]

            # sort the dict and remove the last one if there are more editors
            import operator
            list_recommended_editors_sorted = sorted(dict_recommended_editors.items(), key=operator.itemgetter(1))

            if len(list_recommended_editors_sorted) > self.const_recommendation_nbr:
                list_recommended_editors_sorted.reverse()
                list_recommended_editors_sorted.pop()
            self.dict_project_rule_based_recommendation[project] = dict(list_recommended_editors_sorted)

    def add_project_newcomer_lists(self, editor_text, stats_edits_projects_articles):
        for project in stats_edits_projects_articles.keys():
            project_members = self.dict_project_newcomer_edits[project]
            # get the edits within the project
            project_members[editor_text] = stats_edits_projects_articles[project]

    # computer article edits on the sample projects
    def compute_project_article_edits(self, edits_article_pages):

        stats_edits_project_articles = {}
        for article in edits_article_pages:
            cnt_edits = edits_article_pages[article]

            # TODO: another option: preprocess using the dump data
            # obtain the projects the article within the scope of
            if article.lower() in self.dict_article_projects:
                projects = self.dict_article_projects[article.lower()]

                for project in projects:
                    stats_edits_project_articles[project] = cnt_edits if project not in stats_edits_project_articles \
                                                    else stats_edits_project_articles[project] + cnt_edits

            # if article in self.dict_article_projects.keys():
            #
            #     projects = self.dict_article_projects[article]
            #     if projects[0] == 'NONE':
            #         continue
            # else:
            #     # TODO: write this into a file: this is static..
            #     projects = self.parser_cat.extract_article_projects(article)
            #     # self.dict_article_projects[article] = projects
            #
            # has_sample_projects = False
            # for project in projects:
            #     if project not in self.list_sample_projects:
            #         continue
            #     has_sample_projects = True
            #
            #     if article in self.dict_article_projects:
            #          self.dict_article_projects[article].append(project)
            #     else:
            #          self.dict_article_projects[article] = [project]

                # print("{}**{}".format(article, project), file=self.fout_art_proj)
                # stats_edits_project_articles[project] = cnt_edits if project not in stats_edits_project_articles \
                #                                     else stats_edits_project_articles[project] + cnt_edits

            # if not has_sample_projects:
            #     self.dict_article_projects[article] = ["NONE"]
            #     print("{}**{}".format(article, "NONE"), file=self.fout_art_proj)
            # self.fout_art_proj.flush()

        return stats_edits_project_articles

    # handle user talk pages (ns 3)
    def compute_project_user_edits(self, edits_user_pages):
        stats_edits_users = {}
        for page in edits_user_pages:
            cnt_edits = edits_user_pages[page]
            user_text = page.replace("User talk:", "")

            for project in self.list_sample_projects:
                if project in self.dict_project_contributors and user_text not in self.dict_project_contributors[project]:
                    continue
                stats_edits_users[project] = cnt_edits if project not in stats_edits_users \
                                                    else stats_edits_users[project] + cnt_edits

        return stats_edits_users

    # handle project talk pages (ns 4 and 5)
    def compute_project_page_edits(self, edits_project_pages):
        stats_edits_projects = {}
        for page in edits_project_pages:
            cnt_edits = edits_project_pages[page]

            for project in self.list_sample_projects:
                if project in self.dict_project_contributors and page not in self.dict_project_sub_talkpages[project]:
                    continue

                stats_edits_projects[project] = cnt_edits if project not in stats_edits_projects \
                                                else stats_edits_projects[project] + cnt_edits

        return stats_edits_projects

    def collect_project_related_pages(self):
        cwd = os.getcwd()
        # TODO: create file name
        fname = cwd + "/data/project_pages.csv"

        if os.path.isfile(fname):
            print("### Reading related pages of WikiProjects from file ###")
            for line in open(fname, 'r'):
                project = line.split("**")[0].strip()
                page = line.split('**')[1].strip()
                if project in self.dict_project_sub_pages:
                    self.dict_project_sub_pages[project].append(page)
                else:
                    self.dict_project_sub_pages[project] = [page]
            for project in self.dict_project_sub_pages.keys():
                print("Reading {} related pages for WikiProject: {}.".format(len(self.dict_project_sub_pages[project]),
                                                                             project))
        else:
            print("### Collecting related pages of WikiProjects, and writing into file ###")
            fout = open(fname, 'w')
            for project in self.list_sample_projects:
                search_name = "Wikipedia:WikiProject " + project
                set_project_pages = self.search_project_pages(search_name)
                self.dict_project_sub_pages[project] = list(set_project_pages)

                search_name = "Wikipedia talk:WikiProject " + project
                set_project_talk_pages = self.search_project_pages(search_name)
                self.dict_project_sub_talkpages[project] = list(set_project_talk_pages)

                print("Collected pages for WikiProject:{}. {} related pages.".format(project,
                                                                                     len(set_project_pages)+
                                                                                     len(set_project_talk_pages)))
                # write into file
                for page in set_project_pages:
                    print("{}**{}".format(project, page), file=fout)
                for page in set_project_talk_pages:
                    print("{}**{}".format(project, page), file=fout)
        print()


    def identify_project_members(self):

        # read into a list; create into a set
        cwd = os.getcwd()
        # TODO: create file name
        fname = cwd + "/data/project_members.csv"
        if os.path.isfile(fname):
            print("### Reading members of WikiProjects from file ###")
            for line in open(fname, 'r'):
                project = line.split('**')[0].strip()
                contributor = line.split('**')[1].strip()
                if project in self.dict_project_contributors:
                    self.dict_project_contributors[project].append(contributor)
                else:
                    self.dict_project_contributors[project] = [contributor]
            for project in self.dict_project_contributors.keys():
                print("Reading {} contributors for WikiProject: {}.".format(len(self.dict_project_contributors[project]),
                                                                            project))
        else:
            print("### Collecting members of WikiProjects, and writing into file ###")
            fout = open(fname, 'w')
            for project in self.list_sample_projects:
                contributors = set()
                if project in self.dict_project_sub_pages:
                    contributors = contributors.union(self.search_page_contributors(self.dict_project_sub_pages[project]))

                if project in self.dict_project_sub_talkpages:
                    contributors = contributors.union(self.search_page_contributors(self.dict_project_sub_talkpages[project]))

                self.dict_project_contributors[project] = contributors
                print("Collecting contributors for WikiProject:{}. {} contributors.".format(project,
                                                                                            len(contributors)))
                # write into files
                for contributor in contributors:
                    print("{}**{}".format(project, contributor), file=fout)
        print()


    def constr_original_page(self, pages):
        query = self.url_contributors + "pclimit="+str(self.const_max_requests)+"&titles=" + pages
        return query

    def constr_next_page(self, pages, cont):
        query = self.url_contributors + "pclimit="+str(self.const_max_requests)+"&pccontinue=" + cont + "&titles=" + pages
        return query

    def search_page_contributors(self, page_titles):

        cnt_page, str_pages, pccontinue = 0, "", ""
        contributors = set()

        # create a list of pages to request at the same time (50 maximum)
        for page_title in page_titles:
            if cnt_page < 45:
                cnt_page += 1
                str_pages += page_title + "|"
            else:
                first_request, continue_querying = True, True
                while continue_querying:
                    try:
                        if first_request:
                            query = self.constr_original_page(str_pages)
                            first_request = False
                        else:
                            query = self.constr_next_page(str_pages, pccontinue)

                        # query = self.url_contributors + "pclimit="+str(self.const_max_requests)+"&pccontinue=&titles=" + page_title
                        response = requests.get(query).json()
                        if 'continue' in response:
                            pccontinue = response['continue']['pccontinue']
                        else:
                            continue_querying = False

                        # a bit complicated nested data structure in response, but here only to extract page contributors
                        pages_object = response['query']['pages']
                        for page in pages_object.keys():
                            if 'contributors' in pages_object[page]:
                                for editor in pages_object[page]['contributors']:
                                    editor_text = editor['name']
                                    editor_id = editor['userid']
                                    contributors.add(editor_text)

                    except KeyError:
                        if self.catch_error_to_sleep(response):
                            continue
                        else:
                            break # TODO: not entirely sure about this terminal condition
                    except requests.exceptions.ConnectionError:
                        print("Max retries exceeded with url.")
                        sleep(5)
                        continue
                    except:
                        print("Throwing except: {}".format(response))
                        continue

                cnt_page, str_pages = 0, ""

        return contributors


    def search_project_pages(self, search_name):
        psoffset = "0"
        list_project_pages = []

        continue_querying = True
        while continue_querying:
            try:
                query = self.url_propages + "pslimit="+str(self.const_max_requests)+"&psnamespace=4|5&psoffset=" + str(psoffset) + "&pssearch=" + search_name
                response = requests.get(query).json()
                if 'continue' in response:
                    psoffset = response['continue']['psoffset']
                else:
                    continue_querying = False

                for page in response['query']['prefixsearch']:
                    page_id = page['pageid']
                    page_ns = page['ns']
                    page_title = page['title']

                    self.dict_page_title_id[page_title] = page_id
                    list_project_pages.append(page_title)

            except KeyError:
                if self.catch_error_to_sleep(response):
                    continue
                else:
                    break
            except requests.exceptions.ConnectionError:
                print("Max retries exceeded with url.")
                sleep(5)
                continue
            except:
                print("Throwing except: {}".format(response))
                continue

        return set(list_project_pages)


    def write_rule_recommendations(self):

        fout = open("data/rule_recommendations.csv", "w")
        print("wikiproject**editor_text**user_id**project_edits**wp_edits**last_edit**regstr_time", file=fout)
        for wikiproject in self.list_sample_projects:
            for editor_text in self.dict_project_rule_based_recommendation[wikiproject]:
                print("{}**{}**{}**{}**{}**{}**{}".format(wikiproject, editor_text,
                                                    self.dict_editor_text_id[editor_text],
                                                    self.dict_project_rule_based_recommendation[wikiproject][editor_text],
                                                    self.dict_editor_text_editcount[editor_text],
                                                    self.dict_editor_last_edit_datetime[editor_text],
                                                    self.dict_editor_last_edit_datetime[editor_text]), file=fout)

    def write_newcomer_recommendations(self):
        # TODO: add newcomer's article

        fout = open("data/sample_newcomers.csv", "w")
        print("wikiproject**user_text**user_id**project**project_edits**wp_edits**last_edit**regstr_time", file=fout)
        for wikiproject in self.dict_project_newcomer_edits.keys():
            for editor_text in self.dict_project_newcomer_edits[wikiproject]:
                print("{}**{}**{}**{}**{}**{}**{}".format(wikiproject, editor_text,
                                                       self.dict_newcomer_text_id[editor_text],
                                                       self.dict_project_newcomer_edits[wikiproject][editor_text],
                                                       self.dict_newcomer_editcount[editor_text],
                                                       self.dict_editor_last_edit_datetime[editor_text],
                                                       self.dict_editor_regstr_time[editor_text]), file=fout)

    @staticmethod
    def read_article_projects(filename):
        print("### Reading projects of the articles from file... ###")
        article_projects = {}
        if os.path.isfile(filename):
            for line in open(filename, 'r'):
                article = line.split(",")[1]
                project = line.split(",")[2].strip()
                if article in article_projects:
                    article_projects[article].append(project)
                else:
                    article_projects[article] = [project]
        return article_projects

    @staticmethod
    def catch_error_to_sleep(response):
        if "error" in response:
            print("Code: {}; Info {}".format(response['error']['code'],
                                            response['error']['info']))

            if response['error']['code'] == 'maxlag':
                ptime = max(5, int(response.headers['Retry-After']))
                print('WD API is lagged, waiting {} seconds to try again'.format(ptime))
                sleep(ptime)
                return True

            if response['error']['code'] == 'internal_api_error_DBQueryError':
                sleep(5)
                return True

        return False

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
        dict_project_rule_based_recommendation = {}
        dict_project_newcomer_edits = {}

        for line in open(file_project, "r").readlines()[1:]:
            project = line.split(",")[0].replace("WikiProject_", "").replace("_", " ")
            list_projects.append(project)
            dict_project_rule_based_recommendation[project] = {}
            dict_project_newcomer_edits[project] = {}
        return list_projects, dict_project_rule_based_recommendation, dict_project_newcomer_edits

    @staticmethod
    def read_bot_list(bot_file):
        # TODO: update the bot file
        # each line only contain an editor name
        list_bot = set()
        for line in open(bot_file, "r").readlines()[1:]:
            list_bot.add(line.strip())
        return list_bot

    def run(self):

        # preprocess
        self.collect_project_related_pages()
        self.identify_project_members()
        self.identify_newcomers_and_experienced_editors()

        # collect edits for recommendation
        self.fetch_newcomers_and_experienced_editors_history()






def main():
    from sys import argv
    # if len(argv) != 2:
    # print("Usage: <active_editors> <sample_projects> <bot_list> <article_projects>")
    #     return

    rec_exp = RecommendExperienced(argv)
    rec_exp.run()

import time
start_time = time.time()
main()
print("--- {} hours ---".format(1.0*(time.time() - start_time)/3600))