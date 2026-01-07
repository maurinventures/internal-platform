import { useEffect, useState } from "react";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "./ui/command";
import {
  MessageSquare,
  Video,
  Music,
  FileText,
  Folder,
  Settings,
  Search,
} from "lucide-react";
import { getLibraryCount } from "../data/library-data";

export function CommandPalette() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Search conversations, files, and more..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        <CommandGroup heading="Recent Conversations">
          <CommandItem>
            <MessageSquare className="mr-2 h-4 w-4" />
            <span>Video script for Q1 launch</span>
          </CommandItem>
          <CommandItem>
            <MessageSquare className="mr-2 h-4 w-4" />
            <span>Research on AI trends</span>
          </CommandItem>
          <CommandItem>
            <MessageSquare className="mr-2 h-4 w-4" />
            <span>Content strategy discussion</span>
          </CommandItem>
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Projects">
          <CommandItem>
            <Folder className="mr-2 h-4 w-4 text-primary" />
            <span>Product Launch</span>
          </CommandItem>
          <CommandItem>
            <Folder className="mr-2 h-4 w-4 text-primary" />
            <span>Marketing Campaign</span>
          </CommandItem>
          <CommandItem>
            <Folder className="mr-2 h-4 w-4 text-primary" />
            <span>Research & Development</span>
          </CommandItem>
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Library">
          <CommandItem>
            <Video className="mr-2 h-4 w-4" />
            <span>Videos</span>
            <span className="ml-auto text-xs text-muted-foreground">
              {getLibraryCount("videos")}
            </span>
          </CommandItem>
          <CommandItem>
            <Music className="mr-2 h-4 w-4" />
            <span>Audio</span>
            <span className="ml-auto text-xs text-muted-foreground">
              {getLibraryCount("audio")}
            </span>
          </CommandItem>
          <CommandItem>
            <FileText className="mr-2 h-4 w-4" />
            <span>Transcripts</span>
            <span className="ml-auto text-xs text-muted-foreground">
              {getLibraryCount("transcripts")}
            </span>
          </CommandItem>
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Actions">
          <CommandItem>
            <MessageSquare className="mr-2 h-4 w-4" />
            <span>New Chat</span>
            <kbd className="ml-auto pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border border-border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
              <span className="text-xs">⌘</span>N
            </kbd>
          </CommandItem>
          <CommandItem>
            <Search className="mr-2 h-4 w-4" />
            <span>Search</span>
            <kbd className="ml-auto pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border border-border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
              <span className="text-xs">⌘</span>K
            </kbd>
          </CommandItem>
          <CommandItem>
            <Settings className="mr-2 h-4 w-4" />
            <span>Settings</span>
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}