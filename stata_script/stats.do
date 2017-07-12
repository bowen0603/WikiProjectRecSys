clear all
set more off

import delimited "/Users/bobo/Documents/wikiproject_recsys/data/projects_joined_1edit.csv", encoding(ISO-8859-1)

sum projects_joined , detail


clear all
set more off

import delimited "/Users/bobo/Documents/wikiproject_recsys/data/user_stats.csv", encoding(ISO-8859-1)

reg total_edits projects_joined if projects_joined >= 2 & projects_joined <= 8 & total_edits <  500000

reg tenure_months  projects_joined if projects_joined >= 2 & projects_joined <= 8 & total_edits <  500000


clear all
set more off

import delimited "/Users/bobo/Documents/wikiproject_recsys/data/filtered_users_by_projects_2edits_joining3.csv", encoding(ISO-8859-1)

scatter 
