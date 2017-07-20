__author__ = 'bobo'

def constr_cont_url(self, editor_text, wpcont):
        query = self.url_usercontb + "uclimit="+str(self.const_max_requests)+"&ucnamespace=0|3|4|5&" \
                                     "ucprop=title|timestamp|parsedcomment|sizediff|ids&ucuser=" + editor_text
        query += "&uccontinue=" + wpcont
        return query


def constr_original_url(self, editor_text):
    query = self.url_usercontb + "uclimit="+str(self.const_max_requests)+"&ucnamespace=0|3|4|5&" \
                                 "ucprop=title|timestamp|parsedcomment|sizediff|ids&ucuser=" + editor_text
    return query

cnt_page += 1
if cnt_page == 3:
    break
if first_query:
    query = self.constr_original_url(editor_text)
    first_query=False
else:
    query = self.constr_cont_url(editor_text, uccontinue)


first_query = True
continue_querying = True
cnt_page = 0
latest_datetime = datetime.fromordinal(1)

# TODO: Just fetch 500 edits using one query for each editor
while continue_querying:
    try:
        # TODO: only for the most recent 1000 edits ???
        cnt_page += 1
        if cnt_page == 3:
            break
        if first_query:
            query = self.constr_original_url(editor_text)
            first_query=False
        else:
            query = self.constr_cont_url(editor_text, uccontinue)

        # query = self.url_usercontb + "ucnamespace=0%7C3%7C4%7C5&" \
        #                              "ucprop=title%7Ctimestamp%7Cparsedcomment%7Csizediff&" \
        #                              "ucuser=" + editor_text + "&uccontinue=" + uccontinue
        response = requests.get(query).json()

        if 'continue' in response:
            uccontinue = response['continue']['uccontinue']
        else:
            continue_querying = False

        for usercontrib in response['query']['usercontribs']:
            page_title = usercontrib['title']
            page_id = usercontrib['pageid']
            ns = usercontrib['ns']
            userid = usercontrib['userid']
            user_text = usercontrib['user']

            edit_datetime = datetime.strptime(usercontrib['timestamp'], "%Y-%m-%dT%H:%M:%SZ")
            latest_datetime = max(edit_datetime, latest_datetime)
            self.dict_editor_last_edit_datetime[user_text] = latest_datetime

            # print("{},{},{},{}".format(user_text, userid, page_title, ns))
            if ns == 0:
                edits_ns0_artiles[page_title] = 1 if page_title not in edits_ns0_artiles \
                    else edits_ns0_artiles[page_title] + 1

                # projects = self.parser_cat.extract_article_projects(title)
                # print(projects)
                # todo: create editor-project-editcount
                # todo: handle extracted projects
            elif ns == 3:
                # todo: create a list of editors talked to
                # todo: connect with project members(contributors)
                edits_ns3_users[page_title] = 1 if page_title not in edits_ns3_users \
                    else edits_ns3_users[page_title] + 1
            else:
                # todo: check and considered as project contributors
                edits_ns45_projects[page_title] = 1 if page_title not in edits_ns45_projects \
                else edits_ns45_projects[page_title] + 1
                # TODO: get the page

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

# end of fetching revisions of an editor
stats_edits_projects_articles = self.compute_project_article_edits(edits_ns0_artiles)
print(stats_edits_projects_articles)
self.maintain_project_rule_based_recommendation_lists(editor_text, stats_edits_projects_articles)

#TODO: insert sort to get topic editors who edited project related pages
stats_edits_projects_users = self.compute_project_user_edits(edits_ns3_users)
stats_edits_projects_pages = self.compute_project_page_edits(edits_ns45_projects)


def print_redirects(config_file):
    '''
    Read in the WikiProject configuration file and snapshot,
    identify redirects and print out a wikitable.
    :param config_file: path to the WikiProject YAML configuration file
    :type config_file: str
    '''

    with open(config_file, 'r') as infile:
        proj_conf = yaml.load(infile)

    all_pages = wp.read_snapshot(proj_conf['snapshot file'])

    ## Build a wikitable and print it out
    wikitable = '''{| class="wikitable sortable"
|-
! scope="col" style="width: 40%;" | Title (and talk)
! Rating
! Notes'''

    for page in all_pages:
        if page.is_redirect == "1":
            wikitable = '''{0}
|-
| [[{1}]] <small>([[Talk:{1}]])</small>
| {2}
| '''.format(wikitable, page.talk_page_title.replace("_", " "), page.importance_rating)

    print(wikitable + "\n|}")

    # ok, done
    return()