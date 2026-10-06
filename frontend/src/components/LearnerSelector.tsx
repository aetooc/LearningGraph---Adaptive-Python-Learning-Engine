import { useState } from 'react';
import type { FormEvent } from 'react';

import type { Learner } from '../api/types';

interface Props {
  learners: Learner[];
  selectedId: number | null;
  disabled: boolean;
  loading: boolean;
  onSelect: (id: number | null) => void;
  onCreate: (name: string) => Promise<boolean>;
  onReload: () => void;
}

export function LearnerSelector({ learners, selectedId, disabled, loading, onSelect, onCreate, onReload }: Props) {
  const [name, setName] = useState('');

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!name.trim()) return;
    if (await onCreate(name.trim())) setName('');
  }

  return (
    <section className="card" aria-labelledby="learner-heading">
      <div className="section-title">
        <h2 id="learner-heading">Your learner</h2>
        <button type="button" className="secondary" disabled={disabled || loading} onClick={onReload}>Refresh learners</button>
      </div>
      <label htmlFor="learner-select">Select an existing learner</label>
      <select id="learner-select" value={selectedId ?? ''} disabled={disabled || loading}
        onChange={(event) => onSelect(event.target.value ? Number(event.target.value) : null)}>
        <option value="">{loading ? 'Loading learners…' : 'Choose a learner'}</option>
        {learners.map((learner) => (
          <option key={learner.id} value={learner.id}>{learner.name} (#{learner.id})</option>
        ))}
      </select>
      <form onSubmit={submit} className="create-form">
        <label htmlFor="learner-name">Or create a learner</label>
        <div className="input-row">
          <input id="learner-name" placeholder="e.g. Alice" value={name} maxLength={100}
            required disabled={disabled} onChange={(event) => setName(event.target.value)} />
          <button type="submit" disabled={disabled || !name.trim()}>Create learner</button>
        </div>
      </form>
      <p className="muted small">Goal: Learn Python Fundamentals</p>
    </section>
  );
}
