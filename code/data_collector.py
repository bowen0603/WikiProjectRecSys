from __future__ import print_function
import os
import os.path
import random


class DataCollector:

    def __init__(self):

        self.url_usercontb = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=usercontribs&uclimit=500"


        self.dict_info_organizers_recommending = {}
        self.dict_info_organizers_treatment = {}
        self.dict_info_editor_control = {}

        self.read_recommendation_timestamp()

    def read_control_group_editors(self):
        # project, editor, type, self.batch_nbr
        filename = "data/collection/group_control.csv"
        header = True
        for line in open(filename, "r"):
            if header:
                header = False
                continue

            project = line.split("**")[0]
            editor = line.split("**")[1]
            type = line.split("**")[2]
            batch = line.split("**")[3].strip()

            self.dict_info_editor_control[editor] = {"project": project,
                                                     "type": type,
                                                     "batch": int(batch)}


    def read_treatment_group_editors(self):
        # project, organizer, user_text, type, self.batch_nbr
        filename = "data/collection/group_treatment.csv"
        header = True
        for line in open(filename, "r"):
            if header:
                header = False
                continue

            project = line.split("**")[0]
            organizer = line.split("**")[1]
            user_text = line.split("**")[2]
            type = line.split("**")[3]
            batch = line.split("**")[4].strip()

            if organizer in self.dict_info_organizers_treatment:
                list_recommendations = self.dict_info_organizers_treatment[organizer]['recommendations']
                list_recommendations.append(user_text)
            else:
                list_recommendations = [user_text]
                self.dict_info_organizers_treatment[organizer] = {"project": project,
                                                                  "recommendations": list_recommendations,
                                                                  "type": type,
                                                                  "batch": int(batch)}


    def read_recommendation_timestamp(self):
        #project,organizer,batch#,timestamp
        filename = "data/organizer_recommendations_record.csv"
        header = True
        for line in open(filename, "r"):
            if header:
                header = False
                continue

            project = line.split("**")[0]
            organizer = line.split("**")[1]
            batch = line.split("**")[2]
            timestamp = line.split("**")[3].strip()

            self.dict_info_organizers_recommending[organizer] = {"project": project,
                                                    "batch": int(batch),
                                                    "timestamp": timestamp}



    def identify_recruiting_rate(self):
        # orgnizer, fetch all the edits after the recommendation timestamp
        for organizer in self.dict_info_organizers_recommending:

            try:
                query = self.url_usercontb + "&ucprop=title|timestamp|parsedcomment|flags|ids&ucuser=" + editor_text + "&ucstart="+str(self.dict_info_organizers_treatment[organizer]['timestamp'])
                response = requests.get(query).json()
                latest_datetime = datetime.fromordinal(1)
                current_datetime = datetime.now()
                cnt_mainpage_edits = 0

                for usercontrib in response['query']['usercontribs']:
                    page_title = usercontrib['title']
                    ns = usercontrib['ns']

                    edit_datetime = datetime.strptime(usercontrib['timestamp'], "%Y-%m-%dT%H:%M:%SZ")
                    latest_datetime = max(edit_datetime, latest_datetime)
                    self.dict_editor_last_edit_datetime[editor_text] = latest_datetime

                    if 'parsedcomment' in usercontrib:
                        comment = usercontrib['parsedcomment']
                        if comment.startswith('Revert'):
                            continue

                    # todo: count by the type of recommendations
                    if ns == 3:
                        for editor in self.dict_info_organizers_treatment[organizer]['recommendations']:
                            if editor in page_title:
                                # todo: add different variables to check it
                                pass



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
        # get the edits on ns3 and check with the recommendation editors for reachout rate

        # add the recruiting time, and check the estimated response time of the editor TODO: diffcult to check (manually???)


    def identify_editor_edits_after_recruitment(self):
        # wikiproject, organizer, editor, batch#, recommendation time
        pass