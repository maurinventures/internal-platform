import { Button } from "../ui/button";
import { Download, FileText, FileJson, Loader2 } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { useState } from "react";
import { toast } from "sonner";

export function ExportOptions() {
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async (format: string) => {
    setIsExporting(true);

    try {
      // Simulate getting the script content
      // TODO: Get actual script content from context/props
      const scriptContent = `VIDEO SCRIPT EXPORT

Title: Sample Video Script
Generated: ${new Date().toLocaleString()}

INTRODUCTION
This is where the introduction content would go...

MAIN CONTENT
This is the main body of the script...

CONCLUSION
Closing thoughts and call to action...

---
Asset Clips Used:
- Clip 1: intro_footage.mp4 (0:00 - 0:15)
- Clip 2: main_content.mp4 (0:15 - 1:30)
- Clip 3: conclusion.mp4 (1:30 - 2:00)
`;

      // Add delay to show loading state
      await new Promise(resolve => setTimeout(resolve, 800));

      let blob: Blob;
      let filename: string;

      switch (format) {
        case "txt":
          blob = new Blob([scriptContent], { type: "text/plain" });
          filename = `video-script-${Date.now()}.txt`;
          break;
        case "json":
          const jsonData = {
            title: "Sample Video Script",
            generatedAt: new Date().toISOString(),
            sections: [
              { type: "introduction", content: "This is where the introduction content would go..." },
              { type: "main", content: "This is the main body of the script..." },
              { type: "conclusion", content: "Closing thoughts and call to action..." },
            ],
            clips: [
              { clipNumber: 1, source: "intro_footage.mp4", startTime: "0:00", endTime: "0:15" },
              { clipNumber: 2, source: "main_content.mp4", startTime: "0:15", endTime: "1:30" },
              { clipNumber: 3, source: "conclusion.mp4", startTime: "1:30", endTime: "2:00" },
            ],
          };
          blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: "application/json" });
          filename = `video-script-${Date.now()}.json`;
          break;
        case "pdf":
        case "docx":
          // For PDF/DOCX, we'd need additional libraries
          // For now, export as text with a note
          blob = new Blob([`${scriptContent}\n\nNote: ${format.toUpperCase()} export coming soon!`], { type: "text/plain" });
          filename = `video-script-${Date.now()}.${format}`;
          break;
        default:
          throw new Error("Unknown format");
      }

      // Trigger download
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast.success("Script Exported", {
        description: `Script exported as ${format.toUpperCase()} to your Downloads folder.`,
      });
    } catch (error) {
      toast.error("Export Failed", {
        description: "There was an error exporting the script.",
      });
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="h-7 text-[12px]" disabled={isExporting}>
          {isExporting ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Download className="mr-2 h-4 w-4" />
          )}
          {isExporting ? "Exporting..." : "Export Script"}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuItem onClick={() => handleExport("txt")} className="text-[12px]">
          <FileText className="mr-2 h-4 w-4" />
          Export as Plain Text
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => handleExport("json")} className="text-[12px]">
          <FileJson className="mr-2 h-4 w-4" />
          Export as JSON
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => handleExport("pdf")} className="text-[12px] opacity-60">
          <FileText className="mr-2 h-4 w-4" />
          Export as PDF (Coming Soon)
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleExport("docx")} className="text-[12px] opacity-60">
          <FileText className="mr-2 h-4 w-4" />
          Export as DOCX (Coming Soon)
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}