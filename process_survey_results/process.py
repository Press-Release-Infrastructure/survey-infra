import pandas as pd
import numpy as np
import configparser

config = configparser.ConfigParser()
config.read('process_controls.txt')

raw_survey_results = config['settings']['raw_survey_results']
clean_survey_results = config['settings']['clean_survey_results']
q_desc = config['settings']['q_desc']

raw_survey_results = pd.read_csv(raw_survey_results).iloc[2:].reset_index().drop(columns = ['index'])
q_desc = pd.read_csv(q_desc).drop(columns = ['Unnamed: 0'])

cols_needed = ['PROLIFIC_PID'] + list(q_desc['QID'])
filtered_results = raw_survey_results[cols_needed]

prolific_id = []
headline = []
article_id = []
response_class = []
company_1 = []
company_2 = []

headline_to_qid_mapper = {}

for j, q_info in q_desc.iterrows():
    curr_qid = q_info['QID']
    curr_headline = q_info['Headline']
    curr_qtype = q_info['QType']
    
    if curr_headline in headline_to_qid_mapper:
        headline_to_qid_mapper[curr_headline].append(curr_qid)
    else:
        headline_to_qid_mapper[curr_headline] = [curr_qid]

for i, response in filtered_results.iterrows():
    curr_prolific_id = response['PROLIFIC_PID']
    for h, qids in headline_to_qid_mapper.items():
        headline_responses = list(response[qids])
        if not pd.isna(headline_responses[0]):
            for i in range(0, len(headline_responses), 3):
                if not pd.isna(headline_responses[i]):
                    curr_response_class, curr_company_1, curr_company_2 = headline_responses[i: i+3]

                    prolific_id.append(curr_prolific_id)
                    headline.append(h)
                    article_id.append('stub_article_id')
                    response_class.append(curr_response_class)
                    company_1.append(curr_company_1)
                    company_2.append(curr_company_2)

survey_update_data = pd.DataFrame({
    'prolific_id': prolific_id,
    'headline': headline,
    'article_id': article_id,
    'response_class': response_class,
    'company_1': company_1,
    'company_2': company_2
})
survey_update_data.sort_values('headline', inplace = True)

survey_update_data.to_csv(clean_survey_results)
