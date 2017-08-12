import os
import random
from datetime import datetime
from random import shuffle


class TableGenerator:

    def __init__(self):
        self.table_str = ''  # where the table is being built
        self.output_dir = "data/recommendations/"
        self.message_greeting = """
Hi {},

Here is a list of candidate editors our system generated for your project. They might be interested in working and collaborating with your project. Please go ahead and introduce the project to them. Here are the templates you might want to use for newcomers and experienced editors.

As a part of our study, we'd appreciate it if you could fill the survey to let us know how you think about our recommendations.
        """

        self.message_ending = """
Note about Recommendation Types:

1. Newcomer: This type of editors are newcomers who just registered Wikipedia in the past couple days, and made their first couple edits on your project-related articles. Please welcome and help them.

2. Topic: The topics of articles this type of editors edited are similar to the topics of articles within the scope of the project. Researchers have found that the more the topic match between the editor and the project, the more likely the editor will edit more and stay longer in the project.

3. Bonds: This type of editors have communicated with project members by leaving messages to their user talk pages. Researchers have found that editors who show stronger personal bonds with project members before they participate the project will edit more and stay longer in the project.

4. Rule: This type of editors make a large amount of edits on articles claimed within the scope of the project. They are interested in the project articles and will make contributions to the project.

5. User-User: This type of editors edited articles that are similar to the articles project members edited. They will be interested in the project articles.
        """

        # self.header = '! Username !! Recent Edits within  !! Recent Edits in Wikipedia !! First Edit Date !! Most Recent Edit Date \n'
        self.table_schema_general = '! Username !! Type !! Editor Description !! First Edit Date !! Total Edits in WP !! Recent Activity Level !! Survey \n'
        self.table_header_general = '{| class="wikitable sortable"\n |-\n' + self.table_schema_general  # begining of the table

        self.table_schema_WIR = '! Username !! Editor Description !! First Edit Date !! Total Edits in WP !! Recent Activity Level !! Survey \n'
        self.table_header_WIR = '{| class="wikitable sortable"\n |-\n' + self.table_schema_WIR  # begining of the table

        self.delimiter = '**'  # what the csv is seperated by

        self.projects = dict()  # keeps record of all projects
        self.users = dict()  # keeps record of all users that have been recommended, prevents duplicates

        self.nbr_newcomers = 5
        self.nbr_per_alg = 5
        self.nbr_WIR = 10

        self.file_data = []
        self.files = []

        self.survey_link = "[https://docs.google.com/forms/d/e/1FAIpQLSelCKeHVbwJTupkELLLVOsiyX8rbKn3YuTYI6eBYt6cSC2xIw/viewform?usp=pp_url&entry.808388777={}&entry.2036239070={}&entry.1509434662 survey]"

        self.sample_projects = self.read_sample_projects()
        # self.dict_project_newcomers = self.read_file_newcomers()
        self.dict_project_rules = self.read_file_rule()
        self.dict_project_bonds = self.read_file_bonds()
        self.dict_project_topics = self.read_file_topics()
        # self.dict_project_uucf = {} # TODO work on this

        self.dict_project_organizers = self.read_file_organizers()


    def read_sample_projects(self):
        filename = "data/Top25ProjectsPastYear.csv"
        list_projects = []

        for line in open(filename, "r").readlines()[1:]:
            project = line.split(",")[0].replace("WikiProject_", "").replace("_", " ")
            list_projects.append(project)

        return set(list_projects)

    def read_file_newcomers(self):
        dict_project_newcomers = {}
        filename = "data/recommendations/recommendations_newcomers.csv"
        for line in open(filename, "r").readlines()[1:]:
            project = line.split(self.delimiter)[0]
            user_text = line.split(self.delimiter)[1]
            dict_user_info = {'first_article': line.split(self.delimiter)[2],
                              'project_edits': int(line.split(self.delimiter)[3]),
                              'wp_edits': int(line.split(self.delimiter)[4]),
                              'last_edit': line.split(self.delimiter)[5],
                              'regstr_time': line.split(self.delimiter)[6],
                              'status': line.split(self.delimiter)[7].strip()}

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
        filename = "data/recommendations/recommendations_rule.csv"
        for line in open(filename, "r").readlines()[1:]:
            project = line.split(self.delimiter)[0]
            user_text = line.split(self.delimiter)[1]
            dict_user_info = {'project_edits': int(line.split(self.delimiter)[2]),
                              'wp_edits': int(line.split(self.delimiter)[3]),
                              'last_edit': line.split(self.delimiter)[4],
                              'regstr_time': line.split(self.delimiter)[5],
                              'status': line.split(self.delimiter)[6].strip()}

            if project in dict_project_rules:
                recommended_editors = dict_project_rules[project]
            else:
                recommended_editors = {}
                dict_project_rules[project] = recommended_editors
            recommended_editors[user_text] = dict_user_info
        # TODO: be more precise about the sample projects
        self.sample_projects = self.sample_projects & set(list(dict_project_rules))
        return dict_project_rules

    def read_file_bonds(self):
        dict_project_bonds = {}
        filename = "data/recommendations/recommendations_bonds.csv"
        for line in open(filename, "r").readlines()[1:]:
            project = line.split(self.delimiter)[0]
            user_text = line.split(self.delimiter)[1]
            dict_user_info = {'pjtk_cnt': int(line.split(self.delimiter)[2]),
                              'talker_cnt': int(line.split(self.delimiter)[3]),
                              'wp_edits': int(line.split(self.delimiter)[4]),
                              'last_edit': line.split(self.delimiter)[5],
                              'regstr_time': line.split(self.delimiter)[6],
                              'status': line.split(self.delimiter)[7].strip()}

            if project in dict_project_bonds:
                recommended_editors = dict_project_bonds[project]
            else:
                recommended_editors = {}
                dict_project_bonds[project] = recommended_editors
            recommended_editors[user_text] = dict_user_info
        # TODO: be more precise about the sample projects
        self.sample_projects = self.sample_projects & set(list(dict_project_bonds))
        return dict_project_bonds

    def read_file_topics(self):
        dict_project_topics = {}
        # wikiproject**editor_text**cate_first**cate_second**wp_edits**last_edit**regstr_time**status
        filename = "data/recommendations/recommendations_topics.csv"
        for line in open(filename, "r").readlines()[1:]:
            project = line.split(self.delimiter)[0]
            user_text = line.split(self.delimiter)[1]
            dict_user_info = {'cate_first': line.split(self.delimiter)[2],
                              'cate_second': line.split(self.delimiter)[3],
                              'wp_edits': int(line.split(self.delimiter)[4]),
                              'last_edit': line.split(self.delimiter)[5],
                              'regstr_time': line.split(self.delimiter)[6],
                              'status': line.split(self.delimiter)[7].strip()}

            if project in dict_project_topics:
                recommended_editors = dict_project_topics[project]
            else:
                recommended_editors = {}
                dict_project_topics[project] = recommended_editors
            recommended_editors[user_text] = dict_user_info
        # TODO: be more precise about the sample projects
        self.sample_projects = self.sample_projects & set(list(dict_project_topics))
        return dict_project_topics

    def read_file_WIR(self):
        dict_project_WIR = {}
        project = "WIR"
        # editor_text,page_created,editcount,regstr_ts,article,status
        filename = "data/recommendations/recommendations_WIR.csv"
        for line in open(filename, "r").readlines()[1:]:
            user_text = line.split(self.delimiter)[0]
            dict_user_info = {'page_created': line.split(self.delimiter)[1],
                              'wp_edits': int(line.split(self.delimiter)[2]),
                              'regstr_ts': line.split(self.delimiter)[3],
                              'article': line.split(self.delimiter)[4],
                              'status': line.split(self.delimiter)[5].strip()}

            # if project in dict_project_WIR:
            #     recommended_editors = dict_project_WIR[project]
            # else:
            #     recommended_editors = {}
            #     dict_project_WIR[project] = recommended_editors
            # recommended_editors[user_text] = dict_user_info
            dict_project_WIR[user_text] = dict_user_info
        return dict_project_WIR

    def read_file_organizers(self):
        dict_project_organizers = {}
        filename = "data/project_organizers.csv"
        for line in open(filename, "r").readlines()[1:]:
            project = line.split(self.delimiter)[0]
            editor_text = line.split(self.delimiter)[1].strip()
            if project in dict_project_organizers:
                dict_project_organizers[project].append(editor_text)
            else:
                organizers = [editor_text]
                dict_project_organizers[project] = organizers
        return dict_project_organizers

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
            if project == 'Women in Red':
                continue

            if project not in self.dict_project_organizers:
                continue

            # TODO: chekc if the project exists in the project organizer list
            for organizer in self.dict_project_organizers[project]:

                # use the string list to store the entire list, and then shuffle if needed
                list_editor_wikicodes = []

                # # randomly select editors from each algorithms, and delete the editors/ randomlize the order of the editors
                # nbr_editors = min(self.nbr_newcomers, len(self.dict_project_newcomers[project].keys()))

                # # print newcomers
                # for i in range(nbr_editors):
                #     project_newcomers = self.dict_project_newcomers[project]
                #     editor_text = random.choice(list(project_newcomers.keys()))
                #
                #     str_editor_desription = self.create_newcomer_message(project, organizer, editor_text,
                #                                                 self.dict_project_newcomers[project][editor_text])
                #     list_editor_wikicodes.append(str_editor_desription)
                #     del project_newcomers[editor_text]

                # print rule based
                nbr_editors = min(self.nbr_per_alg, len(self.dict_project_rules[project].keys()))
                for i in range(nbr_editors):
                    project_members = self.dict_project_rules[project]
                    editor_text = random.choice(list(project_members.keys()))

                    str_editor_desription = self.create_message_rule(project, organizer, editor_text,
                                                                self.dict_project_rules[project][editor_text])
                    list_editor_wikicodes.append(str_editor_desription)
                    del project_members[editor_text]

                # print topic based
                nbr_editors = min(self.nbr_per_alg, len(self.dict_project_topics[project].keys()))
                for i in range(nbr_editors):
                    project_members = self.dict_project_topics[project]
                    editor_text = random.choice(list(project_members.keys()))
                    str_editor_desription = self.create_message_topics(project, organizer, editor_text,
                                                                         self.dict_project_topics[project][
                                                                             editor_text])
                    list_editor_wikicodes.append(str_editor_desription)
                    del project_members[editor_text]

                # print bonds based
                nbr_editors = min(self.nbr_per_alg, len(self.dict_project_bonds[project].keys()))
                for i in range(nbr_editors):
                    project_members = self.dict_project_bonds[project]
                    editor_text = random.choice(list(project_members.keys()))
                    str_editor_desription = self.create_message_bonds(project, organizer, editor_text,
                                                                         self.dict_project_bonds[project][
                                                                             editor_text])
                    list_editor_wikicodes.append(str_editor_desription)
                    del project_members[editor_text]

                # # print uucf
                # nbr_editors = min(self.nbr_per_alg, len(self.dict_project_uucf[project].keys()))
                # for i in range(nbr_editors):
                #     project_members = self.dict_project_uucf[project]
                #     editor_text = random.choice(list(project_members.keys()))
                #     str_editor_desription = self.create_message_uucf(project, organizer, editor_text,
                #                                                       self.dict_project_uucf[project][
                #                                                           editor_text])
                #     list_editor_wikicodes.append(str_editor_desription)
                #     del project_members[editor_text]

                fout = open(self.output_dir + project + "_" + organizer + ".csv", "w")
                message_greeting = self.message_greeting.format(organizer)
                print(message_greeting, file=fout)

                print("{}".format(self.table_header_general), file=fout)
                # shuffle the list before printing out
                shuffle(list_editor_wikicodes)
                for editor_wikicode in list_editor_wikicodes:
                    print("{}".format(editor_wikicode), file=fout)
                print("|}", file=fout)

                print(self.message_ending, file=fout)

    def execute_WIR(self):
        self.dict_project_WIR = self.read_file_WIR()

        WIR = 'Women in Red'
        for organizer in self.dict_project_organizers[WIR]:
            list_editor_wikicodes = []

            nbr_editors = min(self.nbr_WIR, len(self.dict_project_WIR))
            for i in range(nbr_editors):
                project_members = self.dict_project_WIR
                editor_text = random.choice(list(project_members.keys()))

                str_editor_desription = self.create_message_WIR(organizer, editor_text,
                                                                self.dict_project_WIR[editor_text])
                list_editor_wikicodes.append(str_editor_desription)
                del project_members[editor_text]

            fout = open(self.output_dir + "WIR_" + organizer + ".csv", "w")
            message_greeting = self.message_greeting.format(organizer)
            print(message_greeting, file=fout)

            print("{}".format(self.table_header_WIR), file=fout)
            # shuffle the list before printing out
            shuffle(list_editor_wikicodes)
            for editor_wikicode in list_editor_wikicodes:
                print("{}".format(editor_wikicode), file=fout)
            print("|}", file=fout)
            print(self.message_ending, file=fout)


    def create_newcomer_message(self, project, organizer, editor_text, editor_info):
        user_page = "{{User | {}}}".format(editor_text)
        date_regstr = datetime.strptime(editor_info['regstr_time'], "%Y-%m-%d %H:%M:%S")
        date_regstr_str = "{}-{}-{}".format(date_regstr.year, date_regstr.month, date_regstr.day)
        description = "{} made her/his first edit on article {} in Wikipedia.".format(editor_text, editor_info['first_article'])

        str = "|-\n | {" + user_page + "}" + "|| {} || {} || {} || {} || {} || {}".format("Newcomer",
                                                                                          description,
                                                                                          date_regstr_str,
                                                                                          editor_info['wp_edits'],
                                                                                          editor_info['status'],
                                                                                          self.form_survey_link(project, organizer))
        return str

    def create_message_rule(self, project, organizer, editor_text, editor_info):
        user_page = "{{User | {}}}".format(editor_text)
        date_regstr = datetime.strptime(editor_info['regstr_time'], "%Y-%m-%d %H:%M:%S")
        date_regstr_str = "{}-{}-{}".format(date_regstr.year, date_regstr.month, date_regstr.day)
        description = "{} made {} edits on articles within the scope of your project.".format(editor_text,
                                                                                     editor_info['project_edits'])

        str = "|-\n | {" + user_page + "}" + "|| {} || {} || {} || {} || {} || {}".format("Rule",
                                                                                          description,
                                                                                          date_regstr_str,
                                                                                          editor_info['wp_edits'],
                                                                                          editor_info['status'],
                                                                                          self.form_survey_link(project, organizer))
        return str

    def create_message_bonds(self, project, organizer, editor_text, editor_info):
        user_page = "{{User | {}}}".format(editor_text)
        date_regstr = datetime.strptime(editor_info['regstr_time'], "%Y-%m-%d %H:%M:%S")
        date_regstr_str = "{}-{}-{}".format(date_regstr.year, date_regstr.month, date_regstr.day)
        description = "{} have left over {} messages on the user talk pages of more than {} project members.".format(editor_text,
                                                                                                                     editor_info['pjtk_cnt'],
                                                                                                                     editor_info['talker_cnt'])

        str = "|-\n | {" + user_page + "}" + "|| {} || {} || {} || {} || {} || {}".format("Bonds",
                                                                                          description,
                                                                                          date_regstr_str,
                                                                                          editor_info['wp_edits'],
                                                                                          editor_info['status'],
                                                                                          self.form_survey_link(project, organizer))
        return str

    def create_message_topics(self, project, organizer, editor_text, editor_info):
        user_page = "{{User | {}}}".format(editor_text)
        date_regstr = datetime.strptime(editor_info['regstr_time'], "%Y-%m-%d %H:%M:%S")
        date_regstr_str = "{}-{}-{}".format(date_regstr.year, date_regstr.month, date_regstr.day)
        if editor_info['cate_second'] != 'None':
            description = "{} edited articles mostly fall into Categories of {} and {}.".format(editor_text,
                                                                                                self.category_link(editor_info['cate_first']),
                                                                                                self.category_link(editor_info['cate_second']))
        else:
            description = "{} edited articles mostly fall into Category of {}.".format(editor_text, self.category_link(editor_info['cate_first']))

        str = "|-\n | {" + user_page + "}" + "|| {} || {} || {} || {} || {} || {}".format("Topic",
                                                                                         description,
                                                                                         date_regstr_str,
                                                                                         editor_info['wp_edits'],
                                                                                         editor_info['status'],
                                                                                         self.form_survey_link(project, organizer))
        return str

    def create_message_uucf(self, project, organizer, editor_text, editor_info):
        user_page = "{{User | {}}}".format(editor_text)
        date_regstr = datetime.strptime(editor_info['regstr_time'], "%Y-%m-%d %H:%M:%S")
        date_regstr_str = "{}-{}-{}".format(date_regstr.year, date_regstr.month, date_regstr.day)
        neighbor1 = "{{User | {}}}".format(editor_info['neighbor1'])
        neighbor2 = "{{User | {}}}".format(editor_info['neighbor2'])
        description = "{} edited articles similar to the articles some project members such as {}, {}, edited.".format(editor_text,
                                                                                                                       neighbor1,
                                                                                                                       neighbor2)
        str = "|-\n | {" + user_page + "}" + "|| {} || {} || {} || {} || {}".format("Rule",
                                                                                   description,
                                                                                   date_regstr_str,
                                                                                   editor_info['wp_edits'],
                                                                                   editor_info['status'],
                                                                                   self.form_survey_link(project, organizer))
        return str

    def create_message_WIR(self, organizer, editor_text, editor_info):
        user_page = "{{User | {}}}".format(editor_text)
        date_regstr = datetime.strptime(editor_info['regstr_ts'], "%Y-%m-%dT%H:%M:%SZ")
        date_regstr_str = "{}-{}-{}".format(date_regstr.year, date_regstr.month, date_regstr.day)
        #[[Nancy_Denton | Article: Nancy Denton]]
        description = "{} created {} articles for WIR this month, such as {}.".format(editor_text,
                                                                                      editor_info['page_created'],
                                                                                      self.article_link(editor_info['article']))
        #editor_text, page_created, editcount, regstr_ts, article, status
        str = "|-\n | {" + user_page + "}" + "|| {} || {} || {} || {} || {}".format(description,
                                                                                   date_regstr_str,
                                                                                   editor_info['wp_edits'],
                                                                                   editor_info['status'],
                                                                                   self.form_survey_link("WIR",
                                                                                                         organizer))
        return str

    def category_link(self, category):
        category = category.title()
        return "[[Portal:{}|{}]]".format(category, category)

    def article_link(self, title):
        return "[[{} | Article:{}]]".format(title, title)

    def form_survey_link(self, project, organizer):
        project = project.replace(" ", "%20")
        organizer = organizer.replace(" ", "%20")
        return self.survey_link.format(project, organizer)

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

    def create_tables(self):
        self.execute()
        self.execute_WIR()


# def main():
#
#
#     table_generator = TableGenerator()
#     table_generator.execute()
#     table_generator.execute_WIR()
#     # table_generator.input_filename() #gets files from command line
#     # table_generator.files_table() #puts data from all tables into one table
#     # table_generator.execute() #creates the table
#     # table_generator.finish() #adds table ends and closes files
#
#
# main()


