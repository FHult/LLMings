/**
 * Template dialogs for saving and loading council configurations
 */
import { useState, useEffect } from 'react';
import type { CouncilTemplate } from './hooks/useCouncilData';

interface SaveTemplateDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (name: string, description: string) => Promise<boolean>;
}

export function SaveTemplateDialog({ isOpen, onClose, onSave }: SaveTemplateDialogProps) {
  const [templateName, setTemplateName] = useState('');
  const [templateDescription, setTemplateDescription] = useState('');

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handleClose();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = async () => {
    const success = await onSave(templateName, templateDescription);
    if (success) {
      setTemplateName('');
      setTemplateDescription('');
      onClose();
    }
  };

  const handleClose = () => {
    setTemplateName('');
    setTemplateDescription('');
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={handleClose}>
      {/* Enter key submits the form */}
      <form
        className="modal-dialog"
        onClick={(e) => e.stopPropagation()}
        onSubmit={(e) => { e.preventDefault(); handleSave(); }}
      >
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
          <button type="button" onClick={handleClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" className="btn-primary">
            Save Template
          </button>
        </div>
      </form>
    </div>
  );
}

interface LoadTemplateDialogProps {
  isOpen: boolean;
  onClose: () => void;
  templates: CouncilTemplate[];
  onLoad: (template: CouncilTemplate) => void;
  onDelete: (templateId: string, templateName: string) => Promise<boolean>;
}

export function LoadTemplateDialog({
  isOpen,
  onClose,
  templates,
  onLoad,
  onDelete,
}: LoadTemplateDialogProps) {
  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
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
                    onClick={() => onLoad(template)}
                    className="btn-load"
                  >
                    Load
                  </button>
                  <button
                    onClick={() => onDelete(template.id, template.name)}
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
          <button onClick={onClose} className="btn-secondary">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
