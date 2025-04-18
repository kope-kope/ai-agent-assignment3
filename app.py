import streamlit as st
import os
from dotenv import load_dotenv

# --- Import the initialized agent executor and other components from agent_setup.py ---
# Make sure agent_setup.py is in the same directory
from agent_setup import agent_executor, llm, tools, prompt # Import what you need

# Load environment variables - good to do this in the Streamlit app as well
load_dotenv() # Fix: load_dotenv()

# --- Basic Streamlit Page Setup ---
st.set_page_config(page_title="Product Agent Assistant", layout="wide") # wide layout can be nice

st.title("✨ Product Agent Assistant")
st.write("Enter a product problem space or topic to generate a market trends report, user stories, prioritization, and roadmap outline.")
st.write("The market trends report will be generated as a PDF and emailed.")


# --- UI Elements: Input Fields and Button ---

# Get user input for the topic
user_topic_input = st.text_input(
    "Enter Topic/Problem Space:",
    "AI in Customer Support", # Default value
    help="e.g., 'Recycling of Tyres', 'AI in Healthcare', 'On-demand Food Delivery'" # Add help text
)

# Get user input for the recipient email
# This is used by the agent's email_sender tool
recipient_email_input = st.text_input(
    "Recipient Email for Report:",
    "your.test.email@example.com", # <-- **REPLACE** with a real test email you can access!
    help="Enter the email address where the generated report should be sent."
)


# --- Button to trigger the agent ---
# Use a unique key if you have multiple buttons or dynamic elements
if st.button("Generate Report & Email", key="generate_report_button"):

    # --- Input Validation ---
    if not user_topic_input:
        st.warning("Please enter a topic to generate the report.")
    elif not recipient_email_input:
        st.warning("Please enter a recipient email address.")
    # Basic email format check (optional but good UX)
    elif '@' not in recipient_email_input or '.' not in recipient_email_input:
         st.warning("Please enter a valid email address.")
    else:
        # --- Agent Execution Logic (Runs ONLY when button is clicked and inputs are valid) ---

        # Display a message to the user that the process has started
        st.info(f"Initiating report generation for topic: **{user_topic_input}**")
        st.info(f"Report will be emailed to: **{recipient_email_input}**")
        st.warning("Check your terminal for verbose output from the agent while it's working.")

        # Use a spinner to show activity while the agent is running (can be long)
        with st.spinner("Agent is working... Researching, generating documents, and sending email..."):
            try:
                # --- Invoke the agent executor ---
                # Pass BOTH the topic and the recipient email from the UI inputs
                result = agent_executor.invoke({
                    "input": user_topic_input,
                    "recipient_email": recipient_email_input # Pass recipient email from UI
                })

                # --- Display the final message from the agent ---
                # This should be the final confirmation message from your prompt's last step
                st.success("Agent execution complete!")
                st.write("Final Agent Message:")
                st.write(result['output']) # Display the agent's final text output

                st.info(f"Please check the inbox for **{recipient_email_input}** for the attached report PDF.")

            except Exception as e:
                st.error(f"An error occurred during agent execution: {e}")
                st.warning("Check your terminal for detailed verbose output from the agent for debugging.")
                # Optionally print the full traceback to the console for server-side debugging
                import traceback
                traceback.print_exc()


# --- No agent invocation code here ---
# AgentExecutor.invoke() is ONLY called inside the button's if block.