import { useTheme } from "next-themes";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "./ui/dialog";
import { Label } from "./ui/label";
import { Switch } from "./ui/switch";
import { Button } from "./ui/button";
import { Moon, Sun, Monitor, LogOut } from "lucide-react";

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onLogout?: () => void;
  userEmail?: string;
}

export function SettingsDialog({ open, onOpenChange, onLogout, userEmail }: SettingsDialogProps) {
  const { theme, setTheme } = useTheme();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>
            Customize your Resonance AI experience
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Theme Selection */}
          <div className="space-y-4">
            <Label>Appearance</Label>
            <div className="grid grid-cols-3 gap-3">
              <Button
                variant={theme === "light" ? "default" : "outline"}
                className="flex flex-col items-center gap-2 h-auto py-3"
                onClick={() => setTheme("light")}
              >
                <Sun className="h-5 w-5" />
                <span className="text-xs">Light</span>
              </Button>
              <Button
                variant={theme === "dark" ? "default" : "outline"}
                className="flex flex-col items-center gap-2 h-auto py-3"
                onClick={() => setTheme("dark")}
              >
                <Moon className="h-5 w-5" />
                <span className="text-xs">Dark</span>
              </Button>
              <Button
                variant={theme === "system" ? "default" : "outline"}
                className="flex flex-col items-center gap-2 h-auto py-3"
                onClick={() => setTheme("system")}
              >
                <Monitor className="h-5 w-5" />
                <span className="text-xs">System</span>
              </Button>
            </div>
          </div>

          {/* Notification Settings */}
          <div className="space-y-3">
            <Label>Notifications</Label>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="text-sm">Enable notifications</div>
                <div className="text-xs text-muted-foreground">
                  Get notified when your content is ready
                </div>
              </div>
              <Switch defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="text-sm">Sound effects</div>
                <div className="text-xs text-muted-foreground">
                  Play sounds for interactions
                </div>
              </div>
              <Switch />
            </div>
          </div>

          {/* AI Settings */}
          <div className="space-y-3">
            <Label>AI Preferences</Label>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="text-sm">Auto-save conversations</div>
                <div className="text-xs text-muted-foreground">
                  Automatically save all chat history
                </div>
              </div>
              <Switch defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="text-sm">Streaming responses</div>
                <div className="text-xs text-muted-foreground">
                  Show AI responses as they're generated
                </div>
              </div>
              <Switch defaultChecked />
            </div>
          </div>

          {/* Keyboard Shortcuts */}
          <div className="space-y-3">
            <Label>Keyboard Shortcuts</Label>
            <div className="text-xs text-muted-foreground space-y-2">
              <div className="flex justify-between">
                <span>New chat</span>
                <kbd className="px-2 py-1 text-xs font-semibold text-foreground bg-muted border border-border rounded">
                  Cmd + N
                </kbd>
              </div>
              <div className="flex justify-between">
                <span>Search</span>
                <kbd className="px-2 py-1 text-xs font-semibold text-foreground bg-muted border border-border rounded">
                  Cmd + K
                </kbd>
              </div>
              <div className="flex justify-between">
                <span>Toggle sidebar</span>
                <kbd className="px-2 py-1 text-xs font-semibold text-foreground bg-muted border border-border rounded">
                  Cmd + B
                </kbd>
              </div>
            </div>
          </div>

          {/* Account Information */}
          {userEmail && (
            <div className="space-y-3">
              <Label>Account</Label>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <div className="text-sm">Email</div>
                  <div className="text-xs text-muted-foreground">
                    {userEmail}
                  </div>
                </div>
                <Button
                  variant="outline"
                  className="flex flex-col items-center gap-2 h-auto py-3"
                  onClick={onLogout}
                >
                  <LogOut className="h-5 w-5" />
                  <span className="text-xs">Logout</span>
                </Button>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}