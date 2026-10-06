import { useEffect, useState } from 'react';

import { api, ApiError } from './api/client';
import type { Attempt, Learner, Lesson, Progress, StudyPlan as StudyPlanData } from './api/types';
import { LearnerSelector } from './components/LearnerSelector';
import { LessonView } from './components/LessonView';
import { StudyPlan } from './components/StudyPlan';

interface LearningState {
  plan: StudyPlanData;
  progress: Progress;
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong. Please try again.';
}

async function loadLearningState(id: number, signal?: AbortSignal): Promise<LearningState> {
  const [plan, progress] = await Promise.all([api.studyPlan(id, signal), api.progress(id, signal)]);
  return { plan, progress };
}

export default function App() {
  const [learners, setLearners] = useState<Learner[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loadingLearners, setLoadingLearners] = useState(true);
  const [learnerListVersion, setLearnerListVersion] = useState(0);
  const [learning, setLearning] = useState<LearningState | null>(null);
  const [loadingPlan, setLoadingPlan] = useState(false);
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [results, setResults] = useState<Record<number, Attempt | undefined>>({});
  const [duplicates, setDuplicates] = useState<Record<number, boolean | undefined>>({});
  const [busy, setBusy] = useState<'create' | 'generate' | 'submit' | 'refresh' | null>(null);
  const [submittingQuestion, setSubmittingQuestion] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const selected = learners.find((learner) => learner.id === selectedId);

  useEffect(() => {
    const controller = new AbortController();
    setLoadingLearners(true);
    setError(null);
    api.learners(controller.signal).then((items) => {
      if (!controller.signal.aborted) setLearners(items);
    }).catch((failure: unknown) => {
      if (!controller.signal.aborted) setError(errorMessage(failure));
    }).finally(() => {
      if (!controller.signal.aborted) setLoadingLearners(false);
    });
    return () => controller.abort();
  }, [learnerListVersion]);

  useEffect(() => {
    const controller = new AbortController();
    setLearning(null);
    setLesson(null);
    setResults({});
    setDuplicates({});
    setError(null);
    setLoadingPlan(selectedId !== null);
    if (selectedId !== null) {
      loadLearningState(selectedId, controller.signal).then((state) => {
        if (!controller.signal.aborted) setLearning(state);
      }).catch((failure: unknown) => {
        if (!controller.signal.aborted) setError(errorMessage(failure));
      }).finally(() => {
        if (!controller.signal.aborted) setLoadingPlan(false);
      });
    }
    return () => controller.abort();
  }, [selectedId]);

  function selectLearner(id: number | null) {
    if (id === selectedId) return;
    // Clear the previous learner's content in the same update as the selection.
    setSelectedId(id);
    setLearning(null);
    setLesson(null);
    setResults({});
    setDuplicates({});
    setError(null);
    setLoadingPlan(id !== null);
  }

  async function createLearner(name: string) {
    setBusy('create');
    setError(null);
    try {
      const learner = await api.createLearner(name);
      setLearners((previous) => [...previous, learner]);
      selectLearner(learner.id);
      return true;
    } catch (failure) {
      setError(errorMessage(failure));
      return false;
    } finally {
      setBusy(null);
    }
  }

  async function refresh() {
    if (selectedId === null) return;
    setBusy('refresh');
    setError(null);
    try {
      setLearning(await loadLearningState(selectedId));
    } catch (failure) {
      setError(errorMessage(failure));
    } finally {
      setBusy(null);
    }
  }

  async function generateLesson() {
    if (selectedId === null || busy !== null) return;
    setBusy('generate');
    setError(null);
    try {
      setLesson(await api.generateLesson(selectedId));
      setResults({});
      setDuplicates({});
    } catch (failure) {
      setError(errorMessage(failure));
    } finally {
      setBusy(null);
    }
  }

  async function submitAnswer(questionId: number, option: number) {
    if (selectedId === null || busy !== null || results[questionId] || duplicates[questionId]) return;
    setBusy('submit');
    setSubmittingQuestion(questionId);
    setError(null);
    try {
      const result = await api.submitAnswer(selectedId, questionId, option);
      setResults((previous) => ({ ...previous, [questionId]: result }));
      // Keep the recorded result visible even if the follow-up progress read fails.
      try {
        setLearning(await loadLearningState(selectedId));
      } catch {
        setError('Your answer was recorded, but progress could not refresh. Use Refresh to load it again.');
      }
    } catch (failure) {
      if (failure instanceof ApiError && failure.status === 409) {
        setDuplicates((previous) => ({ ...previous, [questionId]: true }));
        try {
          setLearning(await loadLearningState(selectedId));
        } catch {
          // The duplicate response remains useful even if the refresh is unavailable.
        }
      }
      setError(errorMessage(failure));
    } finally {
      setSubmittingQuestion(null);
      setBusy(null);
    }
  }

  const disabled = busy !== null || loadingPlan;

  return (
    <main className="app">
      <header className="page-header">
        <p className="eyebrow">Python fundamentals</p>
        <h1>Adaptive Python Learning</h1>
        <p className="muted">Learn one concept at a time. Practise, get feedback, and see your progress.</p>
      </header>
      <LearnerSelector learners={learners} selectedId={selectedId} loading={loadingLearners}
        disabled={busy !== null || loadingLearners} onSelect={selectLearner} onCreate={createLearner}
        onReload={() => setLearnerListVersion((previous) => previous + 1)} />
      {error && <div className="error" role="alert">{error}</div>}
      {selected && <p className="learner-title">Learning as <strong>{selected.name}</strong></p>}
      {loadingPlan && <p role="status">Loading your study plan…</p>}
      {selectedId === null && !loadingLearners && <p className="empty-state">Choose a learner or create one to begin.</p>}
      {selectedId !== null && !loadingPlan && !learning && (
        <button type="button" onClick={refresh} disabled={disabled}>Retry loading study plan</button>
      )}
      {learning && (
        <div className="learning-layout">
          <aside>
            <StudyPlan plan={learning.plan} progress={learning.progress} disabled={disabled}
              generating={busy === 'generate'} onGenerate={generateLesson} onRefresh={refresh} />
          </aside>
          <div>
            {lesson ? (
              <LessonView key={lesson.id} lesson={lesson} results={results} duplicates={duplicates}
                disabled={disabled} submittingQuestion={submittingQuestion} onSubmit={submitAnswer} />
            ) : (
              <section className="card empty-state">
                <h2>{learning.plan.completed ? 'Curriculum complete' : 'Ready for your next lesson?'}</h2>
                <p>{learning.plan.completed ? 'Your completed concepts and mastery are shown in your study plan.' : 'Generate a lesson for your recommended concept to see examples and three practice questions.'}</p>
              </section>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
