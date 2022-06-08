import numpy as np
import math
import json
import copy

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

# QUESTIONS UTILS
# objects

# args needed: flow id, right operand, right operand
branch_logic_template = {
	"Type": "Branch",
	"FlowID": "",
	"Description": "New Branch",
	"BranchLogic": {
		"0": {
			"0": {
				"LogicType": "EmbeddedField",
				"LeftOperand": "Score",
				"Operator": "LessThan",
				"RightOperand": "",
				"_HiddenExpression": False,
				"Type": "Expression",
				"Description": "<span class=\"ConjDesc\">If</span>  <span class=\"LeftOpDesc\">Score</span> <span class=\"OpDesc\">Is Less Than</span> <span class=\"RightOpDesc\"> "" </span>"
			},
			"Type": "If"
		},
		"Type": "BooleanExpression"
	}
}

end_survey_display = {
	"ID": "BL_{}",
	"Type": "Block",
	"FlowID": "FL_{}"
}

end_survey = {
	"Type": "EndSurvey",
	"FlowID": "FL_{}"
}

set_score_prev = {
	"Type": "EmbeddedData",
	"FlowID": "FL_-1",
	"EmbeddedData": [
		{
		"Description": "ScorePrev",
		"Type": "Custom",
		"Field": "ScorePrev",
		"VariableType": "String",
		"DataVisibility": [],
		"AnalyzeText": False,
		"Value": "${gr://SC_0/Score}"
		}
	]
}

set_score_next = {
	"Type": "EmbeddedData",
	"FlowID": "FL_-1",
	"EmbeddedData": [
		{
		"Description": "ScoreNext",
		"Type": "Custom",
		"Field": "ScoreNext",
		"VariableType": "String",
		"DataVisibility": [],
		"AnalyzeText": False,
		"Value": "${gr://SC_0/Score}"
		}
	]
}

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
