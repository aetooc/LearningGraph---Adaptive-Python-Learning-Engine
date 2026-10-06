import type { Attempt, Learner, Lesson, Progress, StudyPlan } from './types';

const baseUrl = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, options);
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error('Cannot reach the API. Check that the backend is running.');
    }
    throw error;
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = typeof body?.detail === 'string' ? body.detail : `Request failed (${response.status}).`;
    throw new ApiError(response.status, detail);
  }
  return response.json() as Promise<T>;
}

function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    ...(body === undefined ? {} : {
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  });
}

export const api = {
  learners: (signal?: AbortSignal) => request<Learner[]>('/learners', { signal }),
  createLearner: (name: string) => post<Learner>('/learners', { name, goal: 'Python Fundamentals' }),
  studyPlan: (id: number, signal?: AbortSignal) => request<StudyPlan>(`/learners/${id}/study-plan`, { signal }),
  progress: (id: number, signal?: AbortSignal) => request<Progress>(`/learners/${id}/progress`, { signal }),
  generateLesson: (id: number) => post<Lesson>(`/learners/${id}/lessons/generate`),
  submitAnswer: (learnerId: number, questionId: number, selectedOptionIndex: number) =>
    post<Attempt>('/attempts', {
      learner_id: learnerId,
      question_id: questionId,
      selected_option_index: selectedOptionIndex,
    }),
};
