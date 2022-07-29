import pandas as pd 
import json
import math
import sys
import numpy as np
import copy
import configparser
import os
from survey_flow_directions import pg1, pg1_alt, pg2, pg3, pg4, pg5, pg6, pg7, pg8, pg9, pg10, pg11, pg12, pg13, pg14
from survey_flow_directions import tt1, tt2, tt3, tt4, tt5, tt6, tt7
from survey_flow_directions import transition_text
from qualtrics_survey_utils import select_att_check_headlines, assign_regular_headlines
from qualtrics_survey_utils import set_score_prev
from qualtrics_survey_utils import setup_survey, create_branch_logic, create_end_of_survey_logic, display_conditional_training
seed = 0
np.random.seed(seed)
rate = 120 # expected rate of problem solving per hour

survey_id = "SV_eLnpGNWb3hM31cy"
highlight_mode = False

# survey settings
config = configparser.ConfigParser()
config.read("qualtrics_survey_controls.txt")

all_titles_df = pd.read_csv(config["settings"]["all_titles_filename"], encoding = 'utf8')
all_titles = list(all_titles_df["Headline"].unique())

num_headlines = int(config["settings"]["num_headlines"]) # unique titles to be classified
num_students = int(config["settings"]["num_students"]) # number of people taking this survey version
overlap = float(config["settings"]["overlap"]) # percent of headlines assigned to 1 respondent that will be duplicated
training_length = int(config["settings"]["training_length"]) # number of training titles
block_size = int(config["settings"]["block_size"]) # number of questions in a block (between attention-check)
attention_check_length = int(config["settings"]["attention_check_length"]) # number of questions in an attention-check block
follow_up_flag = bool(int(config["settings"]["follow_up_flag"]))

training_thresh_mc = float(config["settings"]["training_thresh_mc"])
attention_thresh_mc = float(config["settings"]["attention_thresh_mc"])

# set up question description file: qid | headline | classification (0) / acquirer (1) / acquired (2)
real_qid_lst = []
real_headline_lst = []
real_qtype_lst = []
real_article_id_lst = []

training_mc_weight = 1
attention_mc_weight = 1

survey_name = config["settings"]["survey_name"]

outputs_root = config["settings"]["outputs_root"]
try:
    os.mkdir(outputs_root)
except:
    print("Output directory already exists.")

assignments_name = "{}/{}".format(outputs_root, config["settings"]["assignments_name"])
qsf_name = "{}/{}".format(outputs_root, config["settings"]["qsf_name"])
q_desc_name = "{}/{}".format(outputs_root, config["settings"]["q_desc_name"])

eos_redirect_url = config["settings"]["eos_redirect_url"]

training_flow_headlines_df = pd.read_csv(config["settings"]["training_flow_headlines_filename"], encoding = 'utf8')
training_test_headlines_df = pd.read_csv(config["settings"]["training_test_headlines_filename"], encoding = 'utf8')

titles = np.array(all_titles)
tt = [tt1, tt2, tt3, tt4, tt5, tt6, tt7]

# determine indices for headlines assigned to each student
titles_per_student = math.ceil(num_headlines / ((1 - overlap) * num_students))
uniques_per_student = math.floor(num_headlines / num_students)

att_headlines_df = pd.read_csv(config["settings"]["att_headlines_filename"], encoding = 'utf8').sample(frac = 1, random_state = seed)
att_headlines_df = att_headlines_df.where(pd.notnull(att_headlines_df), "")

attention_check_headlines, attention_check_answers = select_att_check_headlines(att_headlines_df, attention_check_length, titles_per_student, block_size)
student_assignments, titles_to_classify = assign_regular_headlines(titles, num_headlines, num_students, uniques_per_student, assignments_name)

survey_info = {}

end_survey_display_flow_id = -600
end_survey_flow_id = -500
set_score_flow_id = -300
set_end_id_flow_id = -400
prolific_qid = -10000000

survey_elements, flow_elements = setup_survey(survey_info, survey_id, survey_name, num_students)

flow_elements.append({
    "Type": "EmbeddedData",
    "FlowID": "FL_{}".format(prolific_qid),
    "EmbeddedData": [
        {
        "Description": "PROLIFIC_PID",
        "Type": "Recipient",
        "Field": "PROLIFIC_PID",
        "VariableType": "String",
        "DataVisibility": [],
        "AnalyzeText": False
        }
    ]
})

# add directions
directions = [pg1, pg2, pg3, pg4, pg5, pg6, pg7, pg8, pg9, pg10, pg11, pg12, pg13, pg14]
if follow_up_flag:
    directions[0] = pg1_alt 

d_format_elements = [
    ['Title'],
    ['Title'],
    ['Title'],
    ['Title'],
    ['Title'],
    ['Title'],
    ['Title']
]

curr = 0
image_curr = -5000
est_time = round(titles_per_student / rate * 60)
image_ids = ["IM_bw4t0x7DnMJH2Pc", "IM_3frgEdYRwLTYn6C", "IM_0x0KZ7BjmBQT8BE", "IM_09hsfcRZj7I6tMy", "IM_ezkIwvJNG5ojcMe", "IM_72rV391GORh9u06", "IM_e4mKDNPwwIxpuwC"]
for d in directions:
    qid1 = "QID{}".format(curr)
    qid2 = "QID{}".format(image_curr)
    
    if curr == 0:
        d = d % est_time
    elif curr == 3:
        d = d % (titles_per_student, est_time)
    elif 4 <= curr <= 10:
        d_elems = list(training_flow_headlines_df.iloc[curr - 4][d_format_elements[curr - 4]])
        print(d)
        print(curr)
        d = d % tuple(d_elems)

    if 4 <= curr <= 10:
        d = "<b style = 'color: #6082B6;'>TRAINING: Please read the headlines and explanation carefully.</b><br><br><div style = 'font-family: Monaco;'>" + d + "</div>"
    survey_elements.append({
        "SurveyID": "{}".format(survey_id),
        "Element": "SQ",
        "PrimaryAttribute": qid1,
        "SecondaryAttribute": d,
        "TertiaryAttribute": None,
        "Payload": {
        "QuestionText": d,
        "QuestionID": qid1,
        "QuestionType": "DB",
        "Selector": "TB",
        "QuestionDescription": d,
        "Validation": {
        "Settings": {
            "Type": "None"
        }
        },
        "Language": [],
        "DataExportTag": qid1
        }
    })

    if 4 <= curr <= 10:
        survey_elements.append({
            "SurveyID": "{}".format(survey_id),
            "Element": "SQ",
            "PrimaryAttribute": qid2,
            "SecondaryAttribute": " ",
            "TertiaryAttribute": None,
            "Payload": {
            "QuestionText": "",
            "DefaultChoices": False,
            "DataExportTag": qid2,
            "QuestionType": "DB",
            "Selector": "GRB",
            "Configuration": {
                "QuestionDescriptionOption": None
            },
            "QuestionDescription": "",
            "ChoiceOrder": [],
            "Validation": {
                "Settings": {
                "Type": "None"
                }
            },
            "GradingData": [],
            "Language": [],
            "NextChoiceId": 4,
            "NextAnswerId": 1,
            "QuestionID": qid2,
            "SubSelector": "WTXB",
            "GraphicsDescription": str(curr - 4),
            "Graphics": image_ids[curr - 4]
            }
        })

    survey_info["SurveyElements"][0]["Payload"].append({
        "Type": "Standard",
        "SubType": "",
        "Description": "Block {}".format(curr),
        "ID": "BL_{}".format(curr),
        "BlockElements": [],
        "Options": {
            "BlockLocking": "false",
            "RandomizeQuestions": "false",
            "BlockVisibility": "Collapsed",
        }
    })

    block_elements = survey_info["SurveyElements"][0]["Payload"][curr + 1]["BlockElements"]

    survey_info["SurveyElements"][1]["Payload"]["Flow"].append(
        {
            "ID": "BL_{}".format(curr),
            "Type": "Block",
            "FlowID": "FL_{}".format(curr)
        }
    )

    block_elements.append({
        "Type": "Question",
        "QuestionID": qid1
        })

    if 4 <= curr <= 10:
        block_elements.append({
            "Type": "Question",
            "QuestionID": qid2
            })
        
    block_elements.append({
        "Type": "Page Break",
        })

    curr += 1
    image_curr -= 1

title_to_student = {}
attention_check_title_to_student = {}
training_title_to_student = {}

for student, title_idxs in student_assignments.items():
    for t in title_idxs:
        if t in title_to_student:
            title_to_student[t].append(student)
        else:
            title_to_student[t] = [student]

for a_chunk in attention_check_headlines:
    for a in a_chunk:
        attention_check_title_to_student[a] = list(range(num_students))

def add_cond_display(sids):
    q_cond_display = {
        "Type": "BooleanExpression",
        "inPage": False
    }

    q_cond_display["0"] = {"Type": "If"}
    conj = "If"
    for s in range(len(sids)):
        sid = sids[s]
        q_cond_display["0"][str(s)] = {
            "LogicType": "EmbeddedField",
            "LeftOperand": "respondentID",
            "Operator": "EqualTo",
            "RightOperand": str(sid),
            "Type": "Expression",
            "Description": "<span class=\"ConjDesc\">If</span>  <span class=\"LeftOpDesc\">respondentID</span> <span class=\"OpDesc\">Is Equal to</span> <span class=\"RightOpDesc\"> {} </span>".format(sid)
        }
        if s > 0:
            q_cond_display["0"][str(s)]["Conjuction"] = "Or"
        conj = "Or"
    return q_cond_display

eos_payload_blocks = []

def add_score(elem, weight = 1, q_type = "MC", train_ans = -1, merger = False):
    if train_ans != -1:
        if q_type == "MC":
            elem["Payload"]["GradingData"] = [
                {
                    "ChoiceID": "1",
                    "Grades": {
                        "SC_0": 0
                    },
                    "index": 0
                },
                {
                    "ChoiceID": "2",
                    "Grades": {
                        "SC_0": 0
                    },
                    "index": 1
                },
                {
                    "ChoiceID": "3",
                    "Grades": {
                        "SC_0": 0
                    },
                    "index": 2
                },
                {
                    "ChoiceID": "4",
                    "Grades": {
                        "SC_0": 0
                    },
                    "index": 3
                }
            ]
            elem["Payload"]["GradingData"][train_ans]["Grades"]["SC_0"] = weight
        elif q_type == "TE":
            if merger:
                elem["Payload"]["GradingData"] = [{
                    "TextEntry": t,
                    "Grades": {
                        "SC_0": "{}".format(weight)
                    }
                } for t in train_ans]
            else:
                elem["Payload"]["GradingData"] = [{
                    "TextEntry": train_ans,
                    "Grades": {
                        "SC_0": "{}".format(weight)
                    }
                }]

def create_question(curr_title, curr, disp_settings = [], train_ans_lst = [], training = False, default_num_subparts = 5, num_subparts = 5):
    article_id_matches = list(all_titles_df.loc[all_titles_df["Headline"] == curr_title]["Article ID"])
    if len(article_id_matches):
        curr_article_id = article_id_matches[0]
    else:
        curr_article_id = ""
    
    qid = "QID{}".format(curr)

    if len(train_ans_lst):
        train_ans, train_ans_acquirer, train_ans_acquired = train_ans_lst
        mc_weight = training_mc_weight
    else:
        train_ans, train_ans_acquirer, train_ans_acquired = -1, -1, -1
        mc_weight = attention_mc_weight

    survey_info["SurveyElements"][0]["Payload"].append({
        "Type": "Standard",
        "SubType": "",
        "Description": "Block {}".format(curr),
        "ID": "BL_{}".format(curr),
        "BlockElements": [],
        "Options": {
            "BlockLocking": "false",
            "RandomizeQuestions": "false",
            "BlockVisibility": "Collapsed",
        }
    })
    block_elements = survey_info["SurveyElements"][0]["Payload"][curr + 1]["BlockElements"]
    
    # append to flow payload
    survey_info["SurveyElements"][1]["Payload"]["Flow"].append(
        {
            "ID": "BL_{}".format(curr),
            "Type": "Block",
            "FlowID": "FL_{}".format(curr)
        }
    )

    curr_subs = []
    for subpart in range(num_subparts):
        curr_sub = (curr - 1) * default_num_subparts + subpart + 1
        qid = "QID{}".format(curr_sub)
        curr_subs.append(qid)

        if subpart == 1:
            real_qid_lst.append(qid)
            real_headline_lst.append(curr_title)
            real_article_id_lst.append(curr_article_id)

        if subpart == 0:
            displayed_headline = "Headline: <br><br>\n<b>{}</b>\n".format(curr_title)
            
            if training:
                displayed_headline = "<b>TRAINING TEST IN PROGRESS</b><br><br>Headline: <br><br>\n<b>{}</b>\n".format(curr_title)
            
            elem = {
              "SurveyID": "{}".format(survey_id),
              "Element": "SQ",
              "PrimaryAttribute": qid,
              "SecondaryAttribute": "Headline: {}".format(curr_title),
              "TertiaryAttribute": None,
              "Payload": {
                "QuestionText": displayed_headline,
                "QuestionID": qid,
                "QuestionType": "DB",
                "Selector": "TB",
                "QuestionDescription": curr_title,
                "Validation": {
                  "Settings": {
                    "Type": "None"
                  }
                },
                "Language": [],
                "DataExportTag": qid
              }
            }
        elif subpart == 1:
            elem = {
                "SurveyID": "{}".format(survey_id),
                "Element": "SQ",
                "PrimaryAttribute": qid,
                "SecondaryAttribute": "Do you think that this headline refers to an acquisition or merger?",
                "TertiaryAttribute": None,
                "Payload": {
                    "QuestionText": "Do you think that this headline refers to an acquisition or merger?\n\n",
                    "QuestionID": qid,
                    "DataExportTag": qid,
                    "QuestionType": "MC",
                    "Selector": "DL",
                    "Configuration": {
                        "QuestionDescriptionOption": "UseText"
                    },
                    "QuestionDescription": "Do you think that this headline refers to an acquisition or merger?",
                    "Choices": {
                        "1": {
                            "Display": "Merger/Acquisition (between companies)"
                        },
                        "2": {
                            "Display": "Acquiring property"
                        },
                        "3": {
                            "Display": "Not about an acquisition or merger"
                        },
                        "4": {
                            "Display": "Unclear/not sure"
                        }
                    },
                    "ChoiceOrder": [
                        "1",
                        "2",
                        "3",
                        "4"
                    ],
                    "Validation": {
                        "Settings": {
                            "ForceResponse": "ON",
                            "ForceResponseType": "ON",
                            "Type":"None"
                        }
                    },
                    "GradingData": [],
                    "Language": [],
                    "NextChoiceId": 5,
                    "NextAnswerId": 1,
                    "QuestionID": qid
                },
            }

            real_qtype_lst.append(0)
            add_score(elem, mc_weight, "MC", train_ans)
        else:
            continue

        block_elements.append({
            "Type": "Question",
            "QuestionID": qid,
        })

        elem["Payload"]["DisplayLogic"] = add_cond_display(disp_settings)
        survey_elements.append(elem)
    
    block_elements.append({
        "Type": "Page Break"
    })
    return curr_subs

curr_offset = curr
total_questions_done = 0
# start with all training headlines
for t in list(training_title_to_student.keys()):
    create_question(t, curr, list(range(num_students)), training_answers[curr - curr_offset], training = True)
    curr += 1
    total_questions_done += 1

training_test_headlines = list(training_test_headlines_df["Title"])
training_test_acq_status = list(training_test_headlines_df["Acq_Status"])
training_test_c1 = list(training_test_headlines_df["Company 1"])
training_test_c2 = list(training_test_headlines_df["Company 2"])
print(training_test_headlines, training_test_acq_status, training_test_c1, training_test_c2)

set_score_id = -200

qid_curr = curr
for i in range(len(training_test_headlines)):
    curr_title = training_test_headlines[i]
    curr_training_test_ans = [int(training_test_acq_status[i]), "" if pd.isna(training_test_c1[i]) else training_test_c1[i], "" if pd.isna(training_test_c2[i]) else training_test_c2[i]]
    print(curr_title, curr, list(range(num_students)), curr_training_test_ans)

    # set score1 embedded data
    set_score_copy = copy.deepcopy(set_score_prev)
    set_score_copy["FlowID"] = "FL_{}".format(set_score_id)
    set_score_copy["EmbeddedData"][0]["Value"] = "$e{gr://SC_0/Score}"
    flow_elements.append(set_score_copy)
    set_score_id -= 1
    
    _, qid1 = create_question(curr_title, curr, list(range(num_students)), curr_training_test_ans, training = True, num_subparts = 2)
    curr += 1

    # display logic based on whether score2 - score = 1
    text1 = "<div style = 'font-weight: bold; color: #006400; text-align: center;'>Correct!</div><br></br>"
    text2 = "<div style = 'font-weight: bold; color: #8B0000; text-align: center;'>Not correct.</div><br></br>"
    display_conditional_training(qid1, qid2, qid_curr, curr, text1, text2, curr_training_test_ans, tt, i, survey_elements, survey_id, survey_info)
    curr += 1
    qid_curr += 2
    total_questions_done += 1

# create page to indicate that the training test is over
transition_block_num = -100000000
transition_qid = -100000000
transition_element = {
      "SurveyID": survey_id,
      "Element": "SQ",
      "PrimaryAttribute": "QID{}".format(transition_qid),
      "SecondaryAttribute": transition_text,
      "TertiaryAttribute": None,
      "Payload": {
        "QuestionText": transition_text,
        "DefaultChoices": False,
        "DataExportTag": "Q{}".format(transition_qid),
        "QuestionType": "DB",
        "Selector": "TB",
        "Configuration": {
          "QuestionDescriptionOption": "UseText"
        },
        "QuestionDescription": transition_text,
        "ChoiceOrder": [],
        "Validation": {
          "Settings": {
            "Type": "None"
          }
        },
        "GradingData": [],
        "Language": [],
        "NextChoiceId": 4,
        "NextAnswerId": 1,
        "QuestionID": "QID{}".format(transition_qid)
      }
    }
survey_elements.append(transition_element)
survey_info["SurveyElements"][0]["Payload"].append({
        "Type": "Standard",
        "SubType": "",
        "Description": "Block {}".format(curr),
        "ID": "BL_{}".format(curr),
        "BlockElements": [],
        "Options": {
            "BlockLocking": "false",
            "RandomizeQuestions": "false",
            "BlockVisibility": "Collapsed",
        }
    })

block_elements = survey_info["SurveyElements"][0]["Payload"][curr + 1]["BlockElements"]

survey_info["SurveyElements"][1]["Payload"]["Flow"].append(
    {
        "ID": "BL_{}".format(curr),
        "Type": "Block",
        "FlowID": "FL_{}".format(curr)
    }
)

block_elements.append({
    "Type": "Question",
    "QuestionID": "QID{}".format(transition_qid)
    })
curr += 1

# add branch logic to kick respondent out of survey after training q's
eos_block_id = -1000
fl_id = -1

num_blocks = len(attention_check_headlines)

for i in range(num_blocks):
    # in every iteration
    # pick attention check number of attention check headlines
    curr_at_check = attention_check_headlines[i]

    # pick block size - attention check number of regular headlines
    regular_headline_idxes = {}
    regular_headline_to_student = {}
    curr_headlines = set(curr_at_check)
    for j in range(num_students):
        if len(student_assignments[j]) >= block_size - len(curr_at_check):
            regular_headline_idxes[j] = np.random.choice(student_assignments[j], size = block_size - len(curr_at_check), replace = False)
        elif len(student_assignments[j]) > 0:
            regular_headline_idxes[j] = student_assignments[j]
        else:
            continue
        
        # remove the chosen headline idxes from all student assignments
        student_assignments[j] = list(set(student_assignments[j]) - set(regular_headline_idxes[j]))
        regular_headlines = titles[np.array(regular_headline_idxes[j])]
        curr_headlines = curr_headlines.union(set(regular_headlines))
        for r in regular_headlines:
            if r in regular_headline_to_student:
                regular_headline_to_student[r].append(j)
            else:
                regular_headline_to_student[r] = [j]

        if j == 0:
            total_questions_done += block_size
    
    # shuffle attention check and regular headlines in a block
    np.random.shuffle(np.array(list(curr_headlines)))

    for c in curr_headlines:
        if c in regular_headline_to_student:
            # special display settings
            create_question(c, curr, regular_headline_to_student[c])
        else:
            create_question(c, curr, list(range(num_students)), attention_check_answers[c])
        curr += 1

# create the rest of the questions for the remaining regular headlines
remaining_headlines = []
for student, remaining in student_assignments.items():
    remaining_headlines.extend(remaining)
remaining_headlines = list(set(remaining_headlines))
    
for r in remaining_headlines:
    # special display settings
    create_question(titles[r], curr, title_to_student[r])
    total_questions_done += 1
    curr += 1

curr_end_survey_display = create_end_of_survey_logic(fl_id, eos_block_id, end_survey_display_flow_id, eos_payload_blocks, survey_id, survey_elements, segment = 2)
end_survey_display_flow_id -= 1
end_survey_flow_id -= 1
flow_elements.append(curr_end_survey_display)

flow_elements.append({
    "Type": "EndSurvey",
    "FlowID": "FL_{}".format(end_survey_flow_id),
    "EndingType": "Advanced",
    "Options": {
        "Advanced": "true",
        "SurveyTermination": "Redirect",
        "EOSRedirectURL": "{}".format(eos_redirect_url)
    }
})

for eos_block in eos_payload_blocks:
    survey_info["SurveyElements"][0]["Payload"].append(eos_block)

with open(qsf_name, 'w') as f:
    json.dump(survey_info, f, ensure_ascii = False, indent = 2)

# test that all headlines in the MTurk dump are displayed to at least one user
curr_idx = 0
mturk_survey_q_dump = survey_elements[9:]
headlines_displayed = {}
count = 0
while curr_idx < len(mturk_survey_q_dump):
    curr_headline = mturk_survey_q_dump[curr_idx]["Payload"]["QuestionDescription"]
    if not sum([i in curr_headline for i in ["End of survey", "Timing", "Do you think", "(leave blank if not indicated or unclear)"]]):
        if curr_headline in headlines_displayed:
            count += 1
            headlines_displayed[curr_headline] += 1
        else:
            headlines_displayed[curr_headline] = 1
    curr_idx += 1

displayed = set(headlines_displayed.keys())
att_flat = set(np.array(attention_check_headlines).flatten())
assert(len(displayed.intersection(att_flat)) == num_blocks * attention_check_length)
assert(len(displayed.intersection(set(titles_to_classify))) == num_headlines)

q_desc_info = pd.DataFrame({
    "QID": real_qid_lst,
    "Headline": real_headline_lst,
    "QType": real_qtype_lst,
    "Article ID": real_article_id_lst,
})
q_desc_info.to_csv(q_desc_name)
