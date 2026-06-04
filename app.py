import streamlit as st
import json
from datetime import datetime
from ai_code_reviewer import AICodeReviewer


def main():
    """Simple AI-powered code reviewer."""
    st.set_page_config(page_title="Smart Code Reviewer", page_icon="🤖", layout="centered")
    
    # Header
    st.title("🤖 Smart Code Reviewer")
    st.markdown("Get intelligent code feedback with Google Gemini")
    
    # API Key
    api_key = st.text_input("Gemini API Key", type="password", help="Required for AI analysis")
    
    if not api_key:
        st.warning("Please enter your Gemini API key to continue")
        st.stop()
    
    # Language selection
    language = st.selectbox(
        "Language",
        options=['python', 'javascript', 'java', 'typescript', 'go', 'rust'],
        index=0
    )
    
    # Code input
    code_input = st.text_area(
        "Paste your code:",
        height=300,
        help="Enter the code you want to review"
    )
    
    # Review button
    if st.button("Review Code", type="primary"):
        if not code_input.strip():
            st.error("Please enter some code to review")
        else:
            with st.spinner("Analyzing with AI..."):
                reviewer = AICodeReviewer(gemini_api_key=api_key)
                result = reviewer.analyze_code(code_input, language)
                display_results(result, code_input, language)


def display_results(result, code, language):
    """Display review results."""
    # Summary
    st.subheader("Summary")
    st.info(result['summary'])
    
    # Scores
    scores = result['scores']
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Security", f"{scores['security']}/10")
    with col2:
        st.metric("Performance", f"{scores['performance']}/10")
    with col3:
        st.metric("Overall", f"{scores['overall']}/10")
    
    # Issues
    if result['issues']:
        st.subheader("Issues Found")
        
        for issue in result['issues']:
            priority = issue['priority']
            if priority == 'CRITICAL':
                st.error(f"🔴 **{issue['type']}** - {issue['description']}")
            elif priority == 'IMPORTANT':
                st.warning(f"🟡 **{issue['type']}** - {issue['description']}")
            else:
                st.info(f"🔵 **{issue['type']}** - {issue['description']}")
            
            st.write(f"Suggestion: {issue['suggestion']}")
            st.write("---")
    
    # Positive notes
    if result['positive_notes']:
        st.subheader("✅ Good Points")
        for note in result['positive_notes']:
            st.success(note)
    
    # Code
    st.subheader("Reviewed Code")
    st.code(code, language=language)


if __name__ == "__main__":
    main()
