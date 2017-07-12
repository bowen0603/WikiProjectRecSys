from __future__ import print_function
__author__ = 'bobo'

import requests
# dir_name = "project_articles_pairs/"

# project_list = ["Film", "Biography", "Women in Red", "U.S. Roads", "Oregon", "Opera", "Politics", "Ethnic%20groups", "Novels", "Plants"]

def construct_cont_url(project, wpcont):
    url = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=projectpages&wpplimit=500&wppassessments=1&wppprojects=" + project
    url += "&wppcontinue=" + wpcont
    return url


def construct_original_url(project):
    url = "https://en.wikipedia.org/w/api.php?action=query&format=json&list=projectpages&wpplimit=500&wppassessments=1&wppprojects=" + project
    return url


def read_project_list(filename):
    header = True
    project_list = []

    for line in open(filename, 'r'):
        if header:
            header = False
            continue

        project = line.split(",")[0]
        project = project.replace("WikiProject_", "")
        project = project.replace("_", " ")
        project_list.append(project)

    return project_list



def obtain_project_articles(project_list, output_dir):

    cnt = 0
    wp_continue = ""
    project_list = read_project_list(project_list)


    from os import stat, mkdir
    try:
        stat(output_dir)
    except:
        mkdir(output_dir)


    for project in project_list:

        cnt += 1
        import os.path
        if os.path.isfile(output_dir + str(cnt) + project + ".csv"):
            continue

        fout = open(output_dir + str(cnt) + project + ".csv", "w")


        print("wikiproject,art_title,art_pageid,art_ns,art_importance,art_class", file=fout)

        first_request = True
        art_cnt = 0

        print("Working on project {} .. ".format(project))
        import time
        start_time = time.time()

        while True:

            try:

                if first_request:
                    response = requests.get(construct_original_url(project)).json()
                    first_request = False
                else:
                    response = requests.get(construct_cont_url(project, wp_continue)).json()

                for article in response['query']['projects'][project]:
                    art_importance = article['assessment']['importance'].encode('utf-8').lower()
                    art_class = article['assessment']['class'].encode('utf-8').lower()
                    art_ns = article['ns']
                    art_pageid = article['pageid']
                    art_title = article['title'].encode('utf-8').lower()

                    if art_class == 'redirect':
                        continue

                    art_cnt += 1
                    print("{},{},{},{},{},{}".format(project.lower(), art_title, art_pageid, art_ns, art_importance, art_class), file=fout)

                wp_continue = response['continue']['wppcontinue']

                if "error" in response and response['error']['code'] == 'maxlag':
                    ptime = max(5, int(response.headers['Retry-After']))
                    print('WD API is lagged, waiting {} seconds to try again'.format(ptime))
                    from time import sleep
                    sleep(ptime)
                    continue

            except KeyError:
                end_time = time.time()
                # request has a field called batch complete and doesn't have the wppcontinue any more
                print("Stops at {}, {} articles in {} minutes. ".format(project, art_cnt, (end_time-start_time)/60))
                break

'''
sample input:
# args: data/Top40ContentWikiProjects.csv project_article_pairs/
'''

def main():

    from sys import argv
    if len(argv) != 3:
        print("Usage: <input: Project List> <output: file directory>")
        return

    obtain_project_articles(argv[1], argv[2])


main()

