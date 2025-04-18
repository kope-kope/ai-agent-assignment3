

import os
from dotenv import load_dotenv

# LangChain components
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import AgentExecutor, create_react_agent, create_tool_calling_agent # We'll use create_react_agent or create_tool_calling_agent later
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent
from langchain.agents import AgentExecutor
from langchain.tools import Tool
from langchain.tools import StructuredTool
from fpdf import FPDF
import textwrap
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List
from pydantic import BaseModel, Field

import os # Already imported, but ensure it's there

# ... (your existing functions like generate_pdf_document) ...

# Function to send an email with attachments


# Example of how the function might be called (for testing the tool)
# send_email_with_attachments(
#     recipient_email="test_recipient@example.com", # Replace
#     subject="Agent Test Email",
#     body="Here are the attached documents from the agent.",
#     attachment_paths=["market_trends.pdf", "user_stories.pdf", "roadmap.pdf"] # Example paths
# ) # Useful for wrapping long text lines in the PDF

# 1. Load environment variables from .env file
load_dotenv()

class PdfToolInput(BaseModel):
    content: str = Field(description="The text content to include in the PDF.")
    filename: str = Field(description="The desired name of the PDF file (e.g., 'report.pdf').")
    title: str = Field(description="The title for the PDF header.")
# Function to generate a PDF document from text
# Define the expected input schema for the Email Sender tool
class EmailToolInput(BaseModel):
    """Input schema for the Email Sender tool."""
    recipient_email: str = Field(description="The email address of the recipient.")
    subject: str = Field(description="The subject line of the email.")
    body: str = Field(description="The body text of the email (plain text).")
    attachment_paths: List[str] = Field(description="A list of file paths (strings) to attach.") # Using List[str] from typing


def generate_pdf_document(content: str, filename: str, title: str = "Document"):
    """
    Generates a PDF document from the given text content.

    Args:
        content: The text content to include in the PDF.
        filename: The name of the PDF file to save (e.g., "market_trends.pdf").
        title: An optional title for the document header.
    """
    pdf = FPDF()
    pdf.add_page()

    # Set up fonts
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, title, 0, 1, "C") # Add title centered

    pdf.set_font("Arial", "", 12)

    # Add content, handling line breaks
    # We'll split by lines and wrap longer lines
    lines = content.split('\n')
    for line in lines:
        # Use textwrap to handle lines that are too wide
        wrapped_lines = textwrap.wrap(line, width=90) # Adjust width as needed

        if not wrapped_lines: # Handle empty lines
             pdf.ln(5) # Add some vertical space for empty lines
        else:
            for wrapped_line in wrapped_lines:
                pdf.cell(0, 10, wrapped_line, 0, 1) # Add line

    # Ensure the output directory exists if you want to save elsewhere
    # For now, it saves in the current directory.
    pdf.output(filename)
    print(f"Generated PDF: {filename}")

    # Return the filename so the agent knows the file was created
    return f"Successfully generated {filename}"

def send_email_with_attachments(recipient_email: str, subject: str, body: str, attachment_paths: list):
    """
    Sends an email with attachments using credentials from environment variables.

    Args:
        recipient_email: The email address of the recipient.
        subject: The subject line of the email.
        body: The body text of the email (plain text).
        attachment_paths: A list of file paths to attach.

    Returns:
        A success message string.
    Raises:
        Exception: If sending fails.
    """
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587)) # Default to 587 if not set

    if not all([sender_email, sender_password, smtp_server]):
        print("Email credentials not fully set in environment variables.")
        return "Error: Email credentials missing."

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    # Attach files
    for file_path in attachment_paths:
        try:
            with open(file_path, "rb") as f:
                part = MIMEApplication(f.read(), name=os.path.basename(file_path))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            msg.attach(part)
            print(f"Attached: {os.path.basename(file_path)}")
        except FileNotFoundError:
            print(f"Error: Attachment not found at {file_path}")
            return f"Error: Attachment not found at {file_path}"
        except Exception as e:
            print(f"Error attaching file {file_path}: {e}")
            return f"Error attaching file {file_path}: {e}"


    # Send the email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls() # Secure the connection
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
        print(f"Email sent successfully to {recipient_email}")
        return f"Email sent successfully to {recipient_email}"

    except Exception as e:
        print(f"Failed to send email: {e}")
        # Provide a more specific error message if possible (e.g., authentication failed)
        if 'authentication' in str(e).lower():
             return f"Email sending failed (Authentication error). Check credentials and App Password."
        elif 'connection' in str(e).lower():
             return f"Email sending failed (Connection error). Check SMTP server and port."
        else:
             return f"Email sending failed: {e}"

# Check if the OpenAI key is loaded
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("Error: OPENAI_API_KEY not found in .env file.")
    print("Please add OPENAI_API_KEY='your_openai_key_here' to your .env file.")
else:
    print("OpenAI API Key loaded successfully.") # Optional: good for debugging initially

    # 2. Initialize the OpenAI LLM
    # We'll use a recent model, like gpt-4o or gpt-4-turbo,
    # which are good for agent tasks and function calling.
    # You can adjust the temperature (0.0 is more deterministic, higher is more creative)
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    print(f"Initialized LLM: {llm.model_name}")

    # 3. Initialize the DuckDuckGo Search Tool
    # LangChain provides a wrapper for DuckDuckGo search
    search_tool = DuckDuckGoSearchRun()
    search_tool.name = "duckduckgo_search" # Give the tool a descriptive name
    search_tool.description = "Useful for answering questions about current events, facts, and recent information. Input should be a search query."

    pdf_tool = StructuredTool.from_function(
    name="pdf_generator", # Tool name (must match the required pattern!)
    func=generate_pdf_document, # The Python function to run
    description="Generates a PDF document from provided text content. " \
                "Input MUST be a dictionary with THREE keys: " \
                "1. 'content' (string): The main text for the PDF body. " \
                "2. 'filename' (string): The desired name of the PDF file (e.g., 'report.pdf'). This argument is REQUIRED. " \
                "3. 'title' (string): The title for the PDF header. " \
                "Example input: {{'content': '...', 'filename': '...', 'title': '...'}}. " \
                "Use this tool when you have finished compiling text content that needs to be saved as a PDF file. ALWAYS provide all three keys.",
                args_schema=PdfToolInput
)

# ... (previous tool definitions like pdf_tool) ...

# 6. Create the Email Sending Tool
# Wrap the send_email_with_attachments function as a tool
email_tool = StructuredTool.from_function(
    func=send_email_with_attachments, # The Python function to run
    args_schema=EmailToolInput, # <-- Explicitly link the input schema
    description="Sends an email with specified recipient, subject, body, and list of attachment file paths. " \
                "Input must match the EmailToolInput schema. " \
                "Use this tool ONLY after files to be attached have been successfully generated."
)

# 7. Define the tools the agent can use (add the new tool)
tools = [search_tool, pdf_tool, email_tool] # Add email_tool to the list

print(f"Initialized Tool: {email_tool.name}")
print(f"Tool Description: {email_tool.description}")


    # --- Next steps will involve creating the actual agent logic ---
    # We have the LLM (the brain) and the Tool (the capability).
    # The next step is to tell the LLM how to use the tool to achieve the market trends goal.from langchain_core.prompts import ChatPromptTemplate

# 5. Define the prompt for the agent
# This prompt tells the LLM its role, the task, and how to format the output.
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert AI Product Management Assistant. Your primary task is to find market trends for a given topic, create a PDF report of these trends, and email the report.

    For the market trends section, find 5 to 7 key trends, including their source(s) and significance.

    **Follow these steps strictly and in order:**

    1.  **Research Market Trends:** Use the `duckduckgo_search` tool to find relevant market trends, innovations, growth factors, and challenges for the user's topic. Perform multiple targeted searches if helpful.
    2.  **Synthesize Market Trends:** Analyze the search results. Synthesize and clearly format 5 to 7 key market trends, ensuring each includes:
        * Trend description
        * Source(s) (article title or URL)
        * Significance/Implication
    3.  **Generate PDF Report:** Use the `pdf_generator` tool to save the synthesized market trends content as a PDF file.
        * Provide the **full text of the market trends** you generated in Step 2 as the `content`.
        * The `filename` MUST be `market_trends_report.pdf`.
        * The `title` MUST be `Market Trends Report`.
        * Call the `pdf_generator` tool with a dictionary containing keys `content`, `filename`, and `title`.
    4.  After successfully generating the PDF using the `pdf_generator` tool, prepare to email it.
    5.  **Send Email:** Use the `email_sender` tool to email the generated PDF report.
        * The `recipient_email` MUST be 'your.recipient.email@example.com'. **REPLACE THIS WITH A REAL EMAIL ADDRESS YOU CAN CHECK.**
        * The `subject` MUST be 'Market Trends Report for: [User Topic]'. Replace '[User Topic]' with the actual topic from the user input.
        * The `body` MUST be 'Please find the attached market trends report.'.
        * The `attachment_paths` MUST be a list containing the filename of the generated PDF: `['market_trends_report.pdf']`.
        * Call the `email_sender` tool with a dictionary containing keys `recipient_email`, `subject`, `body`, and `attachment_paths`.
    6.  After successfully sending the email using the `email_sender` tool, state clearly and concisely that the market trends report has been generated and emailed to the recipient. This is your final response.

    Be thorough in your research and synthesis, but follow the tool usage instructions precisely.
    """),
  ("user", """Topic: {input}
Recipient Email: {recipient_email}
"""), # This is where the user's query goes
    ("placeholder", "{agent_scratchpad}"), # This is where the agent's thinking process and tool outputs go
])

print("Defined the agent prompt.")


# 6. Create the Tool Calling Agent
# This combines the LLM, the tools the LLM can use, and the prompt instructing the LLM.
agent = create_tool_calling_agent(llm, tools, prompt)

print("Created the tool calling agent.")

# 7. Create the Agent Executor
# This ties the agent to the tools and the prompt, and executes the agent's instructions.
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

print("Created the agent executor.")

# 8. Run the agent with a specific query
user_query = "AI in healthcare, send email to tosinoladokun3@gmail.com"
print(f"\nRunning agent for query: '{user_query}'")
recipient_email_for_agent = "tosinoladokun3@gmail.com"
# The agent_executor will run the agent loop
# It will use the prompt, decide to call the search tool,
# get the results, then use the LLM again to format the final answer
# based on the prompt's instructions.
try:
    result = agent_executor.invoke({"input": user_query})

    # The final output is typically in result['output']
    print("\nAgent finished. Here are the market trends:")
    print(result['output'])

except Exception as e:
    print(f"\nAn error occurred during agent execution: {e}")
    print("Check the verbose output above for clues.")