__author__ = 'bobo'
import mwparserfromhell as mwp
import requests
from time import sleep

class PageParser:

    def __init__(self):
        self.url_article = "https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&titles="
        self.url_user = "https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&titles=User:"
        self.url_talk_user = "https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&titles=User talk:"

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

    # TODO: batch of editors or just a small amount?
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

def main():
    parser = PageParser()
    # parser.extract_article_projects("")
    # parser.extract_userboxes("")
    parser.is_blocked_editor("")

main()