import { Sparkles } from "lucide-react";
import { getGreeting } from "../../utils/greeting";

interface EmptyStateProps {
  onPromptClick: (prompt: string) => void;
  chatInput: React.ReactNode;
  userName?: string;
  userTimezone?: string;
}

export function EmptyState({ onPromptClick, chatInput, userName = "Joseph", userTimezone = "America/New_York" }: EmptyStateProps) {
  const greeting = getGreeting(userName, userTimezone);

  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="max-w-3xl w-full px-6">
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <h1 className="text-2xl">{greeting}</h1>
          </div>
        </div>
        {chatInput}
      </div>
    </div>
  );
}