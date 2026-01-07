import { Video, Music, FileText, FileType, Globe, BookOpen, Paperclip, MoreVertical } from "lucide-react";
import { Button } from "../ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";

interface Asset {
  id: string;
  type: "video" | "audio" | "transcript" | "writing" | "article" | "external-video" | "book" | "web-clip";
  title: string;
  thumbnail?: string;
  duration?: string;
  size?: string;
  date: string;
}

interface AssetCardProps {
  asset: Asset;
  viewMode: "grid" | "list";
  onClick: () => void;
}

const typeIcons = {
  video: Video,
  audio: Music,
  transcript: FileText,
  writing: FileType,
  article: FileText,
  "external-video": Globe,
  book: BookOpen,
  "web-clip": Paperclip,
};

const typeColors = {
  video: "text-blue-500",
  audio: "text-purple-500",
  transcript: "text-green-500",
  writing: "text-amber-500",
  article: "text-orange-500",
  "external-video": "text-cyan-500",
  book: "text-red-500",
  "web-clip": "text-pink-500",
};

export function AssetCard({ asset, viewMode, onClick }: AssetCardProps) {
  const Icon = typeIcons[asset.type];

  if (viewMode === "list") {
    return (
      <div
        className="w-full flex items-center gap-4 p-3 rounded-lg border border-border hover:border-primary hover:bg-accent transition-colors group cursor-pointer"
        onClick={onClick}
      >
        <div className={`p-2 rounded bg-muted ${typeColors[asset.type]}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium truncate">{asset.title}</p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
            <span>{asset.type}</span>
            {asset.duration && (
              <>
                <span>•</span>
                <span>{asset.duration}</span>
              </>
            )}
            {asset.size && (
              <>
                <span>•</span>
                <span>{asset.size}</span>
              </>
            )}
            <span>•</span>
            <span>{new Date(asset.date).toLocaleDateString()}</span>
          </div>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
            <Button variant="ghost" size="icon">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem className="text-[12px]">Open</DropdownMenuItem>
            <DropdownMenuItem className="text-[12px]">Download</DropdownMenuItem>
            <DropdownMenuItem className="text-[12px]">Share</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-destructive text-[12px]">Delete</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    );
  }

  return (
    <div
      className="group relative flex flex-col rounded-lg border border-border hover:border-primary hover:shadow-md transition-all overflow-hidden bg-card cursor-pointer"
      onClick={onClick}
    >
      {/* Thumbnail/Preview */}
      <div className="aspect-video bg-muted flex items-center justify-center">
        {asset.thumbnail ? (
          <img src={asset.thumbnail} alt={asset.title} className="w-full h-full object-cover" />
        ) : (
          <Icon className={`h-12 w-12 ${typeColors[asset.type]}`} />
        )}
        {asset.duration && (
          <div className="absolute bottom-2 right-2 px-2 py-0.5 bg-black/80 text-white text-xs rounded">
            {asset.duration}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-3 flex-1 flex flex-col">
        <p className="font-medium line-clamp-2 mb-1">{asset.title}</p>
        <div className="flex items-center gap-2 text-xs text-muted-foreground mt-auto">
          <span className="capitalize">{asset.type.replace("-", " ")}</span>
          {asset.size && (
            <>
              <span>•</span>
              <span>{asset.size}</span>
            </>
          )}
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          {new Date(asset.date).toLocaleDateString()}
        </p>
      </div>

      {/* Actions */}
      <div className="absolute top-2 right-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
            <Button variant="secondary" size="icon" className="h-8 w-8">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem className="text-[12px]">Open</DropdownMenuItem>
            <DropdownMenuItem className="text-[12px]">Download</DropdownMenuItem>
            <DropdownMenuItem className="text-[12px]">Share</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-destructive text-[12px]">Delete</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}