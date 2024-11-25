import streamlit as st
import pandas as pd
from transformers import pipeline  # Import Hugging Face pipeline

# Upload Excel file
st.header("HowAI’mDoing")

# Sample file download
sample_excel_url = "https://github.com/prasadmadhasi/prasadmadhasi/blob/main/performanceFeedback_sample_data_v1.0.xlsx"

# Add download link for the sample Excel file
st.subheader("Download Sample Excel File:")
st.markdown(f"[Download Sample Excel](https://github.com/prasadmadhasi/prasadmadhasi/blob/main/performanceFeedback_sample_data_v1.0.xlsx)")

with st.sidebar:
    st.title("Your Documents")
    file = st.file_uploader("Upload an Excel file and ask questions", type=["xlsx"])

# Initialize the Hugging Face sentiment-analysis pipeline
classifier = pipeline("sentiment-analysis")

# Sentiment analysis function using Hugging Face model
def analyze_sentiment(text):
    result = classifier(text)[0]
    sentiment = result['label']

    # Classify as positive or negative
    if sentiment == "POSITIVE":
        return "positive"
    elif sentiment == "NEGATIVE":
        return "negative"
    else:
        return "neutral"

# Extract and process the Excel data
if file is not None:
    try:
        df = pd.read_excel(file)

        # Check if the relevant columns exist
        required_columns = [
            'emailid_feedback_for', 'Overall Feedback Comments',
            'Nimble Learning', 'Communicates Effectively',
            'Drives Results', 'Customer Focus', 'Business Insight',
            'Cultivates Innovation', 'Ensures Accountability',
            'Manages Ambiguity', 'Manages Complexity',
            'Decision Quality', 'Professionalism and Attitude',
            'CREATED_DATE_TIME'
        ]

        if not all(col in df.columns for col in required_columns):
            st.error("Required columns not found in the Excel file.")
        else:
            # Ensure CREATED_DATE_TIME is in datetime format
            df['CREATED_DATE_TIME'] = pd.to_datetime(df['CREATED_DATE_TIME'], errors='coerce')

            # Get the name and optional year from user input
            resource_input = st.text_input("Enter the email of the resource and optionally the year (e.g., vmadhasi@mycompany.com (or) vmadhasi@mycompany.com 2024")

            # Extract the resource name and year from the input
            if resource_input:
                # Extract year from input if present
                tokens = resource_input.split()
                year = None
                for token in tokens:
                    if token.isdigit() and len(token) == 4:
                        year = int(token)  # Extract year
                        tokens.remove(token)
                        break
                resource_name = " ".join(tokens)  # Remaining tokens form the resource name

                # Filter the dataframe for the resource name
                resource_data = df[df['emailid_feedback_for'].str.contains(resource_name, case=False, na=False)]

                # If year is provided, filter by year
                if year:
                    resource_data = resource_data[resource_data['CREATED_DATE_TIME'].dt.year == year]

                # Check if data for the resource exists
                if not resource_data.empty:
                    # Extract the "Overall Feedback Comments"
                    overall_comments = resource_data['Overall Feedback Comments'].tolist()

                    # Separate positive and negative feedback
                    positive_feedback = []
                    negative_feedback = []

                    # Analyze sentiment and categorize comments
                    for comment in overall_comments:
                        sentiment = analyze_sentiment(comment)
                        if sentiment == "positive":
                            positive_feedback.append(comment)
                        elif sentiment == "negative":
                            negative_feedback.append(comment)

                    # Display positive feedback
                    st.subheader(f"Positive Feedback for {resource_name} ({year if year else 'All Years'}):")
                    if positive_feedback:
                        st.write("\n".join(positive_feedback))
                    else:
                        st.write("No positive feedback found.")

                    # Display negative feedback
                    st.subheader(f"Negative Feedback for {resource_name} ({year if year else 'All Years'}):")
                    if negative_feedback:
                        st.write("\n".join(negative_feedback))
                    else:
                        st.write("No negative feedback found.")

                    # Calculate and display the averages for the performance attributes
                    st.subheader(f"Performance Averages for {resource_name} ({year if year else 'All Years'}):")

                    # List of attributes
                    attributes = [
                        'Nimble Learning', 'Communicates Effectively',
                        'Drives Results', 'Customer Focus', 'Business Insight',
                        'Cultivates Innovation', 'Ensures Accountability',
                        'Manages Ambiguity', 'Manages Complexity',
                        'Decision Quality', 'Professionalism and Attitude'
                    ]

                    # Iterate over the attributes in chunks of 3 to display 3 per row
                    for i in range(0, len(attributes), 3):
                        # Create columns for 3 attributes per row
                        columns = st.columns(3)
                        for j, attr in enumerate(attributes[i:i+3]):
                            if attr in resource_data.columns:
                                avg_rating = resource_data[attr].mean()
                                formatted_avg = f"{avg_rating:.2f}"  # Format to 2 decimal places
                                columns[j].write(f"**{attr}:** {formatted_avg}")
                            else:
                                columns[j].write(f"**{attr}:** N/A")  # If the attribute is missing in the data

                else:
                    st.warning(f"No feedback found for {resource_name} ({year if year else 'All Years'}).")

    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
else:
    st.info("Please upload an Excel file to get started.")
