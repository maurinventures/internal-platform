import { useState, useEffect } from "react";
import { 
  Send, 
  ArrowLeft, 
  MoreHorizontal, 
  Star, 
  Pencil, 
  Archive, 
  Trash2, 
  Plus,
  ChevronDown 
} from "lucide-react";
import { Button } from "../ui/button";
import { Textarea } from "../ui/textarea";
import { ScrollArea } from "../ui/scroll-area";
import { 
  Select, 
  SelectContent, 
  SelectGroup, 
  SelectItem, 
  SelectLabel, 
  SelectSeparator, 
  SelectTrigger, 
  SelectValue 
} from "../ui/select";
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
import { Label } from "../ui/label";
import { Input } from "../ui/input";
import { Sidebar } from "../chat/sidebar";
import { CommandPalette } from "../command-palette";
import { ShareDialog } from "../shared/share-dialog";
import { ChatInput } from "../chat/chat-input";
import { ChatMessage } from "../chat/chat-message";
import { LoadingMessage } from "../loading-message";
import type { ScriptGenerationData, ScriptSegment } from "../chat/script-generation-response";

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
  timestamp: string;
  starred?: boolean;
  projectId?: string;
  projectName?: string;
  lastModified?: number;
}

interface ProjectDetailScreenProps {
  projectId: string;
  projectName: string;
  onBack: () => void;
  onProjectClick?: (projectId: string) => void;
  onLibraryClick?: (libraryType: "videos" | "audio" | "transcripts" | "pdfs") => void;
  onProjectsClick?: () => void;
  onLibraryHeaderClick?: () => void;
  onNewChat?: () => void;
  allChats: Chat[];
  setAllChats: React.Dispatch<React.SetStateAction<Chat[]>>;
  initialChatId?: string | null;
  onChatSelect?: (chatId: string) => void;
}

export function ProjectDetailScreen({
  projectId,
  projectName,
  onBack,
  onProjectClick,
  onLibraryClick,
  onProjectsClick,
  onLibraryHeaderClick,
  onNewChat,
  allChats,
  setAllChats,
  initialChatId,
  onChatSelect,
}: ProjectDetailScreenProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [starred, setStarred] = useState(false);
  const [instructions, setInstructions] = useState("");
  const [showInstructionsInput, setShowInstructionsInput] = useState(false);
  const [model, setModel] = useState("claude-3-5-sonnet");
  const [quickInput, setQuickInput] = useState("");
  const [renameDialogOpen, setRenameDialogOpen] = useState(false);
  const [renameValue, setRenameValue] = useState("");
  const [selectedChatForRename, setSelectedChatForRename] = useState<string | null>(null);
  
  // Filter chats for this specific project
  const projectChats = allChats.filter(chat => chat.projectId === projectId);
  const [currentChatId, setCurrentChatId] = useState<string | null>(initialChatId || null);
  const [isLoading, setIsLoading] = useState(false);

  const currentChat = projectChats.find(chat => chat.id === currentChatId);
  const messages = currentChat?.messages || [];

  // Sync with initialChatId from parent (when clicking from RECENTS)
  useEffect(() => {
    if (initialChatId && projectChats.some(chat => chat.id === initialChatId)) {
      setCurrentChatId(initialChatId);
    } else {
      setCurrentChatId(null);
    }
  }, [projectId, initialChatId, projectChats]);

  const generateChatTitle = (userMessage: string): string => {
    const title = userMessage.slice(0, 50);
    return title.length < userMessage.length ? `${title}...` : title;
  };

  const handleQuickSend = () => {
    if (!quickInput.trim()) return;

    const timestamp = new Date().toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });

    const userMessage: Message = {
      role: "user",
      content: quickInput,
      timestamp,
    };

    // Create a new chat
    const newChatId = `chat-${Date.now()}`;
    const newChat: Chat = {
      id: newChatId,
      title: generateChatTitle(quickInput),
      messages: [userMessage],
      timestamp: "Just now",
      projectId,
      projectName,
    };
    
    setAllChats(prev => [newChat, ...prev]);
    setQuickInput("");
    
    // Navigate to the chat view with the new chat
    if (onChatSelect) {
      onChatSelect(newChatId);
    }
    
    setIsLoading(true);

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        role: "assistant",
        content: `I understand you'd like me to help with that in the context of the "${projectName}" project. ${instructions ? `Following your instructions: "${instructions}". ` : ""}Here's what I can share...\n\nThis is a demonstration of the project chat interface. In a real application, this would be connected to your AI model and use the project-specific instructions and knowledge base.`,
        timestamp: new Date().toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };
      
      setAllChats(prev => prev.map(chat => 
        chat.id === newChatId
          ? { ...chat, messages: [...chat.messages, aiMessage] }
          : chat
      ));
      setIsLoading(false);
    }, 1500);
  };

  const handleSendMessage = (content: string, persona: string, attachments: File[]) => {
    const timestamp = new Date().toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });

    const userMessage: Message = {
      role: "user",
      content,
      timestamp,
    };

    // Add message to current chat
    setAllChats(prev => prev.map(chat => 
      chat.id === currentChatId 
        ? { ...chat, messages: [...chat.messages, userMessage], lastModified: Date.now() }
        : chat
    ));

    setIsLoading(true);

    // Check if this is a video script request
    const isScriptRequest = /video\s+script|audio\s+script|script\s+(generation|for|about)|create.*script|generate.*script/i.test(content);

    // Simulate AI response
    setTimeout(() => {
      let aiMessage: Message;

      if (isScriptRequest) {
        // Generate script generation response with mock data
        const scriptData: ScriptGenerationData = {
          description: `I've created a video script for the "${projectName}" project using 4 clips from your library and 2 AI-generated segments to fill gaps.`,
          segments: [
            {
              type: "asset",
              assetType: "video",
              sourceFile: "product_demo_final.mp4",
              startTime: "0:15",
              endTime: "0:23",
              duration: "0:08",
              transcript: "Welcome to the future of AI-powered solutions. Our new product revolutionizes how businesses interact with their customers.",
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
              clipNumber: 2,
            },
            {
              type: "asset",
              assetType: "audio",
              sourceFile: "interview_cto_insights.mp3",
              startTime: "3:20",
              endTime: "3:27",
              duration: "0:07",
              transcript: "The technology behind this is cutting-edge. We've built it on a foundation of machine learning and natural language processing.",
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
              sourceFile: "brand_logo_animation.mp4",
              startTime: "0:00",
              endTime: "0:09",
              duration: "0:09",
              transcript: "[Logo animation with tagline: 'Innovate. Transform. Succeed.']",
              clipNumber: 4,
            },
          ],
          totalDuration: "0:45",
          clipCount: 4,
          aiSegmentCount: 2,
        };

        aiMessage = {
          role: "assistant",
          content: `I've generated a video script for the "${projectName}" project. The script combines existing content from your library with AI-generated transitions to create a compelling narrative.`,
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
          content: `I understand you'd like me to help with that in the context of the "${projectName}" project. ${instructions ? `Following your instructions: "${instructions}". ` : ""}Here's what I can share...\n\nThis is a demonstration of the project chat interface. In a real application, this would be connected to your AI model and use the project-specific instructions and knowledge base.`,
          timestamp: new Date().toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
          }),
        };
      }
      
      setAllChats(prev => prev.map(chat => 
        chat.id === currentChatId
          ? { ...chat, messages: [...chat.messages, aiMessage], lastModified: Date.now() }
          : chat
      ));
      setIsLoading(false);
    }, 1500);
  };

  const handleRegenerateMessage = (index: number) => {
    if (!currentChatId || !currentChat) return;

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
          content: `I understand you'd like me to help with that in the context of the "${projectName}" project. ${instructions ? `Following your instructions: "${instructions}". ` : ""}Here's a regenerated response...\n\nThis is a regenerated response for the project. In a real application, this would query your AI model again with the project context.`,
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
    setCurrentChatId(chatId);
    if (onChatSelect) {
      onChatSelect(chatId);
    }
  };

  const handleBackToList = () => {
    setCurrentChatId(null);
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
    
    const newProjectId = projectNameToId[projectName];
    
    // Update the chat to include the project association
    setAllChats(prev => prev.map(chat => 
      chat.id === chatId 
        ? { ...chat, projectId: newProjectId, projectName, lastModified: Date.now() } 
        : chat
    ));
  };

  const handleChatRemoveFromProject = (chatId: string) => {
    // Remove project association from the chat
    setAllChats(prev => prev.map(chat => 
      chat.id === chatId 
        ? { ...chat, projectId: undefined, projectName: undefined, lastModified: Date.now() } 
        : chat
    ));
  };

  const handleChatDelete = (chatId: string) => {
    setAllChats(prev => prev.filter(chat => chat.id !== chatId));
    if (currentChatId === chatId) {
      setCurrentChatId(null);
    }
  };

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <CommandPalette />
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        onNewChat={onNewChat || (() => {})}
        recentChats={[...allChats].sort((a, b) => {
          const aTime = a.lastModified || 0;
          const bTime = b.lastModified || 0;
          return bTime - aTime;
        }).map(chat => ({ 
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

      <div className="flex-1 flex flex-col min-w-0">
        {/* Main Content Area */}
        <div className="flex-1 flex min-h-0">
          {/* Left: Project Content */}
          <div className="flex-1 flex flex-col min-w-0 border-r border-border">
            {currentChatId ? (
              // Show full chat interface
              <>
                {/* Chat Header with dropdown and Share button - matches ChatScreen */}
                <div className="h-10 border-b border-border flex items-center justify-between px-4">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button 
                        variant="ghost" 
                        className="h-7 px-2 gap-2 hover:bg-accent text-[12px] font-normal max-w-md"
                      >
                        <span className="truncate">{projectName} / {currentChat?.title}</span>
                        <ChevronDown className="h-4 w-4 flex-shrink-0" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="start" className="w-56">
                      <DropdownMenuItem 
                        className="text-[12px]"
                        onClick={() => {
                          if (currentChat) {
                            handleChatStar(currentChat.id);
                          }
                        }}
                      >
                        <Star className={`h-4 w-4 mr-2 ${currentChat?.starred ? 'fill-current' : ''}`} />
                        <span>{currentChat?.starred ? 'Unstar' : 'Star'}</span>
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        className="text-[12px]"
                        onClick={() => {
                          if (currentChat) {
                            setSelectedChatForRename(currentChat.id);
                            setRenameValue(currentChat.title);
                            setRenameDialogOpen(true);
                          }
                        }}
                      >
                        <Pencil className="h-4 w-4 mr-2" />
                        <span>Rename</span>
                      </DropdownMenuItem>
                      <DropdownMenuItem className="text-[12px]">
                        <Archive className="h-4 w-4 mr-2" />
                        <span>Change project</span>
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        className="text-[12px]"
                        onClick={() => {
                          if (currentChat) {
                            handleChatRemoveFromProject(currentChat.id);
                          }
                        }}
                      >
                        <Archive className="h-4 w-4 mr-2" />
                        <span>Remove from project</span>
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem 
                        className="text-[12px] text-destructive focus:text-destructive"
                        onClick={() => {
                          if (currentChat) {
                            handleChatDelete(currentChat.id);
                          }
                        }}
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        <span>Delete</span>
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                  
                  <Button variant="outline" size="sm" className="text-[12px] h-7 px-3 font-normal">
                    Share
                  </Button>
                </div>

                {/* Chat Messages */}
                <ScrollArea className="flex-1">
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

                {/* Chat Input */}
                <ChatInput 
                  onSend={handleSendMessage} 
                  disabled={isLoading}
                  model={model}
                  onModelChange={setModel}
                />
              </>
            ) : (
              // Show chat list
              <ScrollArea className="flex-1">
                <div className="px-12 py-8">
                  <div className="space-y-6">
                    {/* Back Button */}
                    <button
                      onClick={onBack}
                      className="flex items-center gap-2 text-[12px] text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <ArrowLeft className="h-3.5 w-3.5" />
                      All projects
                    </button>

                    {/* Project Name with Actions */}
                    <div className="flex items-center justify-between">
                      <h1 className="text-2xl font-semibold">{projectName}</h1>
                      <div className="flex items-center gap-2">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="outline" size="icon" className="h-9 w-9 rounded-lg">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem className="text-[12px]">
                              <Pencil className="h-3.5 w-3.5 mr-2" />
                              Edit details
                            </DropdownMenuItem>
                            <DropdownMenuItem className="text-[12px]">
                              <Archive className="h-3.5 w-3.5 mr-2" />
                              Archive
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="text-[12px] text-destructive">
                              <Trash2 className="h-3.5 w-3.5 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                        <Button
                          variant="outline"
                          size="icon"
                          className="h-9 w-9 rounded-lg"
                          onClick={() => setStarred(!starred)}
                        >
                          <Star className={`h-4 w-4 ${starred ? "fill-primary text-primary" : ""}`} />
                        </Button>
                      </div>
                    </div>

                    {/* Start New Chat Input - Custom for Project */}
                    <div className="border-t border-b border-border pt-6 pb-4">
                      <div className="relative border border-border rounded-xl bg-background shadow-sm hover:shadow-md hover:border-primary/30 focus-within:border-primary focus-within:shadow-md transition-all duration-200 overflow-hidden">
                        <Textarea
                          placeholder="How can I help you today?"
                          value={quickInput}
                          onChange={(e) => setQuickInput(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) {
                              e.preventDefault();
                              handleQuickSend();
                            }
                          }}
                          className="min-h-[100px] border-0 focus-visible:ring-0 resize-none px-4 pt-4 pb-14 text-[14px] placeholder:text-muted-foreground/60 bg-transparent"
                          disabled={isLoading}
                        />
                        <div className="absolute bottom-0 left-0 right-0 flex items-center justify-end px-3 py-2.5 bg-muted/30 border-t border-border/50">
                          <div className="flex items-center gap-2">
                            <Select value={model} onValueChange={setModel}>
                              <SelectTrigger className="w-auto h-7 border-0 bg-background/60 hover:bg-background transition-all gap-1.5 px-2.5 text-[12px] rounded-md [&>svg]:hidden">
                                <SelectValue />
                                <ChevronDown className="h-3.5 w-3.5 opacity-50" />
                              </SelectTrigger>
                              <SelectContent align="end" className="w-[280px]">
                                <SelectGroup>
                                  <SelectLabel className="text-[11px]">Claude (Anthropic)</SelectLabel>
                                  <SelectItem value="claude-3-5-opus">
                                    <div className="flex flex-col items-start gap-0.5">
                                      <span className="font-medium text-[12px]">Claude 3.5 Opus</span>
                                      <span className="text-[11px] text-muted-foreground">Most capable model</span>
                                    </div>
                                  </SelectItem>
                                  <SelectItem value="claude-3-5-sonnet">
                                    <div className="flex flex-col items-start gap-0.5">
                                      <span className="font-medium text-[12px]">Claude 3.5 Sonnet</span>
                                    </div>
                                  </SelectItem>
                                  <SelectItem value="claude-3-5-haiku">
                                    <div className="flex flex-col items-start gap-0.5">
                                      <span className="font-medium text-[12px]">Claude 3.5 Haiku</span>
                                      <span className="text-[11px] text-muted-foreground">Fastest responses</span>
                                    </div>
                                  </SelectItem>
                                  <SelectItem value="claude-3-opus">
                                    <div className="flex flex-col items-start gap-0.5">
                                      <span className="font-medium text-[12px]">Claude 3 Opus</span>
                                      <span className="text-[11px] text-muted-foreground">Previous generation flagship</span>
                                    </div>
                                  </SelectItem>
                                  <SelectItem value="claude-3-sonnet">
                                    <div className="flex flex-col items-start gap-0.5">
                                      <span className="font-medium text-[12px]">Claude 3 Sonnet</span>
                                      <span className="text-[11px] text-muted-foreground">Balanced performance</span>
                                    </div>
                                  </SelectItem>
                                  <SelectItem value="claude-3-haiku">
                                    <div className="flex flex-col items-start gap-0.5">
                                      <span className="font-medium text-[12px]">Claude 3 Haiku</span>
                                      <span className="text-[11px] text-muted-foreground">Fast and efficient</span>
                                    </div>
                                  </SelectItem>
                                </SelectGroup>
                                
                                <SelectSeparator />
                                
                                <SelectGroup>
                                  <SelectLabel className="text-[11px]">OpenAI</SelectLabel>
                                  <SelectItem value="o1">
                                    <div className="flex flex-col items-start gap-0.5">
                                      <span className="font-medium text-[12px]">o1</span>
                                      <span className="text-[11px] text-muted-foreground">Advanced reasoning model</span>
                                    </div>
                                  </SelectItem>
                                  <SelectItem value="o1-mini">
                                    <div className="flex flex-col items-start gap-0.5">
                                      <span className="font-medium text-[12px]">o1-mini</span>
                                      <span className="text-[11px] text-muted-foreground">Faster reasoning model</span>
                                    </div>
                                  </SelectItem>
                                  <SelectItem value="gpt-4o">
                                    <div className="flex flex-col items-start gap-0.5">
                                      <span className="font-medium text-[12px]">GPT-4o</span>
                                      <span className="text-[11px] text-muted-foreground">Multimodal flagship</span>
                                    </div>
                                  </SelectItem>
                                  <SelectItem value="gpt-4-turbo">
                                    <div className="flex flex-col items-start gap-0.5">
                                      <span className="font-medium text-[12px]">GPT-4 Turbo</span>
                                      <span className="text-[11px] text-muted-foreground">Enhanced GPT-4</span>
                                    </div>
                                  </SelectItem>
                                  <SelectItem value="gpt-4">
                                    <div className="flex flex-col items-start gap-0.5">
                                      <span className="font-medium text-[12px]">GPT-4</span>
                                      <span className="text-[11px] text-muted-foreground">Original GPT-4</span>
                                    </div>
                                  </SelectItem>
                                  <SelectItem value="gpt-3.5-turbo">
                                    <div className="flex flex-col items-start gap-0.5">
                                      <span className="font-medium text-[12px]">GPT-3.5 Turbo</span>
                                      <span className="text-[11px] text-muted-foreground">Fast and economical</span>
                                    </div>
                                  </SelectItem>
                                </SelectGroup>
                              </SelectContent>
                            </Select>
                            <Button
                              size="icon"
                              className={`h-7 w-7 rounded-md transition-all duration-200 ${
                                quickInput.trim() 
                                  ? 'bg-primary hover:bg-primary/90' 
                                  : 'bg-muted-foreground/20 hover:bg-muted-foreground/30 cursor-not-allowed'
                              }`}
                              disabled={isLoading || !quickInput.trim()}
                              onClick={handleQuickSend}
                            >
                              <Send className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* List of Chats in Project */}
                    <div className="-mx-12">
                      {projectChats.map((chat, index) => (
                        <div key={chat.id}>
                          <div
                            onClick={() => handleChatSelect(chat.id)}
                            className="px-12 py-3 hover:bg-muted/50 transition-colors group cursor-pointer flex items-center justify-between"
                          >
                            <div className="flex-1">
                              <div className="text-[12px] mb-1">{chat.title}</div>
                              <div className="text-[11px] text-muted-foreground">
                                {chat.timestamp}
                              </div>
                            </div>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                  }}
                                >
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem 
                                  className="text-[12px]"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleChatStar(chat.id);
                                  }}
                                >
                                  <Star className={`h-3.5 w-3.5 mr-2 ${chat.starred ? 'fill-current' : ''}`} />
                                  {chat.starred ? 'Unstar' : 'Star'}
                                </DropdownMenuItem>
                                <DropdownMenuItem 
                                  className="text-[12px]"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedChatForRename(chat.id);
                                    setRenameValue(chat.title);
                                    setRenameDialogOpen(true);
                                  }}
                                >
                                  <Pencil className="h-3.5 w-3.5 mr-2" />
                                  Rename
                                </DropdownMenuItem>
                                <DropdownMenuItem className="text-[12px]">
                                  <Archive className="h-3.5 w-3.5 mr-2" />
                                  Change project
                                </DropdownMenuItem>
                                <DropdownMenuItem 
                                  className="text-[12px]"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleChatRemoveFromProject(chat.id);
                                  }}
                                >
                                  <Archive className="h-3.5 w-3.5 mr-2" />
                                  Remove from project
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem 
                                  className="text-[12px] text-destructive"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleChatDelete(chat.id);
                                  }}
                                >
                                  <Trash2 className="h-3.5 w-3.5 mr-2" />
                                  Delete
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </div>
                          {index < projectChats.length - 1 && <div className="mx-12 border-t border-border" />}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </ScrollArea>
            )}
          </div>

          {/* Right Sidebar: Instructions - Only show when viewing project overview (no chat selected) */}
          {!currentChatId && (
            <div className="w-80 flex flex-col border-l border-border bg-muted/30">
              <ScrollArea className="flex-1">
                <div className="p-6">
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-[12px] font-medium">Instructions</h3>
                      {!showInstructionsInput && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6"
                          onClick={() => setShowInstructionsInput(true)}
                        >
                          <Plus className="h-3.5 w-3.5" />
                        </Button>
                      )}
                    </div>
                    {showInstructionsInput ? (
                      <div className="space-y-2">
                        <Textarea
                          placeholder="Add instructions to tailor Claude's responses"
                          className="min-h-[100px] text-[12px]"
                          value={instructions}
                          onChange={(e) => setInstructions(e.target.value)}
                        />
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            className="text-[12px] h-7"
                            onClick={() => setShowInstructionsInput(false)}
                          >
                            Save
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-[12px] h-7"
                            onClick={() => {
                              setShowInstructionsInput(false);
                              setInstructions("");
                            }}
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : instructions ? (
                      <div className="text-[12px] text-muted-foreground p-3 bg-background rounded-md border border-border">
                        {instructions}
                      </div>
                    ) : (
                      <button
                        onClick={() => setShowInstructionsInput(true)}
                        className="w-full text-left text-[12px] text-muted-foreground p-3 bg-background rounded-md border border-dashed border-border hover:border-primary/50 hover:text-foreground transition-colors"
                      >
                        Add instructions to tailor Claude's responses
                      </button>
                    )}
                  </div>
                </div>
              </ScrollArea>
            </div>
          )}
        </div>
      </div>

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
                if (e.key === "Enter" && renameValue.trim() && selectedChatForRename) {
                  handleChatRename(selectedChatForRename, renameValue.trim());
                  setRenameDialogOpen(false);
                  setRenameValue("");
                  setSelectedChatForRename(null);
                }
              }}
            />
          </div>
          <DialogFooter>
            <Button 
              variant="ghost" 
              onClick={() => {
                setRenameDialogOpen(false);
                setRenameValue("");
                setSelectedChatForRename(null);
              }}
            >
              Cancel
            </Button>
            <Button 
              onClick={() => {
                if (renameValue.trim() && selectedChatForRename) {
                  handleChatRename(selectedChatForRename, renameValue.trim());
                  setRenameDialogOpen(false);
                  setRenameValue("");
                  setSelectedChatForRename(null);
                }
              }} 
              disabled={!renameValue.trim()}
            >
              Rename
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}