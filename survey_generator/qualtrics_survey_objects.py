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