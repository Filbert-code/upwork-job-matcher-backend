import json
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
        self.overall_score_threshold = 0
        self.matched_jobs = []
        self.print_logs = print_logs

    def set_user_keywords_and_weights(self, user_keywords_and_weights):
        self.user_keywords_and_weights = user_keywords_and_weights
        self.overall_score_threshold = len(user_keywords_and_weights.keys()) - 3
        self.matched_jobs = []

    def get_job_matches(self):
        if self.user_keywords_and_weights is None:
            raise Exception('User keywords and weights have not been set')

        for job_key, job_data in self.job_data.items():
            job_keywords = self.get_job_keywords(job_data)
            matches = self.get_job_keyword_matches(job_keywords)
            overall_score = self.calculate_overall_score(matches)
            if overall_score >= self.overall_score_threshold:
                job_match_results = create_job_match_results_object(job_keywords, matches, overall_score, job_key, job_data)
                self.matched_jobs.append(job_match_results)

        if self.print_logs:
            self.print_processing_config()
            self.print_job_results()
            self.print_processing_summary()
        return self.matched_jobs

    def get_job_keywords(self, job_data):
        # create a map of keywords and phrases from the job title/description
        self.rake.extract_keywords_from_text(job_data['description'])
        job_keywords = self.rake.get_ranked_phrases()
        for kw in job_data['skill_badges']:
            job_keywords.append(kw.lower())
        return job_keywords

    def get_job_keyword_matches(self, job_keywords):
        matches = {}
        for job_kw in job_keywords:
            best_user_kw, score = process.extractOne(job_kw, self.user_keywords_and_weights.keys())
            if score >= self.keyword_confidence_threshold:
                if best_user_kw in matches:
                    matches[best_user_kw] = matches[best_user_kw] + 1
                else:
                    matches[best_user_kw] = 1
        return matches

    def calculate_overall_score(self, matches):
        overall_score = 0
        for user_kw, count in matches.items():
            weight = self.user_keywords_and_weights[user_kw]
            kw_score = count * weight
            overall_score += kw_score
        return overall_score

    def print_processing_config(self):
        print('=========================')
        print('PROCESSING CONFIGURATION:')
        print(f'Keyword Confidence Threshold: {self.keyword_confidence_threshold}')
        print(f'Overall Job Match Score Threshold: {self.overall_score_threshold}')
        print(f'User Keywords and Weights: {self.user_keywords_and_weights}')
        print('=========================')

    def print_job_results(self):
        for job in self.matched_jobs:
            print(f'Job Title: {job["job_data"]["title"]}')
            print(f'Keywords: {job["job_keywords"]}')
            print(f'Matches: {job["matches"]}')
            print(f'Overall Score over Base Score: {job["overall_score"]}/{self.overall_score_threshold}')
            print('-------------------------')

    def print_processing_summary(self):
        print(f'Number of jobs processed: {len(self.job_data)}')
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

