from __future__ import print_function
import uuid
from google.cloud import bigquery
from datetime import datetime
import time

__author__ = 'bobo'

"""
1. Basics for writing bigquery in python:
    https://cloud.google.com/bigquery/querying-data#bigquery-query-python
2. How to set parameters for query:
    https://cloud.google.com/bigquery/docs/reference/rest/v2/jobs
3. How to create table:
    https://cloud.google.com/bigquery/docs/tables#bigquery-create-table-python
"""

class QueryHandler:

    def __init__(self):
        self.project_id = "robert-kraut-1234"
        self.client = bigquery.Client(project=self.project_id)

    def run_query(self, query, dest_dataset, dest_table):

        time_start = datetime.now()

        dataset = bigquery.Dataset(dest_dataset, self.client)
        table = bigquery.Table(dest_table, dataset)

        query_job = self.client.run_async_query(str(uuid.uuid4()), query)
        query_job.use_legacy_sql = False
        query_job.destination = table
        query_job.write_disposition = "WRITE_TRUNCATE"
        query_job.allow_large_results = True
        query_job.flatten_results = True

        # Start the query and wait for the job to complete.
        query_job.begin()
        self.wait_for_job(query_job)
        self.print_results(query_job.results())

        time_delta = (datetime.now() - time_start)
        print("Table [{}.{}] created in {} seconds.".format(dest_dataset, dest_table, time_delta.seconds))


    # Creates an empty table with given schema
    def create_table(self, dest_dataset, dest_table, list_schema):

        dataset = self.client.dataset(dest_dataset)
        if not dataset.exists():
            print("Dataset {} does not exist.".format(dest_dataset))
            return

        table = dataset.table(dest_table)
        if table.exists():
            print("Table [{}.{}] existed already. Skip creating.".format(dest_dataset, dest_table))
            return

        schemas = []
        for (item, type) in list_schema:
            schemas.append(bigquery.SchemaField(item, type))
        table.schema = schemas

        table.create()
        print("Empty Table [{}.{}] created.".format(dest_dataset, dest_table))

    def load_data_from_file(self, dest_dataset, dest_table, source_file_name):

        time_start = datetime.now()

        bigquery_client = bigquery.Client()
        dataset = bigquery_client.dataset(dest_dataset)
        table = dataset.table(dest_table)

        # Reload the table to get the schema.
        table.reload()

        with open(source_file_name, 'rb') as source_file:
            job = table.upload_from_file(file_obj=source_file,
                                         field_delimiter='*',
                                         skip_leading_rows=1,
                                         source_format='text/csv')

        self.wait_for_job(job)

        time_delta = (datetime.now() - time_start)
        print("Table [{}.{}] uploaded in {} seconds.".format(dest_dataset, dest_table, time_delta.seconds))

    def wait_for_job(self, job):
        while True:
            job.reload()  # Refreshes the state via a GET request.
            if job.state == 'DONE':
                if job.error_result:
                    raise RuntimeError(job.errors)
                return
            time.sleep(1)



    def print_results(self, query_results):
        """Print the rows in the query's results."""
        rows = query_results.fetch_data(max_results=10)
        for row in rows:
            print(row)

    def table_name(self, name):
        pass


    def execute(self):
        query = """
            SELECT *
            FROM `{}.{}`
            LIMIT 100
        """.format("bowen_quitting_script", "all_user_last_first_edits")
        self.run_query(query, "bowen_quitting_script", "new_place_for_python")

        # schema fields must be in order
        dict_schema = (("wikiproject", "STRING"),
                       ("user_text", "STRING"),
                        ("user_id", "INTEGER"),
                        ("first_article", "STRING"),
                        ("project_edits", "INTEGER"),
                        ("wp_edits", "INTEGER"),
                        ("last_edit", "STRING"),
                        ("regstr_time", "STRING"))

        self.create_table("bowen_quitting_script", "recommendations_newcomers", dict_schema)
        self.load_data_from_file("bowen_quitting_script", "recommendations_newcomers", "data/recommendations_newcomers.csv")

def main():
    handler = QueryHandler()
    handler.execute()

main()

