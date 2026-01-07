import { useState } from "react";
import { Button } from "../ui/button";
import { Download, Search, MessageSquare, ThumbsUp, ThumbsDown, Video, Music, Loader2, Eye } from "lucide-react";
import { FeedbackDialog } from "./feedback-dialog";
import { AlternativeDialog } from "./alternative-dialog";
import { CommentDialog } from "./comment-dialog";
import { toast } from "sonner";

interface AssetClipCardProps {
  type: "video" | "audio";
  thumbnail?: string;
  waveform?: string;
  sourceFile: string;
  startTime: string;
  endTime: string;
  duration: string;
  transcript: string;
  visualAnalysis?: string; // AI analysis of what's happening visually
  clipNumber: number;
}

export function AssetClipCard({
  type,
  thumbnail,
  waveform,
  sourceFile,
  startTime,
  endTime,
  duration,
  transcript,
  visualAnalysis,
  clipNumber,
}: AssetClipCardProps) {
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);
  const [showFeedbackDialog, setShowFeedbackDialog] = useState(false);
  const [feedbackType, setFeedbackType] = useState<"positive" | "negative">("positive");
  const [showAlternativeDialog, setShowAlternativeDialog] = useState(false);
  const [showCommentDialog, setShowCommentDialog] = useState(false);
  const [downloadingClip, setDownloadingClip] = useState(false);
  const [downloadingFull, setDownloadingFull] = useState(false);

  // Mock existing comments (in production, this would come from props or API)
  const [comments, setComments] = useState<Array<{
    id: string;
    user: { name: string; initials: string; email: string };
    content: string;
    timestamp: Date;
    taggedUsers: string[];
  }>>([]);

  // Simulate downloading a clip
  const handleDownloadClip = async () => {
    setDownloadingClip(true);
    
    try {
      // Simulate API call and download
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Create a mock file and trigger download
      const blob = new Blob([`Mock ${type} clip content for ${sourceFile}`], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${sourceFile.replace(/\.[^/.]+$/, "")}_clip_${clipNumber}.${type === 'video' ? 'mp4' : 'mp3'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast.success("Download Complete", {
        description: `Clip ${clipNumber} has been downloaded to your Downloads folder.`,
      });
    } catch (error) {
      toast.error("Download Failed", {
        description: "There was an error downloading the clip.",
      });
    } finally {
      setDownloadingClip(false);
    }
  };

  // Simulate downloading full source
  const handleDownloadFull = async () => {
    setDownloadingFull(true);
    
    try {
      // Simulate API call and download
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Create a mock file and trigger download
      const blob = new Blob([`Mock full ${type} source for ${sourceFile}`], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = sourceFile;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast.success("Download Complete", {
        description: `Full source "${sourceFile}" has been downloaded to your Downloads folder.`,
      });
    } catch (error) {
      toast.error("Download Failed", {
        description: "There was an error downloading the full source.",
      });
    } finally {
      setDownloadingFull(false);
    }
  };

  const handleThumbsUp = () => {
    if (feedback === "up") {
      setFeedback(null);
    } else {
      setFeedback("up");
      setFeedbackType("positive");
      setShowFeedbackDialog(true);
    }
  };

  const handleThumbsDown = () => {
    if (feedback === "down") {
      setFeedback(null);
    } else {
      setFeedback("down");
      setFeedbackType("negative");
      setShowFeedbackDialog(true);
    }
  };

  const handleFeedbackSubmit = async (feedbackText: string) => {
    // Log to backend (RDS)
    console.log("Logging feedback to RDS:", {
      clipNumber,
      sourceFile,
      feedbackType,
      feedback: feedbackText,
      timestamp: new Date().toISOString(),
    });

    // TODO: Send to backend API
    // await fetch('/api/feedback', {
    //   method: 'POST',
    //   body: JSON.stringify({
    //     clipNumber,
    //     sourceFile,
    //     type: feedbackType,
    //     feedback: feedbackText,
    //   })
    // });

    toast.success("Feedback Submitted", {
      description: "Thank you! Your feedback helps our AI learn and improve.",
    });
  };

  const handleAlternativeSubmit = async (requirements: string) => {
    // Log to backend and trigger alternative search
    console.log("Finding alternative clip:", {
      clipNumber,
      sourceFile,
      requirements,
      timestamp: new Date().toISOString(),
    });

    // TODO: Send to backend API to search for alternatives
    // await fetch('/api/clips/find-alternative', {
    //   method: 'POST',
    //   body: JSON.stringify({
    //     clipNumber,
    //     sourceFile,
    //     requirements,
    //   })
    // });

    toast.info("Searching for Alternatives", {
      description: "We're looking for clips that match your requirements...",
    });
  };

  const handleCommentSubmit = async (comment: string, taggedUsers: string[]) => {
    // Create new comment
    const newComment = {
      id: String(comments.length + 1),
      user: {
        name: "You", // In production, get from auth context
        initials: "YO",
        email: "you@resonance.ai",
      },
      content: comment,
      timestamp: new Date(),
      taggedUsers,
    };

    // Add to local state
    setComments([...comments, newComment]);

    // Log to backend (RDS)
    console.log("Logging comment to RDS:", {
      clipNumber,
      sourceFile,
      comment,
      taggedUsers,
      timestamp: new Date().toISOString(),
    });

    // TODO: Send to backend API
    // await fetch('/api/comments', {
    //   method: 'POST',
    //   body: JSON.stringify({
    //     clipNumber,
    //     sourceFile,
    //     comment,
    //     taggedUsers,
    //   })
    // });

    toast.success("Comment Posted", {
      description: taggedUsers.length > 0 
        ? `Comment posted and ${taggedUsers.length} user(s) notified.`
        : "Comment posted successfully.",
    });
  };

  return (
    <>
      <div className="border border-border rounded-lg p-4 bg-card hover:border-primary/50 transition-colors">
        <div className="space-y-3">
          {/* Header with thumbnail on the right */}
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary/10 text-primary">
                  Clip {clipNumber}
                </span>
                <span className="text-xs text-muted-foreground">{duration}</span>
              </div>
              <p className="text-sm font-medium">{sourceFile}</p>
              <p className="text-xs text-muted-foreground">
                {startTime} → {endTime}
              </p>
            </div>

            {/* Thumbnail - Compact on the right */}
            <div className="flex-shrink-0">
              {type === "video" && thumbnail ? (
                <div className="w-24 h-16 rounded bg-muted flex items-center justify-center overflow-hidden">
                  <img src={thumbnail} alt="Video thumbnail" className="w-full h-full object-cover" />
                </div>
              ) : (
                <div className="w-24 h-16 rounded bg-muted flex items-center justify-center">
                  {type === "video" ? (
                    <Video className="h-6 w-6 text-muted-foreground" />
                  ) : (
                    <Music className="h-6 w-6 text-muted-foreground" />
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Transcript */}
          <div className="p-3 bg-muted/50 rounded border border-border">
            <p className="text-sm text-foreground line-clamp-3">{transcript}</p>
          </div>

          {/* Visual Analysis */}
          {visualAnalysis && (
            <div className="p-3 bg-primary/5 rounded border border-primary/20">
              <div className="flex items-start gap-2">
                <Eye className="h-4 w-4 text-primary flex-shrink-0 mt-0.5" />
                <p className="text-sm text-foreground line-clamp-3 flex-1">{visualAnalysis}</p>
              </div>
            </div>
          )}

          {/* Actions - Aligned with AI Segment Card */}
          <div className="flex items-center gap-2 flex-wrap">
            <Button 
              size="sm" 
              variant="default" 
              className="h-7 text-[12px]"
              onClick={handleDownloadClip}
              disabled={downloadingClip}
            >
              {downloadingClip ? (
                <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
              ) : (
                <Download className="mr-1 h-3.5 w-3.5" />
              )}
              {downloadingClip ? "Downloading..." : "Clip"}
            </Button>
            <Button 
              size="sm" 
              variant="outline" 
              className="h-7 text-[12px]"
              onClick={handleDownloadFull}
              disabled={downloadingFull}
            >
              {downloadingFull ? (
                <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
              ) : (
                <Download className="mr-1 h-3.5 w-3.5" />
              )}
              {downloadingFull ? "Downloading..." : "Full"}
            </Button>
            <Button 
              size="sm" 
              variant="outline" 
              className="h-7 text-[12px]"
              onClick={() => setShowAlternativeDialog(true)}
            >
              <Search className="mr-1 h-3.5 w-3.5" />
              Alternative
            </Button>
            <Button 
              size="sm" 
              variant="outline" 
              className="h-7 text-[12px] relative"
              onClick={() => setShowCommentDialog(true)}
            >
              <MessageSquare className="mr-1 h-3.5 w-3.5" />
              Comment
              {comments.length > 0 && (
                <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-destructive text-[10px] font-bold text-destructive-foreground flex items-center justify-center">
                  {comments.length}
                </span>
              )}
            </Button>
            
            {/* Thumbs up/down aligned to right */}
            <div className="ml-auto flex items-center gap-1">
              <Button
                size="sm"
                variant="ghost"
                className="h-7 w-7 p-0"
                onClick={handleThumbsUp}
              >
                <ThumbsUp className={`h-3.5 w-3.5 ${feedback === "up" ? "fill-current text-primary" : ""}`} />
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 w-7 p-0"
                onClick={handleThumbsDown}
              >
                <ThumbsDown className={`h-3.5 w-3.5 ${feedback === "down" ? "fill-current text-destructive" : ""}`} />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Dialogs */}
      <FeedbackDialog
        open={showFeedbackDialog}
        onOpenChange={setShowFeedbackDialog}
        type={feedbackType}
        clipNumber={clipNumber}
        onSubmit={handleFeedbackSubmit}
      />

      <AlternativeDialog
        open={showAlternativeDialog}
        onOpenChange={setShowAlternativeDialog}
        clipNumber={clipNumber}
        currentSource={sourceFile}
        onSubmit={handleAlternativeSubmit}
      />

      <CommentDialog
        open={showCommentDialog}
        onOpenChange={setShowCommentDialog}
        clipNumber={clipNumber}
        existingComments={comments}
        onSubmit={handleCommentSubmit}
      />
    </>
  );
}