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

interface FeedbackDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  type: "positive" | "negative";
  clipNumber: number;
  onSubmit: (feedback: string) => void;
}

export function FeedbackDialog({
  open,
  onOpenChange,
  type,
  clipNumber,
  onSubmit,
}: FeedbackDialogProps) {
  const [feedback, setFeedback] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!feedback.trim()) return;

    setIsSubmitting(true);
    await onSubmit(feedback);
    setIsSubmitting(false);
    setFeedback("");
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="text-base">
            {type === "positive" ? "What makes this clip great?" : "What's wrong with this clip?"}
          </DialogTitle>
          <DialogDescription className="text-[13px]">
            {type === "positive"
              ? "Help us understand what quality looks like. Your feedback trains our AI to find better clips."
              : "Help us improve. Tell us what's wrong so we can learn to avoid similar issues in the future."}
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-muted-foreground">
              Feedback for Clip {clipNumber}
            </label>
            <Textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder={
                type === "positive"
                  ? "e.g., Perfect timing, great visual quality, exactly what I needed..."
                  : "e.g., Audio quality is poor, wrong topic, doesn't match the script..."
              }
              className="min-h-[120px] text-[13px]"
            />
          </div>
          
          <p className="text-[11px] text-muted-foreground">
            💡 This feedback is logged and helps our learning system improve over time.
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
            disabled={!feedback.trim() || isSubmitting}
            className="text-[13px]"
          >
            {isSubmitting ? "Submitting..." : "Submit Feedback"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
