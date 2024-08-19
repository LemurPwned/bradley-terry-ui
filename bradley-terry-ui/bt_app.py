import streamlit as st
import json


if not st.session_state.get("counter"):
    st.session_state["counter"] = 0
    st.session_state["draws"] = 0
    st.session_state["none"] = 0


def read_jsonl(file: str):
    with open(file, "r") as f:
        for line in f:
            yield json.loads(line)


def set_next_prompt(prompt_entry: dict):
    st.session_state["current_prompt"] = prompt_entry["prompt"]
    st.session_state["responseA"] = prompt_entry["responseA"]
    st.session_state["responseB"] = prompt_entry["responseB"]
    st.session_state["counter"] += 1


def handle_any_ans():
    current_prompt = next(st.session_state["prompt_generator"])
    set_next_prompt(current_prompt)
    print(current_prompt)


with st.sidebar:
    st.write("# Bradley Terry UI")
    st.write("## Upload file")
    uploaded_file = st.file_uploader("Choose a file")

    # counter
    st.write("## Statistics")
    st.write(f"\tAnswered: {st.session_state['counter']}")
    st.write(f"\tDraw: {st.session_state['draws']}")
    st.write(f"\tNeither: {st.session_state['none']}")

if not st.session_state.get("prompt_generator"):
    prompt_gen = read_jsonl("prompt_test.jsonl")
    st.session_state["prompt_generator"] = prompt_gen
    current_prompt = next(prompt_gen)
    set_next_prompt(current_prompt)

st.write(f"## Prompt  \n{st.session_state['current_prompt']}")

col1, col_mid, col2 = st.columns((2, 1, 2))
with col1:
    with col1.container(border=True):
        st.write("## A")
        st.write(f"{st.session_state['responseA']}")

with col2:
    with col2.container(border=True):
        st.write("## B")
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
    handle_any_ans()

if b_better:
    handle_any_ans()

if draw:
    handle_any_ans()
    st.session_state["draws"] += 1

if none:
    handle_any_ans()
    st.session_state["none"] += 1
