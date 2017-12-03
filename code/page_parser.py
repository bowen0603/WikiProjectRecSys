from __future__ import print_function
import mwparserfromhell as mwp
import requests
import re
from time import sleep

__author__ = 'bobo'

class PageParser:

    def __init__(self):
        self.url_article = "https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&titles="
        self.url_page = "https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&titles="
        self.url_user = "https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&titles="
        self.url_talk_user = "https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&titles="


    def extract_article_projects(self, page_title):

        try:
            page_title = "Talk:" + page_title
            query = self.url_article + page_title
            response = requests.get(query).json()

            # a bit complicated nested data structure, but here only to extract page object
            page = list(response['query']['pages'].items())[0][1]
            page_ns = page['ns']
            page_text = page['revisions'][0]['*']

        except KeyError:
            if "error" in response:
                print("Error occurs when parsing article talk page. "
                      "Code: {}; Info {}".format(response['error']['code'],
                                                response['error']['info']))
            return []
        except requests.exceptions.ConnectionError:
            print("Max retries exceeded with url.")
            sleep(5)
            return []
        except:
            print("Throwing except: {}".format(response))
            return []

        wikicode = mwp.parse(page_text)
        wikiprojects = []

        if page_ns == 1:
            templates = wikicode.filter_templates()
            for template in templates:
                if template.name == 'WikiProjectBannerShell':
                    continue

                # todo check if need original names
                if template.name.startswith('WikiProject '):
                    wikiproject = str(template.name).replace("WikiProject ", "").strip()
                    wikiprojects.append(wikiproject)

                if template.name.startswith('WIR'):
                    wikiprojects.append("women in red")

        return wikiprojects

    def check_editors_validation(self, set_editors):
        user_talk_pages, user_pages = "", ""
        for editor_text in set_editors:
            user_talk_pages += 'User talk:' + editor_text + '|'
            user_pages += 'User:' + editor_text + '|'

        editor_validation = {}
        empty_page = {}
        try:
            query = self.url_user + user_talk_pages
            response = requests.get(query).json()
            pages = response['query']['pages']
            for page in pages:
                if 'invalid' in pages[page] or 'missing' in pages[page]:
                    continue

                username = pages[page]['title'].replace("User talk:", "")
                page_ns = pages[page]['ns']
                try:
                    page_text = pages[page]['revisions'][0]['*']
                except KeyError:
                    empty_page[username] = True
                    continue

                is_valid = True
                wikicode = mwp.parse(page_text)
                if page_ns == 3:

                    templates = wikicode.filter_templates()
                    for template in templates:
                        if "block" in template:
                            is_valid = False
                        if "vandalism" in template:
                            is_valid = False
                        if "vandal" in template:
                            is_valid = False
                        if "disruptive" in template:
                            is_valid = False
                        if "uw-" in template:
                            is_valid = False
                        if "banned" in template:
                            is_valid = False

                    comments = wikicode.filter_comments()
                    for comment in comments:

                        content = comment.contents
                        if content.contains('Template:') and content.contains('block'):
                            is_valid = False
                        if content.contains('Template:') and content.contains('vandalism'):
                            is_valid = False
                        if content.contains('Template:') and content.contains('vandal'):
                            is_valid = False
                        if content.contains('Template:') and content.contains('disruptive'):
                            is_valid = False
                        if content.contains('Template:') and content.contains('uw-'):
                            is_valid = False
                        if content.contains('Template:') and content.contains('banned'):
                            is_valid = False

                    tags = wikicode.filter_tags()
                    for tag in tags:
                        if "block" in tag:
                            is_valid = False
                        if "vandalism" in tag:
                            is_valid = False
                        if "vandal" in tag:
                            is_valid = False
                        if "disruptive" in tag:
                            is_valid = False
                        if "uw-" in tag:
                            is_valid = False
                        if "banned" in tag:
                            is_valid = False

                editor_validation[username] = is_valid
                print("*** Invalid editors: {} from user page:".format(username))

        except KeyError:
            if "error" in response:
                print("Error occurs when parsing article talk page. "
                      "Code: {}; Info {}".format(response['error']['code'], response['error']['info']))

        try:
            query = self.url_user + user_pages
            response = requests.get(query).json()
            pages = response['query']['pages']
            for page in pages:

                if 'invalid' in pages[page] or 'missing' in pages[page]:
                    continue

                username = pages[page]['title'].replace('User:', "")
                page_ns = pages[page]['ns']

                try:
                    page_text = pages[page]['revisions'][0]['*']
                except KeyError:
                    if username in empty_page:
                        editor_validation[username] = False
                    continue

                is_valid = True
                wikicode = mwp.parse(page_text)

                if page_ns == 2:
                    templates = wikicode.filter_templates()
                    for template in templates:
                        if "block" in template:
                            is_valid = False
                        if "vandalism" in template:
                            is_valid = False
                        if "vandal" in template:
                            is_valid = False
                        if "disruptive" in template:
                            is_valid = False
                        if "uw-" in template:
                            is_valid = False
                        if "banned" in template:
                            is_valid = False

                    comments = wikicode.filter_comments()
                    for comment in comments:

                        content = comment.contents
                        if content.contains('Template:') and content.contains('block'):
                            is_valid = False
                        if content.contains('Template:') and content.contains('vandalism'):
                            is_valid = False
                        if content.contains('Template:') and content.contains('vandal'):
                            is_valid = False
                        if content.contains('Template:') and content.contains('disruptive'):
                            is_valid = False
                        if content.contains('Template:') and content.contains('uw-'):
                            is_valid = False
                        if content.contains('Template:') and content.contains('banned'):
                            is_valid = False

                    tags = wikicode.filter_tags()
                    for tag in tags:
                        if "block" in tag:
                            is_valid = False
                        if "vandalism" in tag:
                            is_valid = False
                        if "vandal" in tag:
                            is_valid = False
                        if "disruptive" in tag:
                            is_valid = False
                        if "uw-" in tag:
                            is_valid = False
                        if "banned" in tag:
                            is_valid = False

                if not is_valid:
                    editor_validation[username] = is_valid

        except KeyError:
            if "error" in response:
                print("Error occurs when parsing article talk page. "
                      "Code: {}; Info {}".format(response['error']['code'], response['error']['info']))

        return editor_validation

    def is_blocked_editor(self, user_name):

        # check user talk page
        try:
            query = self.url_talk_user + user_name
            response = requests.get(query).json()

            page = list(response['query']['pages'].items())[0][1]
            page_ns = page['ns']
            page_text = page['revisions'][0]['*']

        except KeyError:
            if "error" in response:
                print("Error occurs when parsing article talk page. "
                      "Code: {}; Info {}".format(response['error']['code'],
                                                response['error']['info']))
            return True

        wikicode = mwp.parse(page_text)
        if page_ns == 3:
            comments = wikicode.filter_comments()
            for comment in comments:

                content = comment.contents
                if content.contains('Template:') and content.contains('block'):
                    return True

                if content.contains('Template:') and content.contains('vandalism'):
                    return True

                if content.contains('Template:') and content.contains('vandal'):
                    return True

        # check user page
        try:
            query = self.url_user + user_name
            response = requests.get(query).json()

            page = list(response['query']['pages'].items())[0][1]
            page_ns = page['ns']
            page_text = page['revisions'][0]['*']

        except KeyError:
            if "error" in response:
                print("Error occurs when parsing article talk page. "
                      "Code: {}; Info {}".format(response['error']['code'],
                                                response['error']['info']))
            return True

        wikicode = mwp.parse(page_text)
        if page_ns == 2:
            templates = wikicode.filter_templates()
            for template in templates:
                if template.name.contains('banned'):
                    return True
                if template.name.contains('blocked'):
                    return True

        return False



    def extract_userboxes(self, user_name):
        try:
            user_name = "Doc James"
            query = self.url_user + user_name
            response = requests.get(query).json()

            # a bit complicated nested data structure, but here only to extract page object
            page = list(response['query']['pages'].items())[0][1]
            page_ns = page['ns']
            page_text = page['revisions'][0]['*']

        except KeyError:
            if "error" in response:
                print("Error occurs when parsing article talk page. "
                      "Code: {}; Info {}".format(response['error']['code'],
                                                response['error']['info']))
            return []

        wikicode = mwp.parse(page_text)
        wikiprojects = []

        if page_ns == 2:
            templates = wikicode.filter_templates()
            for template in templates:
                # if template.name == 'WikiProjectBannerShell':
                #     continue

                # todo check all the possible names of project templates ...
                if template.name.startswith('User '):
                    wikiproject = str(template.name).replace('User ', '').strip()
                    wikiprojects.append(wikiproject)

                if template.name.startswith('WIR'):
                    wikiprojects.append("women in red")

        # print(wikiprojects)
        return wikiprojects

    def extract_user_projects(self, user_text):
        userboxes = self.extract_userboxes(user_text)
        projects = self.extract_projects_from_userboxes(userboxes)
        return projects

    def extract_projects_from_userboxes(self, userboxes):
        return None

    def WIR_member_parse_template(self, page):
        set_members = set()
        try:
            query = self.url_page + page
            response = requests.get(query).json()
            pages = response['query']['pages']
            for page in pages:
                page_text = pages[page]['revisions'][0]['*']
                wikicode = mwp.parse(page_text)
                for template in wikicode.filter_templates():
                    if template.startswith("{{#target:User talk:"):
                        user_text = template.replace("{{#target:User talk:", "").replace("}}", "")
                        set_members.add(user_text)

        except Exception:
            print("Error when parsing WIR pages")

        print("Identified {} members from the page: {}.".format(len(set_members), page))
        return set_members

    def WIR_member_parse_externallinks(self, page):
        set_members = set()
        try:
            query = self.url_page + page
            response = requests.get(query).json()
            pages = response['query']['pages']
            for page in pages:
                page_text = pages[page]['revisions'][0]['*']
                wikicode = mwp.parse(page_text)

                for link in wikicode.filter_external_links():
                    idx = link.find(":", 6)
                    raw_text = link[idx:]
                    header = raw_text.split(" ")[0]
                    user_text = raw_text.replace(header + " ", "").replace("]", "")
                    set_members.add(user_text)

        except Exception:
            print("Error when parsing WIR pages")

        print("Identified {} members from the page: {}.".format(len(set_members), page))
        return set_members

    def WIR_member_parse_wikilinks(self, page):
        set_members = set()
        try:
            query = self.url_page + page
            response = requests.get(query).json()
            pages = response['query']['pages']
            for page in pages:
                page_text = pages[page]['revisions'][0]['*']
                wikicode = mwp.parse(page_text)
                for link in wikicode.filter_wikilinks():
                    if link.startswith("[[User:"):
                        user_text = link.replace("[[User:", "").replace("]]", "")
                        set_members.add(user_text)

        except Exception:
            print("Error when parsing WIR pages")

        print("Identified {} members from the page: {}.".format(len(set_members), page))
        return set_members

    def admin_parse_templates(self, page):
        set_members = set()
        try:
            query = self.url_page + page
            response = requests.get(query).json()
            pages = response['query']['pages']
            for page in pages:
                page_text = pages[page]['revisions'][0]['*']
                wikicode = mwp.parse(page_text)
                for template in wikicode.filter_templates():
                    if template.startswith("{{user3|"):
                        user_text = template.replace("{{user3|", "").replace("}}", "")
                        set_members.add(user_text)
        except Exception:
            print("Error when parsing admins pages")

        print("Identified {} members from the page: {}.".format(len(set_members), page))
        return set_members

    def WIR_member_parse_text(self, page):
        set_members = set()
        try:
            query = self.url_page + page
            response = requests.get(query).json()
            pages = response['query']['pages']
            for page in pages:
                page_text = pages[page]['revisions'][0]['*']
                wikicode = mwp.parse(page_text)
                for text in wikicode.filter_text():
                    text = text.strip()
                    try:
                        match = re.match(r".*{{User:(.*)/WikiProjectCards/.*", text, re.M | re.I)
                        user_text = match.group(1)
                        user_text = user_text.replace("[[User:", "").replace("]]", "")
                        set_members.add(user_text)
                    except Exception:
                        continue

        except Exception:
            print("Error when parsing WIR pages")

        print("Identified {} members from the page: {}.".format(len(set_members), page))
        return set_members

    def WIR_report_to_candidates(self, month, year):
        # TODO: make the month flexible
        page = "Wikipedia:WikiProject Women in Red/Metrics/{} {}".format(month, year)
        list_articles = []
        try:
            query = self.url_page + page
            response = requests.get(query).json()
            pages = response['query']['pages']
            for page in pages:
                page_text = pages[page]['revisions'][0]['*']
                wikicode = mwp.parse(page_text)
                for article in wikicode.filter_wikilinks():
                    if "Category" in article:
                        continue

                    list_articles.append(article.replace("[[", "").replace("]]", ""))

        except Exception:
            print("Error when parsing WIR pages")

        return list_articles


    def WIR_parse_page_info_box(self, page):
        # print(page)
        try:
            query = self.url_page + page
            response = requests.get(query).json()

            page = list(response['query']['pages'].items())[0][1]
            page_ns = page['ns']
            page_text = page['revisions'][0]['*']

        except KeyError:
            if "error" in response:
                print("Error occurs when parsing article talk page. "
                      "Code: {}; Info {}".format(response['error']['code'],
                                                response['error']['info']))
            return True

        wikicode = mwp.parse(page_text)
        templates = wikicode.filter_templates()

        for template in templates:
            if template.startswith("{{Infobox "):
                import re
                match = re.match(r"{{Infobox (.*)|.*", str(template.name), re.M | re.I)
                info_box = match.group(0).replace("Infobox ", "").strip()
                # print(info_box)
                return info_box
        return None


    # def identify_WIR_article_creators(self):
    #     dict_editor_creators = {}
    #     dict_editor_article = {}
    #     for article in self.WIR_report_to_candidates():
    #
    #         query = "https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvlimit=1&rvprop=timestamp|user&rvdir=newer&format=json&titles="+ article
    #         # query = self.url_page + page
    #         try:
    #             pages = requests.get(query).json()['query']['pages']
    #             for page_id in pages:
    #                 page = pages[page_id]
    #                 page_title = page['title']
    #                 for rev in page['revisions']:
    #                     user_text = rev['user']
    #                     timestamp = rev['timestamp']
    #
    #                     dict_editor_article[user_text] = article
    #                     if user_text in dict_editor_creators:
    #                         dict_editor_creators[user_text] += 1
    #                     else:
    #                         dict_editor_creators[user_text] = 1
    #         except Exception:
    #             print("Errors")
    #
    #     import operator
    #     sorted_x = sorted(dict_editor_creators.items(), key=operator.itemgetter(1), reverse=True)
    #
    #     list_editor_sorted = []
    #     dict_editor_page_creation = {}
    #     for (editor_text, creation_cnt) in sorted_x:
    #         list_editor_sorted.append(editor_text)
    #         dict_editor_page_creation[editor_text] = creation_cnt
    #
    #     return list_editor_sorted, dict_editor_page_creation, dict_editor_article



# def main():
#     parser = PageParser()
#     # parser.extract_article_projects("")
#     # parser.extract_userboxes("")
#     # parser.is_blocked_editor("")
#     # parser.report_parser()
#     s = set()
#     s.add("Wabryant99")
#     s.add("Abbasxali")
#     print(parser.check_editors_validation(s))
#     # parser.identify_WIR_article_creators()
#
# main()