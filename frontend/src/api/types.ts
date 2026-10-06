// Learner-facing REST contracts. Draft answer keys never enter lesson state.
export interface Learner {
  id: number;
  name: string;
  goal: string;
  created_at: string;
}

export interface Concept {
  id: number;
  slug: string;
  name: string;
  description: string;
  prerequisite_ids: number[];
}

export interface StudyPlan {
  goal: string;
  completed: boolean;
  mastered: Concept[];
  available_now: Concept[];
  locked: Concept[];
  recommended_next: Concept | null;
}

export interface ProgressItem {
  concept: Concept;
  mastery_score: number;
  attempts: number;
  updated_at: string | null;
}

export interface Progress {
  learner_id: number;
  mastery_threshold: number;
  concepts: ProgressItem[];
}

export interface Question {
  id: number;
  prompt: string;
  code_snippet: string | null;
  options: string[];
}

export interface Lesson {
  id: number;
  learner_id: number;
  concept_slug: string;
  title: string;
  explanation: string;
  examples: string[];
  questions: Question[];
  created_at: string;
}

export interface Feedback {
  explanation: string;
  what_you_misunderstood: string;
  how_to_improve: string;
  short_example: string;
}

export interface Attempt {
  id: number;
  learner_id: number;
  question_id: number;
  selected_option_index: number;
  correct: boolean;
  correct_option_index: number;
  correct_answer: string;
  misconception_tag: string | null;
  mastery_score: number;
  concept_attempts: number;
  created_at: string;
  feedback: Feedback | null;
  feedback_source: 'llm' | 'fallback' | null;
}
