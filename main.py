import streamlit as st
from typing import Literal
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from langchain.prompts.pipeline import PipelinePromptTemplate
from langchain.prompts import PromptTemplate, FewShotPromptTemplate


from homer_example_selector import HomerExampleSelector

from prompt_templates import MAIN_TEMPLATE, CONVERSATION_TEMPLATE, COMBINED_TEMPLATE, EXAMPLE_TEMPLATE

if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "expanded"

st.set_page_config(
    page_title="Mimicking a Character via Few-Shot Priming without Explicit Instructions",
    initial_sidebar_state=st.session_state.sidebar_state,
)
st.title("Homer Simpson")
st.caption("Mimicking a Character via Few-Shot Priming without Explicit Instructions")

openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")

if not openai_api_key:
    st.session_state.sidebar_state = "expanded"
    st.error("Please add your OpenAI API key to the sidebar.")
    st.stop()
else:
    st.session_state.sidebar_state = "collapsed"

view_info = st.expander("What's this all about?", expanded=True)

with view_info:
    """
    This demonstrates how a pre-trained conversational model can learn to mimic a target character's speech patterns through few-shot learning, without any explicit instructions to imitate that particular character. By priming the model with only a set of relevant example dialogs retrieved via semantic similarity search, the system implicitly adopts the persona's tone and verbal quirks in a completely data-driven fashion, with no manual tuning or training tailored to the character. Remarkably, just a handful of representative dialog snippets provides all the information needed for the AI to convincingly mimic the character, without explicit instructions, modeling or modification.
    """

msgs = StreamlitChatMessageHistory(key="langchain_messages")
memory = ConversationBufferMemory(
    chat_memory=msgs, ai_prefix="Homer", input_key="human_input"
)




example_prompt = PromptTemplate(
    input_variables=["prompt", "response"], template=EXAMPLE_TEMPLATE
)

example_selector = HomerExampleSelector()

examples_prompt = FewShotPromptTemplate(
    example_selector=example_selector,
    example_prompt=example_prompt,
    input_variables=["human_input"],
    suffix="{human_input}",
)

main_prompt = PromptTemplate.from_template(MAIN_TEMPLATE)
conversation_prompt = PromptTemplate.from_template(CONVERSATION_TEMPLATE)


combined_prompt = PromptTemplate.from_template(COMBINED_TEMPLATE)

pipeline_prompt = PipelinePromptTemplate(
    final_prompt=combined_prompt,
    pipeline_prompts=[
        ("main", main_prompt),
        ("examples", examples_prompt),
        ("conversation", conversation_prompt),
    ],
)
llm_chain = LLMChain(
    llm=ChatOpenAI(openai_api_key=openai_api_key, model="gpt-4"),
    prompt=pipeline_prompt,
    memory=memory,
    verbose=True,
)


for msg in msgs.messages:
    AVATAR: Literal['img/homer.png', 'img/anon.png'] = "img/homer.png" if msg.type == "ai" else "img/anon.png"
    st.chat_message(msg.type, avatar=AVATAR).write(msg.content)

if prompt := st.chat_input():
    st.chat_message("human", avatar="img/anon.png").write(prompt)
    response = llm_chain.run(prompt)
    st.chat_message("ai", avatar="img/homer.png").write(response)
