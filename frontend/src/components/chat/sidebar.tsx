import { useState, useRef, useEffect } from "react";
import { 
  ChevronLeft, 
  ChevronRight, 
  Plus, 
  Video, 
  Music, 
  FileText, 
  Folder, 
  Star, 
  MoreHorizontal, 
  Trash2, 
  FolderMinus, 
  MessageSquare,
  PanelLeftOpen,
  PanelLeftClose,
  User,
  Settings,
  LogOut,
  Pencil,
  FolderPlus,
  FolderX,
  Search
} from "lucide-react";
import { Button } from "../ui/button";
import { ScrollArea } from "../ui/scroll-area";
import { cn } from "../ui/utils";
import { PROJECTS, getProjectChatCount, getProjectName } from "../../data/projects";
import { getLibraryCount } from "../../data/library-data";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
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
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { SettingsDialog } from "../settings-dialog";

interface SidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  onNewChat: () => void;
  recentChats?: Array<{ id: string; title: string; starred?: boolean }>;
  onChatSelect?: (chatId: string) => void;
  currentChatId?: string;
  onChatStar?: (chatId: string) => void;
  onChatRename?: (chatId: string, newTitle: string) => void;
  onChatAddToProject?: (chatId: string, projectName: string) => void;
  onChatDelete?: (chatId: string) => void;
  onChatRemoveFromProject?: (chatId: string) => void;
  onProjectClick?: (projectId: string) => void;
  onLibraryClick?: (libraryType: "videos" | "audio" | "transcripts" | "pdfs") => void;
  onProjectsClick?: () => void;
  onLibraryHeaderClick?: () => void;
  allChats?: Array<{ id: string; title: string; starred?: boolean; projectId?: string }>;
}

export function Sidebar({ 
  collapsed, 
  onToggleCollapse, 
  onNewChat, 
  recentChats = [], 
  onChatSelect, 
  currentChatId,
  onChatStar,
  onChatRename,
  onChatAddToProject,
  onChatDelete,
  onChatRemoveFromProject,
  onProjectClick,
  onLibraryClick,
  onProjectsClick,
  onLibraryHeaderClick,
  allChats = [],
}: SidebarProps) {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [renameDialogOpen, setRenameDialogOpen] = useState(false);
  const [addToProjectDialogOpen, setAddToProjectDialogOpen] = useState(false);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [selectedProject, setSelectedProject] = useState("");
  const [projectSearchQuery, setProjectSearchQuery] = useState("");

  // Get current project for selected chat
  const currentChatProject = selectedChatId 
    ? allChats.find(c => c.id === selectedChatId)?.projectId
    : null;

  const handleStarChat = (chatId: string) => {
    onChatStar?.(chatId);
  };

  const handleRenameClick = (chatId: string, currentTitle: string) => {
    setSelectedChatId(chatId);
    setRenameValue(currentTitle);
    setRenameDialogOpen(true);
  };

  const handleRenameSubmit = () => {
    if (selectedChatId && renameValue.trim()) {
      onChatRename?.(selectedChatId, renameValue.trim());
      setRenameDialogOpen(false);
      setRenameValue("");
      setSelectedChatId(null);
    }
  };

  const handleAddToProjectClick = (chatId: string) => {
    setSelectedChatId(chatId);
    setSelectedProject("");
    setProjectSearchQuery("");
    setAddToProjectDialogOpen(true);
  };

  const handleAddToProjectSubmit = () => {
    if (selectedChatId && selectedProject) {
      onChatAddToProject?.(selectedChatId, selectedProject);
      setAddToProjectDialogOpen(false);
      setSelectedProject("");
      setProjectSearchQuery("");
      setSelectedChatId(null);
    }
  };

  const handleDeleteChat = (chatId: string) => {
    onChatDelete?.(chatId);
  };

  const handleRemoveFromProject = (chatId: string) => {
    onChatRemoveFromProject?.(chatId);
  };

  const handleProjectDialogClose = (open: boolean) => {
    setAddToProjectDialogOpen(open);
    if (!open) {
      setSelectedProject("");
      setProjectSearchQuery("");
      setSelectedChatId(null);
    }
  };

  if (collapsed) {
    return (
      <div className="w-16 h-screen bg-card border-r border-border flex flex-col items-center gap-2 flex-shrink-0">
        {/* Maintain header height even when collapsed */}
        <div className="h-10 flex items-center justify-center border-b border-border w-full flex-shrink-0">
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleCollapse}
            className="h-6 w-6 p-0"
          >
            <PanelLeftOpen className="h-3.5 w-3.5" />
          </Button>
        </div>
        <div className="p-2 pt-2">
          <Button
            variant="default"
            size="icon"
            onClick={onNewChat}
          >
            <Plus className="h-5 w-5" />
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`h-screen bg-background border-r flex flex-col transition-all duration-300 flex-shrink-0 ${
        collapsed ? "w-12" : "w-64"
      }`}
    >
      {/* Header with logo and toggle - Fixed */}
      <div className="h-10 p-2 border-b flex items-center justify-between flex-shrink-0">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded bg-primary flex items-center justify-center">
              <span className="text-[10px] font-semibold text-primary-foreground">R</span>
            </div>
            <span className="text-[13px] font-semibold">Resonance AI</span>
          </div>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleCollapse}
          className="h-6 w-6 p-0"
        >
          {collapsed ? <PanelLeftOpen className="h-3.5 w-3.5" /> : <PanelLeftClose className="h-3.5 w-3.5" />}
        </Button>
      </div>

      {!collapsed && (
        <>
          {/* New Chat Button - Fixed */}
          <div className="p-2 pt-4 pb-4 flex-shrink-0">
            <Button onClick={onNewChat} className="w-full justify-start gap-2 h-8 text-[12px]">
              <Plus className="h-3.5 w-3.5" />
              New Chat
            </Button>
          </div>

          {/* Scrollable Navigation */}
          <div className="flex-1 overflow-y-auto min-h-0">
            <div className="space-y-4 pb-4 px-3">
              {/* Projects */}
              <div className="space-y-1">
                <button
                  onClick={onProjectsClick}
                  className="w-full flex items-center gap-2 px-2 py-1.5 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider hover:text-foreground active:text-primary transition-colors"
                >
                  PROJECTS
                </button>
                {PROJECTS.map(project => (
                  <button 
                    key={project.id}
                    onClick={() => onProjectClick?.(project.id)}
                    className="w-full flex items-center gap-1.5 px-2 py-1.5 text-[12px] rounded hover:bg-accent active:scale-[0.98] transition-all text-left"
                  >
                    <Folder className="h-4 w-4 text-primary flex-shrink-0" />
                    <span className="truncate flex-1 min-w-0">{project.name}</span>
                    <span className="text-[12px] text-muted-foreground flex-shrink-0 ml-1">{getProjectChatCount(project.id, allChats)}</span>
                  </button>
                ))}
              </div>

              {/* Library */}
              <div className="space-y-1">
                <button
                  onClick={onLibraryHeaderClick}
                  className="w-full flex items-center gap-2 px-2 py-1.5 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider hover:text-foreground active:text-primary transition-colors"
                >
                  LIBRARY
                </button>
                <button 
                  onClick={() => onLibraryClick?.("videos")}
                  className="w-full flex items-center gap-1.5 px-2 py-1.5 text-[12px] rounded hover:bg-accent transition-colors text-left"
                >
                  <Video className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                  <span className="truncate flex-1 min-w-0">Videos</span>
                  <span className="text-[12px] text-muted-foreground flex-shrink-0 ml-1">{getLibraryCount("videos")}</span>
                </button>
                <button 
                  onClick={() => onLibraryClick?.("audio")}
                  className="w-full flex items-center gap-1.5 px-2 py-1.5 text-[12px] rounded hover:bg-accent transition-colors text-left"
                >
                  <Music className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                  <span className="truncate flex-1 min-w-0">Audio</span>
                  <span className="text-[12px] text-muted-foreground flex-shrink-0 ml-1">{getLibraryCount("audio")}</span>
                </button>
                <button 
                  onClick={() => onLibraryClick?.("transcripts")}
                  className="w-full flex items-center gap-1.5 px-2 py-1.5 text-[12px] rounded hover:bg-accent transition-colors text-left"
                >
                  <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                  <span className="truncate flex-1 min-w-0">Transcripts</span>
                  <span className="text-[12px] text-muted-foreground flex-shrink-0 ml-1">{getLibraryCount("transcripts")}</span>
                </button>
                <button 
                  onClick={() => onLibraryClick?.("pdfs")}
                  className="w-full flex items-center gap-1.5 px-2 py-1.5 text-[12px] rounded hover:bg-accent transition-colors text-left"
                >
                  <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                  <span className="truncate flex-1 min-w-0">PDFs</span>
                  <span className="text-[12px] text-muted-foreground flex-shrink-0 ml-1">{getLibraryCount("pdfs")}</span>
                </button>
              </div>

              {/* Recents */}
              {recentChats.length > 0 && (
                <div className="space-y-1">
                  <div className="px-2 py-1.5 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                    RECENTS
                  </div>
                  {recentChats
                    .sort((a, b) => {
                      // Starred items first
                      if (a.starred && !b.starred) return -1;
                      if (!a.starred && b.starred) return 1;
                      return 0;
                    })
                    .map((chat) => {
                    const chatData = allChats.find(c => c.id === chat.id);
                    const hasProject = !!chatData?.projectId;
                    
                    return (
                    <div key={chat.id} className="group relative">
                      <button 
                        onClick={() => onChatSelect?.(chat.id)}
                        className={`w-full flex items-center gap-1.5 px-2 py-1.5 text-[12px] rounded hover:bg-accent transition-colors text-left ${
                          currentChatId === chat.id ? "bg-accent" : ""
                        }`}
                      >
                        {chat.starred && (
                          <Star 
                            className="h-3.5 w-3.5 text-primary fill-primary flex-shrink-0 cursor-pointer" 
                            onClick={(e) => {
                              e.stopPropagation();
                              handleStarChat(chat.id);
                            }}
                          />
                        )}
                        <span className="truncate flex-1 min-w-0 max-w-[180px]">{chat.title}</span>
                      </button>
                      <button
                        className="absolute right-1 top-1/2 -translate-y-1/2 h-6 w-6 flex items-center justify-center rounded hover:bg-muted"
                        onClick={(e) => {
                          e.stopPropagation();
                        }}
                      >
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <div className="h-6 w-6 flex items-center justify-center">
                              <MoreHorizontal className="h-4 w-4" />
                            </div>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-48">
                            <DropdownMenuItem onClick={() => handleStarChat(chat.id)} className="text-[12px]">
                              <Star className={`mr-2 h-4 w-4 ${chat.starred ? 'fill-current' : ''}`} />
                              {chat.starred ? "Unstar" : "Star"}
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleRenameClick(chat.id, chat.title)} className="text-[12px]">
                              <Pencil className="mr-2 h-4 w-4" />
                              Rename
                            </DropdownMenuItem>
                            {hasProject ? (
                              <>
                                <DropdownMenuItem onClick={() => handleAddToProjectClick(chat.id)} className="text-[12px]">
                                  <FolderPlus className="mr-2 h-4 w-4" />
                                  Change project
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleRemoveFromProject(chat.id)} className="text-[12px]">
                                  <FolderX className="mr-2 h-4 w-4" />
                                  Remove from project
                                </DropdownMenuItem>
                              </>
                            ) : (
                              <DropdownMenuItem onClick={() => handleAddToProjectClick(chat.id)} className="text-[12px]">
                                <FolderPlus className="mr-2 h-4 w-4" />
                                Add to project
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuSeparator />
                            <DropdownMenuItem 
                              onClick={() => handleDeleteChat(chat.id)}
                              className="text-destructive focus:text-destructive text-[12px]"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </button>
                    </div>
                  );})}
                </div>
              )}
            </div>
          </div>

          {/* User Menu */}
          <div className="p-3 border-t border-border">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="w-full flex items-center gap-3 px-3 py-2 rounded hover:bg-accent transition-colors text-left">
                  <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                    <User className="h-4 w-4 text-primary-foreground" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-[12px] font-medium truncate">Alex Chen</div>
                    <div className="text-[12px] text-muted-foreground truncate">alex@company.com</div>
                  </div>
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuItem className="text-[12px]">
                  <User className="mr-2 h-4 w-4" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setSettingsOpen(true)} className="text-[12px]">
                  <Settings className="mr-2 h-4 w-4" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-[12px]">
                  <LogOut className="mr-2 h-4 w-4" />
                  Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <SettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen} />

          {/* Rename Dialog */}
          <Dialog open={renameDialogOpen} onOpenChange={setRenameDialogOpen}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Rename chat</DialogTitle>
                <DialogDescription>
                  Enter a new name for this conversation.
                </DialogDescription>
              </DialogHeader>
              <div className="py-4">
                <Label htmlFor="rename-input" className="text-sm">Chat name</Label>
                <Input
                  id="rename-input"
                  value={renameValue}
                  onChange={(e) => setRenameValue(e.target.value)}
                  className="mt-2"
                  placeholder="Enter chat name..."
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      handleRenameSubmit();
                    }
                  }}
                />
              </div>
              <DialogFooter>
                <Button variant="ghost" onClick={() => setRenameDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleRenameSubmit} disabled={!renameValue.trim()}>
                  Rename
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          {/* Add to Project Dialog */}
          <Dialog open={addToProjectDialogOpen} onOpenChange={handleProjectDialogClose}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="text-[12px]">
                  {currentChatProject ? "Move chat" : "Add to project"}
                </DialogTitle>
                <DialogDescription className="text-[12px]">
                  {currentChatProject 
                    ? `This chat is in ${getProjectName(currentChatProject)}. Select a different project to move it to.`
                    : "Select a project to add this conversation to."
                  }
                </DialogDescription>
              </DialogHeader>
              <div className="py-4 space-y-3">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="project-search"
                    value={projectSearchQuery}
                    onChange={(e) => setProjectSearchQuery(e.target.value)}
                    className="pl-9 text-[12px]"
                    placeholder="Search or create a project"
                  />
                </div>
                <div className="space-y-1">
                  {currentChatProject !== "1" && (
                    <button
                      onClick={() => setSelectedProject("Product Launch")}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors text-left ${
                        selectedProject === "Product Launch" 
                          ? "bg-accent" 
                          : "hover:bg-accent"
                      }`}
                    >
                      <Folder className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                      <span className="text-[12px]">Product Launch</span>
                    </button>
                  )}
                  {currentChatProject !== "2" && (
                    <button
                      onClick={() => setSelectedProject("Marketing Campaign")}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors text-left ${
                        selectedProject === "Marketing Campaign" 
                          ? "bg-accent" 
                          : "hover:bg-accent"
                      }`}
                    >
                      <Folder className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                      <span className="text-[12px]">Marketing Campaign</span>
                    </button>
                  )}
                  {currentChatProject !== "3" && (
                    <button
                      onClick={() => setSelectedProject("Research & Development")}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors text-left ${
                        selectedProject === "Research & Development" 
                          ? "bg-accent" 
                          : "hover:bg-accent"
                      }`}
                    >
                      <Folder className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                      <span className="text-[12px]">Research & Development</span>
                    </button>
                  )}
                </div>
              </div>
              <DialogFooter>
                <Button variant="ghost" onClick={() => handleProjectDialogClose(false)} className="text-[12px]">
                  Cancel
                </Button>
                <Button onClick={handleAddToProjectSubmit} disabled={!selectedProject} className="text-[12px]">
                  {currentChatProject ? "Move to Project" : "Add to Project"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </>
      )}
    </div>
  );
}