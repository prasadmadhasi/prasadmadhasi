import streamlit as st
import pandas as pd
from transformers import pipeline
from concurrent.futures import ThreadPoolExecutor

# Initialize Hugging Face pipelines
classifier = pipeline("sentiment-analysis")  # Sentiment analysis model
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", framework="pt")


# Helper function for sentiment analysis
def analyze_sentiment(text):
    try:
        result = classifier(text)[0]
        sentiment = result['label']
        if sentiment == "POSITIVE":
            return "positive"
        elif sentiment == "NEGATIVE":
            return "negative"
        else:
            return "neutral"
    except Exception as e:
        return f"Error: {e}"

# Helper function for summarizing text in chunks
def summarize_text(texts, max_length=200, min_length=50):
    summaries = []
    for text in texts:
        try:
            summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
            summaries.append(summary[0]['summary_text'])
        except Exception as e:
            summaries.append(f"Error summarizing text: {e}")
    return " ".join(summaries)

# Streamlit UI setup
st.header("HowAI’mDoing")

# Sample file download link
sample_excel_url = "https://github.com/prasadmadhasi/prasadmadhasi/blob/b1aa0d4cd03552fdfa5ebd749287e3be271b121c/performanceFeedback_sample_data_v1.1.xlsx"
st.subheader("Download Sample Excel File:")
st.markdown(f"[Download Sample Excel]({sample_excel_url})")

# Sidebar for file upload
with st.sidebar:
    st.title("Your Documents")
    file = st.file_uploader("Upload an Excel file and ask questions", type=["xlsx"])

# Process the uploaded file
if file is not None:
    try:
        df = pd.read_excel(file)

        # Check required columns
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
            df['CREATED_DATE_TIME'] = pd.to_datetime(df['CREATED_DATE_TIME'], errors='coerce')  # Ensure datetime format

            # User input for resource and year
            resource_input = st.text_input("Enter the email of the resource and optionally the year (e.g., vmadhasi@mycompany.com or vmadhasi@mycompany.com 2024)")

            if resource_input:
                tokens = resource_input.split()
                year = None
                for token in tokens:
                    if token.isdigit() and len(token) == 4:
                        year = int(token)
                        tokens.remove(token)
                        break
                resource_name = " ".join(tokens)

                resource_data = df[df['emailid_feedback_for'].str.contains(resource_name, case=False, na=False)]

                if year:
                    resource_data = resource_data[resource_data['CREATED_DATE_TIME'].dt.year == year]

                include_self_feedback = st.checkbox("Include Self Feedback", value=True)

                if not include_self_feedback:
                    resource_data = resource_data[resource_data['self_feedback'] != 'Y']

                if not resource_data.empty:
                    overall_comments = resource_data['Overall Feedback Comments'].dropna().tolist()

                    # Process sentiment analysis
                    st.subheader(f"Feedback for {resource_name} ({year if year else 'All Years'}):")
                    sentiments = []
                    with ThreadPoolExecutor() as executor:
                        sentiments = list(executor.map(analyze_sentiment, overall_comments))

                    positive_feedback = [c for c, s in zip(overall_comments, sentiments) if s == "positive"]
                    negative_feedback = [c for c, s in zip(overall_comments, sentiments) if s == "negative"]

                    # Display Positive Feedback
                    st.markdown(f"<h3 style='color:green;'>Positive Feedback:</h3>", unsafe_allow_html=True)
                    if positive_feedback:
                        st.write("\n".join(positive_feedback))
                        positive_summary = summarize_text(positive_feedback)
                        st.markdown("<h4 style='color:green;'>Positive Feedback Summary:</h4>", unsafe_allow_html=True)
                        st.write(positive_summary)
                    else:
                        st.write("No positive feedback found.")

                    # Display Negative Feedback
                    st.markdown(f"<h3 style='color:red;'>Negative Feedback:</h3>", unsafe_allow_html=True)
                    if negative_feedback:
                        st.write("\n".join(negative_feedback))
                        negative_summary = summarize_text(negative_feedback)
                        st.markdown("<h4 style='color:red;'>Negative Feedback Summary:</h4>", unsafe_allow_html=True)
                        st.write(negative_summary)
                    else:
                        st.write("No negative feedback found.")

                    # Performance Attribute Averages
                    st.subheader(f"Performance Averages for {resource_name} ({year if year else 'All Years'}):")
                    attributes = [
                        'Nimble Learning', 'Communicates Effectively',
                        'Drives Results', 'Customer Focus', 'Business Insight',
                        'Cultivates Innovation', 'Ensures Accountability',
                        'Manages Ambiguity', 'Manages Complexity',
                        'Decision Quality', 'Professionalism and Attitude'
                    ]

                    for i in range(0, len(attributes), 3):
                        cols = st.columns(3)
                        for j, attr in enumerate(attributes[i:i+3]):
                            if attr in resource_data.columns:
                                avg = resource_data[attr].mean()
                                cols[j].write(f"**{attr}:** {avg:.2f}")
                            else:
                                cols[j].write(f"**{attr}:** N/A")
                else:
                    st.warning(f"No feedback found for {resource_name} ({year if year else 'All Years'}).")

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Please upload an Excel file to get started.")
