// Single source of truth for project data

export interface Project {
  id: string;
  name: string;
  createdAt: number; // timestamp
  updatedAt: number; // timestamp for activity sorting
  updatedAtLabel: string; // human-readable label
}

// Central project data - all components reference this
export const PROJECTS: Project[] = [
  { 
    id: "1", 
    name: "Product Launch", 
    createdAt: Date.now() - 21 * 60 * 60 * 1000,
    updatedAt: Date.now() - 21 * 60 * 60 * 1000,
    updatedAtLabel: "21 hours ago"
  },
  { 
    id: "2", 
    name: "Marketing Campaign", 
    createdAt: Date.now() - 23 * 60 * 60 * 1000,
    updatedAt: Date.now() - 23 * 60 * 60 * 1000,
    updatedAtLabel: "23 hours ago"
  },
  { 
    id: "3", 
    name: "Research & Development", 
    createdAt: Date.now() - 2 * 24 * 60 * 60 * 1000,
    updatedAt: Date.now() - 2 * 24 * 60 * 60 * 1000,
    updatedAtLabel: "2 days ago"
  },
  { 
    id: "4", 
    name: "Customer Feedback Analysis", 
    createdAt: Date.now() - 3 * 24 * 60 * 60 * 1000,
    updatedAt: Date.now() - 3 * 24 * 60 * 60 * 1000,
    updatedAtLabel: "3 days ago"
  },
  { 
    id: "5", 
    name: "Q4 Planning", 
    createdAt: Date.now() - 7 * 24 * 60 * 60 * 1000,
    updatedAt: Date.now() - 7 * 24 * 60 * 60 * 1000,
    updatedAtLabel: "1 week ago"
  },
  { 
    id: "6", 
    name: "Brand Redesign", 
    createdAt: Date.now() - 14 * 24 * 60 * 60 * 1000,
    updatedAt: Date.now() - 14 * 24 * 60 * 60 * 1000,
    updatedAtLabel: "2 weeks ago"
  },
];

// Helper functions
export const getProjectById = (id: string): Project | undefined => {
  return PROJECTS.find(p => p.id === id);
};

export const getProjectName = (id: string): string => {
  return getProjectById(id)?.name || "Unknown Project";
};

export const getProjectIdByName = (name: string): string | undefined => {
  return PROJECTS.find(p => p.name === name)?.id;
};

export const getProjectChatCount = (projectId: string, allChats: Array<{ projectId?: string }>): number => {
  return allChats.filter(chat => chat.projectId === projectId).length;
};
