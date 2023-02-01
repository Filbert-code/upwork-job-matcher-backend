from typing import List
import boto3
from boto3.dynamodb.conditions import Key


class DynamodbClient:
    JOBS_TABLE = 'upwork-jobs-table'
    KEYWORDS_TABLE = 'upwork-user-keywords-table'

    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.upwork_jobs_table = self.dynamodb.Table(self.JOBS_TABLE)
        self.keywords_table = self.dynamodb.Table(self.KEYWORDS_TABLE)

    def put_job(self, job):
        response = self.upwork_jobs_table.put_item(
            Item={
                'title-description20': f'{job["title"]}-{job["description"][:20]}',
                'time_posted': job['time_posted'],
                'title': job['title'],
                'description': job['description'],
                'experience_level': job['experience_level'],
                'hourly_min': job['hourly_min'],
                'hourly_max': job['hourly_max'],
                'skill_badges': job['skill_badges']
            }
        )

    def create_user_keyword_subscription(self, name: str, keywords: List[str], kw_weights: List[int]):
        response = self.keywords_table.put_item(
            Item={
                'name': name,
                'keywords': keywords,
                'keyword_weights': kw_weights,
                'results': []
            }
        )

    def get_all_user_keyword_subscriptions(self):
        items = self.keywords_table.scan()['Items']
        return items

    def get_user_subscription_results(self, subscription_name):
        results = self.keywords_table.get_item(Key={'name': subscription_name})['Item']['results']
        return results

    def is_job_in_table(self, job_key):
        response = self.upwork_jobs_table.query(
            KeyConditionExpression=Key('title-description20').eq(job_key)
        )['Items']
        return len(response) > 0

    def update_user_subscription_results(self, name, new_results):
        response = self.keywords_table.update_item(
            Key={'name': name},
            UpdateExpression='set results = :r',
            ExpressionAttributeValues={
                ':r': new_results,
            },
            ReturnValues="UPDATED_NEW"
        )
        return response


if __name__ == '__main__':
    db_client = DynamodbClient()
    print([item['job_key'] for item in db_client.get_user_subscription_results('Python Data Jobs')])
    # db_client.create_user_keyword_subscription(
    #     'test subscription 2',
    #     ['business', 'awesomeness', 'money', 'spreadsheets', 'computer'],
    #     [1, 20, 1, 1, 1]
    # )
    # print(db_client.get_user_subscription_results(
    #     'test subscription',
    # ))
    # print(db_client.get_all_user_keyword_subscriptions())