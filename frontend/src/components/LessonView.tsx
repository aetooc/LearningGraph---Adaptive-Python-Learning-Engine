import type { Attempt, Lesson } from '../api/types';
import { QuestionCard } from './QuestionCard';

interface Props {
  lesson: Lesson;
  results: Record<number, Attempt | undefined>;
  duplicates: Record<number, boolean | undefined>;
  disabled: boolean;
  submittingQuestion: number | null;
  onSubmit: (questionId: number, option: number) => void;
}

export function LessonView({ lesson, results, duplicates, disabled, submittingQuestion, onSubmit }: Props) {
  return (
    <section className="card lesson" aria-labelledby="lesson-heading">
      <p className="eyebrow">Your lesson</p>
      <h2 id="lesson-heading">{lesson.title}</h2>
      <p className="explanation">{lesson.explanation}</p>
      <h3>Examples</h3>
      {lesson.examples.map((example, index) => <pre key={index}><code>{example}</code></pre>)}
      <h3 className="practice-heading">Practice</h3>
      {lesson.questions.map((question, index) => (
        <QuestionCard key={question.id} question={question} number={index + 1} total={lesson.questions.length}
          disabled={disabled} submitting={submittingQuestion === question.id} result={results[question.id]}
          duplicate={Boolean(duplicates[question.id])} onSubmit={onSubmit} />
      ))}
    </section>
  );
}
