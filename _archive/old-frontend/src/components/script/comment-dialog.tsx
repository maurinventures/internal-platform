import { useState, useRef } from "react";
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
import { Avatar, AvatarFallback } from "../ui/avatar";
import { AtSign } from "lucide-react";
import { ScrollArea } from "../ui/scroll-area";

interface Comment {
  id: string;
  user: {
    name: string;
    initials: string;
    email: string;
  };
  content: string;
  timestamp: Date;
  taggedUsers: string[];
}

interface CommentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  clipNumber: number;
  existingComments: Comment[];
  onSubmit: (comment: string, taggedUsers: string[]) => void;
}

/*
  COMMENT TAGGING - Permissions-Based User Filtering
  
  IMPORTANT: Only users with access to this file/project can be tagged in comments.
  
  PERMISSION-BASED FILTERING:
  1. When this dialog opens, fetch list of users who have access to this clip/file
  2. Access can come from:
     - Direct file sharing (user was explicitly shared this file)
     - Project sharing (user has access to the parent project)
  3. Only show these users in the MOCK_USERS list / autocomplete suggestions
  
  CURRENT STATE (Mock):
  - MOCK_USERS shows all users in the organization
  - This is for demonstration only
  
  PRODUCTION IMPLEMENTATION:
  - Replace MOCK_USERS with API call: GET /api/files/{fileId}/shared-users
  - API should return users with ANY level of access (Viewer, Commenter, Editor)
  - Filter users based on permissions from RDS:
    * Check file_permissions table for direct shares
    * Check project_permissions table for inherited project access
  - Union both lists to get all users who can be tagged
  
  BACKEND QUERY EXAMPLE (RDS):
    SELECT DISTINCT u.id, u.name, u.email, u.initials
    FROM users u
    WHERE u.id IN (
      -- Direct file permissions
      SELECT user_id FROM file_permissions 
      WHERE file_id = ? AND role IN ('viewer', 'commenter', 'editor')
      UNION
      -- Project-level permissions (inherited)
      SELECT user_id FROM project_permissions pp
      JOIN files f ON f.project_id = pp.project_id
      WHERE f.id = ? AND pp.role IN ('viewer', 'commenter', 'editor')
    )
  
  UI BEHAVIOR:
  - Show "No users to tag" message if list is empty (file not shared)
  - In autocomplete, show user name, email, and access level badge
  - Prevent tagging users who don't have access (client-side validation)
*/

// Mock users for tagging
const MOCK_USERS = [
  { id: "1", name: "Sarah Chen", email: "sarah@resonance.ai", initials: "SC" },
  { id: "2", name: "Mike Johnson", email: "mike@resonance.ai", initials: "MJ" },
  { id: "3", name: "Emily Rodriguez", email: "emily@resonance.ai", initials: "ER" },
  { id: "4", name: "David Kim", email: "david@resonance.ai", initials: "DK" },
];

export function CommentDialog({
  open,
  onOpenChange,
  clipNumber,
  existingComments,
  onSubmit,
}: CommentDialogProps) {
  const [comment, setComment] = useState("");
  const [showUserSuggestions, setShowUserSuggestions] = useState(false);
  const [userSearchQuery, setUserSearchQuery] = useState("");
  const [taggedUsers, setTaggedUsers] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Filter users based on search
  const filteredUsers = MOCK_USERS.filter(
    (user) =>
      user.name.toLowerCase().includes(userSearchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(userSearchQuery.toLowerCase())
  );

  const handleCommentChange = (value: string) => {
    setComment(value);

    // Check if user is typing @mention
    const cursorPos = textareaRef.current?.selectionStart || 0;
    const textBeforeCursor = value.slice(0, cursorPos);
    const lastAtIndex = textBeforeCursor.lastIndexOf("@");

    if (
      lastAtIndex !== -1 &&
      !textBeforeCursor.slice(lastAtIndex).includes(" ")
    ) {
      const query = textBeforeCursor.slice(lastAtIndex + 1);
      setUserSearchQuery(query);
      setShowUserSuggestions(true);
    } else {
      setShowUserSuggestions(false);
    }
  };

  const handleUserSelect = (user: typeof MOCK_USERS[0]) => {
    const cursorPos = textareaRef.current?.selectionStart || 0;
    const textBeforeCursor = comment.slice(0, cursorPos);
    const textAfterCursor = comment.slice(cursorPos);
    const lastAtIndex = textBeforeCursor.lastIndexOf("@");

    const newComment =
      comment.slice(0, lastAtIndex) +
      `@${user.name} ` +
      textAfterCursor;

    setComment(newComment);
    setShowUserSuggestions(false);
    
    // Track tagged users
    if (!taggedUsers.includes(user.id)) {
      setTaggedUsers([...taggedUsers, user.id]);
    }

    // Focus back on textarea
    setTimeout(() => {
      textareaRef.current?.focus();
    }, 0);
  };

  const handleSubmit = async () => {
    if (!comment.trim()) return;

    setIsSubmitting(true);
    await onSubmit(comment, taggedUsers);
    setIsSubmitting(false);
    setComment("");
    setTaggedUsers([]);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[80vh] flex flex-col p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b border-border">
          <DialogTitle className="text-base">
            Comments {existingComments.length > 0 && `(${existingComments.length})`}
          </DialogTitle>
          <DialogDescription className="text-[13px]">
            Clip {clipNumber} • Tag team members with @ to assign work or get feedback
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 flex flex-col min-h-0">
          {/* Existing comments */}
          {existingComments.length > 0 && (
            <ScrollArea className="flex-1 px-6 py-4">
              <div className="space-y-4">
                {existingComments.map((existingComment) => (
                  <div key={existingComment.id} className="flex gap-3">
                    <Avatar className="h-8 w-8 flex-shrink-0 mt-1">
                      <AvatarFallback className="text-[11px] bg-primary/10 text-primary">
                        {existingComment.user.initials}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-[13px]">{existingComment.user.name}</span>
                        <span className="text-[11px] text-muted-foreground">
                          {new Date(existingComment.timestamp).toLocaleString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            hour: 'numeric',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                      <p className="text-[13px] text-foreground whitespace-pre-wrap">
                        {existingComment.content}
                      </p>
                      {existingComment.taggedUsers.length > 0 && (
                        <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                          <AtSign className="h-3 w-3 text-muted-foreground" />
                          {existingComment.taggedUsers.map((userId) => {
                            const user = MOCK_USERS.find((u) => u.id === userId);
                            return user ? (
                              <span
                                key={userId}
                                className="inline-flex items-center px-1.5 py-0.5 rounded bg-muted text-[10px] font-medium text-muted-foreground"
                              >
                                {user.name}
                              </span>
                            ) : null;
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}

          {/* Empty state */}
          {existingComments.length === 0 && (
            <div className="flex-1 flex items-center justify-center px-6 py-8">
              <p className="text-[13px] text-muted-foreground">No comments yet. Be the first to comment!</p>
            </div>
          )}

          {/* New comment input - fixed at bottom */}
          <div className="border-t border-border px-6 py-4 bg-muted/30">
            <div className="space-y-3 relative">
              <Textarea
                ref={textareaRef}
                value={comment}
                onChange={(e) => handleCommentChange(e.target.value)}
                placeholder="Type @ to tag someone... e.g., @Sarah can you review this clip?"
                className="min-h-[80px] text-[13px] resize-none"
              />

              {/* User mention suggestions */}
              {showUserSuggestions && filteredUsers.length > 0 && (
                <div className="absolute bottom-full left-0 right-0 mb-2 bg-background border border-border rounded-lg shadow-xl z-20 max-h-[200px] overflow-y-auto">
                  {filteredUsers.map((user) => (
                    <div
                      key={user.id}
                      className="flex items-center gap-3 px-3 py-2.5 cursor-pointer hover:bg-primary/5 transition-colors"
                      onClick={() => handleUserSelect(user)}
                    >
                      <Avatar className="h-7 w-7">
                        <AvatarFallback className="text-[11px] bg-primary/10 text-primary">
                          {user.initials}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-[13px]">{user.name}</div>
                        <div className="text-[11px] text-muted-foreground truncate">
                          {user.email}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {taggedUsers.length > 0 && (
                <div className="flex items-center gap-2 flex-wrap">
                  <AtSign className="h-4 w-4 text-muted-foreground" />
                  <span className="text-[12px] text-muted-foreground">Tagged:</span>
                  {taggedUsers.map((userId) => {
                    const user = MOCK_USERS.find((u) => u.id === userId);
                    return user ? (
                      <span
                        key={userId}
                        className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-primary/10 text-primary text-[11px] font-medium"
                      >
                        {user.name}
                      </span>
                    ) : null;
                  })}
                </div>
              )}

              <div className="flex items-center justify-between">
                <p className="text-[11px] text-muted-foreground">
                  💡 Tagged users will be notified
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    onClick={() => onOpenChange(false)}
                    className="text-[13px] h-8"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSubmit}
                    disabled={!comment.trim() || isSubmitting}
                    className="text-[13px] h-8"
                  >
                    {isSubmitting ? "Posting..." : "Post Comment"}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}