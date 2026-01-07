import { useState } from "react";
import { Sidebar } from "../chat/sidebar";
import { CommandPalette } from "../command-palette";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { ScrollArea } from "../ui/scroll-area";
import { Search, Plus, ChevronDown } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Label } from "../ui/label";
import { type Project } from "../../data/projects";
import { toast } from "sonner";

interface Chat {
  id: string;
  title: string;
  starred?: boolean;
  projectId?: string;
  projectName?: string;
  lastModified?: number;
}

interface ProjectsScreenProps {
  onProjectSelect?: (projectId: string) => void;
  onNewProject?: () => void;
  onLibraryClick?: (libraryType: "videos" | "audio" | "transcripts" | "pdfs") => void;
  onProjectsClick?: () => void;
  onLibraryHeaderClick?: () => void;
  onNewChat?: () => void;
  allChats?: Chat[];
  setAllChats?: React.Dispatch<React.SetStateAction<Chat[]>>;
  onChatSelect?: (chatId: string) => void;
  currentChatId?: string;
  allProjects?: Project[];
  setAllProjects?: React.Dispatch<React.SetStateAction<Project[]>>;
}

export function ProjectsScreen({ 
  onProjectSelect, 
  onNewProject,
  onLibraryClick,
  onProjectsClick,
  onLibraryHeaderClick,
  onNewChat,
  allChats = [],
  setAllChats,
  onChatSelect,
  currentChatId,
  allProjects = [],
  setAllProjects,
}: ProjectsScreenProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeTab, setActiveTab] = useState<"your" | "archived">("your");
  const [sortBy, setSortBy] = useState<"activity" | "name" | "created">("activity");
  const [searchQuery, setSearchQuery] = useState("");
  const [newProjectDialogOpen, setNewProjectDialogOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");

  const projects: Project[] = allProjects;

  const filteredProjects = projects.filter(project =>
    project.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Sort projects based on selected sort option
  const sortedProjects = [...filteredProjects].sort((a, b) => {
    if (sortBy === "name") {
      return a.name.localeCompare(b.name);
    } else if (sortBy === "created") {
      return b.createdAt - a.createdAt; // Most recent first
    } else {
      // activity
      return b.updatedAt - a.updatedAt; // Most recent activity first
    }
  });

  const handleNewProjectClick = () => {
    setNewProjectDialogOpen(true);
  };

  const handleCreateProject = () => {
    if (newProjectName.trim()) {
      console.log("Creating project:", newProjectName);
      // In a real app, this would create the project in the backend
      setNewProjectDialogOpen(false);
      setNewProjectName("");
      onNewProject?.();
      if (setAllProjects) {
        setAllProjects(prev => [...prev, {
          id: Date.now().toString(),
          name: newProjectName,
          createdAt: Date.now(),
          updatedAt: Date.now(),
          updatedAtLabel: "just now",
        }]);
      }
    }
  };

  const handleChatStar = (chatId: string) => {
    if (setAllChats) {
      setAllChats(prev => prev.map(chat => 
        chat.id === chatId ? { ...chat, starred: !chat.starred, lastModified: Date.now() } : chat
      ));
    }
  };

  const handleChatRename = (chatId: string, newTitle: string) => {
    if (setAllChats) {
      setAllChats(prev => prev.map(chat => 
        chat.id === chatId ? { ...chat, title: newTitle, lastModified: Date.now() } : chat
      ));
    }
  };

  const handleChatAddToProject = (chatId: string, projectName: string) => {
    if (setAllChats) {
      // Map project names to IDs
      const projectNameToId: Record<string, string> = {
        "Product Launch": "1",
        "Marketing Campaign": "2",
        "Research & Development": "3",
      };
      
      const newProjectId = projectNameToId[projectName];
      
      setAllChats(prev => prev.map(chat => 
        chat.id === chatId 
          ? { ...chat, projectId: newProjectId, projectName, lastModified: Date.now() } 
          : chat
      ));
    }
  };

  const handleChatRemoveFromProject = (chatId: string) => {
    if (setAllChats) {
      setAllChats(prev => prev.map(chat => 
        chat.id === chatId 
          ? { ...chat, projectId: undefined, projectName: undefined, lastModified: Date.now() } 
          : chat
      ));
    }
  };

  const handleChatDelete = (chatId: string) => {
    if (setAllChats) {
      setAllChats(prev => prev.filter(chat => chat.id !== chatId));
    }
  };

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <CommandPalette />
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        onNewChat={onNewChat}
        recentChats={[...allChats].sort((a, b) => {
          const aTime = a.lastModified || 0;
          const bTime = b.lastModified || 0;
          return bTime - aTime;
        }).map(chat => ({ 
          id: chat.id, 
          title: chat.title,
          starred: chat.starred 
        }))}
        onChatSelect={onChatSelect}
        currentChatId={currentChatId}
        onChatStar={handleChatStar}
        onChatRename={handleChatRename}
        onChatAddToProject={handleChatAddToProject}
        onChatRemoveFromProject={handleChatRemoveFromProject}
        onChatDelete={handleChatDelete}
        onProjectClick={onProjectSelect}
        onLibraryClick={onLibraryClick}
        onProjectsClick={onProjectsClick}
        onLibraryHeaderClick={onLibraryHeaderClick}
        allChats={allChats}
      />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="px-12 py-8 border-b border-border">
          <div className="max-w-5xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <h1 className="text-xl font-semibold">Projects</h1>
              <Button onClick={handleNewProjectClick} className="text-[12px]">
                <Plus className="mr-2 h-4 w-4" />
                New project
              </Button>
            </div>

            {/* Search */}
            <div className="relative mb-6">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search projects..."
                className="pl-10 text-[12px]"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            {/* Tabs and Sort */}
            <div className="flex items-center justify-between">
              <div className="flex gap-6">
                <button
                  onClick={() => setActiveTab("your")}
                  className={`pb-2 text-[12px] transition-colors relative ${
                    activeTab === "your"
                      ? "text-foreground font-medium"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Your projects
                  {activeTab === "your" && (
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                  )}
                </button>
                <button
                  onClick={() => setActiveTab("archived")}
                  className={`pb-2 text-[12px] transition-colors relative ${
                    activeTab === "archived"
                      ? "text-foreground font-medium"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Archived
                  {activeTab === "archived" && (
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                  )}
                </button>
              </div>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm" className="text-[12px]">
                    Sort by{" "}
                    <span className="ml-1 font-medium">
                      {sortBy === "activity" && "Activity"}
                      {sortBy === "name" && "Name"}
                      {sortBy === "created" && "Created"}
                    </span>
                    <ChevronDown className="ml-2 h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => setSortBy("activity")} className="text-[12px]">
                    Activity
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setSortBy("name")} className="text-[12px]">
                    Name
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setSortBy("created")} className="text-[12px]">
                    Created
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>

        {/* Projects Grid */}
        <ScrollArea className="flex-1">
          <div className="px-12 py-8">
            <div className="max-w-5xl mx-auto">
              {activeTab === "your" ? (
                <div className="grid grid-cols-2 gap-4">
                  {sortedProjects.map((project) => (
                    <button
                      key={project.id}
                      onClick={() => onProjectSelect?.(project.id)}
                      className="p-6 border border-border rounded-lg hover:border-primary/50 hover:bg-accent/50 transition-all text-left"
                    >
                      <h3 className="font-medium mb-2 text-[12px]">{project.name}</h3>
                      <p className="text-[12px] text-muted-foreground">
                        Updated {project.updatedAtLabel}
                      </p>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-muted-foreground text-[12px]">
                  No archived projects
                </div>
              )}
            </div>
          </div>
        </ScrollArea>
      </div>

      {/* New Project Dialog */}
      <Dialog open={newProjectDialogOpen} onOpenChange={setNewProjectDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>New Project</DialogTitle>
            <DialogDescription>
              Create a new project to organize your chats and resources.
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col space-y-4">
            <Label htmlFor="name">Project Name</Label>
            <Input
              id="name"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              placeholder="Enter project name"
              className="text-[12px]"
            />
          </div>
          <DialogFooter>
            <Button
              type="button"
              onClick={handleCreateProject}
              className="text-[12px]"
            >
              Create Project
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}