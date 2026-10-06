import { useState } from 'react';

import type { Attempt, Question } from '../api/types';
import { FeedbackCard } from './FeedbackCard';

interface Props {
  question: Question;
  number: number;
  total: number;
  disabled: boolean;
  submitting: boolean;
  result?: Attempt;
  duplicate: boolean;
  onSubmit: (questionId: number, option: number) => void;
}

export function QuestionCard({ question, number, total, disabled, submitting, result, duplicate, onSubmit }: Props) {
  const [selected, setSelected] = useState<number | null>(null);
  const answered = Boolean(result) || duplicate;

  return (
    <article className="question">
      <p className="eyebrow">Question {number} of {total}</p>
      <h3>{question.prompt}</h3>
      {question.code_snippet && <pre><code>{question.code_snippet}</code></pre>}
      <form onSubmit={(event) => {
        event.preventDefault();
        if (selected !== null && !answered && !disabled) onSubmit(question.id, selected);
      }}>
        <fieldset disabled={disabled || answered}>
          <legend className="sr-only">Choose one answer</legend>
          {question.options.map((option, index) => (
            <label className={`option ${selected === index ? 'selected' : ''}`} key={index}>
              <input type="radio" name={`question-${question.id}`} value={index}
                checked={selected === index} onChange={() => setSelected(index)} />
              <span>{option}</span>
            </label>
          ))}
        </fieldset>
        <button type="submit" disabled={disabled || answered || selected === null}>
          {submitting ? 'Submitting answer…' : answered ? 'Answer recorded' : 'Submit answer'}
        </button>
      </form>
      {result && <FeedbackCard result={result} />}
      {duplicate && <p role="status" className="muted">This question was already answered. Generate a new set to continue practising.</p>}
    </article>
  );
}
