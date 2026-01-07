import { useState } from "react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Search, Grid3x3, List, Filter, Upload } from "lucide-react";
import { Tabs, TabsList, TabsTrigger } from "../ui/tabs";
import { AssetCard } from "./asset-card";

interface LibraryAsset {
  id: string;
  type: "video" | "audio" | "transcript" | "writing" | "article" | "external-video" | "book" | "web-clip";
  title: string;
  thumbnail?: string;
  duration?: string;
  size?: string;
  date: string;
}

interface LibraryGridProps {
  onAssetClick: (asset: LibraryAsset) => void;
}

export function LibraryGrid({ onAssetClick }: LibraryGridProps) {
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [searchQuery, setSearchQuery] = useState("");
  const [category, setCategory] = useState("all");

  // Mock data
  const assets: LibraryAsset[] = [
    {
      id: "1",
      type: "video",
      title: "Product Demo Recording",
      duration: "5:32",
      size: "124 MB",
      date: "2026-01-03",
    },
    {
      id: "2",
      type: "audio",
      title: "Team Standup Meeting",
      duration: "12:45",
      size: "45 MB",
      date: "2026-01-02",
    },
    {
      id: "3",
      type: "transcript",
      title: "Interview Transcript - Customer Research",
      size: "32 KB",
      date: "2026-01-01",
    },
    {
      id: "4",
      type: "writing",
      title: "Q1 Marketing Strategy Draft",
      size: "18 KB",
      date: "2025-12-28",
    },
    {
      id: "5",
      type: "article",
      title: "AI Trends in 2026",
      size: "12 KB",
      date: "2025-12-25",
    },
    {
      id: "6",
      type: "external-video",
      title: "YouTube - Industry Conference Keynote",
      duration: "45:20",
      date: "2025-12-20",
    },
  ];

  const filteredAssets = assets.filter((asset) => {
    const matchesSearch = asset.title.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = category === "all" || asset.type === category;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="flex-1 flex flex-col h-screen">
      {/* Header */}
      <div className="border-b border-border bg-card">
        <div className="p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-semibold">Library</h1>
            <Button>
              <Upload className="mr-2 h-4 w-4" />
              Upload
            </Button>
          </div>

          {/* Search & Filters */}
          <div className="flex items-center gap-3">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search library..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button variant="outline" size="icon">
              <Filter className="h-4 w-4" />
            </Button>
            <div className="flex border border-border rounded">
              <Button
                variant={viewMode === "grid" ? "secondary" : "ghost"}
                size="icon"
                onClick={() => setViewMode("grid")}
                className="rounded-r-none"
              >
                <Grid3x3 className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === "list" ? "secondary" : "ghost"}
                size="icon"
                onClick={() => setViewMode("list")}
                className="rounded-l-none"
              >
                <List className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Category Tabs */}
          <Tabs value={category} onValueChange={setCategory}>
            <TabsList>
              <TabsTrigger value="all">All</TabsTrigger>
              <TabsTrigger value="video">Videos</TabsTrigger>
              <TabsTrigger value="audio">Audio</TabsTrigger>
              <TabsTrigger value="transcript">Transcripts</TabsTrigger>
              <TabsTrigger value="writing">Writing</TabsTrigger>
              <TabsTrigger value="article">Articles</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {filteredAssets.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">No assets found</p>
            </div>
          </div>
        ) : (
          <div className={viewMode === "grid" ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4" : "space-y-2"}>
            {filteredAssets.map((asset) => (
              <AssetCard
                key={asset.id}
                asset={asset}
                viewMode={viewMode}
                onClick={() => onAssetClick(asset)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
