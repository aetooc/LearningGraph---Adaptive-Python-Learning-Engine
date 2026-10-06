def valid_lesson(slug="variables"):
    return {
        "title": f"Learn {slug}", "concept_slug": slug,
        "explanation": "Assignment binds a name to a value.",
        "examples": ["x = 1\nprint(x)"],
        "questions": [
            {
                "prompt": f"Question {number}: what does x = 1 bind to x?",
                "code_snippet": "x = 1",
                "options": ["1", "0", "None", "An error"],
                "correct_option_index": 0,
                "misconceptions": [
                    {"option_index": 1, "tag": "default_zero"},
                    {"option_index": 2, "tag": "assignment_is_none"},
                    {"option_index": 3, "tag": "assignment_error"},
                ],
            }
            for number in range(3)
        ],
    }
