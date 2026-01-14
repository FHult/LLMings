import React, { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import type { CouncilMember, PersonalityArchetype, Provider } from '../types';
import { API_URLS } from '../lib/config';

interface CouncilMemberEditorProps {
  members: CouncilMember[];
  onMembersChange: (members: CouncilMember[]) => void;
  providers: Provider[];
}

const generateId = () => `member_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

const PROVIDER_DISPLAY_NAMES: Record<string, string> = {
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  google: 'Google Gemini',
  grok: 'Grok',
  ollama: 'Ollama',
};

const getProviderDisplayName = (providerName: string) => {
  return PROVIDER_DISPLAY_NAMES[providerName] || providerName;
};

interface ModelRAMInfo {
  [modelName: string]: {
    ram_required: number;
    can_run: boolean;
  };
}

interface CouncilTemplate {
  id: string;
  name: string;
  description?: string;
  members: CouncilMember[];
  created_at?: string;
  updated_at?: string;
}

export default function CouncilMemberEditor({
  members,
  onMembersChange,
  providers,
}: CouncilMemberEditorProps) {
  const [archetypes, setArchetypes] = useState<PersonalityArchetype[]>([]);
  const [expandedMember, setExpandedMember] = useState<string | null>(null);
  const [modelRAMInfo, setModelRAMInfo] = useState<ModelRAMInfo>({});
  const [templates, setTemplates] = useState<CouncilTemplate[]>([]);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [showLoadDialog, setShowLoadDialog] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [templateDescription, setTemplateDescription] = useState('');

  const fetchArchetypes = async () => {
    try {
      const response = await fetch(API_URLS.archetypes);
      const data = await response.json();
      setArchetypes(data.archetypes || []);
    } catch (error) {
      console.error('Failed to fetch archetypes:', error);
      toast.error('Failed to load personality archetypes');
    }
  };

  const fetchRAMInfo = async () => {
    try {
      const response = await fetch(API_URLS.systemRamStatus);
      if (response.ok) {
        const data = await response.json();
        // Build a map of model name -> RAM info using all_models (not just recommended)
        const ramMap: ModelRAMInfo = {};
        data.all_models?.forEach((model: any) => {
          ramMap[model.name] = {
            ram_required: model.ram_required,
            can_run: model.can_run,
          };
        });
        setModelRAMInfo(ramMap);
      }
    } catch (error) {
      console.error('Failed to fetch RAM info:', error);
    }
  };

  const addDefaultChair = useCallback(() => {
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
  }, [providers, onMembersChange]);

  useEffect(() => {
    fetchArchetypes();
    fetchRAMInfo();
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await fetch('API_URLS.templates');
      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      }
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    }
  };

  const saveTemplate = async () => {
    if (!templateName.trim()) {
      toast.error('Please enter a template name');
      return;
    }

    if (members.length === 0) {
      toast.error('Cannot save empty council');
      return;
    }

    try {
      const response = await fetch('API_URLS.templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: templateName.trim(),
          description: templateDescription.trim() || null,
          members: members,
        }),
      });

      if (response.ok) {
        setTemplateName('');
        setTemplateDescription('');
        setShowSaveDialog(false);
        fetchTemplates();
        toast.success('Template saved successfully!');
      }
    } catch (error) {
      console.error('Failed to save template:', error);
      toast.error('Failed to save template');
    }
  };

  const loadTemplate = (template: CouncilTemplate) => {
    onMembersChange(template.members);
    setShowLoadDialog(false);
    toast.success(`Loaded template: ${template.name}`);
  };

  const deleteTemplate = async (templateId: string, templateName: string) => {
    if (!confirm(`Delete template "${templateName}"?`)) {
      return;
    }

    try {
      const response = await fetch(`API_URLS.templates/${templateId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        fetchTemplates();
        toast.success('Template deleted');
      }
    } catch (error) {
      console.error('Failed to delete template:', error);
      toast.error('Failed to delete template');
    }
  };

  useEffect(() => {
    // Initialize with one default chair member if empty and providers are loaded
    if (members.length === 0 && providers.length > 0 && providers.some(p => p.configured)) {
      addDefaultChair();
    }
  }, [providers, members.length, addDefaultChair]);

  const addMember = () => {
    const configuredProvider = providers.find(p => p.configured);
    if (!configuredProvider) return;

    // Generate default name based on number of members
    const memberNumber = members.length + 1;
    const defaultRole = `Member ${memberNumber}`;

    const newMember: CouncilMember = {
      id: generateId(),
      provider: configuredProvider.name,
      model: configuredProvider.default_model,
      role: defaultRole,
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

  const updateMemberArchetype = (id: string, newArchetype: string) => {
    const member = members.find(m => m.id === id);
    if (!member) return;

    // Get recommended models for this archetype
    const recommendedModels = getRecommendedModelsForArchetype(newArchetype);

    // Auto-select first recommended model if using Ollama and a recommended model is available
    let modelUpdate = {};
    if (member.provider === 'ollama' && recommendedModels.length > 0) {
      const providerInfo = getProviderInfo(member.provider);
      const availableModels = providerInfo?.available_models || [];

      // Find first recommended model that's actually available
      const preferredModel = recommendedModels.find(rec =>
        availableModels.some(avail => avail.includes(rec) || rec.includes(avail))
      );

      if (preferredModel) {
        // Try to find exact match in available models
        const exactMatch = availableModels.find(avail => avail.includes(preferredModel));
        if (exactMatch) {
          modelUpdate = { model: exactMatch };
        }
      }
    }

    updateMember(id, { archetype: newArchetype, ...modelUpdate });
  };

  const setChair = (id: string, isChair: boolean) => {
    onMembersChange(
      members.map(m => {
        if (m.id === id) {
          // Auto-populate role name when toggling chair status
          const newRole = isChair ? 'Chair' : `Council Member ${members.filter(x => !x.is_chair).length}`;
          return { ...m, is_chair: isChair, role: newRole };
        }
        // Unset chair for other members if setting this one as chair
        return { ...m, is_chair: isChair ? false : m.is_chair };
      })
    );
  };

  // Recommended archetypes for chair role
  const CHAIR_RECOMMENDED_ARCHETYPES = ['synthesizer', 'strategist', 'balanced', 'analyst'];

  const getProviderInfo = (providerName: string) => {
    return providers.find(p => p.name === providerName);
  };

  const getArchetypeInfo = (archetypeId: string) => {
    return archetypes.find(a => a.id === archetypeId);
  };

  const getModelRAM = (provider: string, model: string) => {
    if (provider !== 'ollama') return null;

    // Try exact match first
    if (modelRAMInfo[model]) {
      return modelRAMInfo[model];
    }

    // Try matching by base model name (before colon)
    // e.g., "llama3.1:latest" -> "llama3.1"
    const baseModel = model.split(':')[0];
    if (modelRAMInfo[baseModel]) {
      return modelRAMInfo[baseModel];
    }

    // Try fuzzy matching - check if any known model is a substring or vice versa
    for (const knownModel in modelRAMInfo) {
      if (model.includes(knownModel) || knownModel.includes(baseModel)) {
        return modelRAMInfo[knownModel];
      }
    }

    return null;
  };

  const getRecommendedModelsForArchetype = (archetypeId: string): string[] => {
    const archetype = archetypes.find(a => a.id === archetypeId);
    return archetype?.recommended_models || [];
  };

  return (
    <div className="council-member-editor">
      <div className="editor-header">
        <h3>Council Members</h3>
        <div className="template-buttons">
          <button
            type="button"
            onClick={() => setShowLoadDialog(true)}
            className="btn-template"
            disabled={templates.length === 0}
          >
            📁 Load Team
          </button>
          <button
            type="button"
            onClick={() => setShowSaveDialog(true)}
            className="btn-template"
            disabled={members.length === 0}
          >
            💾 Save Team
          </button>
        </div>
      </div>

      <div className="members-list">
        {members.map((member) => {
          const providerInfo = getProviderInfo(member.provider);
          const archetypeInfo = getArchetypeInfo(member.archetype);
          const isExpanded = expandedMember === member.id;
          const ramInfo = getModelRAM(member.provider, member.model);

          return (
            <div
              key={member.id}
              className={`member-card ${member.is_chair ? 'chair' : ''} ${isExpanded ? 'expanded' : ''}`}
            >
              <div className="member-header" onClick={() => setExpandedMember(isExpanded ? null : member.id)}>
                <div className="expand-indicator">
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 16 16"
                    fill="currentColor"
                    style={{
                      transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)',
                      transition: 'transform 0.2s'
                    }}
                  >
                    <path d="M6 4l4 4-4 4V4z" />
                  </svg>
                </div>
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
                      {archetypeInfo?.name || 'Balanced'} • {getProviderDisplayName(member.provider)} • {member.model}
                      {ramInfo && (
                        <span className={`ram-badge ${ramInfo.can_run ? 'ram-ok' : 'ram-warning'}`}>
                          🧠 {ramInfo.ram_required}GB
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="member-actions" onClick={(e) => e.stopPropagation()}>
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
                    <div className="role-header">
                      <label htmlFor={`role-${member.id}`}>Role / Display Name</label>
                      <label className={`chair-checkbox-label ${member.is_chair ? 'checked' : ''}`}>
                        <input
                          type="checkbox"
                          checked={member.is_chair}
                          onChange={(e) => setChair(member.id, e.target.checked)}
                        />
                        <span className="chair-checkbox-text">
                          <span className="chair-icon">★</span>
                          Team Chair
                        </span>
                      </label>
                    </div>
                    <input
                      id={`role-${member.id}`}
                      type="text"
                      value={member.role}
                      onChange={(e) => updateMember(member.id, { role: e.target.value })}
                      placeholder="e.g., Technical Expert, Devil's Advocate"
                      className="form-input"
                    />
                    {member.is_chair && (
                      <div className="chair-recommendations">
                        💡 Recommended personalities for Team Chair:{' '}
                        {CHAIR_RECOMMENDED_ARCHETYPES.map((recId, idx, arr) => {
                          const recArchetype = archetypes.find(a => a.id === recId);
                          return recArchetype ? (
                            <span key={recId}>
                              <strong>{recArchetype.emoji} {recArchetype.name}</strong>
                              {idx < arr.length - 1 ? ', ' : ''}
                            </span>
                          ) : null;
                        })}
                      </div>
                    )}
                  </div>

                  <div className="form-group">
                    <label htmlFor={`archetype-${member.id}`}>
                      Personality Archetype
                      <span className="label-hint">Defines the member's perspective and role</span>
                    </label>
                    <select
                      id={`archetype-${member.id}`}
                      value={member.archetype}
                      onChange={(e) => updateMemberArchetype(member.id, e.target.value)}
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
                    {member.archetype && getRecommendedModelsForArchetype(member.archetype).length > 0 && (
                      <div className="model-recommendations">
                        💡 Recommended models for {archetypeInfo?.name || 'this personality'}:{' '}
                        {getRecommendedModelsForArchetype(member.archetype).map((rec, idx, arr) => (
                          <span key={rec}>
                            <strong>{rec}</strong>
                            {idx < arr.length - 1 ? ', ' : ''}
                          </span>
                        ))}
                      </div>
                    )}
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
                          {getProviderDisplayName(provider.name)}
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
                      {providerInfo?.available_models?.map((model: string) => {
                        const modelRam = getModelRAM(member.provider, model);
                        return (
                          <option key={model} value={model}>
                            {model}
                            {modelRam ? ` (${modelRam.ram_required}GB RAM${!modelRam.can_run ? ' - May not fit' : ''})` : ''}
                          </option>
                        );
                      })}
                    </select>
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

      <button
        type="button"
        onClick={addMember}
        className="btn-add-member"
        disabled={!providers.some(p => p.configured)}
      >
        + Add Member
      </button>

      {/* Save Template Dialog */}
      {showSaveDialog && (
        <div className="modal-overlay" onClick={() => setShowSaveDialog(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Save Council Template</h3>
            <div className="form-group">
              <label>Template Name *</label>
              <input
                type="text"
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
                placeholder="e.g., Technical Review Team"
                className="form-input"
                autoFocus
              />
            </div>
            <div className="form-group">
              <label>Description (Optional)</label>
              <textarea
                value={templateDescription}
                onChange={(e) => setTemplateDescription(e.target.value)}
                placeholder="Describe when to use this council configuration..."
                className="form-textarea"
                rows={3}
              />
            </div>
            <div className="dialog-actions">
              <button onClick={() => setShowSaveDialog(false)} className="btn-secondary">
                Cancel
              </button>
              <button onClick={saveTemplate} className="btn-primary">
                Save Template
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Load Template Dialog */}
      {showLoadDialog && (
        <div className="modal-overlay" onClick={() => setShowLoadDialog(false)}>
          <div className="modal-dialog modal-wide" onClick={(e) => e.stopPropagation()}>
            <h3>Load Council Template</h3>
            {templates.length === 0 ? (
              <p className="empty-message">No templates saved yet</p>
            ) : (
              <div className="templates-list">
                {templates.map((template) => (
                  <div key={template.id} className="template-item">
                    <div className="template-info">
                      <h4>{template.name}</h4>
                      {template.description && <p>{template.description}</p>}
                      <div className="template-meta">
                        {template.members.length} member{template.members.length !== 1 ? 's' : ''}
                      </div>
                    </div>
                    <div className="template-actions">
                      <button
                        onClick={() => loadTemplate(template)}
                        className="btn-load"
                      >
                        Load
                      </button>
                      <button
                        onClick={() => deleteTemplate(template.id, template.name)}
                        className="btn-delete"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <div className="dialog-actions">
              <button onClick={() => setShowLoadDialog(false)} className="btn-secondary">
                Close
              </button>
            </div>
          </div>
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
          gap: 1rem;
        }

        .editor-header h3 {
          margin: 0;
          font-size: 1.1rem;
          color: #1f2937;
          font-weight: 600;
          flex: 1;
        }

        .template-buttons {
          display: flex;
          gap: 0.5rem;
        }

        .btn-template {
          padding: 0.5rem 1rem;
          background: #f3f4f6;
          border: 1px solid #d1d5db;
          color: #374151;
          border-radius: 6px;
          font-size: 0.875rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-template:hover:not(:disabled) {
          background: #e5e7eb;
          border-color: #9ca3af;
        }

        .btn-template:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .btn-add-member {
          width: 100%;
          padding: 0.75rem 1rem;
          margin-top: 0.75rem;
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
          gap: 0.75rem;
        }

        .member-header:hover {
          background: rgba(74, 158, 255, 0.05);
        }

        .expand-indicator {
          display: flex;
          align-items: center;
          justify-content: center;
          color: #999;
          flex-shrink: 0;
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
          display: flex;
          align-items: center;
          gap: 0.5rem;
          flex-wrap: wrap;
        }

        .ram-badge {
          display: inline-flex;
          align-items: center;
          gap: 0.25rem;
          padding: 0.125rem 0.5rem;
          border-radius: 12px;
          font-size: 0.75rem;
          font-weight: 600;
          white-space: nowrap;
        }

        .ram-badge.ram-ok {
          background: rgba(34, 197, 94, 0.15);
          color: #22c55e;
          border: 1px solid rgba(34, 197, 94, 0.3);
        }

        .ram-badge.ram-warning {
          background: rgba(239, 68, 68, 0.15);
          color: #ef4444;
          border: 1px solid rgba(239, 68, 68, 0.3);
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

        .role-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.5rem;
        }

        .role-header > label {
          font-size: 1.0625rem;
          font-weight: 700;
          color: #f0f0f0;
          letter-spacing: 0.015em;
          text-transform: uppercase;
          font-size: 0.875rem;
        }

        .role-header > label:first-child {
          font-size: 1rem;
          text-transform: none;
        }

        .chair-checkbox-label {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          cursor: pointer;
          user-select: none;
          font-size: 0.9375rem;
          font-weight: 600;
          padding: 0.5rem 0.875rem;
          border-radius: 6px;
          transition: all 0.2s;
          background: rgba(245, 158, 11, 0.08);
          border: 2px solid rgba(245, 158, 11, 0.3);
          color: #fbbf24;
          white-space: nowrap;
        }

        .chair-checkbox-label:hover {
          background: rgba(245, 158, 11, 0.15);
          border-color: rgba(245, 158, 11, 0.5);
        }

        .chair-checkbox-label.checked {
          background: rgba(245, 158, 11, 0.2);
          border-color: #f59e0b;
          color: #fde68a;
        }

        .chair-checkbox-label input[type="checkbox"] {
          cursor: pointer;
          width: 18px;
          height: 18px;
          margin: 0;
          accent-color: #f59e0b;
          flex-shrink: 0;
        }

        .chair-checkbox-text {
          display: inline-flex;
          align-items: center;
          gap: 0.375rem;
          line-height: 1;
        }

        .chair-icon {
          font-size: 1.125rem;
          line-height: 1;
        }

        .chair-recommendations {
          margin-top: 0.5rem;
          padding: 0.5rem;
          background: rgba(245, 158, 11, 0.05);
          border-left: 3px solid #f59e0b;
          font-size: 0.8125rem;
          color: #fbbf24;
          border-radius: 0 4px 4px 0;
        }

        .chair-recommendations strong {
          color: #fde68a;
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

        .model-recommendations {
          margin-top: 0.5rem;
          padding: 0.5rem;
          background: rgba(251, 191, 36, 0.05);
          border-left: 3px solid #fbbf24;
          font-size: 0.8125rem;
          color: #fbbf24;
          border-radius: 0 4px 4px 0;
        }

        .model-recommendations strong {
          color: #fde68a;
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

        /* Modal Styles */
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.75);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal-dialog {
          background: #1a1a1a;
          border: 2px solid #333;
          border-radius: 12px;
          padding: 2rem;
          max-width: 500px;
          width: 90%;
          max-height: 80vh;
          overflow-y: auto;
        }

        .modal-dialog.modal-wide {
          max-width: 700px;
        }

        .modal-dialog h3 {
          margin: 0 0 1.5rem 0;
          color: #e0e0e0;
          font-size: 1.25rem;
        }

        .dialog-actions {
          display: flex;
          justify-content: flex-end;
          gap: 0.75rem;
          margin-top: 1.5rem;
        }

        .btn-primary,
        .btn-secondary {
          padding: 0.625rem 1.25rem;
          border-radius: 6px;
          font-size: 0.875rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-primary {
          background: #4a9eff;
          border: 1px solid #4a9eff;
          color: #000;
        }

        .btn-primary:hover {
          background: #6bb0ff;
          border-color: #6bb0ff;
        }

        .btn-secondary {
          background: #333;
          border: 1px solid #555;
          color: #e0e0e0;
        }

        .btn-secondary:hover {
          background: #444;
          border-color: #666;
        }

        .empty-message {
          color: #999;
          text-align: center;
          padding: 2rem;
        }

        .templates-list {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          max-height: 400px;
          overflow-y: auto;
        }

        .template-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1rem;
          background: #2a2a2a;
          border: 1px solid #444;
          border-radius: 8px;
          gap: 1rem;
        }

        .template-info {
          flex: 1;
        }

        .template-info h4 {
          margin: 0 0 0.25rem 0;
          color: #e0e0e0;
          font-size: 1rem;
        }

        .template-info p {
          margin: 0 0 0.5rem 0;
          color: #999;
          font-size: 0.875rem;
        }

        .template-meta {
          font-size: 0.8125rem;
          color: #666;
        }

        .template-actions {
          display: flex;
          gap: 0.5rem;
        }

        .btn-load,
        .btn-delete {
          padding: 0.5rem 1rem;
          border-radius: 6px;
          font-size: 0.875rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-load {
          background: #4a9eff;
          border: 1px solid #4a9eff;
          color: #000;
        }

        .btn-load:hover {
          background: #6bb0ff;
          border-color: #6bb0ff;
        }

        .btn-delete {
          background: transparent;
          border: 1px solid #ef4444;
          color: #ef4444;
        }

        .btn-delete:hover {
          background: rgba(239, 68, 68, 0.1);
        }
      `}</style>
    </div>
  );
}
