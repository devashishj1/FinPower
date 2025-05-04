from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from langchain_chroma import Chroma
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .structure_outputs import *
from .prompts import *

class Agents():
    def __init__(self):
        # Initialize OpenAI GPT-4o for chat and embeddings
        llm = ChatOpenAI(model_name="gpt-4o", temperature=0.1)
        
        # QA assistant chat
        embeddings = OpenAIEmbeddings()
        vectorstore = Chroma(persist_directory="db", embedding_function=embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

        # Categorize email chain
        email_category_prompt = PromptTemplate(
            template=CATEGORIZE_EMAIL_PROMPT, 
            input_variables=["email"]
        )
        self.categorize_email = email_category_prompt | llm.with_structured_output(CategorizeEmailOutput)

        # Used to design queries for RAG retrieval
        generate_query_prompt = PromptTemplate(
            template=GENERATE_RAG_QUERIES_PROMPT, 
            input_variables=["email"]
        )
        self.design_rag_queries = generate_query_prompt | llm.with_structured_output(RAGQueriesOutput)
        
        # Generate answer to queries using RAG
        qa_prompt = ChatPromptTemplate.from_template(GENERATE_RAG_ANSWER_PROMPT)
        self.generate_rag_answer = (
            {"context": retriever, "question": RunnablePassthrough()}
            | qa_prompt
            | llm
            | StrOutputParser()
        )

        # Used to write a draft email based on category and related informations
        writer_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", EMAIL_WRITER_PROMPT),
                MessagesPlaceholder("history"),
                ("human", "{email_information}")
            ]
        )
        self.email_writer = writer_prompt | llm.with_structured_output(WriterOutput)

        # Verify the generated email
        proofreader_prompt = PromptTemplate(
            template=EMAIL_PROOFREADER_PROMPT, 
            input_variables=["initial_email", "generated_email"]
        )
        self.email_proofreader = proofreader_prompt | llm.with_structured_output(ProofReaderOutput)