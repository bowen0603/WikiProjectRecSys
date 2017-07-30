from __future__ import print_function
from page_parser import PageParser
from recommend_cf_editors import UUCF


__author__ = 'bobo'

"""
Related APIs for different methods
1. identify_newcomers_and_experienced_editors(): https://www.mediawiki.org/w/api.php?action=help&modules=query%2Busers
TODO: need to handle maximum request threshold and sleeping...

2. Create active editors in the past week to start with:
    https://quarry.wmflabs.org/query/20246
"""
import requests
from time import sleep
import random
from datetime import datetime
import os.path


class RecommendExperienced():
    def __init__(self, argv):

        # TODO to chagne
        self.const_recommendation_nbr = 20  # 20
        self.const_max_requests = 500  # 500
        self.constr_newcomer_days = 5
        self.debug = True
        self.debug_nbr = 100

        self.list_active_editors = []
        self.list_bots = []
        self.list_sample_projects = []

        self.dict_editor_text_id = {}
        self.dict_editor_text_editcount = {}
        self.dict_editor_last_edit_datetime = {}
        self.dict_editor_is_valid = self.read_editor_validation_from_file()
        # computed by the contributors of project related pages
        # self.dict_project_members = {}
        self.dict_project_sub_pages = {}
        self.dict_project_sub_talkpages = {}
        self.dict_page_title_id = {}
        self.dict_project_contributors = {}

        self.dict_newcomer_text_id = {}
        self.dict_editor_regstr_time = {}
        self.dict_newcomer_editcount = {}
        self.dict_newcomer_first_edit_article = {}
        self.dict_editor_project_talker_nbr = {}

        self.exp_editor_thr = 100

        self.url_userinfo = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=users"
        self.url_usercontb = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=usercontribs&"
        self.url_propages = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=prefixsearch&"
        self.url_contributors = "https://en.wikipedia.org/w/api.php?action=query&format=json&prop=contributors&"

        self.list_active_editors = self.read_active_editors()
        self.list_sample_projects, self.dict_topic_based_recommendation, self.dict_rule_based_recommendation, \
            self.dict_bonds_based_recommendation, self.dict_project_newcomer_edits = self.read_sample_projects()
        self.list_bots = self.read_bot_list()

        self.page_parser = PageParser()
        self.uucf = UUCF()

        # the projects an article within the scope of - parsed from article talk pages
        self.dict_article_projects = self.read_article_projects()
        self.dict_article_categories = self.read_article_categories()

        self.dict_project_categories = self.read_project_categories()


    # query the active editors to obtain their total edits in Wikipedia
    def identify_newcomers_and_experienced_editors(self):
        print("### Identifying newcomers and active experienced editors to recommend ###")

        cnt_total_editor, cnt_editor, str_editors = 0, 0, ""
        for editor_text in self.list_active_editors:

            if self.debug:
                if cnt_total_editor > self.debug_nbr:
                    break
                cnt_total_editor += 1

            # check if the editor is vandal or blocked
            if editor_text in self.dict_editor_is_valid:
                if not self.dict_editor_is_valid[editor_text]:
                    continue

            is_valid = self.page_parser.is_blocked_editor(editor_text)
            self.dict_editor_is_valid[editor_text] = is_valid
            if not is_valid:
                continue

            # create a list of editors to request at the same time (50 maximum)
            if cnt_editor < 45:
                cnt_editor += 1
                str_editors += editor_text + "|"
            else:
                try:
                    query = self.url_userinfo + "&usprop=editcount|registration&ususers=" + str_editors
                    response = requests.get(query).json()
                    for editor_info in response['query']['users']:
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

                            self.dict_editor_regstr_time[editor_text] = regstr_datetime

                        # collect data for experienced editors
                        if editor_editcount >= self.exp_editor_thr and editor_text not in self.list_bots:
                            self.dict_editor_text_id[editor_text] = editor_id
                            self.dict_editor_text_editcount[editor_text] = editor_editcount

                            self.dict_editor_regstr_time[editor_text] = regstr_datetime
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

                    # print("{},{},{}".format(editor_text, editor_id, editor_editcount))

                cnt_editor, str_editors = 0, ""
        print(
            "Number of active editors: {}; experienced editors: {}; newcomers: {}".format(len(self.list_active_editors),
                                                                                          len(self.dict_editor_text_id),
                                                                                          len(self.dict_newcomer_text_id)))

    def recommend_editors(self):
        print("#### Working on newcomers... ####")
        self.fetch_history(self.dict_newcomer_text_id.keys(), True)
        self.write_newcomer_recommendations()

        print("#### Working on experienced editors... ####")
        self.fetch_history(self.dict_editor_text_id.keys(), False)
        self.write_rule_recommendations()
        self.write_bonds_recommendations()


    def fetch_history(self, editor_list, is_newcomers):

        # TODO: write members that are done fetching into a file with the latest timestamp
        # TODO: write the articles editor edited into files to fasten the process
        editor_cnt = 0

        for editor_text in editor_list:
            if editor_cnt % 1000 == 0:
                print("## Retrieving and analyzing {}k editors.. ".format(editor_cnt / 1000))

            # print("#{}. Retrieving and analyzing edits of editor: {}.".format(editor_cnt, editor_text))
            editor_cnt += 1
            latest_datetime = datetime.fromordinal(1)

            edits_ns0_articles = {}
            edits_ns3_users = {}

            # todo: extract projects from userboxes
            # projects_userbox = self.page_parser.extract_user_projects(editor_text)

            # Just fetch 500 edits using one query for each editor
            try:
                query = self.url_usercontb + "uclimit=" + str(self.const_max_requests) + "&ucnamespace=0|3|4|5&" \
                                                                                         "ucprop=title|timestamp|parsedcomment|sizediff|ids&ucuser=" + editor_text
                response = requests.get(query).json()

                for usercontrib in response['query']['usercontribs']:
                    page_title = usercontrib['title']
                    page_id = usercontrib['pageid']
                    ns = usercontrib['ns']
                    userid = usercontrib['userid']
                    # user_text = usercontrib['user']

                    edit_datetime = datetime.strptime(usercontrib['timestamp'], "%Y-%m-%dT%H:%M:%SZ")
                    latest_datetime = max(edit_datetime, latest_datetime)
                    self.dict_editor_last_edit_datetime[editor_text] = latest_datetime

                    if ns == 0:
                        # TODO: check if this is the first edit of the editor ...
                        if is_newcomers and editor_text not in self.dict_newcomer_first_edit_article:
                            self.dict_newcomer_first_edit_article[editor_text] = page_title

                        page_title = page_title.lower()
                        edits_ns0_articles[page_title] = 1 if page_title not in edits_ns0_articles \
                            else edits_ns0_articles[page_title] + 1

                    elif ns == 3:
                        if not is_newcomers:
                            edits_ns3_users[page_title] = 1 if page_title not in edits_ns3_users \
                                else edits_ns3_users[page_title] + 1
                    else:
                        # don't really need to do anything for edits on project pages,
                        # since project contributors have been identified
                        pass

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

            # process editor's revisions for recommendations

            # handle rule-based recommendation by article page edits
            stats_edits_projects_articles = self.compute_project_article_edits(edits_ns0_articles)
            if is_newcomers:
                # TODO: need to get the first edit for newcomers
                self.maintain_project_newcomer_recommendation_lists(editor_text, stats_edits_projects_articles)
            else:

                editor_topic_vector = self.compute_editor_topic_vector(edits_ns0_articles)
                # ignore not valid editors
                if not editor_topic_vector:
                    continue

                self.maintain_project_topic_based_recommendation_lists(editor_text, editor_topic_vector)

                self.maintain_project_rule_based_recommendation_lists(editor_text, stats_edits_projects_articles)

                # TODO: insert sort to get topic editors who edited project related pages
                stats_edits_projects_users, self.dict_editor_project_talker_nbr[editor_text] = \
                    self.compute_project_user_edits(edits_ns3_users)
                self.maintain_project_bonds_based_recommendation_lists(editor_text, stats_edits_projects_users)



                # editor - project - edits
                # TODO: identify himself as project contributor
                # stats_edits_projects_pages = self.compute_project_page_edits(edits_ns45_projects)

    def maintain_project_topic_based_recommendation_lists(self, user_text, editor_topic_vector):
        for project in self.dict_project_categories:
            val = self.compute_topic_cosine_similarity(editor_topic_vector, self.dict_project_categories[project])

            # todo: how to deal with the duplicated recommendations for different projects ??

            # insert the new editor
            dict_recommended_editors = self.dict_topic_based_recommendation[project]
            dict_recommended_editors[user_text] = val

            # identify the least to recommending editor, and remove it from the list
            if len(dict_recommended_editors) > self.const_recommendation_nbr:
                editor_min = min(dict_recommended_editors, key=dict_recommended_editors.get)
                del dict_recommended_editors[editor_min]


    # maintain the list in sorted order by editors who made top N edits on artiles within the scope of the project
    def maintain_project_rule_based_recommendation_lists(self, user_text, stats_edits_projects_articles):
        for project in self.dict_project_contributors.keys():

            # skip if is project member TODO: or has userbox
            if project in self.dict_project_contributors and user_text in self.dict_project_contributors[project]:
                continue

            if project not in stats_edits_projects_articles:
                continue

            # insert the new editor
            dict_recommended_editors = self.dict_rule_based_recommendation[project]
            dict_recommended_editors[user_text] = stats_edits_projects_articles[project]

            # identify the least to recommending editor, and remove it from the list
            if len(dict_recommended_editors) > self.const_recommendation_nbr:
                editor_min = min(dict_recommended_editors, key=dict_recommended_editors.get)
                del dict_recommended_editors[editor_min]


    def maintain_project_bonds_based_recommendation_lists(self, user_text, stats_edits_projects_users):
        for project in self.dict_project_contributors:

            # skip if is project member TODO: or has userbox
            if project in self.dict_project_contributors and user_text in self.dict_project_contributors[project]:
                continue

            if project not in stats_edits_projects_users:
                continue

            # insert the new editor
            dict_recommended_editors = self.dict_bonds_based_recommendation[project]
            dict_recommended_editors[user_text] = stats_edits_projects_users[project]

            if len(dict_recommended_editors) > self.const_recommendation_nbr:
                editor_min = min(dict_recommended_editors, key=dict_recommended_editors.get)
                del dict_recommended_editors[editor_min]

    # randomly pick one project for the newcomer to recommend based on the first article the editor edited
    def maintain_project_newcomer_recommendation_lists(self, editor_text, stats_edits_projects_articles):
        # it is possible that the new editor didn't edit the article page
        if editor_text not in self.dict_newcomer_first_edit_article:
            return

        if self.dict_newcomer_first_edit_article[editor_text].lower() in self.dict_article_projects:
            projects = self.dict_article_projects[self.dict_newcomer_first_edit_article[editor_text].lower()]
            project = random.choice(projects)

            project_members = self.dict_project_newcomer_edits[project]
            # get the edits within the project
            project_members[editor_text] = stats_edits_projects_articles[project]


    def compute_editor_topic_vector(self, edits_article_pages):
        editor_topic_vector = {}
        for article in edits_article_pages:
            cnt_edits = edits_article_pages[article]

            # get the project of the articles read from dump data
            if article in self.dict_article_categories:
                categories = self.dict_article_categories[article]

                # nested structure with both (category, category weight)
                for category in categories:
                    weight = cnt_edits * categories[category]
                    editor_topic_vector[category] = weight if category not in editor_topic_vector \
                        else editor_topic_vector[category] + weight
        sum_value = sum(editor_topic_vector.values())
        if sum_value != 0:
            factor = 1.0 / sum_value
            editor_topic_vector = {k: v * factor for k, v in editor_topic_vector.items()}
        return editor_topic_vector

    # computer article edits on the sample projects
    def compute_project_article_edits(self, edits_article_pages):

        stats_edits_project_articles = {}
        for article in edits_article_pages:
            cnt_edits = edits_article_pages[article]

            # get the project of the articles read from dump data
            if article in self.dict_article_projects:
                projects = self.dict_article_projects[article]

                for project in projects:
                    stats_edits_project_articles[project] = cnt_edits if project not in stats_edits_project_articles \
                        else stats_edits_project_articles[project] + cnt_edits
        return stats_edits_project_articles

    # handle user talk pages (ns 3)
    def compute_project_user_edits(self, edits_user_pages):
        stats_edits_users = {}
        stats_project_per_talker = {}
        for page in edits_user_pages:
            cnt_edits = edits_user_pages[page]
            user_text = page.replace("User talk:", "")

            for project in self.list_sample_projects:
                if project in self.dict_project_contributors and \
                                user_text not in self.dict_project_contributors[project]:
                    continue
                stats_edits_users[project] = cnt_edits if project not in stats_edits_users \
                    else stats_edits_users[project] + cnt_edits
                stats_project_per_talker[project] = 1 if project not in stats_project_per_talker \
                    else stats_project_per_talker[project] + 1
        return stats_edits_users, stats_project_per_talker

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
                                                                                     len(set_project_pages) +
                                                                                     len(set_project_talk_pages)))
                # write into file
                for page in set_project_pages:
                    print("{}**{}".format(project, page), file=fout)
                for page in set_project_talk_pages:
                    print("{}**{}".format(project, page), file=fout)
        print()


    def identify_project_members_and_edits(self):

        # read into a list; create into a set
        cwd = os.getcwd()
        # TODO: create file name
        fname = cwd + "/data/project_members.csv"
        if os.path.isfile(fname):
            print("### Reading members of WikiProjects from file ###")
            header = True
            for line in open(fname, 'r'):
                if header:
                    header = False
                    continue
                project = line.split('*')[0].strip()
                contributor = line.split('*')[1].strip()
                if project in self.dict_project_contributors:
                    self.dict_project_contributors[project].append(contributor)
                else:
                    self.dict_project_contributors[project] = [contributor]
            for project in self.dict_project_contributors.keys():
                print(
                    "Reading {} contributors for WikiProject: {}.".format(len(self.dict_project_contributors[project]),
                                                                          project))
        else:
            print("### Collecting members of WikiProjects, and writing into file ###")
            fout = open(fname, 'w')
            for project in self.list_sample_projects:
                contributors = set()
                if project in self.dict_project_sub_pages:
                    contributors = contributors.union(
                        self.search_page_contributors(self.dict_project_sub_pages[project]))

                if project in self.dict_project_sub_talkpages:
                    contributors = contributors.union(
                        self.search_page_contributors(self.dict_project_sub_talkpages[project]))

                self.dict_project_contributors[project] = contributors

                # TODO: identify project memebers' most recent 500 edits on articles
                print("Collecting contributors for WikiProject:{}. {} contributors.".format(project,
                                                                                            len(contributors)))
                # write into files
                print("wikiproject*editor_text", file=fout)
                for contributor in contributors:
                    print("{}*{}".format(project, contributor), file=fout)
        print()


    def constr_original_page(self, pages):
        query = self.url_contributors + "pclimit=" + str(self.const_max_requests) + "&titles=" + pages
        return query

    def constr_next_page(self, pages, cont):
        query = self.url_contributors + "pclimit=" + str(
            self.const_max_requests) + "&pccontinue=" + cont + "&titles=" + pages
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
                            break  # TODO: not entirely sure about this terminal condition
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
                query = self.url_propages + "pslimit=" + str(
                    self.const_max_requests) + "&psnamespace=4|5&psoffset=" + str(psoffset) + "&pssearch=" + search_name
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
        # sort the list if needed
        # import operator
        # list_recommended_editors_sorted = sorted(dict_recommended_editors.items(), key=operator.itemgetter(1))

        fout = open("data/recommendations_rule.csv", "w")
        print("wikiproject**editor_text**user_id**project_edits**wp_edits**last_edit**regstr_time", file=fout)
        for wikiproject in self.list_sample_projects:
            for editor_text in self.dict_rule_based_recommendation[wikiproject]:
                print("{}**{}**{}**{}**{}**{}**{}".format(wikiproject, editor_text,
                                                          self.dict_editor_text_id[editor_text],
                                                          self.dict_rule_based_recommendation[wikiproject][editor_text],
                                                          self.dict_editor_text_editcount[editor_text],
                                                          self.dict_editor_last_edit_datetime[editor_text],
                                                          self.dict_editor_regstr_time[editor_text]), file=fout)

    def write_bonds_recommendations(self):
        fout = open("data/recommendations_bonds.csv", "w")
        print("wikiproject**editor_text**user_id**pjtk_cnt**talker_cnt**wp_edits**last_edit**regstr_time", file=fout)
        for wikiproject in self.list_sample_projects:
            for editor_text in self.dict_bonds_based_recommendation[wikiproject]:
                print("{}**{}**{}**{}**{}**{}**{}**{}".format(wikiproject, editor_text,
                                                              self.dict_editor_text_id[editor_text],
                                                              self.dict_bonds_based_recommendation[wikiproject][
                                                                  editor_text],
                                                              self.dict_editor_project_talker_nbr[editor_text][
                                                                  wikiproject],
                                                              self.dict_editor_text_editcount[editor_text],
                                                              self.dict_editor_last_edit_datetime[editor_text],
                                                              self.dict_editor_regstr_time[editor_text]), file=fout)

    def write_newcomer_recommendations(self):
        fout = open("data/recommendations_newcomers.csv", "w")
        print("wikiproject**user_text**user_id**first_article**project_edits**wp_edits**last_edit**regstr_time",
              file=fout)
        for wikiproject in self.dict_project_newcomer_edits.keys():
            for editor_text in self.dict_project_newcomer_edits[wikiproject]:
                print("{}**{}**{}**{}**{}**{}**{}**{}".format(wikiproject, editor_text,
                                                              self.dict_newcomer_text_id[editor_text],
                                                              self.dict_newcomer_first_edit_article[editor_text],
                                                              self.dict_project_newcomer_edits[wikiproject][
                                                                  editor_text],
                                                              self.dict_newcomer_editcount[editor_text],
                                                              self.dict_editor_last_edit_datetime[editor_text],
                                                              self.dict_editor_regstr_time[editor_text]), file=fout)


    @staticmethod
    def compute_topic_cosine_similarity(editor_vector, project_vector):
        cos_val = 0
        for cate in project_vector:
            if cate in editor_vector:
                cos_val += project_vector[cate] * editor_vector[cate]
        return cos_val

    @staticmethod
    def read_project_categories():
        print("### Reading categories of the projects from file... ###")
        projects_categories = {}
        filename = "data/projects_categories.csv"
        if os.path.isfile(filename):
            with open(filename, 'r') as fin:
                next(fin)
                for line in fin:
                    project = line.split(",")[0]
                    projects_categories[project] = {}
                    projects_categories[project]['arts'] = float(line.split(",")[1])
                    projects_categories[project]['geography'] = float(line.split(",")[2])
                    projects_categories[project]['health'] = float(line.split(",")[3])
                    projects_categories[project]['mathematics'] = float(line.split(",")[4])
                    projects_categories[project]['history'] = float(line.split(",")[5])
                    projects_categories[project]['science'] = float(line.split(",")[6])
                    projects_categories[project]['people'] = float(line.split(",")[7])
                    projects_categories[project]['philosophy'] = float(line.split(",")[8])
                    projects_categories[project]['religion'] = float(line.split(",")[9])
                    projects_categories[project]['society'] = float(line.split(",")[10])
                    projects_categories[project]['technology'] = float(line.split(",")[11])
                    projects_categories[project]['NF'] = float(line.split(",")[12].strip())
        return projects_categories


    @staticmethod
    def read_article_projects():
        print("### Reading projects of the articles from file... ###")
        filename = "data/articles_top25_projects.csv"
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
    def read_article_categories():

        print("### Reading categories of the articles from file... ###")
        filename = "data/articles_categories.csv"

        article_categories = {}
        cnt_line = 0
        debug = True
        if os.path.isfile(filename):
            with open(filename, 'r') as fin:
                next(fin)
                for line in fin:
                    if cnt_line > 5000:
                        break
                    cnt_line += 1
                    try:
                        article = line.split(",")[0]
                        category = line.split(",")[1]
                        cnt = int(line.split(",")[2].strip())
                    except ValueError:
                        # skip file reading errors ..
                        continue

                    if article not in article_categories:
                        article_categories[article] = {}
                        article_categories[article][category] = cnt
                    else:
                        article_categories[article][category] = cnt
        return article_categories

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
    def read_active_editors():

        filename = "data/active_editors_past_week.csv"
        list_editors = []
        # each line only contain an editor name
        for line in open(filename, "r").readlines()[1:]:
            list_editors.append(line.replace("\n", ""))
        return list_editors

    @staticmethod
    def read_sample_projects():
        # each line only contain an editor name
        filename = "data/Top25ProjectsPastYear.csv"
        list_projects = []
        dict_project_identity_based_recommendation = {}
        dict_project_rule_based_recommendation = {}
        dict_project_bonds_based_recommendation = {}
        dict_project_newcomer_edits = {}

        for line in open(filename, "r").readlines()[1:]:
            project = line.split(",")[0].replace("WikiProject_", "").replace("_", " ")
            list_projects.append(project)
            dict_project_rule_based_recommendation[project] = {}
            dict_project_bonds_based_recommendation[project] = {}
            dict_project_newcomer_edits[project] = {}
            dict_project_identity_based_recommendation[project] = {}

        return list_projects, dict_project_rule_based_recommendation, \
               dict_project_identity_based_recommendation, dict_project_bonds_based_recommendation, \
               dict_project_newcomer_edits

    def write_experienced_editors_to_file(self):
        with open("data/experienced_editors.csv", "w") as fout:
            print("user_text", file=fout)
            for user_text in self.dict_editor_text_id.keys():
                print("{}".format(user_text), file=fout)

    @staticmethod
    def read_editor_validation_from_file():
        cwd = os.getcwd()
        fname = cwd + "/data/editor_validation.csv"
        dict_editor_is_valid = {}

        if os.path.isfile(fname):
            with open("data/editor_validation.csv", "r") as fin:
                header = True
                for line in fin:
                    if header:
                        header = False
                        continue
                    user_text = line.split('*')[0]
                    is_valid = True if line.split('*')[1].split() == 'True' else False
                    dict_editor_is_valid[user_text] = is_valid
        return dict_editor_is_valid


    def write_editor_validation_to_file(self):
        with open("data/editor_validation.csv", "w") as fout:
            print("user_text,is_valid", file=fout)
            for user_text in self.dict_editor_is_valid.keys():
                print("{}*{}".format(user_text,
                                     self.dict_editor_is_valid[user_text]), file=fout)


    @staticmethod
    def read_bot_list():

        filename = "data/bot_list.csv"
        # each line only contain an editor name
        list_bot = set()
        for line in open(filename, "r").readlines()[1:]:
            list_bot.add(line.strip())
        return list_bot

    def run(self):

        # pre-process
        self.collect_project_related_pages()
        self.identify_project_members_and_edits()
        self.identify_newcomers_and_experienced_editors()

        self.write_experienced_editors_to_file()
        self.write_editor_validation_to_file()

        # recommend editors
        self.recommend_editors()

        # recommend uu cf based editors
        self.uucf.recommend_editors()




def main():
    from sys import argv
    # if len(argv) != 2:
    # print("Usage: <active_editors> <sample_projects> <bot_list> <article_projects>")
    # return
    para1 = argv[1]

    rec_exp = RecommendExperienced(argv)
    rec_exp.run()


import time

start_time = time.time()
main()
print("--- {} hours ---".format(1.0 * (time.time() - start_time) / 3600))