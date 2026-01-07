import { useState, useEffect } from "react";
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
  MoreHorizontal,
  Download,
  Trash2,
  ExternalLink,
  Pencil,
  Check,
  X,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { getLibraryItems, LibraryItem } from "../../data/library-data";

interface LibraryScreenProps {
  type: "videos" | "audio" | "transcripts" | "pdfs";
  onProjectClick?: (projectId: string) => void;
  onLibraryClick?: (libraryType: "videos" | "audio" | "transcripts" | "pdfs") => void;
  onProjectsClick?: () => void;
  onLibraryHeaderClick?: () => void;
  onNewChat?: () => void;
  allChats?: Array<{ id: string; title: string; starred?: boolean; projectId?: string; lastModified?: number }>;
  onChatSelect?: (chatId: string) => void;
}

export function LibraryScreen({
  type,
  onProjectClick,
  onLibraryClick,
  onProjectsClick,
  onLibraryHeaderClick,
  onNewChat,
  allChats,
  onChatSelect,
}: LibraryScreenProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [editedItem, setEditedItem] = useState<LibraryItem | null>(null);
  const [localItems, setLocalItems] = useState<LibraryItem[]>([]);

  const getLibraryData = () => {
    switch (type) {
      case "videos":
        return { items: getLibraryItems("videos"), icon: Video, title: "Videos" };
      case "audio":
        return { items: getLibraryItems("audio"), icon: Music, title: "Audio" };
      case "transcripts":
        return { items: getLibraryItems("transcripts"), icon: FileText, title: "Transcripts" };
      case "pdfs":
        return { items: getLibraryItems("pdfs"), icon: FileText, title: "PDFs" };
    }
  };

  const { items: originalItems, icon: Icon, title } = getLibraryData();
  
  // Initialize local items when type changes
  useEffect(() => {
    setLocalItems(originalItems);
    setEditingItemId(null);
    setEditedItem(null);
  }, [type]);

  const filteredItems = localItems.filter(
    (item) =>
      item.fileName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.keyPeople.some((person) =>
        person.toLowerCase().includes(searchQuery.toLowerCase())
      )
  );

  const handleStartEdit = (item: LibraryItem) => {
    setEditingItemId(item.id);
    setEditedItem({ ...item });
  };

  const handleCancelEdit = () => {
    setEditingItemId(null);
    setEditedItem(null);
  };

  const handleSaveEdit = () => {
    if (editedItem) {
      setLocalItems(prev => 
        prev.map(item => item.id === editedItem.id ? editedItem : item)
      );
    }
    setEditingItemId(null);
    setEditedItem(null);
  };

  const handleEditChange = (field: keyof LibraryItem, value: any) => {
    if (editedItem) {
      setEditedItem({ ...editedItem, [field]: value });
    }
  };

  const handleAddKeyPerson = (newPerson: string) => {
    if (editedItem && newPerson.trim()) {
      setEditedItem({ 
        ...editedItem, 
        keyPeople: [...editedItem.keyPeople, newPerson.trim()] 
      });
    }
  };

  const handleRemoveKeyPerson = (index: number) => {
    if (editedItem) {
      setEditedItem({ 
        ...editedItem, 
        keyPeople: editedItem.keyPeople.filter((_, i) => i !== index) 
      });
    }
  };

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <CommandPalette />
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        onNewChat={onNewChat}
        recentChats={[...allChats || []].sort((a, b) => {
          const aTime = a.lastModified || 0;
          const bTime = b.lastModified || 0;
          return bTime - aTime;
        }).map(chat => ({ 
          id: chat.id, 
          title: chat.title,
          starred: chat.starred 
        })) || []}
        allChats={allChats || []}
        onChatSelect={onChatSelect}
        onProjectClick={onProjectClick}
        onLibraryClick={onLibraryClick}
        onProjectsClick={onProjectsClick}
        onLibraryHeaderClick={onLibraryHeaderClick}
      />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="px-12 py-6 border-b border-border">
          <div className="flex items-center gap-3 mb-6">
            <Icon className="h-5 w-5 text-muted-foreground" />
            <h1 className="text-xl font-semibold">{title}</h1>
            <span className="text-[12px] text-muted-foreground">
              ({localItems.length})
            </span>
          </div>

          {/* Search */}
          <div className="relative max-w-xl">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder={`Search ${title.toLowerCase()}...`}
              className="pl-10 text-[12px]"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        {/* Table */}
        <ScrollArea className="flex-1">
          <div className="px-12 py-4">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-2.5 px-4 text-[12px] font-medium text-muted-foreground">
                    File name
                  </th>
                  <th className="text-left py-2.5 px-4 text-[12px] font-medium text-muted-foreground">
                    Description
                  </th>
                  <th className="text-left py-2.5 px-4 text-[12px] font-medium text-muted-foreground">
                    Key people
                  </th>
                  <th className="text-left py-2.5 px-4 text-[12px] font-medium text-muted-foreground">
                    {type === "videos" || type === "audio" ? "Length" : "Size"}
                  </th>
                  <th className="text-left py-2.5 px-4 text-[12px] font-medium text-muted-foreground">
                    Date
                  </th>
                  <th className="w-12"></th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((item) => {
                  const isEditing = editingItemId === item.id;
                  const displayItem = isEditing && editedItem ? editedItem : item;
                  
                  return (
                    <tr
                      key={item.id}
                      className={`border-b border-border transition-colors group ${isEditing ? 'bg-accent/30' : 'hover:bg-accent/50'}`}
                    >
                      {/* File name */}
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <Icon className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                          {isEditing ? (
                            <Input
                              value={displayItem.fileName}
                              onChange={(e) => handleEditChange('fileName', e.target.value)}
                              className="h-7 text-[12px] font-medium !text-[12px]"
                            />
                          ) : (
                            <span className="font-medium truncate text-[12px]">
                              {displayItem.fileName}
                            </span>
                          )}
                        </div>
                      </td>
                      
                      {/* Description */}
                      <td className="py-3 px-4">
                        {isEditing ? (
                          <Input
                            value={displayItem.description}
                            onChange={(e) => handleEditChange('description', e.target.value)}
                            className="h-7 text-[12px] !text-[12px]"
                          />
                        ) : (
                          <span className="text-[12px] text-muted-foreground line-clamp-2">
                            {displayItem.description}
                          </span>
                        )}
                      </td>
                      
                      {/* Key people */}
                      <td className="py-3 px-4">
                        {isEditing ? (
                          <div className="space-y-2">
                            <div className="flex flex-wrap gap-1">
                              {displayItem.keyPeople.map((person, index) => (
                                <span
                                  key={index}
                                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] bg-accent text-foreground"
                                >
                                  {person}
                                  <button
                                    onClick={() => handleRemoveKeyPerson(index)}
                                    className="hover:text-destructive"
                                  >
                                    <X className="h-3 w-3" />
                                  </button>
                                </span>
                              ))}
                            </div>
                            <Input
                              placeholder="Add person..."
                              className="h-7 text-[11px] !text-[11px] placeholder:text-[11px]"
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  handleAddKeyPerson(e.currentTarget.value);
                                  e.currentTarget.value = '';
                                }
                              }}
                            />
                          </div>
                        ) : (
                          <div className="flex flex-wrap gap-1">
                            {displayItem.keyPeople.map((person, index) => (
                              <span
                                key={index}
                                className="inline-flex items-center px-2 py-0.5 rounded text-[11px] bg-accent text-foreground"
                              >
                                {person}
                              </span>
                            ))}
                          </div>
                        )}
                      </td>
                      
                      {/* Length */}
                      <td className="py-3 px-4">
                        {isEditing ? (
                          <Input
                            value={displayItem.length}
                            onChange={(e) => handleEditChange('length', e.target.value)}
                            className="h-7 text-[12px] w-28 !text-[12px]"
                          />
                        ) : (
                          <span className="text-[12px] text-muted-foreground">
                            {displayItem.length}
                          </span>
                        )}
                      </td>
                      
                      {/* Date */}
                      <td className="py-3 px-4">
                        {isEditing ? (
                          <Input
                            value={displayItem.date}
                            onChange={(e) => handleEditChange('date', e.target.value)}
                            className="h-7 text-[12px] w-32 !text-[12px]"
                          />
                        ) : (
                          <span className="text-[12px] text-muted-foreground">
                            {displayItem.date}
                          </span>
                        )}
                      </td>
                      
                      {/* Actions */}
                      <td className="py-3 px-4">
                        {isEditing ? (
                          <div className="flex items-center gap-1">
                            <Button 
                              variant="ghost" 
                              size="icon" 
                              className="h-8 w-8 text-green-600 hover:text-green-700 hover:bg-green-50"
                              onClick={handleSaveEdit}
                            >
                              <Check className="h-4 w-4" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="icon" 
                              className="h-8 w-8 text-destructive hover:bg-destructive/10"
                              onClick={handleCancelEdit}
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </div>
                        ) : (
                          <div>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8">
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem 
                                  className="text-[12px]"
                                  onClick={() => handleStartEdit(item)}
                                >
                                  <Pencil className="mr-2 h-4 w-4" />
                                  Edit
                                </DropdownMenuItem>
                                <DropdownMenuItem className="text-[12px]">
                                  <ExternalLink className="mr-2 h-4 w-4" />
                                  Open
                                </DropdownMenuItem>
                                <DropdownMenuItem className="text-[12px]">
                                  <Download className="mr-2 h-4 w-4" />
                                  Download
                                </DropdownMenuItem>
                                {(type === "videos" || type === "audio") && (
                                  <DropdownMenuItem className="text-[12px]">
                                    <FileText className="mr-2 h-4 w-4" />
                                    Download transcript
                                  </DropdownMenuItem>
                                )}
                                <DropdownMenuSeparator />
                                <DropdownMenuItem className="text-destructive text-[12px]">
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  Delete
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {filteredItems.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                No {title.toLowerCase()} found
              </div>
            )}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}