from collections import Counter
from functools import partial
import streamlit as st
import numpy as np
import json

DEBUG = False

if not st.session_state.get("memory_responses"):
    st.session_state["memory_responses"] = []

if "counter" not in st.session_state:
    st.session_state["counter"] = 0
    st.session_state["draw"] = 0
    st.session_state["none"] = 0
    st.session_state["a"] = 0
    st.session_state["b"] = 0

if "stop" not in st.session_state:
    st.session_state["stop"] = False


@st.cache_data
def get_output_json(input_ranking: dict):
    return json.dumps(
        input_ranking,
        indent=4,
        ensure_ascii=False,
    )


def read_jsonl(file):
    if isinstance(file, str):
        file = open(file, "r")
    else:
        file = file.getvalue().decode("utf-8").split("\n")

    for line in file:
        if not len(line):
            return
        el = json.loads(line)
        assert "prompt" in el, "Prompt not found"
        assert "responseA" in el, "Response A not found"
        assert "responseB" in el, "Response B not found"
        assert "idA" in el, "ID A not found"
        assert "idB" in el, "ID B not found"
        yield el
    if isinstance(file, str):
        file.close()


def record_ans(ans: str):
    st.session_state[ans.lower()] += 1
    print(f"[RECORD] Response: {st.session_state['counter']}")
    st.session_state.memory_responses.append(
        {
            **st.session_state["current_input"],
            "answer": ans,
        }
    )
    handle_any_ans()


def rank(responses: dict, iterations: int = 1000):
    # get all ids
    ids = set()
    wins = Counter()
    comps = {}
    for r in responses:
        ids.add(r["idA"])
        ids.add(r["idB"])
        if r["answer"] == "A":
            wins[r["idA"]] += 1
        if r["answer"] == "B":
            wins[r["idB"]] += 1
        if r["answer"] == "draw":
            wins[r["idA"]] += 0.5
            wins[r["idB"]] += 0.5
        # create a dictionary of comparisons
        comps[tuple(sorted((r["idA"], r["idB"])))] = 1

    total_options = len(ids)
    ids = sorted(list(ids))
    # initialize ranks to 1/N   where N is the number of options
    ranks = np.ones(total_options) / total_options
    for steps in range(iterations):
        prev_ranks = ranks.copy()  # copy old ranks
        for i in range(total_options):
            # for each option, calculate the sum of all the other options
            # and update the rank
            # key is (A, B) where A is the option being ranked and B is the other option
            # order invariant
            denom = 0
            for j in range(total_options):
                if i == j:
                    continue
                comparison_between_options = comps.get(
                    tuple(sorted((ids[i], ids[j]))), 0
                )
                if comparison_between_options == 0:
                    continue

                denom += comparison_between_options / (ranks[i] + ranks[j])
            ranks[i] = wins[ids[i]] / denom
        ranks /= sum(ranks)
        if np.sum(np.abs(ranks - prev_ranks)) < 1e-6:
            st.toast(f"Converged in {steps}", icon="🎉")
            break
    st.toast(f"BT rank completed in {steps}", icon="🎉")
    ranks = ranks.tolist()
    id_rank = {k: v * 100 for k, v in zip(ids, ranks)}
    return id_rank


def handle_any_ans():
    print(f"[HANDLE] Response: {st.session_state['counter']}")
    try:
        st.session_state["current_input"] = next(st.session_state["prompt_generator"])
        st.session_state["counter"] += 1
    except StopIteration:
        st.toast("No more prompts!", icon="🚨")
        st.write("No more prompts!")
        st.session_state["stop"] = True
        return False
    return True


def compute_bt_ranking(responses: list):
    if not len(responses):
        return {"ranking_plain": [], "ranking_bt": [], "responses": []}
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
    # simple Bradley Terry ranking
    bradely_terry_ranking = rank(responses=responses)

    return {
        "ranking_plain": ranking.most_common(),
        "ranking_bt": bradely_terry_ranking,
        "responses": responses,
    }


main_holder = st.container()


def write_response():
    main_holder.write(f"## Prompt  \n{st.session_state['current_input']['prompt']}")

    col1, col_mid, col2 = main_holder.columns((2, 1, 2))
    with col1:
        with col1.container(border=True):
            st.markdown("## A")
            st.write(f"{st.session_state['current_input']['responseA']}")

    with col2:
        with col2.container(border=True):
            st.markdown("## B")
            st.write(f"{st.session_state['current_input']['responseB']}")

    col11, col12, col13 = col1.columns(3)
    a_better = col12.button(
        "A is better",
        type="primary",
        key="ansA",
        use_container_width=True,
        on_click=partial(record_ans, "A"),
    )
    col11, col12, col13 = col2.columns(3)
    b_better = col12.button(
        "B is better",
        type="primary",
        key="ansB",
        use_container_width=True,
        on_click=partial(record_ans, "B"),
    )

    c1, c2, c3 = main_holder.columns((1, 1, 1))
    with c2:
        draw = st.button(
            "Draw",
            key="draw_btn",
            use_container_width=True,
            on_click=partial(record_ans, "draw"),
        )
        none = st.button(
            "None",
            key="none_btn",
            use_container_width=True,
            on_click=partial(record_ans, "none"),
        )


def initiate():
    try:

        fnobj = (
            st.session_state.file_uploader_debug
            if DEBUG
            else st.session_state.file_uploader
        )
        st.session_state["prompt_generator"] = read_jsonl(fnobj)
        handle_any_ans()
    except AssertionError as e:
        st.toast(f"Error: {e}", icon="🚨")


with st.sidebar:
    st.write("# Bradley Terry UI")
    st.write("## Instructions")
    st.write(
        "1. Upload a jsonl file with the following keys: `prompt`, `responseA`, `responseB`, `idA`, `idB`"
    )
    st.write("2. Click on the buttons to select the better response")
    st.write("3. Click on the download button to download the responses and ranking")

    st.write("#### Note")
    st.write("The first click on any of the buttons will start the ranking process")
    st.write("## Upload file")
    uploaded_file = st.file_uploader(
        "Choose a file", key="file_uploader", type="jsonl", on_change=initiate
    )
    if DEBUG and "file_uploader_debug" not in st.session_state:
        st.session_state.file_uploader_debug = "sample_responses.jsonl"
        initiate()

    with st.expander("Parameters"):
        st.write("## Parameters")
        st.write("### Bradley Terry")
        st.number_input("Max iterations", value=1000, min_value=1, key="max_iters")
        st.number_input("Error tolerance", value=1e-3, min_value=1e-6, key="error_tol")
    # counter
    with st.expander("Stats"):
        st.write(f"\tAnswered: {st.session_state['counter']}")
        st.write(f"\tDraw: {st.session_state['draw']}")
        st.write(f"\tNeither: {st.session_state['none']}")

    my_json = get_output_json(compute_bt_ranking(st.session_state.memory_responses))
    # download responses
    st.download_button(
        label="Download responses and ranking",
        data=my_json,
        file_name="responses.json",
        mime="application/json",
        type="primary",
    )


if st.session_state.get("prompt_generator") and not st.session_state.get("stop", False):
    write_response()

if st.session_state.stop:
    # clear the screen
    main_holder.empty()
    st.write(
        "# Congrats! No more prompts! 🎉\n" "Download responses from the sidebar menu"
    )
