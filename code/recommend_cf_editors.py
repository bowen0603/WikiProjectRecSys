from GQuerier import QueryHandler

__author__ = 'bobo'

class UUCF:

    def __init__(self):

        # self.query = QueryHandler()
        self.query = None
        self.top_n = 20
        self.dataset = "bowen_script_uucf"


    def upload_files(self):
        # upload the list of the experienced editors
        dict_schema = [("user_text", "STRING")]
        self.query.create_table(self.dataset, "experienced_editors", dict_schema)
        # TODO: change the file: experienced_editors.csv
        self.query.load_data_from_file(self.dataset, "experienced_editors", "data/experienced_editors.csv")

        # upload project members
        dict_schema = (("wikiproject", "STRING"), ("user_text", "STRING"))
        self.query.create_table(self.dataset, "project_members", dict_schema)
        self.query.load_data_from_file(self.dataset, "project_members", "data/project_members.csv")


    def recommend_editors(self):

        # # extract experienced editors edits on articles: user - article
        # query = """
        #     SELECT t1.rev_user_text AS user_text,
        #         t1.rev_page_title AS article,
        #         COUNT(*) AS article_edits
        #         FROM `{}.{}` t1
        #         INNER JOIN `{}.{}` t2
        #         ON t1.rev_user_text = t2.user_text
        #         WHERE t1.ns = 0
        #         GROUP BY user_text, article
        # """.format("bowen_user_dropouts", "revs",
        #            self.dataset, "experienced_editors") # TODO: change to updated revs table
        # self.query.run_query(query, self.dataset, "experienced_editors_article_edits")
        #
        # # extract project members edits on articles: project - user - article
        # query = """
        #     SELECT t1.rev_user_text AS user_text,
        #         t1.rev_page_title AS article,
        #         COUNT(*) AS article_edits
        #         FROM `{}.{}` t1
        #         INNER JOIN `{}.{}` t2
        #         ON t1.rev_user_text = t2.user_text
        #         WHERE t1.ns = 0
        #         GROUP BY user_text, article
        # """.format("bowen_user_dropouts", "revs", # TODO: change to updated revs table
        #            self.dataset, "project_members")
        # self.query.run_query(query, self.dataset, "project_members_article_edits")
        #
        # query = """
        #     SELECT t1.user_text AS user_text,
        #         t2.wikiproject AS wikiproject,
        #         t1.article AS article,
        #         t1.article_edits AS article_edits
        #         FROM `{}.{}` t1
        #         INNER JOIN `{}.{}` t2
        #         ON t1.user_text = t2.user_text
        # """.format(self.dataset, "project_members_article_edits",
        #            self.dataset, "project_members")
        # self.query.run_query(query, self.dataset, "project_members_project_article_edits")
        #
        # # experienced editors' article edits
        #
        # query = """
        #     SELECT user_text,
        #     COUNT(*) AS article_nbr
        #     FROM `{}.{}`
        #     GROUP BY user_text
        # """.format(self.dataset, "experienced_editors_article_edits")
        # self.query.run_query(query, self.dataset, "experienced_editors_article_counts")
        #
        # # project members article edits
        # query = """
        #     SELECT user_text,
        #     COUNT(*) AS article_nbr
        #     FROM `{}.{}`
        #     GROUP BY user_text
        # """.format(self.dataset, "project_members_article_edits")
        # self.query.run_query(query, self.dataset, "project_members_article_counts")
        #
        #
        # query = """
        #     SELECT t1.user_text AS user_text,
        #     t1.article_nbr AS article_nbr,
        #     t2.wikiproject AS wikiproject
        #     FROM `{}.{}` t1
        #     INNER JOIN `{}.{}` t2
        #     ON t1.user_text = t2.user_text
        # """.format(self.dataset, "project_members_article_counts",
        #            self.dataset, "project_members")
        # self.query.run_query(query, self.dataset, "project_members_project_article_counts")

        # intersections of project members and experienced editors
        query = """
            SELECT t1.user_text AS experienced_editor,
            t2.user_text AS project_member,
            COUNT(*) AS intersections
            FROM `{}.{}` t1
            CROSS JOIN `{}.{}` t2
            WHERE t1.user_text != t2.user_text
            GROUP BY experienced_editor, project_member
        """.format(self.dataset, "experienced_editors_article_edits",
                   self.dataset, "project_members_article_edits")
        self.query.run_query(query, self.dataset, "project_member_experienced_editors_intersections")

        # add in experienced editors article number
        query = """
            SELECT t1.experienced_editor AS experienced_editor,
            t1.project_member AS project_member,
            t1.intersections AS intersections,
            t2.article_nbr AS article_nbr
            FROM `{}.{}` t1
            INNER JOIN `{}.{}` t2
            ON t1.experienced_editor = t2.user_text
        """.format(self.dataset, "project_member_experienced_editors_intersections",
                   self.dataset, "experienced_editors_article_counts")
        self.query.run_query(query, self.dataset, "member_editor_cnt_intersections")

        query = """
            SELECT t1.experienced_editor AS experienced_editor,
            t1.project_member AS project_member,
            t1.intersections AS intersections,
            t1.article_nbr AS exp_art_nbr,
            t2.article_nbr AS mbr_art_nbr
            FROM `{}.{}` t1
            INNER JOIN `{}.{}` t2
            ON t1.project_member = t2.user_text
        """.format(self.dataset, "member_editor_cnt_intersections",
                   self.dataset, "project_members_project_article_counts")
        self.query.run_query(query, self.dataset, "member_cnt_editor_cnt_intersections")


        # compute user cf scores for all pairs of editors
        query = """
            SELECT experienced_editor,
            project_member,
            intersections,
            exp_art_nbr,
            mbr_art_nbr,
            intersections / ((SQRT(exp_art_nbr) * SQRT(mbr_art_nbr)) AS cos_sim
            FROM `{}.{}`
        """.format(self.dataset, "member_cnt_editor_cnt_intersections")
        self.query.run_query(query, self.dataset, "uucf_scores")

        # join and combine with projects
        query = """
            SELECT t1.experienced_editor AS experienced_editor,
            t1.project_member AS project_member,
            t1.cos_sim AS cos_sim,
            t2.wikiproject AS wikiproject
            FROM `{}.{}` t1
            INNER JOIN `{}.{}` t2
            ON t1.project_member = t2.user_text
        """.format(self.dataset, "uucf_scores",
                   self.dataset, "project_members")
        self.query.run_query(query, self.dataset, "uucf_project_scores")

        # only extract top 40? for each project based on the score
        """
        util.runQuery("select * from (select *, ROW_NUMBER() OVER (PARTITION BY nwikiproject " +
                        "ORDER BY nwikiproject, total_edits DESC) as pos FROM " +
                        util.tableName(defaultDataset, "editor_project_edits_on_total_edits") +
                        "order by nwikiproject, total_edits DESC, pos ASC) where pos <= "+topN,
                TableId.of(defaultDataset, "rule_recsys_valid_projects_on_edits_top"+topN));
        """
        query = """
            SELECT * FROM (
                SELECT *
                       ROW_NUMBER() OVER (
                       PARTITION BY wikiproject
                       ORDER BY wikiproject, cos_sim DESC) AS pos
                FROM `{}.{}`)
                ORDER BY wikiproject, cos_sim DESC, pos ASC) WhERE pos <= `{}`
        """.format(self.dataset, "uucf_project_scores", self.top_n)
        self.query.run_query(query, self.dataset, "recommendations_uucf")


    def execute(self):
        # self.upload_files()
        self.recommend_editors()


# def main():
#     uucf = UUCF()
#     uucf.execute()
#
# main()