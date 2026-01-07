import { useState } from "react";
import { Clock, Copy, Check, ThumbsUp, ThumbsDown } from "lucide-react";
import { Button } from "../ui/button";
import { copyToClipboard } from "../../utils/clipboard";

interface AISegmentCardProps {
  content: string;
  duration: string;
  segmentNumber: number;
  reason: string;
}

export function AISegmentCard({ content, duration, segmentNumber, reason }: AISegmentCardProps) {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);

  const handleCopy = async () => {
    const success = await copyToClipboard(content);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="border border-dashed border-primary/50 rounded-lg p-4 bg-primary/5">
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary text-primary-foreground">
                <Clock className="mr-1 h-3 w-3" />
                AI Generated Segment {segmentNumber}
              </span>
              <span className="text-xs text-muted-foreground">{duration}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">{reason}</p>
          </div>
        </div>

        {/* Content */}
        <div className="p-3 bg-background rounded border border-border">
          <p className="text-sm text-foreground">{content}</p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 flex-wrap">
          <Button size="sm" variant="outline" onClick={handleCopy} className="h-7 text-[12px]">
            {copied ? (
              <>
                <Check className="mr-1 h-3.5 w-3.5 text-green-500" />
                Copied
              </>
            ) : (
              <>
                <Copy className="mr-1 h-3.5 w-3.5" />
                Copy
              </>
            )}
          </Button>
          <Button size="sm" variant="outline" className="h-7 text-[12px]">
            <Clock className="mr-1 h-3.5 w-3.5" />
            Regenerate
          </Button>
          <Button size="sm" variant="outline" className="h-7 text-[12px]">
            <Clock className="mr-1 h-3.5 w-3.5" />
            Comment
          </Button>
          
          {/* Thumbs up/down aligned to right */}
          <div className="ml-auto flex items-center gap-1">
            <Button
              size="sm"
              variant="ghost"
              className="h-7 w-7 p-0"
              onClick={() => setFeedback(feedback === "up" ? null : "up")}
            >
              <ThumbsUp className={`h-3.5 w-3.5 ${feedback === "up" ? "fill-current text-primary" : ""}`} />
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 w-7 p-0"
              onClick={() => setFeedback(feedback === "down" ? null : "down")}
            >
              <ThumbsDown className={`h-3.5 w-3.5 ${feedback === "down" ? "fill-current text-destructive" : ""}`} />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}