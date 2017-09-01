from __future__ import print_function
from page_parser import PageParser


class RecommendWIR:
    def __init__(self):
        self.set_members = set()
        self.parser = PageParser()

    def create_WIR_member_list(self):
        set_members = set()

        page = "Wikipedia:WikiProject_Women_in_Red/Outreach/List"
        members = self.parser.WIR_member_parse_template(page)
        set_members = set_members.union(members)


        page = "Wikipedia:WikiProject_Women_in_Red/Outreach/International_list"
        members = self.parser.WIR_member_parse_externallinks(page)
        set_members = set_members.union(members)

        page = "Wikipedia:WikiProject_Women_in_Red/Outreach/Opt-out"
        members = self.parser.WIR_member_parse_wikilinks(page)
        set_members = set_members.union(members)

        page = "Wikipedia:WikiProject_Women_in_Red/Members"
        members = self.parser.WIR_member_parse_text(page)
        set_members = set_members.union(members)


        self.set_members = set_members
        return set_members

    def identify_WIR_article_creators(self):
        dict_editor_creators = {}
        dict_editor_article = {}
        for article in self.parser.WIR_report_to_candidates():

            query = "https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvlimit=1&rvprop=timestamp|user&rvdir=newer&format=json&titles="+ article
            # query = self.url_page + page
            try:
                pages = requests.get(query).json()['query']['pages']
                for page_id in pages:
                    page = pages[page_id]
                    page_title = page['title']
                    for rev in page['revisions']:
                        user_text = rev['user']
                        timestamp = rev['timestamp']


                        if user_text in dict_editor_creators:
                            dict_editor_creators[user_text] += 1
                            dict_editor_article[user_text].add(article)
                        else:
                            dict_editor_creators[user_text] = [article]
            except Exception:
                print("Errors")

        import operator
        sorted_x = sorted(dict_editor_creators.items(), key=operator.itemgetter(1), reverse=True)

        list_editor_sorted = []
        dict_editor_page_creation = {}
        for (editor_text, creation_cnt) in sorted_x:
            list_editor_sorted.append(editor_text)
            dict_editor_page_creation[editor_text] = creation_cnt

        return list_editor_sorted, dict_editor_page_creation, dict_editor_article

    def identify_WIR_candidate_info(self):
        # TODO: activity level
        # TODO: regstration time
        # TODO: total edits in ENWP
        pass

    def execute(self):
        self.create_WIR_member_list()
        self.identify_WIR_article_creators()

        self.identify_WIR_candidate_info()

        # TODO: send to table generator to create the recommendaiton table


def main():
    self = RecommendWIR()
    self.create_WIR_member_list()


main()