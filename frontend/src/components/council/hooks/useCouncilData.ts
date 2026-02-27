/**
 * Hook for fetching council-related data (archetypes, RAM info, templates)
 */
import { useState, useEffect, useRef } from 'react';
import toast from 'react-hot-toast';
import { API_URLS } from '@/lib/config';
import type { PersonalityArchetype } from '@/types';
import type { ModelRAMInfo } from '../utils/council-helpers';

interface ModelData {
  name: string;
  ram_required: number;
  can_run: boolean;
}

export interface CouncilTemplate {
  id: string;
  name: string;
  description?: string;
  members: import('@/types').CouncilMember[];
  created_at?: string;
  updated_at?: string;
}

interface UseCouncilDataReturn {
  archetypes: PersonalityArchetype[];
  modelRAMInfo: ModelRAMInfo;
  templates: CouncilTemplate[];
  fetchTemplates: () => Promise<void>;
  saveTemplate: (name: string, description: string, members: import('@/types').CouncilMember[]) => Promise<boolean>;
  deleteTemplate: (templateId: string, templateName: string) => Promise<boolean>;
}

export function useCouncilData(): UseCouncilDataReturn {
  const [archetypes, setArchetypes] = useState<PersonalityArchetype[]>([]);
  const [modelRAMInfo, setModelRAMInfo] = useState<ModelRAMInfo>({});
  const [templates, setTemplates] = useState<CouncilTemplate[]>([]);
  const hasShownError = useRef(false);

  const fetchTemplates = async () => {
    try {
      const response = await fetch(API_URLS.templates);
      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      }
    } catch {
      // Silently fail - templates are optional
    }
  };

  const saveTemplate = async (
    name: string,
    description: string,
    members: import('@/types').CouncilMember[]
  ): Promise<boolean> => {
    if (!name.trim()) {
      toast.error('Please enter a template name');
      return false;
    }

    if (members.length === 0) {
      toast.error('Cannot save empty council');
      return false;
    }

    try {
      const response = await fetch(API_URLS.templates, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name.trim(),
          description: description.trim() || null,
          members: members,
        }),
      });

      if (response.ok) {
        await fetchTemplates();
        toast.success('Template saved successfully!');
        return true;
      }
      return false;
    } catch {
      toast.error('Failed to save template');
      return false;
    }
  };

  const deleteTemplate = async (templateId: string, _templateName: string): Promise<boolean> => {
    try {
      const response = await fetch(`${API_URLS.templates}/${templateId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        await fetchTemplates();
        toast.success('Template deleted');
        return true;
      }
      return false;
    } catch {
      toast.error('Failed to delete template');
      return false;
    }
  };

  useEffect(() => {
    let isMounted = true;

    const loadData = async () => {
      // Fire all three requests in parallel
      const [archetypesResult, ramResult, templatesResult] = await Promise.allSettled([
        fetch(API_URLS.archetypes),
        fetch(API_URLS.systemRamStatus),
        fetch(API_URLS.templates),
      ]);

      if (!isMounted) return;

      // Archetypes
      if (archetypesResult.status === 'fulfilled' && archetypesResult.value.ok) {
        try {
          const data = await archetypesResult.value.json();
          if (isMounted) setArchetypes(data.archetypes || []);
        } catch (error) {
          console.error('Failed to parse archetypes:', error);
          if (!hasShownError.current) {
            hasShownError.current = true;
            toast.error('Failed to load personality archetypes');
          }
        }
      } else if (archetypesResult.status === 'rejected' || !archetypesResult.value?.ok) {
        console.error('Failed to load archetypes');
        if (!hasShownError.current) {
          hasShownError.current = true;
          toast.error('Failed to load personality archetypes');
        }
      }

      // RAM info (optional)
      if (ramResult.status === 'fulfilled' && ramResult.value.ok) {
        try {
          const data = await ramResult.value.json();
          if (isMounted) {
            const ramMap: ModelRAMInfo = {};
            data.all_models?.forEach((model: ModelData) => {
              ramMap[model.name] = { ram_required: model.ram_required, can_run: model.can_run };
            });
            setModelRAMInfo(ramMap);
          }
        } catch {
          // Silently fail - RAM info is optional
        }
      }

      // Templates (optional)
      if (templatesResult.status === 'fulfilled' && templatesResult.value.ok) {
        try {
          const data = await templatesResult.value.json();
          if (isMounted) setTemplates(data);
        } catch {
          // Silently fail - templates are optional
        }
      }
    };

    loadData();

    return () => {
      isMounted = false;
    };
  }, []);

  return {
    archetypes,
    modelRAMInfo,
    templates,
    fetchTemplates,
    saveTemplate,
    deleteTemplate,
  };
}
