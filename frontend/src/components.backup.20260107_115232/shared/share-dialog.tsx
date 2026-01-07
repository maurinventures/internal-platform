import { useState } from "react";
import { X, Trash2, ChevronDown } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { ScrollArea } from "../ui/scroll-area";

/*
  SHARE DIALOG - Invite-Only Sharing Model
  
  SHARING MODEL:
  1. Individual File/Chat Sharing:
     - Share specific chats/files with selected users
     - Permissions: Viewer, Commenter, Editor
  
  2. Project Sharing:
     - Share entire project = all files inherit permissions
     - Users get access to everything in the project
  
  3. Access Control:
     - INVITE-ONLY: Users MUST be explicitly invited by owner
     - NO link sharing - no "Anyone with link" option
     - Only invited users can access resources
  
  BACKEND INTEGRATION (RDS):
  - Table: file_permissions (file_id, user_id, role, granted_at, granted_by)
  - Table: project_permissions (project_id, user_id, role, granted_at, granted_by)
*/

interface SharedUser {
  id: string;
  name: string;
  email: string;
  initials: string;
  role: "viewer" | "commenter" | "editor" | "owner";
}

interface ShareDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  resourceType: "chat" | "project";
  resourceName: string;
  resourceId: string;
  // Current sharing settings
  currentUsers?: SharedUser[];
}

// Mock organization users for demonstration
const MOCK_ORG_USERS = [
  { id: "1", name: "Sarah Chen", email: "sarah@resonance.ai", initials: "SC" },
  { id: "2", name: "Mike Johnson", email: "mike@resonance.ai", initials: "MJ" },
  { id: "3", name: "Emily Rodriguez", email: "emily@resonance.ai", initials: "ER" },
  { id: "4", name: "David Kim", email: "david@resonance.ai", initials: "DK" },
  { id: "5", name: "Alex Turner", email: "alex@resonance.ai", initials: "AT" },
];

export function ShareDialog({
  open,
  onOpenChange,
  resourceType,
  resourceName,
  resourceId,
  currentUsers = [],
}: ShareDialogProps) {
  const [emailInput, setEmailInput] = useState("");
  const [selectedRole, setSelectedRole] = useState<"viewer" | "commenter" | "editor">("viewer");
  const [sharedUsers, setSharedUsers] = useState<SharedUser[]>(currentUsers);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Filter suggestions based on email input
  const suggestions = MOCK_ORG_USERS.filter(user => 
    (user.email.toLowerCase().includes(emailInput.toLowerCase()) ||
     user.name.toLowerCase().includes(emailInput.toLowerCase())) &&
    !sharedUsers.some(su => su.id === user.id)
  );

  const handleAddUser = (user: typeof MOCK_ORG_USERS[0]) => {
    const newUser: SharedUser = {
      ...user,
      role: selectedRole,
    };
    
    setSharedUsers([...sharedUsers, newUser]);
    setEmailInput("");
    setShowSuggestions(false);
    
    // TODO: API call to backend - MUST update in real-time
    // POST /api/share/${resourceType}/${resourceId}
    // Body: { userId: user.id, role: selectedRole }
    // 
    // CRITICAL: Access must be granted immediately in RDS:
    // - Insert into file_permissions or project_permissions table
    // - User gets immediate access (no delay)
    // - Email notification sent to user about new access
    
    toast.success(`Access updated: ${user.name} can now ${selectedRole === "viewer" ? "view" : selectedRole === "commenter" ? "view and comment on" : "edit"} this ${resourceType}`);
  };

  const handleRemoveUser = (userId: string) => {
    const removedUser = sharedUsers.find(u => u.id === userId);
    setSharedUsers(sharedUsers.filter(u => u.id !== userId));
    
    // TODO: API call to backend - MUST update in real-time
    // DELETE /api/share/${resourceType}/${resourceId}/users/${userId}
    // 
    // CRITICAL: Access must be revoked immediately in RDS:
    // - Delete from file_permissions or project_permissions table
    // - User loses access immediately (no delay)
    // - Email notification sent to user about access removal
    
    toast.success(`Access updated: ${removedUser?.name || "User"}'s access has been removed`);
  };

  const handleChangeUserRole = (userId: string, newRole: "viewer" | "commenter" | "editor") => {
    const user = sharedUsers.find(u => u.id === userId);
    setSharedUsers(sharedUsers.map(u => 
      u.id === userId ? { ...u, role: newRole } : u
    ));
    
    // TODO: API call to backend - MUST update in real-time
    // PATCH /api/share/${resourceType}/${resourceId}/users/${userId}
    // Body: { role: newRole }
    // 
    // CRITICAL: Permission must be updated immediately in RDS:
    // - Update file_permissions or project_permissions table
    // - User's access level changes immediately (no delay)
    // - Email notification sent to user about permission change
    
    toast.success(`Access updated: ${user?.name || "User"} can now ${newRole === "viewer" ? "view" : newRole === "commenter" ? "view and comment on" : "edit"} this ${resourceType}`);
  };

  const getRoleLabel = (role: string) => {
    switch (role) {
      case "owner": return "Owner";
      case "editor": return "Can edit";
      case "commenter": return "Can comment";
      case "viewer": return "Can view";
      default: return role;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[520px]">
        <DialogHeader>
          <DialogTitle className="text-[16px]">
            Share "{resourceName}"
          </DialogTitle>
          <DialogDescription className="text-[12px]">
            {resourceType === "project" 
              ? "Share this project and all its files with others"
              : "Share this conversation with others"
            }
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Add People */}
          <div className="space-y-2">
            <Label className="text-[12px] text-muted-foreground">Add people</Label>
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <Input
                  placeholder="Enter email address"
                  value={emailInput}
                  onChange={(e) => {
                    setEmailInput(e.target.value);
                    setShowSuggestions(e.target.value.length > 0);
                  }}
                  onFocus={() => setShowSuggestions(emailInput.length > 0)}
                  className="text-[13px]"
                />
                
                {/* Suggestions Dropdown */}
                {showSuggestions && suggestions.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-1 bg-background border border-border rounded-lg shadow-lg z-50 max-h-[200px] overflow-auto">
                    {suggestions.map((user) => (
                      <button
                        key={user.id}
                        onClick={() => handleAddUser(user)}
                        className="w-full px-3 py-2 hover:bg-muted transition-colors flex items-center gap-3 text-left"
                      >
                        <Avatar className="h-8 w-8">
                          <AvatarFallback className="text-[11px] bg-primary/10 text-primary">
                            {user.initials}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1 min-w-0">
                          <div className="text-[12px] font-medium truncate">{user.name}</div>
                          <div className="text-[11px] text-muted-foreground truncate">{user.email}</div>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
              
              <Select value={selectedRole} onValueChange={(value: any) => setSelectedRole(value)}>
                <SelectTrigger className="w-[140px] text-[12px] h-9">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="viewer" className="text-[12px]">
                    <div className="flex flex-col items-start">
                      <span>Viewer</span>
                      <span className="text-[10px] text-muted-foreground">Can view</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="commenter" className="text-[12px]">
                    <div className="flex flex-col items-start">
                      <span>Commenter</span>
                      <span className="text-[10px] text-muted-foreground">Can comment</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="editor" className="text-[12px]">
                    <div className="flex flex-col items-start">
                      <span>Editor</span>
                      <span className="text-[10px] text-muted-foreground">Can edit</span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* People with Access */}
          <div className="space-y-2">
            <Label className="text-[12px] text-muted-foreground">People with access</Label>
            <ScrollArea className="max-h-[200px]">
              <div className="space-y-1">
                {sharedUsers.map((user) => (
                  <div key={user.id} className="flex items-center gap-3 py-2 px-2 hover:bg-muted rounded-md group">
                    <Avatar className="h-8 w-8">
                      <AvatarFallback className="text-[11px] bg-primary/10 text-primary">
                        {user.initials}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <div className="text-[12px] font-medium truncate">{user.name}</div>
                      <div className="text-[11px] text-muted-foreground truncate">{user.email}</div>
                    </div>
                    
                    {user.role === "owner" ? (
                      <div className="text-[12px] text-muted-foreground px-3">Owner</div>
                    ) : (
                      <div className="flex items-center gap-1">
                        <Select 
                          value={user.role} 
                          onValueChange={(value: any) => handleChangeUserRole(user.id, value)}
                        >
                          <SelectTrigger className="w-[120px] text-[12px] h-7 border-0 hover:bg-muted">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="viewer" className="text-[12px]">
                              {getRoleLabel("viewer")}
                            </SelectItem>
                            <SelectItem value="commenter" className="text-[12px]">
                              {getRoleLabel("commenter")}
                            </SelectItem>
                            <SelectItem value="editor" className="text-[12px]">
                              {getRoleLabel("editor")}
                            </SelectItem>
                          </SelectContent>
                        </Select>
                        
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={() => handleRemoveUser(user.id)}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    )}
                  </div>
                ))}
                
                {sharedUsers.length === 0 && (
                  <div className="text-[12px] text-muted-foreground text-center py-6">
                    No one has access yet. Add people above to share.
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>

          {/* Done Button */}
          <div className="flex justify-end pt-2">
            <Button
              onClick={() => onOpenChange(false)}
              className="text-[12px] h-9"
            >
              Done
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}