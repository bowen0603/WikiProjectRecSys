import os
import random
from datetime import datetime


class TableGenerator:

    def __init__(self):
        self.table_str = ''  # where the table is being built
        self.output_dir = "data/recommendations/"

        self.header = '! Username !! Recent Edits within  !! Recent Edits in Wikipedia !! First Edit Date !! Most Recent Edit Date \n'
        self.file_start = '{| class="wikitable sortable"\n |-\n' + self.header  # begining of the table

        self.delimiter = '**'  # what the csv is seperated by

        self.projects = dict()  # keeps record of all projects
        self.users = dict()  # keeps record of all users that have been recommended, prevents duplicates

        self.nbr_newcomers = 4
        self.nbr_per_alg = 5

        self.file_data = []
        self.files = []

        self.sample_projects = set()
        self.dict_project_newcomers = self.read_file_newcomers()
        self.dict_project_rules = self.read_file_rule()

    def read_file_newcomers(self):
        dict_project_newcomers = {}
        filename = "data/recommendations_newcomers.csv"
        for line in open(filename, "r").readlines()[1:]:
            project = line.split(self.delimiter)[0]

            user_text = line.split(self.delimiter)[1]
            dict_user_info = {'user_id': int(line.split(self.delimiter)[2]),
                              'first_article': line.split(self.delimiter)[3],
                              'project_edits': int(line.split(self.delimiter)[4]),
                              'wp_edits': int(line.split(self.delimiter)[5]),
                              'last_edit': line.split(self.delimiter)[6],
                              'regstr_time': line.split(self.delimiter)[7].strip()}

            if project in dict_project_newcomers:
                recommended_newcomers = dict_project_newcomers[project]
            else:
                recommended_newcomers = {}
                dict_project_newcomers[project] = recommended_newcomers
            recommended_newcomers[user_text] = dict_user_info

        projects = list(dict_project_newcomers)
        self.sample_projects = self.sample_projects.union(projects)
        return dict_project_newcomers


    def read_file_rule(self):
        dict_project_rules = {}
        filename = "data/recommendations_rule.csv"
        for line in open(filename, "r").readlines()[1:]:
            project = line.split(self.delimiter)[0]

            user_text = line.split(self.delimiter)[1]
            dict_user_info = {'user_id': int(line.split(self.delimiter)[2]),
                              'project_edits': int(line.split(self.delimiter)[3]),
                              'wp_edits': int(line.split(self.delimiter)[4]),
                              'last_edit': line.split(self.delimiter)[5],
                              'regstr_time': line.split(self.delimiter)[6].strip()}

            if project in dict_project_rules:
                recommended_editors = dict_project_rules[project]
            else:
                recommended_editors = {}
                dict_project_rules[project] = recommended_editors
            recommended_editors[user_text] = dict_user_info
        self.sample_projects = self.sample_projects & set(list(dict_project_rules))
        return dict_project_rules


    def input_filename(self):
        from sys import argv
        param1 = argv[0]
        argv.remove(param1)
        self.files = argv


    def input_files(self):
        print('Enter the name(s) of newcomer files')
        something = True
        while something:
            file_name = input('File: ')
            if file_name == '':
                something = False
            else:
                self.files.append(file_name)  # files is a list of all the newcomer files

    def execute(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        for project in self.sample_projects:
            # write newcomers into file
            fout = open(self.output_dir + project + ".csv", "w")

            print("{}".format(self.file_start), file=fout)

            nbr_editors = min(self.nbr_newcomers, len(self.dict_project_newcomers[project].keys()))

            for i in range(nbr_editors):
                project_newcomers = self.dict_project_newcomers[project]
                editor_text = random.choice(list(project_newcomers.keys()))
                user_page = "{{User | {0}}}".format(editor_text)

                date_regstr = datetime.strptime(project_newcomers[editor_text]['regstr_time'], "%Y-%m-%d %H:%M:%S")
                date_regstr_str = "{}-{}-{}".format(date_regstr.year, date_regstr.month, date_regstr.day)

                date_last = datetime.strptime(project_newcomers[editor_text]['last_edit'], "%Y-%m-%d %H:%M:%S")
                date_last_str = "{}-{}-{}".format(date_last.year, date_last.month, date_last.day)

                # print("|-\n | {{}} || {} || {} || {} || {} ".format(user_page,
                #                                                   project_newcomers[editor_text]['project_edits'],
                #                                                   project_newcomers[editor_text]['wp_edits'],
                #                                                   date_regstr_str,
                #                                                   date_last_str), file=fout)
                str = "|-\n | {" + user_page + "}" + "|| {} || {} || {} || {} ".format(
                                                                  project_newcomers[editor_text]['project_edits'],
                                                                  project_newcomers[editor_text]['wp_edits'],
                                                                  date_regstr_str,
                                                                  date_last_str)
                print(str, file=fout)
                del project_newcomers[editor_text]

            nbr_editors = min(self.nbr_per_alg, len(self.dict_project_rules[project].keys()))
            for i in range(nbr_editors):
                project_members = self.dict_project_rules[project]
                editor_text = random.choice(list(project_members.keys()))
                user_page = "{{User | {}}}".format(editor_text)

                date_regstr = datetime.strptime(project_members[editor_text]['regstr_time'], "%Y-%m-%d %H:%M:%S")
                date_regstr_str = "{}-{}-{}".format(date_regstr.year, date_regstr.month, date_regstr.day)

                date_last = datetime.strptime(project_members[editor_text]['last_edit'], "%Y-%m-%d %H:%M:%S")
                date_last_str = "{}-{}-{}".format(date_last.year, date_last.month, date_last.day)

                str = "|-\n | {" + user_page + "}" + "|| {} || {} || {} || {} ".format(
                                                                  project_members[editor_text]['project_edits'],
                                                                  project_members[editor_text]['wp_edits'],
                                                                  date_regstr_str,
                                                                  date_last_str)

                # print("|-\n | {} ), file=fout)
                print(str, file=fout)
                del project_members[editor_text]
            print("|}", file=fout)


    def finish(self):
        for key in self.projects:
            project_file_name = key + '.csv'
            project_file = open(project_file_name, 'a')
            project_file.write('|}')
            project_file.close()

    def files_table(self):
        files_lst = self.files
        for file in files_lst:
            f = open(file, 'r')
            f.readline()  # removes titles
            self.file_data += list(f)  # still in string format
            f.close()
        #self.file_data = random.shuffle(self.file_data)  # mixes together all file data points


def main():


    table_generator = TableGenerator()
    table_generator.execute()
    # table_generator.input_filename() #gets files from command line
    # table_generator.files_table() #puts data from all tables into one table
    # table_generator.execute() #creates the table
    # table_generator.finish() #adds table ends and closes files


main()


