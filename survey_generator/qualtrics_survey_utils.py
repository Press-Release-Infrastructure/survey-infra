import numpy as np
import math
import json
import copy
from qualtrics_survey_objects import branch_logic_template, end_survey_display, end_survey, set_score_prev, set_score_next

def select_att_check_headlines(att_headlines_df, attention_check_length, titles_per_student, block_size):
    # pick groups of att length headlines from att_headlines_df without replacement
    all_att_idxes = set(np.arange(0, len(att_headlines_df)))
    
    attention_check_headlines = []
    attention_check_answers = {}
    
    for j in range(math.ceil(titles_per_student / block_size)):
        curr_idxes = np.random.choice(list(all_att_idxes), size = attention_check_length, replace = False)
        curr_att = att_headlines_df.iloc[curr_idxes]
        for c in curr_idxes:
            all_att_idxes = list(set(all_att_idxes) - set(curr_idxes))
        curr_att_headlines = []
        for _, c in curr_att.iterrows():
            curr_att_headlines.append(str(c["Title"]))
            attention_check_answers[str(c["Title"])] = [int(c["Acq_Status"]), str(c["Company 1"]), str(c["Company 2"])]
        attention_check_headlines.append(curr_att_headlines)
    return attention_check_headlines, attention_check_answers

def save_headline_assignments(assignments_name, student_assignments_json):
    with open(assignments_name, 'w') as f:
	    json.dump(student_assignments_json, f, ensure_ascii = False, indent = 2)

def assign_regular_headlines(titles, num_headlines, num_students, uniques_per_student, assignments_name):
    uniques_left = num_headlines - num_students * uniques_per_student
    uniques = [uniques_per_student for i in range(num_students)]
    idx = 0
    while uniques_left:
        uniques[idx] += 1
        idx = (idx + 1) % num_students
        uniques_left -= 1

    student_assignments = {}
    curr_idx = 0
    idx_set = range(num_headlines)
    for i in range(num_students):
        unique_selection = idx_set[curr_idx:(curr_idx + uniques[i])]
        student_assignments[i] = list(unique_selection)
        curr_idx += len(unique_selection)

    used_headlines = set()
    prev_student_headlines = student_assignments[num_students - 1]
    for i in range(num_students):
        curr_student_headlines = student_assignments[i]
        dup_headlines = prev_student_headlines[-int(max(len(curr_student_headlines), len(prev_student_headlines))):].copy()
        prev_student_headlines = student_assignments[i].copy()
        student_assignments[i] = list(set(np.concatenate([student_assignments[i], dup_headlines])))

    # check that each headline is assigned twice
    headline_dict = {}
    for k, v in student_assignments.items():
        for h in v:
            if h in headline_dict:
                headline_dict[h] += 1
            else:
                headline_dict[h] = 1

    for v in headline_dict.values():
        assert(v == 2)

    student_assignments_json = {}
    titles_to_classify = []
    for student, assignments in student_assignments.items():
        student_assignments_json[str(student)] = [titles[a] for a in assignments]
        titles_to_classify.extend(student_assignments_json[str(student)])

    save_headline_assignments(assignments_name, student_assignments_json)
    return student_assignments, titles_to_classify

# Survey setup
def setup_survey(survey_info, survey_id, survey_name, num_students):
    survey_info["SurveyEntry"] = {
        "SurveyID": "{}".format(survey_id),
        "SurveyName": survey_name,
        "SurveyDescription": None,
        "SurveyOwnerID": "UR_3WUHDMGK0A1YPvo",
        "SurveyBrandID": "",
        "DivisionID": "DV_bCz0vLDEYcivdHv",
        "SurveyLanguage": "EN",
        "SurveyActiveResponseSet": "RS_dgMRsbI5TIbBjLw",
        "SurveyStatus": "Inactive",
        "SurveyStartDate": "0000-00-00 00:00:00",
        "SurveyExpirationDate": "0000-00-00 00:00:00",
        "SurveyCreationDate": "2021-09-02 21:33:29",
        "CreatorID": "UR_3WUHDMGK0A1YPvo",
        "LastModified": "2021-09-02 21:35:33",
        "LastAccessed": "0000-00-00 00:00:00",
        "LastActivated": "0000-00-00 00:00:00",
        "Deleted": None,
    }

    survey_info["SurveyElements"] = [
        {
            "SurveyID": "{}".format(survey_id),
            "Element": "BL",
            "PrimaryAttribute": "Survey Blocks",
            "SecondaryAttribute": None,
            "TertiaryAttribute": None,
            "Payload": [],
        },
        {
        "SurveyID": "{}".format(survey_id),
        "Element": "FL",
        "PrimaryAttribute": "Survey Flow",
        "SecondaryAttribute": None,
        "TertiaryAttribute": None,
        "Payload": {
            "Type": "Root",
            "FlowID": "FL_-1000000",
            "Flow": [
                {
                    "Type": "EmbeddedData",
                    "FlowID": "FL_-2000000",
                    "EmbeddedData": [
                        {
                            "Description": "respondentID",
                            "Type": "Custom",
                            "Field": "respondentID",
                            "VariableType": "String",
                            "DataVisibility": [],
                            "AnalyzeText": False,
                            "Value": "${rand://int/0:" + str(num_students - 1) + "}"
                        }
                    ]
                },
            ],
            "Properties": {
            "Count": 3,
            },
        }
        },
        {
        "SurveyID": "{}".format(survey_id),
        "Element": "SO",
        "PrimaryAttribute": "Survey Options",
        "SecondaryAttribute": None,
        "TertiaryAttribute": None,
        "Payload": {
            "BackButton": "false",
            "SaveAndContinue": "true",
            "SurveyProtection": "PublicSurvey",
            "BallotBoxStuffingPrevention": "false",
            "NoIndex": "Yes",
            "SecureResponseFiles": "true",
            "SurveyExpiration": "None",
            "SurveyTermination": "DefaultMessage",
            "Header": "",
            "Footer": "",
            "ProgressBarDisplay": "None",
            "PartialData": "+1 week",
            "ValidationMessage": "",
            "PreviousButton": "",
            "NextButton": "",
            "SurveyTitle": "Qualtrics Survey | Qualtrics Experience Management",
            "SkinLibrary": "ucdavis",
            "SkinType": "templated",
            "Skin": {
            "brandingId": None,
            "templateId": "*base",
            "overrides": {
                "questionText": {
                "size": "16px"
                },
                "answerText": {
                "size": "14px"
                },
                "layout": {
                    "spacing": 0
                }
            }
            },
            "NewScoring": 1
        }
        },
        {
        "SurveyID": "{}".format(survey_id),
        "Element": "SCO",
        "PrimaryAttribute": "Scoring",
        "SecondaryAttribute": None,
        "TertiaryAttribute": None,
        "Payload": {
            "ScoringCategories": [
            {
                "ID": "SC_0",
                "Name": "Score",
                "Description": ""
            }
            ],
            "ScoringCategoryGroups": [],
            "ScoringSummaryCategory": None,
            "ScoringSummaryAfterQuestions": 0,
            "ScoringSummaryAfterSurvey": 0,
            "DefaultScoringCategory": "SC_0",
            "AutoScoringCategory": None
        }
        },
        {
        "SurveyID": "{}".format(survey_id),
        "Element": "PROJ",
        "PrimaryAttribute": "CORE",
        "SecondaryAttribute": None,
        "TertiaryAttribute": "1.1.0",
        "Payload": {
            "ProjectCategory": "CORE",
            "SchemaVersion": "1.1.0"
        }
        },
        {
        "SurveyID": "{}".format(survey_id),
        "Element": "STAT",
        "PrimaryAttribute": "Survey Statistics",
        "SecondaryAttribute": None,
        "TertiaryAttribute": None,
        "Payload": {
            "MobileCompatible": True,
            "ID": "Survey Statistics"
        }
        },
        {
        "SurveyID": "{}".format(survey_id),
        "Element": "QC",
        "PrimaryAttribute": "Survey Question Count",
        "SecondaryAttribute": "3",
        "TertiaryAttribute": None,
        "Payload": None
        },
        {
        "SurveyID": "{}".format(survey_id),
        "Element": "QO",
        "PrimaryAttribute": "QO_IJT5FQU4tu7CjjC",
        "SecondaryAttribute": "In-progress respondents",
        "TertiaryAttribute": None,
        "Payload": {
            "Name": "In-progress respondents",
            "Occurrences": num_students,
            "Logic": {
            "0": {
                "0": {
                "LogicType": "Question",
                "QuestionID": "QID1",
                "QuestionIsInLoop": "no",
                "ChoiceLocator": "q://QID1/DisplayableQuestion/1",
                "Operator": "Displayed",
                "QuestionIDFromLocator": "QID1",
                "LeftOperand": "q://QID1/QuestionDisplayed",
                "Type": "Expression",
                "Description": "<span class=\"ConjDesc\">If</span> <span class=\"QuestionDesc\">\nWe are working on a non-profit project for research purposes to identify company acquisitions and mergers from a large number of business headlines.\n\nAn acquisition is when one company buys anothe...</span> <span class=\"LeftOpDesc\"></span> <span class=\"OpDesc\">Is Displayed</span> "
                },
                "Type": "If"
            },
            "Type": "BooleanExpression"
            },
            "LogicType": "Simple",
            "QuotaAction": "EndCurrentSurvey",
            "OverQuotaAction": None,
            "ActionInfo": {
            "0": {
                "0": {
                "ActionType": "EndCurrentSurvey",
                "Type": "Expression",
                "LogicType": "QuotaAction"
                },
                "Type": "If"
            },
            "Type": "BooleanExpression"
            },
            "ID": "QO_IJT5FQU4tu7CjjC",
            "QuotaRealm": "Survey",
            "QuotaSchedule": None,
            "EndSurveyOptions": {
            "EndingType": "Default",
            "ResponseFlag": "QuotaMet",
            "SurveyTermination": "DefaultMessage"
            }
        }
        },
        {
        "SurveyID": "{}".format(survey_id),
        "Element": "QG",
        "PrimaryAttribute": "QG_M8GH3g6zuPBjQgw",
        "SecondaryAttribute": "Default Quota Group",
        "TertiaryAttribute": None,
        "Payload": {
            "ID": "QG_M8GH3g6zuPBjQgw",
            "Name": "Default Quota Group",
            "Selected": True,
            "MultipleMatch": "PlaceInAll",
            "Public": False,
            "Quotas": [
            "QO_IJT5FQU4tu7CjjC"
            ]
        }
        },
    ]

    survey_info["SurveyElements"][0]["Payload"].append(
        {
            "Type": "Trash",
            "Description": "Trash / Unused Questions",
            "ID": "BL_3JCZSrANuFazQ7I",
        }
    )
    survey_elements = survey_info["SurveyElements"]
    flow_elements = survey_elements[1]["Payload"]["Flow"]

    return survey_elements, flow_elements

# QUESTIONS UTILS
# functions
def create_branch_logic(branch_logic_template, fl_id, eos_block_id, thresh_mc, thresh_te, total_questions_done, survey_id, segment = False):
	branch_logic_template_copy = copy.deepcopy(branch_logic_template)
	branch_logic_template_copy["FlowID"] = "FL_{}".format(fl_id)
	curr_end_survey_display = create_end_of_survey_logic(fl_id, eos_block_id, segment)

	set_end_id_copy = copy.deepcopy(set_end_id)
	set_end_id_copy["EmbeddedData"][0]["Value"] = "$e{" + str(total_questions_done) + " * 100}${rand://int/100000:1000000}"
	end_survey_copy = copy.deepcopy(end_survey)
	set_end_id_copy["FlowID"] = "FL_{}".format(set_end_id_flow_id)
	end_survey_copy["FlowID"] = "FL_{}".format(end_survey_flow_id)
	branch_logic_template_copy["Flow"] = [set_end_id_copy, curr_end_survey_display, end_survey_copy]
	branch_logic_template_copy["BranchLogic"]["0"]["0"]["RightOperand"] = str(thresh_mc + thresh_te)
	branch_logic_template_copy["BranchLogic"]["0"]["0"]["Description"] = "<span class=\"ConjDesc\">If</span>  <span class=\"LeftOpDesc\">Score</span> <span class=\"OpDesc\">Is Less Than</span> <span class=\"RightOpDesc\"> {} </span>".format(thresh_mc + thresh_te)
	return branch_logic_template_copy

def create_end_of_survey_logic(fl_id, eos_block_id, end_survey_display_flow_id, eos_payload_blocks, survey_id, survey_elements, segment = 0):
	curr_end_survey_display = copy.deepcopy(end_survey_display)
	curr_end_survey_display["ID"] = curr_end_survey_display["ID"].format(eos_block_id)
	curr_end_survey_display["FlowID"] = curr_end_survey_display["FlowID"].format(end_survey_display_flow_id)
	qid = "QID{}".format(eos_block_id - 1)
	eos_payload = {
		"Type": "Standard",
		"SubType": "",
		"Description": "Block {}".format(eos_block_id),
		"ID": "BL_{}".format(eos_block_id),
		"BlockElements": [
			{
				"Type": "Question",
				"QuestionID": "QID{}".format(eos_block_id - 1),
			}
		],
		"Options": {
			"BlockLocking": "false",
			"RandomizeQuestions": "false",
			"BlockVisibility": "Collapsed",
		}
	}
	eos_payload_blocks.append(eos_payload)

	msg = "You have completed the survey."

	elem = {
		"SurveyID": "{}".format(survey_id),
		"Element": "SQ",
		"PrimaryAttribute": qid,
		"SecondaryAttribute": "End of survey",
		"TertiaryAttribute": None,
		"Payload": {
		"QuestionText": msg + "<br><br>Clicking the 'next' arrow on this page will redirect you back to Prolific and register your submission.",
		"QuestionID": qid,
		"QuestionType": "DB",
		"Selector": "TB",
		"QuestionDescription": "End of survey",
		"Validation": {
			"Settings": {
			"Type": "None"
			}
		},
		"Language": [],
		"DataExportTag": qid
		}
	}

	survey_elements.append(elem)
	return curr_end_survey_display

def add_cond_display_training(qid1, qid2, training_test_ans, correct = False):
	acq_status, c1, c2 = training_test_ans

	q_cond_display = {
		"Type": "BooleanExpression",
		"inPage": False
	}

	if correct:
		q_cond_display["0"] = {
			"0": {
              "LogicType": "EmbeddedField",
              "LeftOperand": "ScorePrev",
              "Operator": "LessThanOrEqual",
              "RightOperand": "$e{gr://SC_0/Score - 1}",
              "Type": "Expression",
              "Description": "<span class=\"ConjDesc\">If</span>  <span class=\"LeftOpDesc\">ScorePrev</span> <span class=\"OpDesc\">Is Less Than or Equal to</span> <span class=\"RightOpDesc\"> $e{${gr://SC_0/Score} - 1} </span>"
            },
            "Type": "If"
        }
	else:
		q_cond_display["0"] = {
			"0": {
              "LogicType": "EmbeddedField",
              "LeftOperand": "ScorePrev",
              "Operator": "GreaterThan",
              "RightOperand": "$e{gr://SC_0/Score - 1}",
              "Type": "Expression",
              "Description": "<span class=\"ConjDesc\">If</span>  <span class=\"LeftOpDesc\">ScorePrev</span> <span class=\"OpDesc\">Is Greater Than</span> <span class=\"RightOpDesc\"> $e{${gr://SC_0/Score} - 1} </span>"
            },
            "Type": "If"
        }
	return q_cond_display

def display_conditional_training(qid_q1, qid_q2, qid_curr, curr, t1, t2, curr_training_test_ans, tt, tt_ind, survey_elements, survey_id, survey_info):
	qid1 = "QID{}".format(qid_curr)
	qid2 = "QID{}".format(qid_curr + 1)
	print("QIDs", qid1, qid2)

	text1 = tt[tt_ind].format(t1)
	text2 = tt[tt_ind].format(t2)

	survey_elements.append({
        "SurveyID": "{}".format(survey_id),
        "Element": "SQ",
        "PrimaryAttribute": qid1,
        "SecondaryAttribute": text1,
        "TertiaryAttribute": None,
        "Payload": {
        "QuestionText": text1,
        "QuestionID": qid1,
        "QuestionType": "DB",
        "Selector": "TB",
        "QuestionDescription": text1,
        "Validation": {
        "Settings": {
            "Type": "None"
        }
        },
        "Language": [],
        "DataExportTag": qid1,
		"DisplayLogic": add_cond_display_training(qid_q1, qid_q2, curr_training_test_ans, correct = True)
        }
    })	

	survey_elements.append({
        "SurveyID": "{}".format(survey_id),
        "Element": "SQ",
        "PrimaryAttribute": qid2,
        "SecondaryAttribute": text2,
        "TertiaryAttribute": None,
        "Payload": {
        "QuestionText": text2,
        "QuestionID": qid2,
        "QuestionType": "DB",
        "Selector": "TB",
        "QuestionDescription": text2,
        "Validation": {
        "Settings": {
            "Type": "None"
        }
        },
        "Language": [],
        "DataExportTag": qid2,
		"DisplayLogic": add_cond_display_training(qid_q1, qid_q2, curr_training_test_ans, correct = False)
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

	block_elements.append({
        "Type": "Question",
        "QuestionID": qid2
        })

	block_elements.append({
        "Type": "Page Break",
        })

def set_end_id_embedded_data(set_end_id, total_questions_done, set_end_id_flow_id, flow_elements):
    set_end_id_copy = copy.deepcopy(set_end_id)
    set_end_id_copy["EmbeddedData"][0]["Value"] = "$e{" + str(total_questions_done) + " * 100}${rand://int/100000:1000000}"
    set_end_id_copy["FlowID"] = "FL_{}".format(set_end_id_flow_id)
    flow_elements.append(set_end_id_copy)
    set_end_id_flow_id -= 1
    return send_end_id_flow_id
