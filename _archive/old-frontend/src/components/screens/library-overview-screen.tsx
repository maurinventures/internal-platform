import { useState } from "react";
import { Sidebar } from "../chat/sidebar";
import { CommandPalette } from "../command-palette";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { ScrollArea } from "../ui/scroll-area";
import {
  Search,
  Video,
  Music,
  FileText,
  File,
} from "lucide-react";
import { getLibraryCount } from "../../data/library-data";

interface LibraryOverviewScreenProps {
  onProjectClick?: (projectId: string) => void;
  onLibraryClick?: (libraryType: "videos" | "audio" | "transcripts" | "pdfs") => void;
  onProjectsClick?: () => void;
  onLibraryHeaderClick?: () => void;
  onNewChat?: () => void;
  allChats?: Array<{ id: string; title: string; starred?: boolean; projectId?: string; lastModified?: number }>;
  onChatSelect?: (chatId: string | null) => void;
}

export function LibraryOverviewScreen({
  onProjectClick,
  onLibraryClick,
  onProjectsClick,
  onLibraryHeaderClick,
  onNewChat,
  allChats = [],
  onChatSelect,
}: LibraryOverviewScreenProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const libraryCategories = [
    {
      id: "videos",
      name: "Videos",
      icon: Video,
      count: getLibraryCount("videos"),
      updatedAt: "2 hours ago",
      type: "videos" as const,
    },
    {
      id: "audio",
      name: "Audio",
      icon: Music,
      count: getLibraryCount("audio"),
      updatedAt: "5 hours ago",
      type: "audio" as const,
    },
    {
      id: "transcripts",
      name: "Transcripts",
      icon: FileText,
      count: getLibraryCount("transcripts"),
      updatedAt: "1 day ago",
      type: "transcripts" as const,
    },
    {
      id: "pdfs",
      name: "PDFs",
      icon: File,
      count: getLibraryCount("pdfs"),
      updatedAt: "3 days ago",
      type: "pdfs" as const,
    },
  ];

  const filteredCategories = libraryCategories.filter((category) =>
    category.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
        allChats={allChats}
        onChatSelect={onChatSelect}
        onProjectClick={onProjectClick}
        onLibraryClick={onLibraryClick}
        onProjectsClick={onProjectsClick}
        onLibraryHeaderClick={onLibraryHeaderClick}
      />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="px-12 py-8 border-b border-border">
          <div className="max-w-5xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <h1 className="text-xl font-semibold">Library</h1>
            </div>

            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search library..."
                className="pl-10 text-[12px]"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Categories Grid */}
        <ScrollArea className="flex-1">
          <div className="px-12 py-8">
            <div className="max-w-5xl mx-auto">
              <div className="grid grid-cols-2 gap-4">
                {filteredCategories.map((category) => {
                  const Icon = category.icon;
                  return (
                    <button
                      key={category.id}
                      onClick={() => onLibraryClick?.(category.type)}
                      className="p-6 border border-border rounded-lg hover:border-primary/50 hover:bg-accent/50 transition-all text-left group"
                    >
                      <div className="flex items-start gap-4">
                        <div className="p-2 rounded-lg bg-muted group-hover:bg-primary/10 transition-colors">
                          <Icon className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-medium mb-1 text-[12px]">{category.name}</h3>
                          <p className="text-[12px] text-muted-foreground mb-2">
                            {category.count} {category.count === 1 ? 'item' : 'items'}
                          </p>
                          <p className="text-[12px] text-muted-foreground">
                            Updated {category.updatedAt}
                          </p>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}