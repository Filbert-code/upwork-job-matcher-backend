from datetime import datetime, timedelta
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import boto3

from job_match_determinator import JobMatchDeterminator
from lib.data_cleaning_operations import get_min_max_hourly_rates
from lib.date_operations import convert_posted_time_to_datetime
from lib.dynamodb_client import DynamodbClient

base_endpoint = 'https://www.upwork.com/nx/jobs/search/'

# Sorting by:
# 1. recency
# 2. location match
# 3. Payment Verified
# 4. Hourly rate at least 25
sort_by = '?sort=recency&user_location_match=1&t=0&payment_verified=1&hourly_rate=25-'


def scrape_upwork():
    chrome_options = Options()
    # chrome_options.headless = True
    # chrome_options.add_argument("start-maximized")
    s = Service(r'C:\Users\alex\PycharmProjects\upwork_scraper\chromedriver.exe')
    driver = webdriver.Chrome(service=s, options=chrome_options)
    driver.implicitly_wait(10)

    driver.get(f'{base_endpoint}{sort_by}')
    titles = driver.find_elements(By.CLASS_NAME, 'job-tile-title')
    descriptions = driver.find_elements(By.XPATH, '//span[@data-test="job-description-text"]')
    experience_levels = driver.find_elements(By.XPATH, '//span[@data-test="contractor-tier"]')
    times_posted = driver.find_elements(By.XPATH, '//span[@data-test="posted-on"]')

    hourly_div = driver.find_elements(By.XPATH, '//div[@data-test="JobTileFeatures"]')
    hourly_rates = [div.find_element(By.TAG_NAME, 'strong').text for div in hourly_div]

    skill_badge_lists = []
    job_cards = driver.find_elements(By.XPATH, '//section[@data-test="JobTile"]')
    for card in job_cards:
        skill_badge_list = [badge.text for badge in card.find_elements(By.CLASS_NAME, 'up-skill-badge')]
        skill_badge_lists.append(skill_badge_list)

    # for i in range(len(titles)):
    #     print(titles[i].text)
    #     print(descriptions[i].text)
    #     print(experience_levels[i].text)
    #     print(times_posted[i].text)
    #     print(hourly_rates[i])
    #     print(skill_badge_lists[i])
    #     print('-------------------------------------------------')
    new_job_data = []
    for i in range(len(titles)):
        posted_time_to_datetime = convert_posted_time_to_datetime(times_posted[i].text).isoformat()
        hourly_min, hourly_max = get_min_max_hourly_rates(hourly_rates[i])
        new_job_data.append({
            'title': titles[i].text,
            'description': descriptions[i].text,
            'experience_level': experience_levels[i].text,
            'time_posted': posted_time_to_datetime,
            'hourly_min': hourly_min,
            'hourly_max': hourly_max,
            'skill_badges': skill_badge_lists[i]
        })
    driver.close()

    # add new jobs to the Jobs Table
    dynamodb_client = DynamodbClient()
    # get all job keys currently in the database
    new_jobs_count = 0
    new_jobs_titles = []
    job_data_map = {}
    for new_job in new_job_data:
        # add new job to the jobs table if it isn't already there
        job_key = f'{new_job["title"]}-{new_job["description"][:20]}'
        if not dynamodb_client.is_job_in_table(job_key):
            dynamodb_client.put_job(new_job)
            new_jobs_count += 1
            new_jobs_titles.append(new_job['title'])
            job_data_map[job_key] = new_job


    # find new job matches and update the subscriptions results
    job_matcher = JobMatchDeterminator(job_data_map, print_logs=True)
    for user_subscription in dynamodb_client.get_all_user_keyword_subscriptions():
        sub_name = user_subscription['name']
        user_kws_and_weights = dict(zip(user_subscription['keywords'], user_subscription['keyword_weights']))
        # run the job match determinator
        job_matcher.set_user_keywords_and_weights(user_kws_and_weights)
        job_matcher.overall_score_threshold = len(user_kws_and_weights.keys()) / 2
        matched_jobs = job_matcher.get_job_matches()
        # add matched jobs to the results attribute of the subscription
        curr_user_sub_matched_jobs = dynamodb_client.get_user_subscription_results(sub_name)
        dynamodb_client.update_user_subscription_results(
            name=sub_name,
            new_results=(curr_user_sub_matched_jobs + matched_jobs)[-8:]
        )

    # data to print as logs in the bot loop
    return new_jobs_count, new_jobs_titles


def run_scrape_upwork_loop():
    minutes_to_sleep = 10
    while True:
        # run the bot
        new_jobs_count, new_jobs_titles = scrape_upwork()
        # print current time and output
        # ------------------------
        print(f'Current time: {datetime.now().strftime("%H:%M:%S")}')
        if new_jobs_count > 0:
            print(f'Found {new_jobs_count} new jobs:')
            for title in new_jobs_titles:
                print(title)
            print('-------------------------------------------------')
        else:
            print(f'No new jobs found. ')
            print('-------------------------------------------------')
        sleep(60 * minutes_to_sleep)
        # ------------------------


if __name__ == '__main__':
    run_scrape_upwork_loop()
