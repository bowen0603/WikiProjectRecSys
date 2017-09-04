from __future__ import print_function
from page_parser import PageParser
from wikitable_generator import TableGenerator
import requests
from datetime import datetime
import os
from time import sleep


class RecommendWIR:

    def __init__(self, month, year, threshold):
        self.const_one_month_in_days = 30

        self.article_creation_threshold = threshold
        self.threshold_very_active = 100
        self.threshold_active = 5
        self.const_very_active = "Very Active"
        self.const_active = "Active"
        self.const_not_active = "Not Active"
        self.month = month
        self.year = year

        self.const_max_requests = 500
        self.url_userinfo = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=users"
        self.url_usercontb = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=usercontribs&"

        self.debug = False

        self.list_editors_sorted = []
        self.editors_WIR = {}
        self.dict_editor_article = {}

        self.set_members = set()
        self.parser = PageParser()
        self.tabler = TableGenerator()


    def create_WIR_member_list(self):

        page = "Wikipedia:WikiProject_Women_in_Red/Outreach/List"
        members = self.parser.WIR_member_parse_template(page)
        self.set_members = self.set_members.union(members)

        page = "Wikipedia:WikiProject_Women_in_Red/Outreach/International_list"
        members = self.parser.WIR_member_parse_externallinks(page)
        self.set_members = self.set_members.union(members)

        page = "Wikipedia:WikiProject_Women_in_Red/Outreach/Opt-out"
        members = self.parser.WIR_member_parse_wikilinks(page)
        self.set_members = self.set_members.union(members)

        page = "Wikipedia:WikiProject_Women_in_Red/Members"
        members = self.parser.WIR_member_parse_text(page)
        self.set_members = self.set_members.union(members)


    def identify_WIR_article_creators(self):
        cnt = 0
        dict_editor_creation = {}
        list_articles = self.parser.WIR_report_to_candidates(self.month, self.year)
        print("Extracting creators from {} articles..".format(len(list_articles)))
        for article in list_articles:

            cnt += 1
            if cnt % 500 == 0:
                print("{} articles processed..".format(cnt))
            if self.debug:
                if cnt == 50:
                    break

            query = "https://en.wikipedia.org/w/api.php?action=query" \
                    "&prop=revisions&rvlimit=1&rvprop=timestamp|user&rvdir=newer&format=json&titles="+ article
            # query = self.url_page + page
            try:
                pages = requests.get(query).json()['query']['pages']
                for page_id in pages:
                    page = pages[page_id]
                    page_title = page['title']
                    for rev in page['revisions']:
                        user_text = rev['user']
                        timestamp = rev['timestamp']

                        if user_text in dict_editor_creation:
                            dict_editor_creation[user_text] += 1
                            self.dict_editor_article[user_text].append(article)
                        else:
                            dict_editor_creation[user_text] = 1
                            self.dict_editor_article[user_text] = [article]
            except Exception as e:
                print("Errors")

        print("Sorting editors by articles processed.. ")
        import operator
        sorted_x = sorted(dict_editor_creation.items(), key=operator.itemgetter(1), reverse=True)

        cnt_threshold = 0
        dict_editor_page_creation = {}
        for (editor_text, creation_cnt) in sorted_x:
            if creation_cnt >= self.article_creation_threshold:
                cnt_threshold += 1
                self.list_editors_sorted.append(editor_text)
                dict_editor_page_creation[editor_text] = creation_cnt


        print("All article processed")
        print("Total of {} articles created by {} editors."
              "{} editors created more than 1 articles.".format(len(list_articles),
                                                                len(self.dict_editor_article),
                                                                cnt_threshold))
        return dict_editor_page_creation

    def identify_WIR_candidate_info(self):

        print("### Recommending editors for WIR... ###")
        dict_editor_page_creation = self.identify_WIR_article_creators()
        cnt_editor, str_editors, cnt_recommendations = 0, "", 0

        for i in range(len(self.list_editors_sorted)):
            editor_text = self.list_editors_sorted[i]
            if editor_text in self.set_members:
                continue

            if cnt_editor < 45 and i != len(self.list_editors_sorted)-1:
                cnt_editor += 1
                str_editors += editor_text + "|"
            else:
                try:
                    str_editors += editor_text + "|"
                    query = self.url_userinfo + "&usprop=editcount|registration&ususers=" + str_editors
                    response = requests.get(query).json()
                    for editor_info in response['query']['users']:

                        if 'userid' not in editor_info:
                            continue

                        # check basic info
                        editor_text = editor_info['name']
                        editor_editcount = editor_info['editcount']
                        editor_regstr_ts = editor_info['registration']

                        if editor_regstr_ts is None:
                            continue
                        regstr_datetime = datetime.strptime(editor_regstr_ts, "%Y-%m-%dT%H:%M:%SZ")

                        # check most recent 500 edits
                        query = self.url_usercontb + "uclimit=" + str(self.const_max_requests) + "&ucprop=title|timestamp|parsedcomment|flags|ids&ucuser=" + editor_text
                        response = requests.get(query).json()
                        latest_datetime = datetime.fromordinal(1)
                        current_datetime = datetime.now()
                        cnt_mainpage_edits = 0

                        for usercontrib in response['query']['usercontribs']:
                            ns = usercontrib['ns']

                            edit_datetime = datetime.strptime(usercontrib['timestamp'], "%Y-%m-%dT%H:%M:%SZ")

                            if 'parsedcomment' in usercontrib:
                                comment = usercontrib['parsedcomment']
                                if comment.startswith('Revert'):
                                    continue

                            if ns == 0:
                                # count the number of edits within 30 days
                                if (current_datetime - edit_datetime).days <= self.const_one_month_in_days:
                                    cnt_mainpage_edits += 1


                        if cnt_mainpage_edits >= self.threshold_very_active:
                            status = self.const_very_active
                        elif cnt_mainpage_edits >= self.threshold_active:
                            status = self.const_active
                        else:
                            status = self.const_not_active

                        self.editors_WIR[editor_text] = {"page_created": dict_editor_page_creation[editor_text],
                                                    "editcount": editor_editcount,
                                                    "regstr_ts": editor_regstr_ts,
                                                    "status": status}
                        cnt_recommendations += 1

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

                cnt_editor, str_editors = 0, ""

        print("### Writing out recommendations...")
        cwd = os.getcwd()
        fout = open(cwd + "/data/recommendations/recommendations_WIR.csv", "w")
        print("editor_text,page_created,editcount,regstr_ts,article,status", file=fout)
        for editor_text in self.editors_WIR:
            print("{}**{}**{}**{}**{}".format(editor_text,
                                              self.editors_WIR[editor_text]['page_created'],
                                              self.editors_WIR[editor_text]['editcount'],
                                              self.editors_WIR[editor_text]['regstr_ts'],
                                              self.editors_WIR[editor_text]['status']), file=fout)

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

    def execute(self):
        self.create_WIR_member_list()
        # self.identify_WIR_article_creators()

        self.identify_WIR_candidate_info()
        self.tabler.execute_WIR_group(self.list_editors_sorted, self.editors_WIR, self.dict_editor_article, self.month)


def main():
    from sys import argv
    if len(argv) != 4:
        print("Usage: <month> <year> <article_threshold>")
        return

    self = RecommendWIR(month=argv[1], year=argv[2], threshold=int(argv[3]))
    self.execute()


main()