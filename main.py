import streamlit as st
import json
import random

# --- Load Data ---
def load_data():
    with open('questions.json') as f:
        data = json.load(f)
    categories = list(data.keys())
    return data, categories

data, categories = load_data()

mode = st.sidebar.radio("Select mode", ["Learning", "Test-Exam", "Random"])
categories.insert(0, "All")
selected_category = st.selectbox('Select a category', categories)

def get_questions(data, selected_category):
    if selected_category == 'All':
        questions = [q for sublist in data.values() for q in sublist]
    else:
        questions = [q for q in data[selected_category]]
    random.shuffle(questions)
    return questions

# --- Session State Initialization ---
if 'init' not in st.session_state or st.session_state.category != selected_category or st.session_state.mode != mode:
    st.session_state.category = selected_category
    st.session_state.mode = mode
    st.session_state.questions = get_questions(data, selected_category)
    st.session_state.learning_queue = st.session_state.questions.copy()
    st.session_state.learning_index = 0
    st.session_state.learning_feedback = None
    st.session_state.learning_answer = None
    st.session_state.learning_checked = False
    st.session_state.learning_repeat_queue = []
    st.session_state.test_exam_mode_started = False
    st.session_state.test_exam_results = []
    st.session_state.test_exam_questions = []
    st.session_state.test_exam_index = 0
    st.session_state.test_exam_num_questions = 5
    st.session_state.test_exam_choice = None
    st.session_state.show_test_results = False
    st.session_state.random_index = 0
    st.session_state.random_feedback = None
    st.session_state.random_answer = None
    st.session_state.random_checked = False
    st.session_state.init = True

# --- LEARNING MODE ---
def learning_check():
    idx = st.session_state.learning_index
    queue = st.session_state.learning_queue
    if len(queue) == 0:
        return
    q = queue[idx]
    selected = st.session_state.learning_answer
    correct_answer_index = ["A", "B", "C", "D"].index(q['answer'])
    correct_answer = q['choices'][correct_answer_index]
    explanation = q['reason']
    if selected == correct_answer:
        st.session_state.learning_feedback = ("Correct!", True)
    else:
        st.session_state.learning_feedback = (f"Incorrect. {explanation}", False)
    st.session_state.learning_checked = True
    # only pop and requeue on continue, not here

def learning_continue():
    idx = st.session_state.learning_index
    queue = st.session_state.learning_queue
    if len(queue) == 0:
        return
    q = queue[idx]
    if st.session_state.learning_feedback and not st.session_state.learning_feedback[1]:
        st.session_state.learning_repeat_queue.append(q)
    queue.pop(idx)
    queue.extend(st.session_state.learning_repeat_queue)
    st.session_state.learning_repeat_queue.clear()
    st.session_state.learning_index = 0 if len(queue) else 0
    st.session_state.learning_feedback = None
    st.session_state.learning_answer = None
    st.session_state.learning_checked = False

if mode == "Learning":
    st.markdown(f"**Learning Mode** ({len(st.session_state.learning_queue)} remaining)")
    if len(st.session_state.learning_queue) == 0:
        st.success("Learning session complete!")
    else:
        q = st.session_state.learning_queue[st.session_state.learning_index]
        st.markdown(q['question'])
        st.session_state.learning_answer = st.radio(
            "Choices", q['choices'],
            index=0 if st.session_state.learning_answer is None else q['choices'].index(st.session_state.learning_answer),
            key=f"learn_radio_{st.session_state.learning_index}",
            disabled=st.session_state.learning_checked
        )

        if not st.session_state.learning_checked:
            st.button("Check Answer", key="learning_check_btn", on_click=learning_check)
        else:
            feedback, correct = st.session_state.learning_feedback
            if correct:
                st.success(feedback)
            else:
                st.error(feedback)
            st.markdown(f"**Your answer:** {st.session_state.learning_answer}")
            st.button("Continue", key="learning_continue_btn", on_click=learning_continue)

# --- TEST-EXAM MODE ---
def test_exam_start():
    st.session_state.test_exam_mode_started = True
    st.session_state.test_exam_index = 0
    st.session_state.test_exam_results = []
    st.session_state.show_test_results = False
    qlist = st.session_state.questions[:st.session_state.test_exam_num_questions]
    st.session_state.test_exam_questions = qlist
    st.session_state.test_exam_choice = None

def test_exam_continue():
    idx = st.session_state.test_exam_index
    questions = st.session_state.test_exam_questions
    q = questions[idx]
    selected = st.session_state.test_exam_choice
    correct_answer_index = ["A", "B", "C", "D"].index(q['answer'])
    correct_answer = q['choices'][correct_answer_index]
    is_correct = (selected == correct_answer)
    st.session_state.test_exam_results.append({
        'question': q,
        'selected': selected,
        'correct': is_correct
    })
    st.session_state.test_exam_index += 1
    st.session_state.test_exam_choice = None
    if st.session_state.test_exam_index >= len(questions):
        st.session_state.show_test_results = True

def test_exam_restart():
    st.session_state.test_exam_mode_started = False
    st.session_state.show_test_results = False

if mode == "Test-Exam":
    if not st.session_state.test_exam_mode_started:
        st.session_state.test_exam_num_questions = st.number_input(
            "Number of questions", min_value=1, max_value=len(st.session_state.questions),
            value=st.session_state.test_exam_num_questions, key="exam_num")
        st.button("Start Test", key="start_exam_btn", on_click=test_exam_start)
    elif st.session_state.show_test_results:
        results = st.session_state.test_exam_results
        correct_count = sum([res['correct'] for res in results])
        st.markdown("### Test Results")
        st.write(f"Score: {correct_count}/{len(results)}")
        for idx, res in enumerate(results):
            result_icon = '✅' if res['correct'] else '❌'
            q = res['question']
            correct_answer_index = ["A", "B", "C", "D"].index(q['answer'])
            correct_answer = q['choices'][correct_answer_index]
            explanation = q['reason']
            st.write(f"**Q{idx + 1}:** {q['question']}")
            st.write(f"{result_icon} Your answer: {res['selected']}")
            st.write(f"Correct answer: {correct_answer}")
            st.write(f"Reason: {explanation}")
            st.write("---")
        st.button("Restart Test", key="restart_exam_btn", on_click=test_exam_restart)
    else:
        idx = st.session_state.test_exam_index
        questions = st.session_state.test_exam_questions
        q = questions[idx]
        st.markdown(f"**Test-Exam** ({idx + 1}/{len(questions)})")
        st.markdown(q['question'])
        st.session_state.test_exam_choice = st.radio(
            "Choices", q['choices'],
            index=0 if st.session_state.test_exam_choice is None else q['choices'].index(st.session_state.test_exam_choice),
            key=f"exam_radio_{idx}",
        )
        st.button("Continue", key=f"exam_continue_{idx}", on_click=test_exam_continue)

# --- RANDOM MODE ---
def random_check():
    idx = st.session_state.random_index
    q = st.session_state.questions[idx]
    selected = st.session_state.random_answer
    correct_answer_index = ["A", "B", "C", "D"].index(q['answer'])
    correct_answer = q['choices'][correct_answer_index]
    explanation = q['reason']
    if selected == correct_answer:
        st.session_state.random_feedback = ("Correct!", True)
    else:
        st.session_state.random_feedback = (f"Incorrect. {explanation}", False)
    st.session_state.random_checked = True

def random_continue():
    st.session_state.random_index = (st.session_state.random_index + 1) % len(st.session_state.questions)
    st.session_state.random_feedback = None
    st.session_state.random_answer = None
    st.session_state.random_checked = False

if mode == "Random":
    idx = st.session_state.random_index
    q = st.session_state.questions[idx]
    st.markdown("**Random Mode**")
    st.markdown(q['question'])
    st.session_state.random_answer = st.radio(
        "Choices", q['choices'],
        index=0 if st.session_state.random_answer is None else q['choices'].index(st.session_state.random_answer),
        key=f"rand_radio_{idx}",
        disabled=st.session_state.random_checked
    )
    if not st.session_state.random_checked:
        st.button("Check Answer", key=f"rand_check_{idx}", on_click=random_check)
    else:
        feedback, correct = st.session_state.random_feedback
        if correct:
            st.success(feedback)
        else:
            st.error(feedback)
        st.markdown(f"**Your answer:** {st.session_state.random_answer}")
        st.button("Continue", key=f"rand_continue_{idx}", on_click=random_continue)