from collections import Counter
import streamlit as st
import numpy as np
import json


if not st.session_state.get("memory_responses"):
    st.session_state["memory_responses"] = []

if not st.session_state.get("counter"):
    st.session_state["counter"] = 0
    st.session_state["draws"] = 0
    st.session_state["none"] = 0


def read_jsonl(file: str):
    with open(file, "r") as f:
        for line in f:
            if not len(line):
                return
            yield json.loads(line)


def set_next_prompt(prompt_entry: dict):
    st.session_state["current_prompt"] = prompt_entry["prompt"]
    st.session_state["responseA"] = prompt_entry["responseA"]
    st.session_state["responseB"] = prompt_entry["responseB"]
    st.session_state["counter"] += 1


def record_ans(ans: str):
    st.session_state.memory_responses.append(
        {
            "prompt": st.session_state["current_prompt"],
            "responseA": st.session_state["responseA"],
            "responseB": st.session_state["responseB"],
            "answer": ans,
        }
    )


def handle_any_ans():
    try:
        current_prompt = next(st.session_state["prompt_generator"])
        set_next_prompt(current_prompt)
        return True
    except StopIteration:
        st.toast("No more prompts!", icon="🚨")
        st.write("No more prompts!")
        return False


def compute_bt_ranking(responses: list):
    if not len(responses):
        return {"ranking_plain": [], "ranking_bt": []}
    # simple Bradley Terry ranking
    ranking = Counter()
    for resp in responses:
        if resp["answer"] == "A":
            ranking[resp["responseA"]] += 1
        if resp["answer"] == "B":
            ranking[resp["responseB"]] += 1
        if resp["answer"] == "draw":
            ranking[resp["responseA"]] += 0.5
            ranking[resp["responseB"]] += 0.5

    for k, v in ranking.items():
        ranking[k] = v / len(responses)
    response_matrix = np.zeros((len(ranking), len(ranking)))
    rlen = len(ranking)
    ranking_items = list(ranking.items())
    for i in range(rlen):
        ritem_i = ranking_items[i]
        for j in range(i + 1, rlen):
            ritem_j = ranking_items[j]
            response_matrix[i, j] = ritem_i[1] / (ritem_i[1] + ritem_j[1])
            response_matrix[j, i] = ritem_j[1] / (ritem_i[1] + ritem_j[1])

    ranking_from_matrix = np.argsort(response_matrix, axis=1)
    rr = [ranking_items[i][0] for i in ranking_from_matrix[:, -1]]
    return {"ranking_plain": ranking.most_common(), "ranking_bt": rr}


with st.sidebar:
    st.write("# Bradley Terry UI")
    st.write("## Upload file")
    uploaded_file = st.file_uploader("Choose a file")

    # counter
    st.write("## Statistics")
    st.write(f"\tAnswered: {st.session_state['counter']}")
    st.write(f"\tDraw: {st.session_state['draws']}")
    st.write(f"\tNeither: {st.session_state['none']}")

    # download responses
    st.download_button(
        label="Download responses and ranking",
        data=json.dumps(
            {
                "responses": st.session_state["memory_responses"],
                **compute_bt_ranking(st.session_state["memory_responses"]),
            },
            indent=4,
        ),
        file_name="responses.json",
        mime="application/json",
    )

if not st.session_state.get("prompt_generator"):
    prompt_gen = read_jsonl("prompt_test.jsonl")
    st.session_state["prompt_generator"] = prompt_gen
    current_prompt = next(prompt_gen)
    set_next_prompt(current_prompt)

st.write(f"## Prompt  \n{st.session_state['current_prompt']}")

col1, col_mid, col2 = st.columns((2, 1, 2))
with col1:
    with col1.container(border=True):
        st.markdown("## A")
        st.write(f"{st.session_state['responseA']}")

with col2:
    with col2.container(border=True):
        st.markdown("## B")
        st.write(f"{st.session_state['responseB']}")

col11, col12, col13 = col1.columns(3)
a_better = col12.button(
    "A is better", type="primary", key="ansA", use_container_width=True
)
col11, col12, col13 = col2.columns(3)
b_better = col12.button(
    "B is better", type="primary", key="ansB", use_container_width=True
)

c1, c2, c3 = st.columns((1, 1, 1))
with c2:
    draw = st.button("Draw", key="draw_btn", use_container_width=True)
    none = st.button("None", key="none_btn", use_container_width=True)


if a_better:
    record = handle_any_ans()
    if record_ans:
        record_ans("A")

if b_better:
    record = handle_any_ans()
    if record:
        record_ans("B")

if draw:
    record = handle_any_ans()
    if record:
        st.session_state["draws"] += 1
        record_ans("draw")

if none:
    record = handle_any_ans()
    if record:
        st.session_state["none"] += 1
        record_ans("none")
