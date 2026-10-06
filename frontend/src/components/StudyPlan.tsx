import type { Progress, StudyPlan as StudyPlanData } from '../api/types';

interface Props {
  plan: StudyPlanData;
  progress: Progress;
  disabled: boolean;
  generating: boolean;
  onGenerate: () => void;
  onRefresh: () => void;
}

export function StudyPlan({ plan, progress, disabled, generating, onGenerate, onRefresh }: Props) {
  return (
    <>
      <section className="card recommendation" aria-labelledby="next-heading">
        <p className="eyebrow">Recommended next</p>
        <h2 id="next-heading">{plan.completed ? 'Python fundamentals complete' : plan.recommended_next?.name ?? 'No concept available'}</h2>
        <p>{plan.completed ? 'You have mastered every concept in this curriculum.' : plan.recommended_next?.description}</p>
        <button type="button" onClick={onGenerate} disabled={disabled || plan.completed || !plan.recommended_next}>
          {generating ? 'Generating lesson…' : 'Generate lesson / practice set'}
        </button>
        {!plan.completed && <p className="muted small">You can generate another set to keep practising this concept.</p>}
      </section>
      <section className="card" aria-labelledby="progress-heading">
        <div className="section-title">
          <h2 id="progress-heading">Current progress</h2>
          <button type="button" className="secondary" onClick={onRefresh} disabled={disabled}>Refresh</button>
        </div>
        <p className="muted small">Mastery threshold: {Math.round(progress.mastery_threshold * 100)}%</p>
        <ul className="progress-list">
          {progress.concepts.map((item) => {
            // These statuses come from the backend's lists, never score comparisons.
            const mastered = plan.mastered.some((concept) => concept.id === item.concept.id);
            const locked = plan.locked.some((concept) => concept.id === item.concept.id);
            const available = plan.available_now.some((concept) => concept.id === item.concept.id);
            const status = mastered ? 'Mastered' : locked ? 'Locked' : available ? 'Available' : 'Unknown';
            return (
              <li key={item.concept.id}>
                <div className="progress-label">
                  <span>{item.concept.name}</span>
                  <span className={`badge ${status.toLowerCase()}`}>{status}</span>
                </div>
                <div className="progress-value">
                  <progress value={item.mastery_score} max={1} aria-label={`${item.concept.name} mastery`} />
                  <span>{Math.round(item.mastery_score * 100)}%</span>
                </div>
                <span className="muted small">{item.attempts} {item.attempts === 1 ? 'attempt' : 'attempts'}</span>
              </li>
            );
          })}
        </ul>
        <details>
          <summary>Available and locked concepts</summary>
          <p><strong>Available now:</strong> {plan.available_now.map((concept) => concept.name).join(', ') || 'None'}</p>
          <p><strong>Locked:</strong> {plan.locked.map((concept) => concept.name).join(', ') || 'None'}</p>
        </details>
      </section>
    </>
  );
}
