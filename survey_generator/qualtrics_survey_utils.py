import numpy as np
import math
import json

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
