import streamlit as st
import re
import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import google.generativeai as genai


class AICodeReviewer:
    """AI-powered code reviewer with custom instructions and priority-based analysis using Gemini."""
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
        self.custom_instructions = self._load_custom_instructions()
    
    def _load_custom_instructions(self) -> str:
        """Load custom review instructions from smart_code_reviewer_prompt.md"""
        try:
            with open('smart_code_reviewer_prompt.md', 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return self._get_default_instructions()
    
    def _get_default_instructions(self) -> str:
        """Default instructions when smart_code_reviewer_prompt.md is not found"""
        return """
You are a code reviewer. Focus on:
1. CRITICAL: Security vulnerabilities, breaking changes
2. IMPORTANT: Performance issues, error handling
3. MEDIUM: Code quality, style improvements
Provide actionable suggestions with clear priority levels.
"""
    
    def analyze_code(self, code: str, language: str) -> Dict:
        """Analyze code using AI with custom instructions."""
        if not self.model:
            return self._get_error_result("Gemini API key not configured")
        
        return self._ai_analyze_code(code, language)
    
    def _ai_analyze_code(self, code: str, language: str) -> Dict:
        """Use AI to analyze code with custom instructions."""
        try:
            prompt = f"""
{self.custom_instructions}

Please review the following {language} code and provide feedback:

```{language}
{code}
```

Provide your analysis in the following JSON format:
{{
    "summary": "Overall assessment of the code",
    "issues": [
        {{
            "priority": "CRITICAL|IMPORTANT|MEDIUM",
            "type": "Issue category",
            "description": "Detailed description of the issue",
            "suggestion": "Specific actionable suggestion",
            "line_number": 1
        }}
    ],
    "positive_notes": [
        "Positive observations about the code"
    ],
    "scores": {{
        "security": 1-10,
        "performance": 1-10,
        "reliability": 1-10,
        "maintainability": 1-10,
        "overall": 1-10
    }}
}}
"""
            
            response = self.model.generate_content(prompt)
            content = response.text
            
            # Try to extract JSON from the response
            try:
                # Look for JSON content in the response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return self._validate_and_normalize_result(result)
                else:
                    return self._parse_text_response(content)
            except json.JSONDecodeError:
                return self._parse_text_response(content)
                
        except Exception as e:
            return self._get_error_result(f"AI analysis failed: {str(e)}")
    
    def _validate_and_normalize_result(self, result: Dict) -> Dict:
        """Validate and normalize AI response format."""
        normalized = {
            'summary': result.get('summary', 'AI analysis completed'),
            'issues': [],
            'positive_notes': result.get('positive_notes', []),
            'scores': {
                'security': 8,
                'performance': 8,
                'reliability': 8,
                'maintainability': 8,
                'overall': 8
            }
        }
        
        # Validate and normalize issues
        for issue in result.get('issues', []):
            normalized_issue = {
                'priority': issue.get('priority', 'MEDIUM'),
                'type': issue.get('type', 'General'),
                'description': issue.get('description', ''),
                'suggestion': issue.get('suggestion', ''),
                'line_number': issue.get('line_number', 1)
            }
            
            # Validate priority
            if normalized_issue['priority'] not in ['CRITICAL', 'IMPORTANT', 'MEDIUM']:
                normalized_issue['priority'] = 'MEDIUM'
            
            normalized['issues'].append(normalized_issue)
        
        # Validate scores
        if 'scores' in result:
            for key, value in result['scores'].items():
                if key in normalized['scores']:
                    normalized['scores'][key] = max(1, min(10, int(value)))
        
        return normalized
    
    def _parse_text_response(self, content: str) -> Dict:
        """Parse non-JSON AI response."""
        # Extract issues from text
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if any(keyword in line.upper() for keyword in ['CRITICAL', 'IMPORTANT', 'MEDIUM']):
                priority = 'MEDIUM'
                if 'CRITICAL' in line.upper():
                    priority = 'CRITICAL'
                elif 'IMPORTANT' in line.upper():
                    priority = 'IMPORTANT'
                
                issues.append({
                    'priority': priority,
                    'type': 'AI Detected Issue',
                    'description': line.strip(),
                    'suggestion': 'Review the AI suggestion above',
                    'line_number': 1
                })
        
        return {
            'summary': content[:200] + '...' if len(content) > 200 else content,
            'issues': issues[:5],  # Limit to 5 issues
            'positive_notes': ['AI analysis completed'],
            'scores': {
                'security': 7,
                'performance': 7,
                'reliability': 7,
                'maintainability': 7,
                'overall': 7
            }
        }
    
    def _get_error_result(self, error_message: str) -> Dict:
        """Return error result when AI analysis fails."""
        return {
            'summary': f'Error: {error_message}',
            'issues': [{
                'priority': 'CRITICAL',
                'type': 'Configuration Error',
                'description': error_message,
                'suggestion': 'Please check your Gemini API key configuration',
                'line_number': 1
            }],
            'positive_notes': [],
            'scores': {
                'security': 1,
                'performance': 1,
                'reliability': 1,
                'maintainability': 1,
                'overall': 1
            }
        }
