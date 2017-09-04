from GQuerier import QueryHandler

__author__ = 'bobo'

class ArticleProject:

    def __init__(self):
        self.query = QueryHandler()
        self.top_n = 20
        self.dataset = "bowen_script_uucf"

    def get_sample_project_categories(self):
        query = """
            SELECT t2.wikiproject AS wikiproject,
            t1.arts AS arts,
            t1.geography AS geography,
            t1.health AS health,
            t1.mathematics AS mathematics,
            t1.history AS history,
            t1.science AS science,
            t1.people AS people,
            t1.philosophy AS philosophy,
            t1.religion AS religion,
            t1.society AS society,
            t1.technology AS technology,
            t1.NF AS NF
            FROM `{}.{}` t1
            INNER JOIN `{}.{}` t2
            ON t1.wikiproject = t2.wikiproject_lower
        """.format("bowen_wiki_recsys", "wikiproject_category_distribution_normalized",
                   self.dataset, "list_sample_project")
        self.query.run_query(query, self.dataset, "projects_categories")


    def get_list_sample_projects(self):
        # upload the project list file
        dict_schema = [("wikiproject", "STRING")]
        self.query.create_table(self.dataset, "list_sample_project_raw", dict_schema)
        # TODO: this will be appended.. need to delete the table
        self.query.load_data_from_file(self.dataset, "list_sample_project_raw", "data/Top25ProjectsPastYear.csv")

        # rename the project list file
        query = """
            SELECT REPLACE(wikiproject, "WikiProject_", "") AS wikiproject
            FROM `{}.{}`
        """.format(self.dataset, "list_sample_project_raw")
        self.query.run_query(query, self.dataset, "list_sample_project_raw1")

        query = """
            SELECT REPLACE(wikiproject, "_", " ") AS wikiproject
            FROM `{}.{}`
        """.format(self.dataset, "list_sample_project_raw1")
        self.query.run_query(query, self.dataset, "list_sample_project_raw2")

        query = """
            SELECT wikiproject
            FROM `{}.{}`
            GROUP BY wikiproject
        """.format(self.dataset, "list_sample_project_raw2")
        self.query.run_query(query, self.dataset, "list_sample_project_raw3")

        query = """
            SELECT wikiproject,
            LOWER(wikiproject) AS wikiproject_lower
            FROM `{}.{}`
        """.format(self.dataset, "list_sample_project_raw3")
        self.query.run_query(query, self.dataset, "list_sample_project")

        # TODO: can decide if we need a filter on article importance
        query = """
            SELECT t1.wikiproject AS wikiproject,
            t1.title AS title,
            t2.wikiproject AS wikiproject_f
            FROM `{}.{}` t1
            INNER JOIN `{}.{}` t2
            ON t1.wikiproject = t2.wikiproject_lower
        """.format('bowen_user_dropouts', 'article_wikiprojects',
                   self.dataset, 'list_sample_project')
        self.query.run_query(query, self.dataset, "articles_top25_projects")

def main():
    runner = ArticleProject()
    runner.get_list_sample_projects()

    runner.get_sample_project_categories()

main()