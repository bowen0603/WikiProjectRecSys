from __future__ import print_function
import os
import os.path
import random
from datetime import datetime
from random import shuffle


class TableGenerator:

    def __init__(self, file_organizer=None, batch_nbr=None):

        # self.dict_editor_wp_edits = dict_editor_wp_edits
        # self.dict_editor_date_regstr_str = dict_editor_date_regstr_str
        # self.dict_editor_status = dict_editor_status

        self.table_str = ''  # where the table is being built
        self.output_dir = "data/recommendation_messages/"
        self.message_greeting = """
Hi {},

Our system generated a list of potential new editors for your project. They may be interested in collaborating with your project members to on your project's articles. As you will notice, the list contains both experienced editors and newcomers. Both are valuable for Wikipedia and your project. Please go ahead and introduce your project to them, and point them to some project tasks to start with. We also provide a template invitation message to make it easier to contact the potential new editors. Just click the invite link to write the invitation message.

We'd appreciate it if you could fill the survey to let us know what you think about our recommendations so we can improve our system.
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
        self.table_schema_general = '! Username  !! Why we recommend this editor !! First Edit Date !! Total Edits in ENWP !! Recent Activity Level !! Invite !! Survey \n'
        self.table_header_general = '{| class="wikitable sortable"\n |-\n' + self.table_schema_general  # begining of the table

        invite = "{{H:title|Please sign your signature when inviting the editor. |Invitation Status}}"
        self.table_schema_WIR = '! Username !! Articles Created !! First Edit Date !! Total Edits in ENWP !! Recent Activity Level !! {} \n'.format(invite)
        self.table_header_WIR = '{| class="wikitable sortable"\n |-\n' + self.table_schema_WIR  # begining of the table

        self.delimiter = '**'  # what the csv is seperated by

        self.projects = dict()  # keeps record of all projects
        self.users = dict()  # keeps record of all users that have been recommended, prevents duplicates

        self.nbr_newcomers = 4
        self.nbr_per_alg = 4
        self.nbr_WIR = 10

        self.file_organizer = file_organizer
        self.batch_nbr = batch_nbr

        self.set_editors_treatment_group = set()
        self.set_editors_control_group = set()
        self.set_recommended_editors = set()

        # self.survey_link = "[https://docs.google.com/forms/d/e/1FAIpQLSelCKeHVbwJTupkELLLVOsiyX8rbKn3YuTYI6eBYt6cSC2xIw/viewform?usp=pp_url&entry.253397030={}&entry.808388777={}&entry.2036239070={}&entry.1509434662 survey]"
        self.survey_link = "[https://docs.google.com/forms/d/e/1FAIpQLSdAM9iz28eh5l0tiGznlaLk4tDprU3OSs5d4PY_Xq75lG-U8w/viewform?usp=pp_url&entry.12717926={}&entry.1380059197={}&entry.661705997={}&entry.1106258057 survey]"
        self.invitation_link_exp = "[https://en.wikipedia.org/w/index.php?title=User_talk:{}&action=edit&section=new&preload=User:Bobo.03/InviteExpEditors&editintro=User:Bobo.03/Study_Intro invite] "
        self.invitation_link_newcomers = "[https://en.wikipedia.org/w/index.php?title=User_talk:{}&action=edit&section=new&preload=User:Bobo.03/InviteNewcomers&editintro=User:Bobo.03/Study_Intro invite] "

        # self.dict_editor_wp_edits, self.dict_editor_date_regstr_str, self.dict_editor_status = self.read_editor_info()
        self.list_bots = self.read_bot_list()
        self.read_recommended_editors()

        self.sample_projects = self.read_sample_projects()
        self.project_first_category, self.project_second_category = self.read_project_categories()
        self.dict_project_newcomers = self.read_file_newcomers()
        self.dict_project_rules = self.read_file_rule()
        self.dict_project_bonds = self.read_file_bonds()
        self.dict_project_topics = self.read_file_topics()
        self.dict_project_uucf = self.read_file_uucf()

        self.dict_project_organizers = self.read_file_organizers()


    def compute_recommendation_overlaps(self):
        set_editors_rule = set()
        for project in self.dict_project_rules:
            for editor in self.dict_project_rules[project]:
                set_editors_rule.add(editor)

        set_editors_topics = set()
        for project in self.dict_project_topics:
            for editor in self.dict_project_topics[project]:
                set_editors_topics.add(editor)

        set_editors_bonds = set()
        for project in self.dict_project_bonds:
            for editor in self.dict_project_bonds[project]:
                set_editors_bonds.add(editor)

        set_editors_uucf = set()
        for project in self.dict_project_uucf:
            for editor in self.dict_project_uucf[project]:
                set_editors_uucf.add(editor)

        print("Total editors: rule: {}, topics: {}, bonds: {}, uucf: {}".format(len(set_editors_rule),
                                                                                len(set_editors_topics),
                                                                                len(set_editors_bonds),
                                                                                len(set_editors_uucf)))
        list_set = []
        list_set.append(("rule", set_editors_rule))
        list_set.append(("topics", set_editors_topics))
        list_set.append(("bonds", set_editors_bonds))
        list_set.append(("uucf", set_editors_uucf))

        for i in range(len(list_set)):
            type_i, editors_i = list_set[i]
            for j in range(len(list_set)):
                if i >= j:
                    continue
                type_j, editors_j = list_set[j]
                print("{} and {} shared {} editors.".format(type_i, type_j, len(editors_i & editors_j)))



    # read editors who have been shown to organizers, skip them; skip them. It's fine to keep updating the control groups
    def read_recommended_editors(self):
        filename = os.getcwd() + "/data/collection/group_treatment.csv"
        if os.path.isfile(filename):
            with open(filename, 'r') as fin:
                for line in fin:
                    if line.startswith("******"):
                        continue
                    project = line.split(",")[0]
                    organizer = line.split(",")[1]
                    user_text = line.split(",")[2]
                    type = line.split(",")[3].strip()

                    self.set_recommended_editors.add(user_text)


    def read_sample_projects(self):
        filename = "data/pre-processing/Top25ProjectsPastYear.csv"
        list_projects = []

        for line in open(filename, "r").readlines()[1:]:
            project = line.split(",")[0].replace("WikiProject_", "").replace("_", " ")
            list_projects.append(project)

        return set(list_projects)

    def read_project_categories(self):
        filename = "data/pre-processing/projects_categories.csv"
        project_first_category = {}
        project_second_category = {}

        max_cate, max_cate_value = "", -1
        dict_value = {}
        for line in open(filename, 'r').readlines()[1:]:
            wikiproject = line.split(",")[0]
            dict_value['arts'] = float(line.split(",")[1])
            dict_value['geography'] = float(line.split(",")[2])
            dict_value['health'] = float(line.split(",")[3])
            dict_value['mathematics'] = float(line.split(",")[4])
            dict_value['history'] = float(line.split(",")[5])
            dict_value['science'] = float(line.split(",")[6])
            dict_value['people'] = float(line.split(",")[7])
            dict_value['philosophy'] = float(line.split(",")[8])
            dict_value['religion'] = float(line.split(",")[9])
            dict_value['society'] = float(line.split(",")[10])
            dict_value['technology'] = float(line.split(",")[11])
            dict_value['NF'] = float(line.split(",")[12].strip())

            import operator
            sorted_dict_value = sorted(dict_value.items(), key=operator.itemgetter(1), reverse=True)
            project_first_category[wikiproject], project_second_category[wikiproject] = sorted_dict_value[0][0], sorted_dict_value[1][0]

        return project_first_category, project_second_category

    def read_editor_info(self):
        filename = "data/pre-processing/valid_experienced_editors.csv"
        dict_editor_wp_edits = {}
        dict_editor_date_regstr_str = {}
        dict_editor_status = {}

        header = True
        for line in open(filename, "r"):
            if header:
                header = False
                continue
            try:
                editor_text = line.split("*")[0]
                editor_id = line.split(("*"))[1]
                editcount = int(line.split("*")[2])
                regtr_time = line.split("*")[3].strip()
                # status = line.split("*")[4].strip()
            except:
                continue

            dict_editor_wp_edits[editor_text] = editcount
            dict_editor_date_regstr_str[editor_text] = regtr_time
            # dict_editor_status[editor_text] = status
        return dict_editor_wp_edits, dict_editor_date_regstr_str, dict_editor_status

    def read_file_newcomers(self):
        dict_project_newcomers = {}
        filename = "data/recommendations/recommendations_newcomers.csv"
        for line in open(filename, "r").readlines()[1:]:
            project = line.split(self.delimiter)[0]
            user_text = line.split(self.delimiter)[1]
            if user_text in self.list_bots:
                continue

            # skip editors who have been shown on the list
            if user_text in self.set_recommended_editors:
                continue

            try:
                dict_user_info = {'first_article': line.split(self.delimiter)[2],
                                  'project_edits': int(line.split(self.delimiter)[3]),
                                  'wp_edits': int(line.split(self.delimiter)[4]),
                                  'last_edit': line.split(self.delimiter)[5],
                                  'regstr_time': line.split(self.delimiter)[6],
                                  'status': line.split(self.delimiter)[7].strip()}
            except Exception as e:
                print(e)
                continue

            if project in dict_project_newcomers:
                recommended_newcomers = dict_project_newcomers[project]
            else:
                recommended_newcomers = {}
                dict_project_newcomers[project] = recommended_newcomers
            recommended_newcomers[user_text] = dict_user_info

        projects = list(dict_project_newcomers)
        # self.sample_projects = self.sample_projects.union(projects)
        return dict_project_newcomers


    def read_file_rule(self):
        dict_project_rules = {}
        filename = "data/recommendations/recommendations_rule.csv"
        for line in open(filename, "r").readlines()[1:]:
            project = line.split(self.delimiter)[0]
            user_text = line.split(self.delimiter)[1]
            if user_text in self.list_bots:
                continue

            # skip editors who have been shown on the list
            if user_text in self.set_recommended_editors:
                continue

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
        # self.sample_projects = self.sample_projects & set(list(dict_project_rules))
        return dict_project_rules

    def read_file_bonds(self):
        dict_project_bonds = {}
        filename = "data/recommendations/recommendations_bonds.csv"
        for line in open(filename, "r").readlines()[1:]:
            project = line.split(self.delimiter)[0]
            user_text = line.split(self.delimiter)[1]
            if user_text in self.list_bots:
                continue

            # skip editors who have been shown on the list
            if user_text in self.set_recommended_editors:
                continue

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
        # self.sample_projects = self.sample_projects & set(list(dict_project_bonds))
        return dict_project_bonds

    def read_file_topics(self):
        dict_project_topics = {}
        filename = "data/recommendations/recommendations_topics.csv"
        for line in open(filename, "r").readlines()[1:]:
            project = line.split(self.delimiter)[0]
            user_text = line.split(self.delimiter)[1]
            if user_text in self.list_bots:
                continue

            # skip editors who have been shown on the list
            if user_text in self.set_recommended_editors:
                continue

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
        # self.sample_projects = self.sample_projects & set(list(dict_project_topics))
        return dict_project_topics

    def read_file_uucf(self):
        dict_project_uucf = {}
        # wikiproject**editor_text**cate_first**cate_second**wp_edits**last_edit**regstr_time**status
        filename = "data/recommendations/recommendations_uucf.csv"
        for line in open(filename, "r").readlines()[1:]:

            project = line.split('**')[0]

            user_text = line.split('**')[1]
            if user_text in self.list_bots:
                continue

            # skip editors who have been shown on the list
            if user_text in self.set_recommended_editors:
                continue

            # skip in case the neighbor is a bot
            neighbor = line.split('**')[2]
            if neighbor in self.list_bots:
                continue

            try:
                dict_user_info = {'uucf_score': float(line.split('**')[3]),
                                  'rank': int(line.split('**')[4]),
                                  'neighbor1': neighbor,
                                  'common_edits': int(line.split('**')[4]),
                                  'wp_edits': int(line.split('**')[5]),
                                  'last_edit': line.split(self.delimiter)[6],
                                  'regstr_time': line.split(self.delimiter)[7],
                                  'status': line.split(self.delimiter)[8].strip()}
            except KeyError:
                #TODO: change here later
                # print(user_text)
                continue

            if project in dict_project_uucf:
                recommended_editors = dict_project_uucf[project]
            else:
                recommended_editors = {}
                dict_project_uucf[project] = recommended_editors
            recommended_editors[user_text] = dict_user_info
        # TODO: be more precise about the sample projects
        # self.sample_projects = self.sample_projects & set(list(dict_project_topics))
        return dict_project_uucf

    def read_file_WIR(self):
        dict_project_WIR = {}
        project = "Women in Red"
        # editor_text,page_created,editcount,regstr_ts,article,status
        filename = "data/recommendations/recommendations_WIR.csv"
        for line in open(filename, "r").readlines()[1:]:
            user_text = line.split(self.delimiter)[0]
            # TODO: skip recommended editors

            dict_user_info = {'page_created': line.split(self.delimiter)[1],
                              'wp_edits': int(line.split(self.delimiter)[2]),
                              'regstr_ts': line.split(self.delimiter)[3],
                              'article': line.split(self.delimiter)[4],
                              'status': line.split(self.delimiter)[5].strip()}

            dict_project_WIR[user_text] = dict_user_info
        return dict_project_WIR

    def read_file_organizers(self):
        dict_project_organizers = {}
        filename = self.file_organizer
        for line in open(filename, "r").readlines()[1:]:
            project = line.split('*')[0]
            editor_text = line.split('*')[1].strip()
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

        recommended_editors = set()
        for project in self.sample_projects:
            if project == 'Women in Red':
                continue

            if project not in self.dict_project_organizers:
                continue

            for organizer in self.dict_project_organizers[project]:
                # use the string list to store the entire list, and then shuffle if needed
                list_editor_wikicodes = []

                # randomly select editors from each algorithms, and delete the editors/ randomlize the order of the editors
                try:
                    nbr_editors = min(self.nbr_newcomers, len(self.dict_project_newcomers[project].keys()))
                except KeyError:
                    nbr_editors = 0

                # print newcomers
                i = 0
                while i < nbr_editors:
                    project_newcomers = self.dict_project_newcomers[project]
                    try:
                        editor_text = random.choice(list(project_newcomers.keys()))
                    except IndexError:
                        break

                    if editor_text in recommended_editors:
                        del project_newcomers[editor_text]
                        continue
                    i += 1

                    str_editor_desription = self.create_newcomer_message(project, organizer, editor_text,
                                                                self.dict_project_newcomers[project][editor_text])
                    list_editor_wikicodes.append(str_editor_desription)
                    self.set_editors_treatment_group.add((project, organizer, editor_text, "new"))
                    del project_newcomers[editor_text]
                    recommended_editors.add(editor_text)

                # print rule based
                nbr_editors = min(self.nbr_per_alg, len(self.dict_project_rules[project].keys()))
                i = 0
                while i < nbr_editors:
                    project_members = self.dict_project_rules[project]
                    try:
                        editor_text = random.choice(list(project_members.keys()))
                    except IndexError:
                        break

                    if editor_text in recommended_editors:
                        del project_members[editor_text]
                        continue
                    i += 1

                    str_editor_desription = self.create_message_rule(project, organizer, editor_text,
                                                                self.dict_project_rules[project][editor_text])
                    list_editor_wikicodes.append(str_editor_desription)
                    self.set_editors_treatment_group.add((project, organizer, editor_text, "rule"))
                    del project_members[editor_text]
                    recommended_editors.add(editor_text)

                # # print topic based
                # nbr_editors = min(self.nbr_per_alg, len(self.dict_project_topics[project].keys()))
                # i = 0
                # while i < nbr_editors:
                #     project_members = self.dict_project_topics[project]
                #     try:
                #         editor_text = random.choice(list(project_members.keys()))
                #     except IndexError:
                #         break
                #
                #     if editor_text in recommended_editors:
                #         del project_members[editor_text]
                #         continue
                #     i += 1
                #
                #     str_editor_desription = self.create_message_topics(project, organizer, editor_text,
                #                                                          self.dict_project_topics[project][
                #                                                              editor_text])
                #     list_editor_wikicodes.append(str_editor_desription)
                #     self.set_editors_treatment_group.add((project, organizer, editor_text, "topic"))
                #     del project_members[editor_text]
                #     recommended_editors.add(editor_text)

                # # print bonds based
                # nbr_editors = min(self.nbr_per_alg, len(self.dict_project_bonds[project].keys()))
                # i = 0
                # while i < nbr_editors:
                #     project_members = self.dict_project_bonds[project]
                #     try:
                #         editor_text = random.choice(list(project_members.keys()))
                #     except IndexError:
                #         break
                #
                #     if editor_text in recommended_editors:
                #         del project_members[editor_text]
                #         continue
                #     i += 1
                #
                #     str_editor_desription = self.create_message_bonds(project, organizer, editor_text,
                #                                                          self.dict_project_bonds[project][
                #                                                              editor_text])
                #     list_editor_wikicodes.append(str_editor_desription)
                #     self.set_editors_treatment_group.add((project, organizer, editor_text, "bonds"))
                #     del project_members[editor_text]
                #     recommended_editors.add(editor_text)

                # print uucf
                nbr_editors = min(self.nbr_per_alg, len(self.dict_project_uucf[project].keys()))
                i = 0
                while i < nbr_editors:
                    project_members = self.dict_project_uucf[project]
                    try:
                        editor_text = random.choice(list(project_members.keys()))
                    except IndexError:
                        break

                    if editor_text in recommended_editors:
                        del project_members[editor_text]
                        continue
                    i += 1

                    str_editor_desription = self.create_message_uucf(project, organizer, editor_text,
                                                                      self.dict_project_uucf[project][
                                                                          editor_text])
                    list_editor_wikicodes.append(str_editor_desription)
                    self.set_editors_treatment_group.add((project, organizer, editor_text, "uucf"))
                    del project_members[editor_text]
                    recommended_editors.add(editor_text)

                fout = open(self.output_dir + project.replace(" ", "_") + "_" + organizer.replace(" ", "_") + "_"+ str(self.batch_nbr) + ".csv", "w")
                message_greeting = self.message_greeting.format(organizer)
                print(message_greeting, file=fout)

                print("{}".format(self.table_header_general), file=fout)
                # shuffle the list before printing out
                # shuffle(list_editor_wikicodes)
                for editor_wikicode in list_editor_wikicodes:
                    print("{}".format(editor_wikicode), file=fout)
                print("|}", file=fout)

                print("Recommending {} editors for {} of WikiProject {}".format(len(list_editor_wikicodes),
                                                                                    organizer,
                                                                                    project))

                # print(self.message_ending, file=fout)

        # after recommendations, the editors who are randomly left out will go into this group.
        self.identify_control_group_editors()
        # keep track of the editors who have been recommended to editors
        self.write_recommendations_treatment_and_control()

    def identify_control_group_editors(self):
        for project in self.sample_projects:
            if project not in self.dict_project_topics:
                continue

            if project in self.dict_project_newcomers:
                for editor in self.dict_project_newcomers[project]:
                    self.set_editors_control_group.add((project, editor, "new"))

            for editor in self.dict_project_topics[project]:
                self.set_editors_control_group.add((project, editor, "topic"))
            for editor in self.dict_project_rules[project]:
                self.set_editors_control_group.add((project, editor, "rule"))
            for editor in self.dict_project_bonds[project]:
                self.set_editors_control_group.add((project, editor, "bonds"))
            for editor in self.dict_project_uucf[project]:
                self.set_editors_control_group.add((project, editor, "uucf"))

    def write_recommendations_treatment_and_control(self):
        filename = "data/collection/group_treatment2.csv"
        fout = open(filename, "a")
        for (project, organizer, editor, type) in self.set_editors_treatment_group:
            print("{}*{}*{}*{}*{}".format(project, organizer, editor, type, self.batch_nbr), file=fout)

        from datetime import datetime
        print("******{}".format(str(datetime.now())), file=fout)

        filename = "data/collection/group_control2.csv"
        fout = open(filename, "w")
        for (project, editor, type) in self.set_editors_control_group:
            print("{}*{}*{}*{}".format(project, editor, type, self.batch_nbr), file=fout)

    def execute_WIR(self):
        self.dict_project_WIR = self.read_file_WIR()

        WIR = 'Women in Red'
        for organizer in self.dict_project_organizers[WIR]:
            list_editor_wikicodes = []

            nbr_editors = min(self.nbr_WIR, len(self.dict_project_WIR))
            for i in range(nbr_editors):
                project_members = self.dict_project_WIR
                editor_text = random.choice(list(project_members.keys()))

                str_editor_desription = self.create_message_WIR(organizer, editor_text, self.dict_project_WIR[editor_text])
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

    def create_message_WIR_group(self, editor_text, editor_info, infoboxes, editor_articles, month):
        user_page = "{{noping2 | {}}}".format(editor_text)
        date_regstr = datetime.strptime(editor_info['regstr_ts'], "%Y-%m-%dT%H:%M:%SZ")
        date_regstr_str = "{}-{}-{}".format(date_regstr.year, date_regstr.month, date_regstr.day)

        str_article_list = ""
        for article in editor_articles:
            str_article_list += self.article_link(article) + ", "

        description = "{} created {} WIR articles in {}: {}.".format(editor_text,
                                                                     editor_info['page_created'],
                                                                     month,
                                                                     str_article_list)

        description = "{} created {} WIR articles in {}".format(editor_text,
                                                                     editor_info['page_created'],
                                                                     month)

        if infoboxes:
            str_infoboxes_list = ""
            for infobox, cnt in infoboxes:
                str_infoboxes_list += infobox + ":" + str(cnt) + ", "

            infobox_info = "Major occupations this editor created: {}".format(str_infoboxes_list)
            message_with_mouseover = "{{" + "H:title|{}|{}".format(infobox_info, description) + "}}"

            message_with_mouseover += ": {}".format(str_article_list)
        else:
            message_with_mouseover = description + ": {}".format(str_article_list)

        str_message = "|-\n | {" + user_page + "}" + "|| {} || {} || {} || {} ||".format(message_with_mouseover,
                                                                              date_regstr_str,
                                                                              editor_info['editcount'],
                                                                              self.form_editor_status(editor_info['status']))
        return str_message

    def execute_WIR_group(self, list_editors_sorted, dict_editor_infoboxes, dict_editor_info, dict_editor_articles, month):

        list_editor_wikicodes = []
        for editor in list_editors_sorted:
            if editor not in dict_editor_info:
                continue

            if editor in dict_editor_infoboxes:
                infoboxes = dict_editor_infoboxes[editor]
            else:
                infoboxes = None
            str_editor_description = self.create_message_WIR_group(editor, dict_editor_info[editor], infoboxes, dict_editor_articles[editor], month)
            list_editor_wikicodes.append(str_editor_description)

        fout = open(self.output_dir + "WIR_group_" + month + ".csv", "w")
        print(self.table_header_WIR, file=fout)
        for editor_code in list_editor_wikicodes:
            print("{}".format(editor_code), file=fout)
        print("|}", file=fout)



    def create_newcomer_message(self, project, organizer, editor_text, editor_info):
        user_page = "{{noping2 | {}}}".format(editor_text)
        date_regstr = datetime.strptime(editor_info['regstr_time'], "%Y-%m-%d %H:%M:%S")
        date_regstr_str = "{}-{}-{}".format(date_regstr.year, date_regstr.month, date_regstr.day)
        description = "{} just joined Wikipedia and made her/his first edit on {} which is in the scope of your project." \
                      "It's a strong indication that she/he will like your project. Please welcome our Wikipedia newbies!".format(editor_text,
                                                                                                                              self.article_link(editor_info['first_article']))

        description = "{} just joined Wikipedia and made the first edit on an article " \
                      "within the scope of your project, {}.".format(editor_text, self.article_link(editor_info['first_article']))

        rationale = "The first edit is a strong indication on editor's interest. " \
                    "They might be interested in working on your project. " \
                    "Their recent edits show their good editing records. " \
                    "Please welcome Wikipedia newbies, and help them onboard!"
        message_with_mouseover = "{{" + "H:title|{}|{}".format(rationale, description) + "}}"

        str = "|-\n | {" + user_page + "}" + "|| {} || {} || {} || {} || {} || {}".format(message_with_mouseover,
                                                                                          date_regstr_str,
                                                                                          editor_info['wp_edits'],
                                                                                          self.form_editor_status(editor_info['status']),
                                                                                          self.form_template_link_newcomers(project, editor_text),
                                                                                          self.form_survey_link(project, organizer, editor_text))
        return str

    def create_message_rule(self, project, organizer, editor_text, editor_info):

        # invite = "{{H:title|Please sign your signature when inviting the editor. |Invitation Status}}"

        user_page = "{{noping2 | {}}}".format(editor_text)
        date_regstr = datetime.strptime(editor_info['regstr_time'], "%Y-%m-%d %H:%M:%S")
        date_regstr_str = "{}-{}-{}".format(date_regstr.year, date_regstr.month, date_regstr.day)
        description = "{} made {} out of their most recent 500 edits to " \
                      "articles within the scope of your project. ".format(editor_text,
                                                                      editor_info['project_edits'])

        rationale = "These editors might not be aware of your project. " \
                    "Their recent edits on project-related articles indicate their interest to your project. " \
                    "Their recent edits also show their good editing records. " \
                    "Invite them to your project. They will have the opportunity to contribute more!"
        message_with_mouseover = "{{" + "H:title|{}|{}".format(rationale, description) + "}}"

        str = "|-\n | {" + user_page + "}" + "|| {} || {} || {} || {} || {} || {}".format(message_with_mouseover,
                                                                                          date_regstr_str,
                                                                                          editor_info['wp_edits'],
                                                                                          self.form_editor_status(editor_info['status']),
                                                                                          self.form_template_link(project, editor_text),
                                                                                          self.form_survey_link(project, organizer, editor_text))
        return str


    def create_message_uucf(self, project, organizer, editor_text, editor_info):
        user_page = "{{noping2 | {}}}".format(editor_text)
        date_regstr = datetime.strptime(editor_info['regstr_time'], "%Y-%m-%d %H:%M:%S")
        date_regstr_str = "{}-{}-{}".format(date_regstr.year, date_regstr.month, date_regstr.day)
        neighbor1 = "{{noping2 | {}}}".format(editor_info['neighbor1'])
        # neighbor2 = "{{User | {}}}".format(editor_info['neighbor2'])
        # description = "{} edited articles similar to the articles your project members edited. " \
        #               "For instance, {} and project member {} edited {} articles in common.
        # She/He will be interested in your project articles!".format(editor_text,
        #                                                              editor_text,
        #                                                              editor_info['neighbor1'],
        #                                                              editor_info['common_edits'])

        # description = "{} edited articles similar to articles your project members edited. " \
        #               "For example, {} and project member {} edited {} of the same articles in their most recent 500 edits. " \
        #               "This suggests that {} will be interested in " \
        #               "editing your project's articles!".format(editor_text,
        #                                                         editor_text,
        #                                                         editor_info['neighbor1'],
        #                                                         editor_info['common_edits'], editor_text)
        description1 = "{} edited articles similar to articles your project members edited. " \
                      "For example, {} and you project member ".format(editor_text, editor_text) + "{" + neighbor1 + "}"#"{{User | {}}}".format(editor_info['neighbor1'])
        description2 = " edited {} of the same articles in their most recent 500 edits. ".format(editor_info['common_edits'])
                      # "This suggests that {} will be interested in editing your project's articles!".format(editor_info['common_edits'], editor_text)
        description = description1 + description2

        rationale = "These editors might not be aware of your project. " \
                    "Their recent edits that are similar to your project members indicate they will be interested in editing your project's articles. " \
                    "Their recent edits also show their good editing records. " \
                    "Invite them to your project. They will have the opportunity to contribute more!"
        message_with_mouseover = "{{" + "H:title|{}|{}".format(rationale, description) + "}}"

        str = "|-\n | {" + user_page + "}" + "|| " + message_with_mouseover + " || {} || {} || {} || {} || {}".format(date_regstr_str,
                                                                                                          editor_info['wp_edits'],
                                                                                                          self.form_editor_status(editor_info['status']),
                                                                                                          self.form_template_link(project, editor_text),
                                                                                                          self.form_survey_link(project, organizer, editor_text))
        return str

    def create_message_bonds(self, project, organizer, editor_text, editor_info):
        user_page = "{{noping2 | {}}}".format(editor_text)
        date_regstr = datetime.strptime(editor_info['regstr_time'], "%Y-%m-%d %H:%M:%S")
        date_regstr_str = "{}-{}-{}".format(date_regstr.year, date_regstr.month, date_regstr.day)
        description = "{} has strong bonds with your project members! She/He has sent over {} messages to more than {} your project members on their user talk pages. " \
                      "Researchers have found that editors with stronger bonds to project members will edit more and stay longer in the project.".format(editor_text,
                                                                                                                     editor_info['pjtk_cnt'],
                                                                                                                     editor_info['talker_cnt'])

        description = "{}'s editing history shows connections with your project members! " \
                      "They have posted multiple messages on the user talk pages of a number of your project members. " \
                      "Studies have found that editors with these kinds of connections to project members " \
                      "tend to edit more and stay longer in the project!".format(editor_text)

        str = "|-\n | {" + user_page + "}" + "|| {} || {} || {} || {} || {} || {}".format(description,
                                                                                          date_regstr_str,
                                                                                          editor_info['wp_edits'],
                                                                                          self.form_editor_status(editor_info['status']),
                                                                                          self.form_template_link(project, editor_text),
                                                                                          self.form_survey_link(project, organizer, editor_text))
        return str

    def create_message_topics(self, project, organizer, editor_text, editor_info):
        user_page = "{{noping2 | {}}}".format(editor_text)
        date_regstr = datetime.strptime(editor_info['regstr_time'], "%Y-%m-%d %H:%M:%S")
        date_regstr_str = "{}-{}-{}".format(date_regstr.year, date_regstr.month, date_regstr.day)
        if editor_info['cate_second'] != 'None':
            description = "{} has a strong topic match with your project. She/He edited articles mostly fall into Category {} and {}. " \
                          "Your project's articles are mostly under Category {} and {}. Researchers have found that editors with a stronger " \
                          "topic match with the project will edit more and stay longer in the project!".format(editor_text,
                                                                                                self.category_link(editor_info['cate_first']),
                                                                                                self.category_link(editor_info['cate_second']),
                                                                                                self.category_link(self.project_first_category[project]),
                                                                                                self.category_link(self.project_second_category[project]))
            description = "{}'s editing history suggests a strong match with your project. Most articles they have edited fall under the Category {} and {}, " \
                          "and most of your project's articles also fall under these categories. " \
                          "Studies have found that editors with a stronger topic match with a project tend to edit more and stay longer in the project! ".format(
                editor_text,
                self.category_link(editor_info['cate_first']),
                self.category_link(editor_info['cate_second']),
                self.category_link(self.project_first_category[project]),
                self.category_link(self.project_second_category[project]))

        else:
            description = "{} has a strong topic match with your project. She/He edited articles mostly fall into Category {}. " \
                          "Your project's articles are mostly under Category {} and {}. Researchers have found that editors with a stronger " \
                          "topic match with the project will edit more and stay longer in the project!".format(editor_text,
                                                                                                               self.category_link(editor_info['cate_first']),
                                                                                                               self.category_link(self.project_first_category[project]),
                                                                                                               self.category_link(self.project_second_category[project]))

            description = "{}'s editing history suggests a strong match with your project. Most articles they have edited fall under the Category {}, " \
                          "and most of your project's articles also fall under this category. " \
                          "Studies have found that editors with a stronger topic match with a project tend to edit more and stay longer in the project! ".format(
                editor_text,
                self.category_link(editor_info['cate_first']),
                self.category_link(self.project_first_category[project]),
                self.category_link(self.project_second_category[project]))



        str = "|-\n | {" + user_page + "}" + "|| {} || {} || {} || {} || {} || {}".format(description,
                                                                                          date_regstr_str,
                                                                                          editor_info['wp_edits'],
                                                                                          self.form_editor_status(editor_info['status']),
                                                                                          self.form_template_link(project, editor_text),
                                                                                          self.form_survey_link(project, organizer, editor_text))
        return str


    def create_message_WIR(self, organizer, editor_text, editor_info):
        user_page = "{{User | {}}}".format(editor_text)
        date_regstr = datetime.strptime(editor_info['regstr_ts'], "%Y-%m-%dT%H:%M:%SZ")
        date_regstr_str = "{}-{}-{}".format(date_regstr.year, date_regstr.month, date_regstr.day)
        #[[Nancy_Denton | Article: Nancy Denton]]
        description = "{} created {} articles for Women in Red this month, such as {}.".format(editor_text,
                                                                                      editor_info['page_created'],
                                                                                      self.article_link(editor_info['article']))
        #editor_text, page_created, editcount, regstr_ts, article, status
        str = "|-\n | {" + user_page + "}" + "|| {} || {} || {} || {} || {}".format(description,
                                                                                   date_regstr_str,
                                                                                   editor_info['wp_edits'],
                                                                                    self.form_editor_status(editor_info['status']),
                                                                                   self.form_survey_link("Women in Red",
                                                                                                         organizer, editor_text))
        return str

    def category_link(self, category):
        category = category.title()
        return "[[Portal:{}|{}]]".format(category, category)

    def article_link(self, title):
        return "[[{} | Article:{}]]".format(title, title)

    def form_survey_link(self, project, organizer, editor):
        project = project.replace(" ", "%20")
        organizer = organizer.replace(" ", "%20")
        editor = editor.replace(" ", "%20")
        return self.survey_link.format(project, organizer, editor)

    def form_template_link(self, project, editor):
        editor = editor.replace(" ", "_")
        str = self.invitation_link_exp.format(editor)
        return str

    def form_template_link_newcomers(self, project, editor):
        editor = editor.replace(" ", "_")
        str = self.invitation_link_newcomers.format(editor)
        return str

    def form_editor_status(self, status):
        if status == 'Active':
            str = "{{H:title|Active: made 5 + edits in 30 days. |Active}}"
        elif status == 'Very Active':
            str = "{{H:title|Very Active: made 100+ edits in 30 days. |Very Active}}"
        else:
            str = "{{H:title|New Editor: Joined Wikipedia in 5 days. |New Editor}}"
        return str

    def finish(self):
        for key in self.projects:
            project_file_name = key + '.csv'
            project_file = open(project_file_name, 'a')
            project_file.write('|}')
            project_file.close()

    @staticmethod
    def read_bot_list():
        filename = os.getcwd() + "/data/bot_list.csv"
        # each line only contain an editor name
        list_bots = set()
        for line in open(filename, "r").readlines()[1:]:
            list_bots.add(line.strip())
        return list_bots

    def create_tables(self):

        self.execute()
        # self.execute_WIR()
#
def main():
    from sys import argv
    if len(argv) != 3:
        print("Usage: <organizer file> <batch number>")
        return


    table_generator = TableGenerator(argv[1], int(argv[2]))
    table_generator.compute_recommendation_overlaps()
    table_generator.execute()

main()


