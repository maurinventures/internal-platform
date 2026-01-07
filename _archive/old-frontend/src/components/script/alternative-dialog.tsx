import { useState } from "react";
import { Button } from "../ui/button";
import { Textarea } from "../ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../ui/dialog";

interface AlternativeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  clipNumber: number;
  currentSource: string;
  onSubmit: (requirements: string) => void;
}

export function AlternativeDialog({
  open,
  onOpenChange,
  clipNumber,
  currentSource,
  onSubmit,
}: AlternativeDialogProps) {
  const [requirements, setRequirements] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  const handleSubmit = async () => {
    if (!requirements.trim()) return;

    setIsSearching(true);
    await onSubmit(requirements);
    setIsSearching(false);
    setRequirements("");
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="text-base">Find Alternative Clip</DialogTitle>
          <DialogDescription className="text-[13px]">
            Describe what you're looking for and we'll search for a better match.
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <div className="p-3 bg-muted rounded-lg border border-border">
            <p className="text-[11px] text-muted-foreground mb-1">Current clip</p>
            <p className="text-[13px] font-medium">{currentSource}</p>
            <p className="text-[12px] text-muted-foreground">Clip {clipNumber}</p>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-muted-foreground">
              What are you looking for instead?
            </label>
            <Textarea
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              placeholder="e.g., Try to find something more energetic, with better lighting, closer to the subject..."
              className="min-h-[120px] text-[13px]"
            />
          </div>
          
          <p className="text-[11px] text-muted-foreground">
            💡 Be specific about what you want: style, mood, visual elements, timing, etc.
          </p>
        </div>

        <DialogFooter>
          <Button
            variant="ghost"
            onClick={() => onOpenChange(false)}
            className="text-[13px]"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!requirements.trim() || isSearching}
            className="text-[13px]"
          >
            {isSearching ? "Searching..." : "Find Alternative"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
