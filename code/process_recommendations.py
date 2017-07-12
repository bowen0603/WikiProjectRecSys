from __future__ import print_function
__author__ = 'bobo'

class Recommendations():

    def __init__(self, wikiproject_file, proj_art_dir, newcomers_dir, output_dir):

        self.USER_LIST = {}
        self.recommendation_total = 45
        self.wikiproject_file = wikiproject_file
        self.project_article_dir = proj_art_dir
        self.newcomer_dir = newcomers_dir
        self.recommendation_dir = output_dir
        self.file_date = 28

        # create output directory
        import os
        if not os.path.exists(self.recommendation_dir):
            os.makedirs(self.recommendation_dir)

    def get_wikiproject_list(self):
        header = True
        project_list = []

        for line in open(self.wikiproject_file, 'r'):
            if header:
                header = False
                continue

            project = line.split(",")[0]
            project = project.replace("WikiProject_", "")
            project = project.replace("_", " ")
            project_list.append(project)

        return project_list

    def select_30_ramdom_projects(self, project_list):
        project_idx = [5, 28, 18, 1, 16, 26, 29, 10, 9, 25, 24, 11, 21, 23, 20]
        sample_project_list = []
        for i in range(len(project_list)):
            if (i+1) in project_idx:
                sample_project_list.append(project_list[i])

        return sample_project_list

    def get_articles(self, wikiproject):

        # construct file name
        filename = None
        for idx in range(41):
            import os.path
            fname = self.project_article_dir + "/" + str(idx) + wikiproject + ".csv"
            if os.path.isfile(fname):
                filename = fname
                break

        # TODO: can set some limit for selected articles
        header = True
        article_list = []
        if filename:
            for line in open(filename, "r"):
                if header:
                    header = False
                    continue
                article = line.split(",")[1]
                article_list.append(article)

        # all in lowercase
        return article_list

    def construct_file_name(self, file_date):

        filename = None
        import os.path
        fname = self.newcomer_dir + "/newcomers" + str(file_date) + ".csv"
        if os.path.isfile(fname):
            filename = fname
            # print("working on date: {}".format(file_date))
        return filename


    def recommend(self):

        project_list = self.select_30_ramdom_projects(self.get_wikiproject_list())
        from random import shuffle
        shuffle(project_list)

        for project in project_list:

            fout = open(self.recommendation_dir + "/" + project + ".csv", "w")
            print("editor,article_edited,wikiproject,timestamp", file=fout)

            recommendation_cnt = 0
            articles = self.get_articles(project)

            # read in users
            enough_editors = False
            file_date = self.file_date

            while not enough_editors:

                filename = self.construct_file_name(file_date)
                # prepare to read editors in the previous day
                file_date -= 1

                # TODO: may set a limit for the number of files to read

                if filename is None:
                    break

                header = True
                for line in open(filename, "r"):
                    if header:
                        header = False
                        continue

                    editor = line.split("**")[0]
                    article = line.split("**")[1].lower()
                    timestamp = line.split("**")[2].replace("\n", "")

                    if editor in self.USER_LIST:
                        continue


                    if article in articles:
                        recommendation_cnt += 1
                        self.USER_LIST[editor] = project
                        print("{},{},{},{}".format(editor, article, project, timestamp), file=fout)
                        fout.flush()

                        if recommendation_cnt >= self.recommendation_total:
                            enough_editors = True
                            break

            print("{} editors recommended for WikiProject: {}.. ".format(recommendation_cnt, project))


def main():
    # data/Top40ContentWikiProjects.csv data/project_articles data/newcomers data/recommendations
    from sys import argv
    if len(argv) != 5:
        print("Usage: <wikiproject-file> <project-article-dir> <newcomers-dir> <output-dir>")
        return

    rec = Recommendations(argv[1], argv[2], argv[3], argv[4])
    rec.recommend()

main()

