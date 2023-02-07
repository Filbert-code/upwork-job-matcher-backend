import json
from decimal import Decimal

from rake_nltk import Rake, Metric
from thefuzz import process


def create_job_match_results_object(job_keywords, matches, overall_score, job_key, job_data):
    return {
        'job_keywords': job_keywords,
        'matches': matches,
        'overall_score': overall_score,
        'job_key': job_key,
        'job_data': job_data
    }


class JobMatchDeterminator:
    keyword_confidence_threshold = 80

    def __init__(self, job_data, print_logs=False):
        self.job_data = job_data
        self.rake = Rake(max_length=3, ranking_metric=Metric.WORD_DEGREE)
        self.user_keywords_and_weights = None
        self.matched_jobs = []
        self.print_logs = print_logs
        self.sub_name = None

    def set_user_keywords_and_weights(self, user_keywords_and_weights):
        self.user_keywords_and_weights = user_keywords_and_weights
        self.matched_jobs = []

    def get_job_matches(self):
        self.print_processing_config()
        if self.user_keywords_and_weights is None:
            raise Exception('User keywords and weights have not been set')

        for job_key, job_data in self.job_data.items():
            job_keywords = self.get_job_keywords(job_data)
            matches = self.get_job_keyword_matches(job_keywords)
            overall_score, keyword_scores_log_data = self.calculate_overall_score(matches, job_keywords)
            if overall_score >= 1:
                job_match_results = create_job_match_results_object(job_keywords, matches, Decimal(overall_score), job_key, job_data)
                self.matched_jobs.append(job_match_results)
                self.print_keyword_scores_log_data(keyword_scores_log_data)

        if self.print_logs:
            self.print_job_results()
            self.print_processing_summary()
        return self.matched_jobs

    def get_job_keywords(self, job_data):
        # create a map of keywords and phrases from the job title/description
        self.rake.extract_keywords_from_text(job_data['description'])
        job_keywords = [w for w in self.rake.get_ranked_phrases() if len(w) > 1]
        for kw in job_data['skill_badges']:
            job_keywords.append(kw.lower())
        return job_keywords

    def get_job_keyword_matches(self, job_keywords):
        matches = {}
        for job_kw in job_keywords:
            # extract the word with the highest confidence score
            best_user_kw, score = process.extractOne(job_kw, self.user_keywords_and_weights.keys())
            if score >= self.keyword_confidence_threshold:
                if best_user_kw in matches:
                    matches[best_user_kw] = matches[best_user_kw] + 1
                else:
                    matches[best_user_kw] = 1
        return matches

    def calculate_overall_score(self, matches, job_keywords):
        overall_score = 0
        log_data = []
        for user_kw, count in matches.items():
            weight = self.user_keywords_and_weights[user_kw]
            kw_score = count * float(weight) * (len(job_keywords) / len(self.user_keywords_and_weights))
            overall_score += kw_score
            log_data.append({
                'user_keyword': user_kw,
                'user_keyword_count': count,
                'kw_score': overall_score,
            })
        overall_score = (overall_score / len(job_keywords))
        return overall_score, log_data

    def print_keyword_scores_log_data(self, log_data):
        for log in log_data:
            print(f'User Keyword: {log["user_keyword"]}, Count: {log["user_keyword_count"]}, Score: {log["kw_score"]}')

    def print_processing_config(self):
        print('=========================')
        print(f'PROCESSING {self.sub_name} SUBSCRIPTION:')
        print(f'Keyword Confidence Threshold: {self.keyword_confidence_threshold}')
        print(f'User Keywords and Weights: {self.user_keywords_and_weights}')
        print('=========================')

    def print_job_results(self):
        for job in self.matched_jobs:
            print(f'Job Title: {job["job_data"]["title"]}')
            print(f'Keywords: {job["job_keywords"]}')
            print(f'Matches: {job["matches"]}')
            print('-------------------------')

    def print_processing_summary(self):
        print(f'Number of jobs matched: {len(self.matched_jobs)}')


if __name__ == '__main__':
    user_kws_and_weights = {
        'data entry': 1,
        'excel': 2,
        'python': 1,
        'data': 1,
        'data mining': 1,
        'data cleaning': 1
    }
    with open('job_data.json', 'r') as f:
        job_data_map = json.load(f)

    job_matcher = JobMatchDeterminator(job_data_map, print_logs=True)
    job_matcher.set_user_keywords_and_weights(user_kws_and_weights)
    job_matcher.overall_score_threshold = len(user_kws_and_weights.keys())
    matched_jobs = job_matcher.get_job_matches()
    print(matched_jobs)

