import React, { useState, useEffect } from 'react';
import type { CouncilMember, PersonalityArchetype, Provider } from '../types';

interface CouncilMemberEditorProps {
  members: CouncilMember[];
  onMembersChange: (members: CouncilMember[]) => void;
  providers: Provider[];
}

const generateId = () => `member_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

export default function CouncilMemberEditor({
  members,
  onMembersChange,
  providers,
}: CouncilMemberEditorProps) {
  const [archetypes, setArchetypes] = useState<PersonalityArchetype[]>([]);
  const [expandedMember, setExpandedMember] = useState<string | null>(null);

  useEffect(() => {
    fetchArchetypes();
    // Initialize with one default chair member if empty
    if (members.length === 0) {
      addDefaultChair();
    }
  }, []);

  const fetchArchetypes = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/archetypes');
      const data = await response.json();
      setArchetypes(data.archetypes || []);
    } catch (error) {
      console.error('Failed to fetch archetypes:', error);
    }
  };

  const addDefaultChair = () => {
    // Find first configured provider
    const configuredProvider = providers.find(p => p.configured);
    if (!configuredProvider) return;

    const chairMember: CouncilMember = {
      id: generateId(),
      provider: configuredProvider.name,
      model: configuredProvider.default_model,
      role: 'Chair',
      archetype: 'balanced',
      is_chair: true,
    };

    onMembersChange([chairMember]);
    setExpandedMember(chairMember.id);
  };

  const addMember = () => {
    const configuredProvider = providers.find(p => p.configured);
    if (!configuredProvider) return;

    const newMember: CouncilMember = {
      id: generateId(),
      provider: configuredProvider.name,
      model: configuredProvider.default_model,
      role: 'Council Member',
      archetype: 'balanced',
      is_chair: false,
    };

    onMembersChange([...members, newMember]);
    setExpandedMember(newMember.id);
  };

  const removeMember = (id: string) => {
    const member = members.find(m => m.id === id);
    if (member?.is_chair && members.length > 1) {
      // If removing chair, assign to first remaining member
      const updatedMembers = members.filter(m => m.id !== id);
      updatedMembers[0].is_chair = true;
      onMembersChange(updatedMembers);
    } else {
      onMembersChange(members.filter(m => m.id !== id));
    }
  };

  const updateMember = (id: string, updates: Partial<CouncilMember>) => {
    onMembersChange(
      members.map(m => (m.id === id ? { ...m, ...updates } : m))
    );
  };

  const setChair = (id: string) => {
    onMembersChange(
      members.map(m => ({ ...m, is_chair: m.id === id }))
    );
  };

  const getProviderInfo = (providerName: string) => {
    return providers.find(p => p.name === providerName);
  };

  const getArchetypeInfo = (archetypeId: string) => {
    return archetypes.find(a => a.id === archetypeId);
  };

  return (
    <div className="council-member-editor">
      <div className="editor-header">
        <h3>Council Members</h3>
        <button
          type="button"
          onClick={addMember}
          className="btn-add-member"
          disabled={!providers.some(p => p.configured)}
        >
          + Add Member
        </button>
      </div>

      <div className="members-list">
        {members.map((member) => {
          const providerInfo = getProviderInfo(member.provider);
          const archetypeInfo = getArchetypeInfo(member.archetype);
          const isExpanded = expandedMember === member.id;

          return (
            <div
              key={member.id}
              className={`member-card ${member.is_chair ? 'chair' : ''} ${isExpanded ? 'expanded' : ''}`}
            >
              <div className="member-header" onClick={() => setExpandedMember(isExpanded ? null : member.id)}>
                <div className="member-summary">
                  <div className="member-icon">
                    {archetypeInfo?.emoji || '👤'}
                  </div>
                  <div className="member-info">
                    <div className="member-title">
                      <strong>{member.role}</strong>
                      {member.is_chair && <span className="chair-badge">★ Chair</span>}
                    </div>
                    <div className="member-subtitle">
                      {archetypeInfo?.name || 'Balanced'} • {providerInfo?.displayName || member.provider}
                    </div>
                  </div>
                </div>
                <div className="member-actions" onClick={(e) => e.stopPropagation()}>
                  <button
                    type="button"
                    onClick={() => setExpandedMember(isExpanded ? null : member.id)}
                    className="btn-icon"
                    title={isExpanded ? 'Collapse' : 'Expand'}
                  >
                    {isExpanded ? '▼' : '▶'}
                  </button>
                  <button
                    type="button"
                    onClick={() => removeMember(member.id)}
                    className="btn-icon btn-remove"
                    title="Remove member"
                    disabled={members.length === 1}
                  >
                    ×
                  </button>
                </div>
              </div>

              {isExpanded && (
                <div className="member-details">
                  <div className="form-group">
                    <label htmlFor={`role-${member.id}`}>Role / Display Name</label>
                    <input
                      id={`role-${member.id}`}
                      type="text"
                      value={member.role}
                      onChange={(e) => updateMember(member.id, { role: e.target.value })}
                      placeholder="e.g., Technical Expert, Devil's Advocate"
                      className="form-input"
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor={`provider-${member.id}`}>Provider</label>
                    <select
                      id={`provider-${member.id}`}
                      value={member.provider}
                      onChange={(e) => {
                        const newProvider = providers.find(p => p.name === e.target.value);
                        updateMember(member.id, {
                          provider: e.target.value,
                          model: newProvider?.default_model || '',
                        });
                      }}
                      className="form-select"
                    >
                      {providers.filter(p => p.configured).map((provider) => (
                        <option key={provider.name} value={provider.name}>
                          {provider.displayName}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor={`model-${member.id}`}>Model</label>
                    <select
                      id={`model-${member.id}`}
                      value={member.model}
                      onChange={(e) => updateMember(member.id, { model: e.target.value })}
                      className="form-select"
                    >
                      {providerInfo?.available_models?.map((model: string) => (
                        <option key={model} value={model}>
                          {model}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor={`archetype-${member.id}`}>
                      Personality Archetype
                      <span className="label-hint">Defines the member's perspective and role</span>
                    </label>
                    <select
                      id={`archetype-${member.id}`}
                      value={member.archetype}
                      onChange={(e) => updateMember(member.id, { archetype: e.target.value })}
                      className="form-select"
                    >
                      {archetypes.map((archetype) => (
                        <option key={archetype.id} value={archetype.id}>
                          {archetype.emoji} {archetype.name}
                        </option>
                      ))}
                    </select>
                    {archetypeInfo && (
                      <div className="archetype-description">
                        {archetypeInfo.description}
                      </div>
                    )}
                  </div>

                  <div className="form-group">
                    <label htmlFor={`personality-${member.id}`}>
                      Custom Personality
                      <span className="label-hint">Optional: Add specific instructions or personality traits</span>
                    </label>
                    <textarea
                      id={`personality-${member.id}`}
                      value={member.custom_personality || ''}
                      onChange={(e) => updateMember(member.id, { custom_personality: e.target.value })}
                      placeholder="e.g., Focus on cost-effectiveness, Be skeptical of new technologies, Prioritize user experience..."
                      className="form-textarea"
                      rows={3}
                    />
                  </div>

                  <div className="form-group">
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={member.is_chair}
                        onChange={() => setChair(member.id)}
                        disabled={member.is_chair}
                      />
                      <span>Chair (synthesizes and leads final decisions)</span>
                    </label>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {members.length === 0 && (
        <div className="empty-state">
          <p>No council members yet. Add your first member to get started!</p>
        </div>
      )}

      <style>{`
        .council-member-editor {
          margin: 1.5rem 0;
        }

        .editor-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
        }

        .editor-header h3 {
          margin: 0;
          font-size: 1.1rem;
          color: #e0e0e0;
        }

        .btn-add-member {
          padding: 0.5rem 1rem;
          background: #4a9eff;
          border: none;
          color: #000;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 600;
          font-size: 0.875rem;
          transition: all 0.2s;
        }

        .btn-add-member:hover:not(:disabled) {
          background: #6bb0ff;
          transform: translateY(-1px);
        }

        .btn-add-member:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .members-list {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .member-card {
          background: #1e1e1e;
          border: 2px solid #333;
          border-radius: 8px;
          overflow: hidden;
          transition: all 0.2s;
        }

        .member-card.chair {
          border-color: #f59e0b;
        }

        .member-card.expanded {
          border-color: #4a9eff;
        }

        .member-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1rem;
          cursor: pointer;
          user-select: none;
        }

        .member-header:hover {
          background: rgba(74, 158, 255, 0.05);
        }

        .member-summary {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          flex: 1;
        }

        .member-icon {
          font-size: 2rem;
          width: 48px;
          height: 48px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(74, 158, 255, 0.1);
          border-radius: 50%;
        }

        .member-info {
          flex: 1;
        }

        .member-title {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 1rem;
          color: #e0e0e0;
          margin-bottom: 0.25rem;
        }

        .member-subtitle {
          font-size: 0.875rem;
          color: #999;
        }

        .chair-badge {
          background: #f59e0b;
          color: #000;
          padding: 0.125rem 0.5rem;
          border-radius: 12px;
          font-size: 0.75rem;
          font-weight: 600;
        }

        .member-actions {
          display: flex;
          gap: 0.5rem;
        }

        .btn-icon {
          background: none;
          border: none;
          color: #999;
          cursor: pointer;
          font-size: 1.25rem;
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          transition: all 0.2s;
        }

        .btn-icon:hover:not(:disabled) {
          background: rgba(74, 158, 255, 0.1);
          color: #4a9eff;
        }

        .btn-icon.btn-remove:hover:not(:disabled) {
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
        }

        .btn-icon:disabled {
          opacity: 0.3;
          cursor: not-allowed;
        }

        .member-details {
          padding: 0 1rem 1rem 1rem;
          border-top: 1px solid #333;
          animation: slideDown 0.2s ease;
        }

        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .form-group {
          margin-top: 1rem;
        }

        .form-group label {
          display: block;
          margin-bottom: 0.5rem;
          font-size: 0.875rem;
          font-weight: 500;
          color: #e0e0e0;
        }

        .label-hint {
          display: block;
          font-weight: 400;
          color: #999;
          font-size: 0.8125rem;
          margin-top: 0.125rem;
        }

        .form-input,
        .form-select,
        .form-textarea {
          width: 100%;
          padding: 0.625rem;
          background: #2a2a2a;
          border: 1px solid #444;
          color: #e0e0e0;
          border-radius: 6px;
          font-size: 0.875rem;
          transition: border-color 0.2s;
        }

        .form-input:focus,
        .form-select:focus,
        .form-textarea:focus {
          outline: none;
          border-color: #4a9eff;
        }

        .form-textarea {
          resize: vertical;
          font-family: inherit;
        }

        .archetype-description {
          margin-top: 0.5rem;
          padding: 0.5rem;
          background: rgba(74, 158, 255, 0.05);
          border-left: 3px solid #4a9eff;
          font-size: 0.8125rem;
          color: #b3d4ff;
          border-radius: 0 4px 4px 0;
        }

        .checkbox-label {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          cursor: pointer;
          user-select: none;
        }

        .checkbox-label input[type="checkbox"] {
          width: 18px;
          height: 18px;
          cursor: pointer;
        }

        .checkbox-label input[type="checkbox"]:disabled {
          cursor: not-allowed;
        }

        .empty-state {
          padding: 3rem 2rem;
          text-align: center;
          color: #999;
          background: #1e1e1e;
          border: 2px dashed #333;
          border-radius: 8px;
        }
      `}</style>
    </div>
  );
}
