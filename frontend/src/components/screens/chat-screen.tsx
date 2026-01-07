import { useState } from "react";
import { Sidebar } from "../chat/sidebar";
import { CommandPalette } from "../command-palette";
import { ShareDialog } from "../shared/share-dialog";
import { ChatInput } from "../chat/chat-input";
import { ChatMessage } from "../chat/chat-message";
import { LoadingMessage } from "../loading-message";
import { EmptyState } from "../chat/empty-state";
import { Button } from "../ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { ScrollArea } from "../ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Label } from "../ui/label";
import { Input } from "../ui/input";
import { 
  Star, 
  Pencil, 
  Archive, 
  Trash2, 
  ChevronDown, 
  FolderPlus,
  Search,
  FolderInput
} from "lucide-react";
import type { ScriptGenerationData } from "../chat/script-generation-response";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  scriptData?: ScriptGenerationData; // Optional script generation data
}

interface Chat {
  id: string;
  title: string;
  messages: Message[];
  starred?: boolean;
  projectId?: string;
  projectName?: string;
  lastModified?: number; // Timestamp for sorting
}

interface ChatScreenProps {
  onProjectClick?: (projectId: string) => void;
  onLibraryClick?: (libraryType: "videos" | "audio" | "transcripts" | "pdfs") => void;
  onProjectsClick?: () => void;
  onLibraryHeaderClick?: () => void;
  allChats: Chat[];
  setAllChats: React.Dispatch<React.SetStateAction<Chat[]>>;
  currentChatId?: string | null;
  onChatSelect?: (chatId: string) => void;
  onNewChat?: () => void;
}

export function ChatScreen({ 
  onProjectClick,
  onLibraryClick,
  onProjectsClick,
  onLibraryHeaderClick,
  allChats,
  setAllChats,
  currentChatId,
  onChatSelect,
  onNewChat,
}: ChatScreenProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [model, setModel] = useState("claude-3-5-sonnet");
  const [isLoading, setIsLoading] = useState(false);
  const [renameDialogOpen, setRenameDialogOpen] = useState(false);
  const [renameValue, setRenameValue] = useState("");
  const [addToProjectDialogOpen, setAddToProjectDialogOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState("");
  const [projectSearchQuery, setProjectSearchQuery] = useState("");
  const [shareDialogOpen, setShareDialogOpen] = useState(false);

  // Get the current chat from all chats
  const currentChat = allChats.find(chat => chat.id === currentChatId);
  const messages = currentChat?.messages || [];
  
  // RECENTS shows ALL chats (including those in projects), sorted by last modified
  const recentChats = [...allChats].sort((a, b) => {
    const aTime = a.lastModified || 0;
    const bTime = b.lastModified || 0;
    return bTime - aTime; // Most recent first
  });

  const generateChatTitle = (userMessage: string): string => {
    // Take first 50 characters of the user message for the title
    const title = userMessage.slice(0, 50);
    return title.length < userMessage.length ? `${title}...` : title;
  };

  const handleNewChat = () => {
    // Call parent's onNewChat to handle navigation
    if (onNewChat) {
      onNewChat();
    }
  };

  const handleChatStar = (chatId: string) => {
    setAllChats(prev => prev.map(chat => 
      chat.id === chatId ? { ...chat, starred: !chat.starred, lastModified: Date.now() } : chat
    ));
  };

  const handleChatRename = (chatId: string, newTitle: string) => {
    setAllChats(prev => prev.map(chat => 
      chat.id === chatId ? { ...chat, title: newTitle, lastModified: Date.now() } : chat
    ));
  };

  const handleChatAddToProject = (chatId: string, projectName: string) => {
    // Map project names to IDs
    const projectNameToId: Record<string, string> = {
      "Product Launch": "1",
      "Marketing Campaign": "2",
      "Research & Development": "3",
    };
    
    const projectId = projectNameToId[projectName];
    
    // Update the chat to include the project association
    setAllChats(prev => prev.map(chat => 
      chat.id === chatId 
        ? { ...chat, projectId, projectName, lastModified: Date.now() } 
        : chat
    ));
    
    console.log(`Chat ${chatId} moved to project: ${projectName}`);
  };

  const handleChatRemoveFromProject = (chatId: string) => {
    // Remove project association from the chat
    setAllChats(prev => prev.map(chat => 
      chat.id === chatId 
        ? { ...chat, projectId: undefined, projectName: undefined, lastModified: Date.now() } 
        : chat
    ));
    
    console.log(`Chat ${chatId} removed from project`);
  };

  const handleChatDelete = (chatId: string) => {
    setAllChats(prev => prev.filter(chat => chat.id !== chatId));
    if (currentChatId === chatId && onChatSelect) {
      onChatSelect(null);
    }
  };

  const handleSendMessage = (content: string, persona: string, attachments: File[], isVideoScript?: boolean) => {
    const timestamp = new Date().toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });

    const userMessage: Message = {
      role: "user",
      content,
      timestamp,
    };

    // If no current chat, create a new one
    if (!currentChatId) {
      const newChatId = `chat-${Date.now()}`;
      const newChat: Chat = {
        id: newChatId,
        title: generateChatTitle(content),
        messages: [userMessage],
        starred: false,
        lastModified: Date.now(),
      };
      setAllChats(prev => [newChat, ...prev]);
      // Use the parent callback to set the current chat
      if (onChatSelect) {
        onChatSelect(newChatId);
      }
    } else {
      // Add message to existing chat
      setAllChats(prev => prev.map(chat => 
        chat.id === currentChatId 
          ? { ...chat, messages: [...chat.messages, userMessage], lastModified: Date.now() }
          : chat
      ));
    }

    setIsLoading(true);

    // Simulate AI response
    setTimeout(() => {
      let aiMessage: Message;

      if (isVideoScript) {
        // Generate script generation response with mock data
        const scriptData: ScriptGenerationData = {
          description: "I've created a 60-second video script using 4 clips from your library and 2 AI-generated segments to fill gaps.",
          segments: [
            {
              type: "asset",
              assetType: "video",
              sourceFile: "product_demo_final.mp4",
              startTime: "0:15",
              endTime: "0:23",
              duration: "0:08",
              transcript: "Welcome to the future of AI-powered solutions. Our new product revolutionizes how businesses interact with their customers.",
              visualAnalysis: "Dan Goldin in a navy suit standing in a modern office, gesturing confidently while presenting to camera, bright natural lighting from windows behind",
              clipNumber: 1,
            },
            {
              type: "ai",
              content: "[Transition] This innovation didn't happen overnight. It's the result of years of research and development.",
              duration: "0:05",
              segmentNumber: 1,
              reason: "Connecting product intro to customer testimonials",
            },
            {
              type: "asset",
              assetType: "video",
              sourceFile: "customer_testimonial_sarah.mp4",
              startTime: "1:42",
              endTime: "1:54",
              duration: "0:12",
              transcript: "Since implementing this solution, we've seen a 300% increase in customer engagement. It's been absolutely transformative for our business.",
              visualAnalysis: "Dan Goldin walking through a manufacturing facility in business casual attire, talking with factory workers, industrial equipment visible in background",
              clipNumber: 2,
            },
            {
              type: "asset",
              assetType: "video",
              sourceFile: "beach_stairs_run.mp4",
              startTime: "0:05",
              endTime: "0:12",
              duration: "0:07",
              transcript: "[Background music and ambient sound]",
              visualAnalysis: "Dan Goldin running up wooden stairs at the beach during golden hour, athletic wear, ocean and sunset visible in background, dynamic upward camera angle",
              clipNumber: 3,
            },
            {
              type: "ai",
              content: "[Call to Action] Ready to transform your business? Join thousands of companies already using our platform.",
              duration: "0:04",
              segmentNumber: 2,
              reason: "Strong closing call-to-action",
            },
            {
              type: "asset",
              assetType: "video",
              sourceFile: "executive_meeting_discussion.mp4",
              startTime: "2:30",
              endTime: "2:39",
              duration: "0:09",
              transcript: "The key to scaling this technology is understanding both the human element and the technical infrastructure required to support it at scale.",
              visualAnalysis: "Dan Goldin in a charcoal suit sitting at a conference table during executive meeting, leaning forward engaged in discussion, glass windows and city skyline behind",
              clipNumber: 4,
            },
          ],
          totalDuration: "0:45",
          clipCount: 4,
          aiSegmentCount: 2,
        };

        aiMessage = {
          role: "assistant",
          content: "I've analyzed your request and generated a complete video script based on content from your library.",
          timestamp: new Date().toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
          }),
          scriptData,
        };
      } else {
        // Regular text response
        aiMessage = {
          role: "assistant",
          content: "I understand you'd like me to help with that. Based on your knowledge base and the context you've provided, here's what I can share...\n\nThis is a demonstration of the chat interface. In a real application, this would be connected to your AI model and knowledge base to provide intelligent responses based on your private data stored in S3 and RDS.",
          timestamp: new Date().toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
          }),
        };
      }
      
      setAllChats(prev => prev.map(chat => 
        chat.id === currentChatId || (currentChatId === null && chat.id === prev[0]?.id)
          ? { ...chat, messages: [...chat.messages, aiMessage] }
          : chat
      ));
      setIsLoading(false);
    }, 1500);
  };

  const handlePromptClick = (prompt: string) => {
    handleSendMessage(prompt, "default", []);
  };

  const handleRegenerateMessage = (index: number) => {
    if (!currentChatId || !currentChat) return;

    // Find the user message that prompted this response
    if (index > 0 && currentChat.messages[index - 1].role === "user") {
      // Remove the current assistant message
      setAllChats(prev => prev.map(chat => 
        chat.id === currentChatId
          ? { ...chat, messages: chat.messages.slice(0, index) }
          : chat
      ));
      setIsLoading(true);

      // Generate new response
      setTimeout(() => {
        const aiMessage: Message = {
          role: "assistant",
          content: "I understand you'd like me to help with that. Based on your knowledge base and the context you've provided, here's what I can share...\n\nThis is a regenerated response. In a real application, this would query your AI model again to provide a different perspective or improved answer.",
          timestamp: new Date().toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
          }),
        };
        setAllChats(prev => prev.map(chat => 
          chat.id === currentChatId
            ? { ...chat, messages: [...chat.messages, aiMessage] }
            : chat
        ));
        setIsLoading(false);
      }, 1500);
    }
  };

  const handleChatSelect = (chatId: string) => {
    if (onChatSelect) {
      onChatSelect(chatId);
    }
  };

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <CommandPalette />
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        onNewChat={handleNewChat}
        recentChats={recentChats.map(chat => ({ 
          id: chat.id, 
          title: chat.title,
          starred: chat.starred 
        }))}
        onChatSelect={handleChatSelect}
        currentChatId={currentChatId}
        onChatStar={handleChatStar}
        onChatRename={handleChatRename}
        onChatAddToProject={handleChatAddToProject}
        onChatRemoveFromProject={handleChatRemoveFromProject}
        onChatDelete={handleChatDelete}
        onProjectClick={onProjectClick}
        onLibraryClick={onLibraryClick}
        onProjectsClick={onProjectsClick}
        onLibraryHeaderClick={onLibraryHeaderClick}
        allChats={allChats}
      />

      <div className="flex-1 flex flex-col min-w-0 h-full">
        {/* Chat Header - Fixed at top */}
        <div className="h-10 border-b border-border flex items-center justify-between px-4 flex-shrink-0 bg-background">
          {currentChat ? (
            <>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button 
                    variant="ghost" 
                    className="h-7 px-3 gap-2 hover:bg-accent text-[12px] font-normal max-w-[400px]"
                  >
                    <span className="truncate flex-1 text-left">
                      {currentChat.projectName ? (
                        <>
                          <span className="text-muted-foreground">{currentChat.projectName}</span>
                          <span className="text-muted-foreground mx-1.5">/</span>
                          <span>{currentChat.title}</span>
                        </>
                      ) : (
                        currentChat.title
                      )}
                    </span>
                    <ChevronDown className="h-4 w-4 flex-shrink-0" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="w-56">
                  <DropdownMenuItem 
                    onClick={() => handleChatStar(currentChat.id)}
                    className="text-[12px]"
                  >
                    <Star className={`h-4 w-4 mr-2 ${currentChat.starred ? 'fill-current' : ''}`} />
                    <span>{currentChat.starred ? 'Unstar' : 'Star'}</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem 
                    onClick={() => {
                      setRenameValue(currentChat.title);
                      setRenameDialogOpen(true);
                    }}
                    className="text-[12px]"
                  >
                    <Pencil className="h-4 w-4 mr-2" />
                    <span>Rename</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem 
                    onClick={() => {
                      setSelectedProject(currentChat.projectId ? currentChat.projectName || "" : "");
                      setAddToProjectDialogOpen(true);
                    }}
                    className="text-[12px]"
                  >
                    <FolderInput className="h-4 w-4 mr-2" />
                    <span>{currentChat.projectId ? 'Change project' : 'Add to project'}</span>
                  </DropdownMenuItem>
                  {currentChat.projectId && (
                    <DropdownMenuItem 
                      onClick={() => handleChatRemoveFromProject(currentChat.id)}
                      className="text-[12px]"
                    >
                      <FolderInput className="h-4 w-4 mr-2" />
                      <span>Remove from project</span>
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuSeparator />
                  <DropdownMenuItem 
                    onClick={() => handleChatDelete(currentChat.id)}
                    className="text-[12px] text-destructive focus:text-destructive"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    <span>Delete</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              
              {/* 
                SHARE BUTTON - Google Docs-style Permissions Model
                
                SHARING BEHAVIOR:
                1. CHAT/FILE SHARING (Individual):
                   - When you click Share on a specific chat/file, you grant access to ONLY that specific chat/file
                   - Only users with explicit access can view/edit this chat
                   - Permissions: Viewer, Commenter, Editor (similar to Google Docs)
                
                2. PROJECT SHARING (Bulk):
                   - When you share a PROJECT, users get access to ALL files within that project
                   - Similar to Google Drive folder sharing
                   - All chats/files under the project inherit project-level permissions
                   - If a file is in a shared project, those users can access it
                
                3. COMMENT TAGGING PERMISSIONS:
                   - Only users who have access (either via direct file share OR project share) can be tagged in comments
                   - The comment dialog should filter the user list to show only users with access
                   - If a user doesn't have access, they can't be tagged (prevents accidental data leakage)
                
                PERMISSION HIERARCHY:
                - Direct file sharing > Project sharing > No access
                - If someone has Editor on file but Viewer on project, file-level Editor wins
                
                IMPLEMENTATION NOTES:
                - Share dialog should show current collaborators
                - Should allow adding users by email with role selection (Viewer/Commenter/Editor)
                - Should show "Anyone with link" vs "Restricted" options
                - Backend (RDS) tracks: file_id, user_id, role, granted_at, granted_by
                - Comments system checks permissions before allowing tags
                
                TODO: 
                - Create ShareDialog component
                - Implement permission checking API
                - Filter taggable users in CommentDialog based on permissions
              */}
              <Button 
                variant="outline" 
                size="sm" 
                className="text-[12px] h-7 px-3 font-normal"
                onClick={() => setShareDialogOpen(true)}
              >
                Share
              </Button>
            </>
          ) : (
            // Empty state - just show empty header to maintain height
            <div></div>
          )}
        </div>

        {messages.length === 0 && !isLoading ? (
          <EmptyState 
            onPromptClick={handlePromptClick}
            chatInput={
              <ChatInput 
                onSend={handleSendMessage} 
                disabled={isLoading}
                model={model}
                onModelChange={setModel}
                centered
              />
            }
          />
        ) : (
          <>
            <ScrollArea className="flex-1 overflow-auto">
              <div className="pb-8">
                {messages.map((message, index) => (
                  <ChatMessage 
                    key={index} 
                    {...message} 
                    onRegenerate={message.role === "assistant" ? () => handleRegenerateMessage(index) : undefined}
                  />
                ))}
                {isLoading && <LoadingMessage />}
              </div>
            </ScrollArea>

            <ChatInput 
              onSend={handleSendMessage} 
              disabled={isLoading}
              model={model}
              onModelChange={setModel}
            />
          </>
        )}
      </div>

      {/* Share Dialog */}
      {currentChat && (
        <ShareDialog
          open={shareDialogOpen}
          onOpenChange={setShareDialogOpen}
          resourceType="chat"
          resourceName={currentChat.title}
          resourceId={currentChat.id}
          currentUsers={[
            // Mock owner - in production, fetch from API
            { id: "current-user", name: "You", email: "you@resonance.ai", initials: "YO", role: "owner" },
          ]}
          linkSharing="restricted"
          linkRole="viewer"
        />
      )}

      {/* Rename Dialog */}
      {currentChat && (
        <Dialog open={renameDialogOpen} onOpenChange={setRenameDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Rename chat</DialogTitle>
              <DialogDescription>
                Choose a new name for this chat.
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <Label htmlFor="chat-name" className="text-[13px]">
                Chat name
              </Label>
              <Input
                id="chat-name"
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                className="mt-2 text-[13px]"
                placeholder="Enter chat name..."
              />
            </div>
            <DialogFooter>
              <Button
                variant="ghost"
                onClick={() => {
                  setRenameDialogOpen(false);
                  setRenameValue("");
                }}
              >
                Cancel
              </Button>
              <Button
                onClick={() => {
                  if (renameValue.trim() && currentChat) {
                    handleChatRename(currentChat.id, renameValue.trim());
                  }
                  setRenameDialogOpen(false);
                  setRenameValue("");
                }}
              >
                Rename
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* Add to Project Dialog */}
      {currentChat && (
        <Dialog open={addToProjectDialogOpen} onOpenChange={setAddToProjectDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="text-[12px]">{currentChat.projectId ? 'Move chat' : 'Add to project'}</DialogTitle>
              <DialogDescription className="text-[12px]">
                {currentChat.projectId 
                  ? `This chat is in ${currentChat.projectName}. Select a different project to move it to.`
                  : 'Select a project to add this conversation to.'
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
                {currentChat.projectId !== "1" && (
                  <button
                    onClick={() => setSelectedProject("Product Launch")}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors text-left ${
                      selectedProject === "Product Launch" 
                        ? "bg-accent" 
                        : "hover:bg-accent"
                    }`}
                  >
                    <span className="text-[12px]">Product Launch</span>
                  </button>
                )}
                {currentChat.projectId !== "2" && (
                  <button
                    onClick={() => setSelectedProject("Marketing Campaign")}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors text-left ${
                      selectedProject === "Marketing Campaign" 
                        ? "bg-accent" 
                        : "hover:bg-accent"
                    }`}
                  >
                    <span className="text-[12px]">Marketing Campaign</span>
                  </button>
                )}
                {currentChat.projectId !== "3" && (
                  <button
                    onClick={() => setSelectedProject("Research & Development")}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors text-left ${
                      selectedProject === "Research & Development" 
                        ? "bg-accent" 
                        : "hover:bg-accent"
                    }`}
                  >
                    <span className="text-[12px]">Research & Development</span>
                  </button>
                )}
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="ghost"
                onClick={() => {
                  setAddToProjectDialogOpen(false);
                  setSelectedProject("");
                  setProjectSearchQuery("");
                }}
                className="text-[12px]"
              >
                Cancel
              </Button>
              <Button
                onClick={() => {
                  if (selectedProject && currentChat) {
                    handleChatAddToProject(currentChat.id, selectedProject);
                  }
                  setAddToProjectDialogOpen(false);
                  setSelectedProject("");
                  setProjectSearchQuery("");
                }}
                disabled={!selectedProject}
                className="text-[12px]"
              >
                {currentChat.projectId ? 'Move to Project' : 'Add to Project'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}