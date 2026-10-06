import type { Attempt } from '../api/types';

export function FeedbackCard({ result }: { result: Attempt }) {
  return (
    <div className={`feedback ${result.correct ? 'correct' : 'incorrect'}`} role="status">
      <h4>{result.correct ? 'Correct' : 'Incorrect'}</h4>
      {!result.correct && <p><strong>Correct answer:</strong> {result.correct_answer}</p>}
      <p><strong>Updated mastery:</strong> {Math.round(result.mastery_score * 100)}%</p>
      {result.feedback && (
        <>
          <p>{result.feedback.explanation}</p>
          <p><strong>What you misunderstood:</strong> {result.feedback.what_you_misunderstood}</p>
          <p><strong>How to improve:</strong> {result.feedback.how_to_improve}</p>
          <pre><code>{result.feedback.short_example}</code></pre>
        </>
      )}
      <p className="small">Your answer was recorded. Continue with another question or generate a new practice set.</p>
    </div>
  );
}
