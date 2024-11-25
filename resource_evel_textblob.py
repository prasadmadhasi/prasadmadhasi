import streamlit as st
import pandas as pd
from transformers import pipeline  # Import Hugging Face pipeline

# Initialize the Hugging Face sentiment-analysis pipeline
classifier = pipeline("sentiment-analysis")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
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

# Upload Excel file
st.header("HowAI’mDoing")

# Sample file download
sample_excel_url = "https://github.com/prasadmadhasi/prasadmadhasi/blob/b1aa0d4cd03552fdfa5ebd749287e3be271b121c/performanceFeedback_sample_data_v1.1.xlsx"
st.subheader("Download Sample Excel File:")
st.markdown(f"[Download Sample Excel](https://github.com/prasadmadhasi/prasadmadhasi/blob/b1aa0d4cd03552fdfa5ebd749287e3be271b121c/performanceFeedback_sample_data_v1.1.xlsx)")

with st.sidebar:
    st.title("Your Documents")
    file = st.file_uploader("Upload an Excel file and ask questions", type=["xlsx"])

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
            'CREATED_DATE_TIME', 'self_feedback'
        ]

        if not all(col in df.columns for col in required_columns):
            st.error("Required columns not found in the Excel file.")
        else:
            # Ensure CREATED_DATE_TIME is in datetime format
            df['CREATED_DATE_TIME'] = pd.to_datetime(df['CREATED_DATE_TIME'], errors='coerce')

            # Get the name and optional year from user input
            resource_input = st.text_input("Enter the email of the resource and optionally the year (e.g., vmadhasi@mycompany.com (or) vmadhasi@mycompany.com 2024)")

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

                # Add checkbox to include or exclude self_feedback in analysis
                include_self_feedback = st.checkbox("Include Self Feedback", value=True)

                # Filter the data based on the checkbox value
                if include_self_feedback:
                    # Include all rows
                    filtered_data = resource_data
                else:
                    # Exclude rows where self_feedback == 'Y'
                    filtered_data = resource_data[resource_data['self_feedback'] != 'Y']

                # Check if the filtered data exists
                if not filtered_data.empty:
                    # Extract the "Overall Feedback Comments" from the filtered data
                    overall_comments = filtered_data['Overall Feedback Comments'].tolist()

                    # Process the comments for sentiment analysis
                    positive_feedback = []
                    negative_feedback = []

                    for comment in overall_comments:
                        # Analyze sentiment for each comment
                        sentiment = analyze_sentiment(comment)
                        if sentiment == "positive":
                            positive_feedback.append(comment)
                        elif sentiment == "negative":
                            negative_feedback.append(comment)

                    # Display positive feedback
                    # Subheader in red
                    st.markdown(
                        f"""
                        <h3 style='color: Green;'>Positive Feedback for {resource_name} ({year if year else 'All Years'}):</h3>
                        """,
                        unsafe_allow_html=True
                    )
                    if positive_feedback:
                        st.write("\n".join(positive_feedback))
                        st.markdown(
                        f"""
                        <h4 style='color: Green;'>Positive Feedback Summary:</h3>
                        """,
                        unsafe_allow_html=True
                    )
                        positive_summary=summarizer("\n".join(positive_feedback), max_length=10000, min_length=1, do_sample=False)
                        st.write(positive_summary[0]['summary_text'])
                    else:
                        st.write("No positive feedback found.")

                    # Display negative feedback
                    st.markdown(
                        f"""
                        <h3 style='color: red;'>Negative Feedback for {resource_name} ({year if year else 'All Years'}):</h3>
                        """,
                        unsafe_allow_html=True
                    )
                    if negative_feedback:
                        st.write("\n".join(negative_feedback))
                        st.markdown(
                        f"""
                        <h4 style='color: red;'>Negative Feedback Summary:</h3>
                        """,
                        unsafe_allow_html=True
                    )
                        negative_summary=summarizer("\n".join(negative_feedback), max_length=10000, min_length=1, do_sample=False)
                        st.write(negative_summary[0]['summary_text'])
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
                            if attr in filtered_data.columns:
                                avg_rating = filtered_data[attr].mean()
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
