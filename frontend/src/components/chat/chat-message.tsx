import { useState } from "react";
import { Button } from "../ui/button";
import { User, Bot, Copy, RotateCw, ThumbsUp, ThumbsDown, Check } from "lucide-react";
import { Textarea } from "../ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { 
  ScriptGenerationResponse, 
  ScriptGenerationData,
  ScriptSegment 
} from "./script-generation-response";
import { copyToClipboard } from "../../utils/clipboard";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
  onRegenerate?: () => void;
  scriptData?: ScriptGenerationData; // Optional script generation data
}

export function ChatMessage({ role, content, timestamp, onRegenerate, scriptData }: ChatMessageProps) {
  const [copied, setCopied] = useState(false);
  const [feedbackType, setFeedbackType] = useState<"up" | "down" | null>(null);
  const [feedbackDialogOpen, setFeedbackDialogOpen] = useState(false);
  const [feedbackComment, setFeedbackComment] = useState("");
  const [submittedFeedback, setSubmittedFeedback] = useState<"up" | "down" | null>(null);

  const handleCopy = async () => {
    const success = await copyToClipboard(content);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleFeedbackClick = (type: "up" | "down") => {
    setFeedbackType(type);
    setFeedbackDialogOpen(true);
  };

  const handleFeedbackSubmit = () => {
    console.log("Feedback submitted:", { type: feedbackType, comment: feedbackComment });
    setSubmittedFeedback(feedbackType);
    setFeedbackDialogOpen(false);
    setFeedbackComment("");
  };

  const handleFeedbackCancel = () => {
    setFeedbackDialogOpen(false);
    setFeedbackComment("");
  };

  return (
    <>
      <div className="group py-4">
        <div className="max-w-3xl mx-auto px-6">
          {role === "user" ? (
            // User message - right aligned
            <div className="flex justify-end">
              <div className="max-w-[80%] bg-primary text-primary-foreground rounded-2xl px-4 py-2.5">
                <p className="whitespace-pre-wrap leading-relaxed text-[13px]">
                  {content}
                </p>
                {timestamp && (
                  <div className="text-[11px] opacity-70 mt-1 text-right">{timestamp}</div>
                )}
              </div>
            </div>
          ) : (
            // Assistant message - text aligns with chat input left edge
            <div className="relative">
              {/* Avatar - positioned to the left, outside the text area */}
              <div className="absolute left-0 top-0 flex-shrink-0 -ml-11">
                <div className="w-7 h-7 rounded-full flex items-center justify-center bg-foreground">
                  <Bot className="h-3.5 w-3.5 text-background" />
                </div>
              </div>

              {/* Content - starts at the same left edge as chat input */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-[12px]">Internal Platform</span>
                  {timestamp && (
                    <span className="text-[11px] text-muted-foreground">{timestamp}</span>
                  )}
                </div>

                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <p className="whitespace-pre-wrap text-foreground leading-relaxed text-[13px]">
                    {content}
                  </p>
                </div>

                {/* Script Generation Response */}
                {scriptData && (
                  <ScriptGenerationResponse data={scriptData} />
                )}

                {/* Actions - Only for assistant messages */}
                <div className="flex items-center gap-1 pt-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0"
                    onClick={handleCopy}
                    title="Copy"
                  >
                    {copied ? (
                      <Check className="h-3.5 w-3.5 text-green-500" />
                    ) : (
                      <Copy className="h-3.5 w-3.5" />
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0"
                    onClick={onRegenerate}
                    title="Regenerate"
                  >
                    <RotateCw className="h-3.5 w-3.5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0"
                    onClick={() => handleFeedbackClick("up")}
                    title="Good response"
                  >
                    <ThumbsUp className={`h-3.5 w-3.5 ${submittedFeedback === "up" ? "fill-current text-primary" : ""}`} />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0"
                    onClick={() => handleFeedbackClick("down")}
                    title="Bad response"
                  >
                    <ThumbsDown className={`h-3.5 w-3.5 ${submittedFeedback === "down" ? "fill-current text-destructive" : ""}`} />
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Feedback Dialog */}
      <Dialog open={feedbackDialogOpen} onOpenChange={setFeedbackDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {feedbackType === "up" ? "What did you like?" : "What went wrong?"}
            </DialogTitle>
            <DialogDescription>
              {feedbackType === "up" 
                ? "Your feedback helps Internal Platform learn what works well and improve future responses."
                : "Your feedback helps Internal Platform learn from mistakes and improve the quality of future responses."
              }
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Textarea
              placeholder={feedbackType === "up" 
                ? "Tell us what you liked about this response..."
                : "Tell us what could be improved..."
              }
              value={feedbackComment}
              onChange={(e) => setFeedbackComment(e.target.value)}
              className="min-h-[100px] text-[13px]"
            />
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={handleFeedbackCancel}>
              Cancel
            </Button>
            <Button onClick={handleFeedbackSubmit}>
              Submit Feedback
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}