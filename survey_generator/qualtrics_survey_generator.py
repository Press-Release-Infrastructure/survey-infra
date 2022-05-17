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
training_thresh_te = float(config["settings"]["training_thresh_te"])
attention_thresh_mc = float(config["settings"]["attention_thresh_mc"])
attention_thresh_te = float(config["settings"]["attention_thresh_te"])

# set up question description file: qid | headline | classification (0) / acquirer (1) / acquired (2)
real_qid_lst = []
real_headline_lst = []
real_qtype_lst = []
real_article_id_lst = []

training_mc_weight = 0.5
training_te_weight = 0.25
# training_mc_weight = training_thresh_mc / (training_thresh_mc + 2 * training_thresh_te)
# training_te_weight = training_thresh_te / (training_thresh_mc + 2 * training_thresh_te)
attention_mc_weight = attention_thresh_mc / (attention_thresh_mc + 2 * attention_thresh_te)
attention_te_weight = attention_thresh_te / (training_thresh_mc + 2 * training_thresh_te)

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
attention_check_headlines = []

# pick groups of att length headlines from att_headlines_df without replacement
all_att_idxes = set(np.arange(0, len(att_headlines_df)))
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

with open(assignments_name, 'w') as f:
	json.dump(student_assignments_json, f, ensure_ascii = False, indent = 2)

survey_info = {}

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

end_survey_display_flow_id = -600
end_survey_display = {
	"ID": "BL_{}",
	"Type": "Block",
	"FlowID": "FL_{}"
}

end_survey_flow_id = -500
end_survey = {
	"Type": "EndSurvey",
	"FlowID": "FL_{}"
}

set_score_flow_id = -300
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

set_end_id_flow_id = -400
set_end_id = {
	"Type": "EmbeddedData",
	"FlowID": "FL_{}",
	"EmbeddedData": [
		{
			"Description": "endID",
			"Type": "Custom",
			"Field": "endID",
			"VariableType": "String",
			"DataVisibility": [],
			"AnalyzeText": False,
			"Value": "$e{round(${gr://SC_0/Score}) * 100}${rand://int/100000:1000000}"
		}
	]
}

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

prolific_qid = -10000000
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
	['Title', 'Company 1', 'Company 2'],
	['Title', 'Company 2', 'Company 1', 'Company 1', 'Company 2'],
	['Title'],
	['Title'],
	['Title', 'Company 1', 'Company 1'],
	['Title', 'Company 2', 'Company 2'],
	['Title']
]

curr = 0
image_curr = -5000
est_time = round(titles_per_student / rate * 60)
image_ids = ["IM_9B5dS6U26s0YYRM", "IM_0OMSPpaZ6IPdKtg", "IM_bwqhodFXsvLLnj8", "IM_0AL9PxBO1HSum5U", "IM_0jpOZB2TB4XXIhM", "IM_bQuvbckdHqNZxie", "IM_51OYNiheRmKoVYa"]
for d in directions:
	qid1 = "QID{}".format(curr)
	qid2 = "QID{}".format(image_curr)
	
	if curr == 0:
		d = d % est_time
	elif curr == 3:
		d = d % (titles_per_student, est_time)
	elif 4 <= curr <= 10:
		d_elems = list(training_flow_headlines_df.iloc[curr - 4][d_format_elements[curr - 4]])
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

num_subparts = 5

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

def create_highlight_question(qid, mode = "acquirer"):
	q_text = "Click and drag / press to highlight the {} company name in the headline.".format(mode.upper())
	q = {
      "SurveyID": qid,
      "Element": "SQ",
      "PrimaryAttribute": qid,
      "SecondaryAttribute": "Click and drag / press to highlight the ACQUIRED company name in the headline.",
      "TertiaryAttribute": None,
      "Payload": {
        "QuestionText": "Click and drag / press to highlight the <strong>ACQUIRED</strong> company name in the headline.",
        "DefaultChoices": False,
        "DataExportTag": qid,
        "QuestionID": qid,
        "QuestionType": "HL",
        "Selector": "Text",
        "DataVisibility": {
          "Private": False,
          "Hidden": False
        },
        "Configuration": {
          "QuestionDescriptionOption": "UseText",
          "CustomTextSize": False,
          "AutoStopWords": False
        },
        "QuestionDescription": "Click and drag / press to highlight the ACQUIRED company name in the headline.",
        "Choices": {
          "298": {
            "WordIndex": 0,
            "WordLength": 7,
            "Word": "Synergy",
            "Display": "1: Synergy"
          },
          "299": {
            "WordIndex": 8,
            "WordLength": 4,
            "Word": "Plus",
            "Display": "2: Plus"
          },
          "300": {
            "WordIndex": 13,
            "WordLength": 9,
            "Word": "Acquiring",
            "Display": "3: Acquiring"
          },
          "301": {
            "WordIndex": 23,
            "WordLength": 7,
            "Word": "AirData",
            "Display": "4: AirData"
          }
        },
        "DisplayLogic": {
          "0": {
            "0": {
              "Description": "<span class=\"ConjDesc\">If</span>  <span class=\"LeftOpDesc\">respondentID</span> <span class=\"OpDesc\">Is Equal to</span> <span class=\"RightOpDesc\"> 2 </span>",
              "LeftOperand": "respondentID",
              "LogicType": "EmbeddedField",
              "Operator": "EqualTo",
              "RightOperand": "2",
              "Type": "Expression"
            },
            "1": {
              "Conjuction": "Or",
              "Description": "<span class=\"ConjDesc\">If</span>  <span class=\"LeftOpDesc\">respondentID</span> <span class=\"OpDesc\">Is Equal to</span> <span class=\"RightOpDesc\"> 3 </span>",
              "LeftOperand": "respondentID",
              "LogicType": "EmbeddedField",
              "Operator": "EqualTo",
              "RightOperand": "3",
              "Type": "Expression"
            },
            "Type": "If"
          },
          "Type": "BooleanExpression",
          "inPage": False
        },
        "ChoiceOrder": [
          298,
          299,
          300,
          301
        ],
        "Validation": {
          "Settings": {
            "ForceResponse": "OFF",
            "Type": "None"
          }
        },
        "GradingData": [],
        "Language": [],
        "NextChoiceId": 302,
        "NextAnswerId": 4,
        "Answers": {
          "1": {
            "Display": "ACQUIRED",
            "BGColor": "#1a9641",
            "TextColor": "#ffffff"
          }
        },
        "ExcludedWords": [],
        "WordChoiceIds": [
          298,
          299,
          300,
          301
        ],
        "HighlightText": "Synergy Plus Acquiring AirData",
        "ColorScale": "RdYlGn"
      }
    }
	return q

def add_cond_display(student_qid, sids):
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

eos_payload_blocks = []

def create_end_of_survey_logic(fl_id, eos_block_id, segment = 0):
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

def create_branch_logic(branch_logic_template, fl_id, eos_block_id, thresh_mc, thresh_te, total_questions_done, segment = False):
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

def create_question(curr_title, curr, disp_settings = [], train_ans_lst = [], training = False):
	article_id_matches = list(all_titles_df.loc[all_titles_df["Headline"] == curr_title]["Article ID"])
	if len(article_id_matches):
		curr_article_id = article_id_matches[0]
	else:
		curr_article_id = ""
	
	qid = "QID{}".format(curr)

	if len(train_ans_lst):
		train_ans, train_ans_acquirer, train_ans_acquired = train_ans_lst
		mc_weight, te_weight = training_mc_weight, training_te_weight
	else:
		train_ans, train_ans_acquirer, train_ans_acquired = -1, -1, -1
		mc_weight, te_weight = attention_mc_weight, attention_te_weight

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
		curr_sub = (curr - 1) * num_subparts + subpart + 1
		qid = "QID{}".format(curr_sub)
		curr_subs.append(qid)

		if subpart in [1, 2, 3]:
			real_qid_lst.append(qid)
			real_headline_lst.append(curr_title)
			real_article_id_lst.append(curr_article_id)

		block_elements.append({
			"Type": "Question",
			"QuestionID": qid,
		})

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
							"Display": "Acquisition"
						},
						"2": {
							"Display": "Merger"
						},
						"3": {
							"Display": "Neither / Not sure / Unclear"
						},
					},
					"ChoiceOrder": [
						"1",
						"2",
						"3",
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
					"NextChoiceId": 4,
        			"NextAnswerId": 1,
					"QuestionID": qid
				},
			}

			real_qtype_lst.append(0)

			add_score(elem, mc_weight, "MC", train_ans)
		elif subpart == 2:
			if highlight_mode:
				elem = create_highlight_question(qid, mode = "acquirer")
			else:
				elem = {
					"SurveyID": "{}".format(survey_id),
					"Element": "SQ",
					"PrimaryAttribute": qid,
					"SecondaryAttribute": "ACQUIRER (Leave blank if not indicated or unclear. You are encouraged to copy-paste from the headline text.):",
					"TertiaryAttribute": None,
					"Payload": {
						"QuestionText": "ACQUIRER (Leave blank if not indicated or unclear. You are encouraged to copy-paste from the headline text.):\n\n",
						"DefaultChoices": False,
						"QuestionID": qid,
						"QuestionType": "TE",
						"Selector": "SL",
						"Configuration": {
							"QuestionDescriptionOption": "UseText"
						},
						"QuestionDescription": "ACQUIRER (Leave blank if not indicated or unclear. You are encouraged to copy-paste from the headline text.):",
						"Validation": {
							"Settings": {
								"ForceResponse": "OFF",
								"Type": "None"
							}
						},
						"GradingData": [],
						"Language": [],
						"NextChoiceId": 4,
						"NextAnswerId": 1,
						"SearchSource": {
							"AllowFreeResponse": "false"
						},
						"DataExportTag": qid,
					}
				}

			real_qtype_lst.append(1)

			merger = train_ans == 1
			if merger: train_ans_arg = [train_ans_acquirer, train_ans_acquired]
			else: train_ans_arg = train_ans_acquirer
			add_score(elem, te_weight, "TE", train_ans_arg, merger = merger)
		elif subpart == 3:
			if highlight_mode:
				elem = create_highlight_question(qid, mode = "acquired")
			else: 
				elem = {
					"SurveyID": "{}".format(survey_id),
					"Element": "SQ",
					"PrimaryAttribute": qid,
					"SecondaryAttribute": "ACQUIRED (Leave blank if not indicated or unclear. You are encouraged to copy-paste from the headline text.):",
					"TertiaryAttribute": None,
					"Payload": {
						"QuestionText": "ACQUIRED (Leave blank if not indicated or unclear. You are encouraged to copy-paste from the headline text.):\n\n",
						"DefaultChoices": False,
						"QuestionID": qid,
						"QuestionType": "TE",
						"Selector": "SL",
						"Configuration": {
							"QuestionDescriptionOption": "UseText"
						},
						"QuestionDescription": "ACQUIRED (Leave blank if not indicated or unclear. You are encouraged to copy-paste from the headline text.):",
						"Validation": {
							"Settings": {
								"ForceResponse": "OFF",
								"Type": "None"
							}
						},
						"GradingData": [],
						"Language": [],
						"NextChoiceId": 4,
						"NextAnswerId": 1,
						"SearchSource": {
							"AllowFreeResponse": "false"
						},
						"DataExportTag": qid,
					}
				}

			real_qtype_lst.append(2)

			merger = train_ans == 1
			if merger: train_ans_arg = [train_ans_acquired, train_ans_acquirer]
			else: train_ans_arg = train_ans_acquired
			add_score(elem, te_weight, "TE", train_ans_arg, merger = merger)
		elif subpart == 4:
			elem = {
		      "SurveyID": "{}".format(survey_id),
		      "Element": "SQ",
		      "PrimaryAttribute": qid,
		      "SecondaryAttribute": "Timing",
		      "TertiaryAttribute": None,
		      "Payload": {
		        "QuestionText": "Timing",
		        "DefaultChoices": False,
		        "DataExportTag": qid,
		        "QuestionType": "Timing",
		        "Selector": "PageTimer",
		        "Configuration": {
		          "QuestionDescriptionOption": "UseText",
		          "MinSeconds": "0",
		          "MaxSeconds": "0"
		        },
		        "QuestionDescription": "Timing",
		        "Choices": {
		          "1": {
		            "Display": "First Click"
		          },
		          "2": {
		            "Display": "Last Click"
		          },
		          "3": {
		            "Display": "Page Submit"
		          },
		          "4": {
		            "Display": "Click Count"
		          }
		        },
		        "GradingData": [],
		        "Language": [],
		        "NextChoiceId": 4,
		        "NextAnswerId": 1,
		        "QuestionID": qid
		      }
		    }

		elem["Payload"]["DisplayLogic"] = add_cond_display("QID{}".format(0), disp_settings)
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

def display_conditional_training(qid_q1, qid_q2, qid_curr, curr, t1, t2, curr_training_test_ans, tt_ind):
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
	
	_, qid1, qid2, qid3, _ = create_question(curr_title, curr, list(range(num_students)), curr_training_test_ans, training = True)
	print(qid1, qid2, qid3)
	curr += 1

	# # set score2 embedded data
	# set_score_copy = copy.deepcopy(set_score_next)
	# set_score_copy["FlowID"] = "FL_{}".format(set_score_id)
	# set_score_copy["EmbeddedData"][0]["Value"] = "${gr://SC_0/Score}"
	# flow_elements.append(set_score_copy)
	# set_score_id -= 1

	# display logic based on whether score2 - score = 1
	text1 = "Correct!"
	text2 = "Not correct."
	display_conditional_training(qid1, qid2, qid_curr, curr, text1, text2, curr_training_test_ans, i)
	curr += 1
	qid_curr += 2
	total_questions_done += 1

# # set score embedded data
# set_score_copy = copy.deepcopy(set_score)
# set_score_copy["FlowID"] = "FL_{}".format(set_score_id)
# flow_elements.append(set_score_copy)
# set_score_id -= 1

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

	# # set score embedded data
	# set_score_copy = copy.deepcopy(set_score)
	# set_score_copy["FlowID"] = "FL_{}".format(set_score_id)
	# flow_elements.append(set_score_copy)
	# set_score_id -= 1

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

set_end_id_copy = copy.deepcopy(set_end_id)
set_end_id_copy["EmbeddedData"][0]["Value"] = "$e{" + str(total_questions_done) + " * 100}${rand://int/100000:1000000}"
set_end_id_copy["FlowID"] = "FL_{}".format(set_end_id_flow_id)
flow_elements.append(set_end_id_copy)
set_end_id_flow_id -= 1

curr_end_survey_display = create_end_of_survey_logic(fl_id, eos_block_id, segment = 2)
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
