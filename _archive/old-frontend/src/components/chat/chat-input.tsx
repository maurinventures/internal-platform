import { useState, useRef, useEffect } from "react";
import { Button } from "../ui/button";
import { Textarea } from "../ui/textarea";
import { Send, ChevronDown, Video } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  SelectGroup,
  SelectLabel,
  SelectSeparator,
} from "../ui/select";

interface ChatInputProps {
  onSend: (message: string, persona: string, attachments: File[], isVideoScript?: boolean) => void;
  disabled?: boolean;
  model?: string;
  onModelChange?: (model: string) => void;
  centered?: boolean;
}

export function ChatInput({ onSend, disabled, model = "claude-3-5-sonnet", onModelChange, centered = false }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestionIndex, setSuggestionIndex] = useState(0);
  const [cursorPosition, setCursorPosition] = useState({ top: 0, left: 0 });
  const [searchQuery, setSearchQuery] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Available mentions/commands
  const suggestions = [
    { label: "@video", description: "Generate a video script", category: "Media" },
    // Future: @audio, @image, @doc, etc.
  ];

  // Detect @video mention
  const hasVideoMention = message.includes("@video");

  // Filter suggestions based on search query
  const filteredSuggestions = suggestions.filter(s => 
    s.label.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Get the current suggestion for ghost text
  const currentSuggestion = filteredSuggestions[suggestionIndex];
  
  // Calculate ghost text (inline preview)
  const getGhostText = () => {
    if (!showSuggestions || !currentSuggestion) return "";
    
    const remaining = currentSuggestion.label.slice(searchQuery.length);
    return remaining;
  };

  // Check if user is typing a mention
  useEffect(() => {
    const text = message;
    const cursorPos = textareaRef.current?.selectionStart || 0;
    
    // Find @ symbol before cursor
    const textBeforeCursor = text.slice(0, cursorPos);
    const lastAtIndex = textBeforeCursor.lastIndexOf("@");
    
    if (lastAtIndex !== -1 && !textBeforeCursor.slice(lastAtIndex).includes(" ")) {
      // We're in a mention
      const query = textBeforeCursor.slice(lastAtIndex);
      setSearchQuery(query);
      setShowSuggestions(true);
      setSuggestionIndex(0);
      
      // Calculate dropdown position based on cursor
      if (textareaRef.current) {
        const textarea = textareaRef.current;
        const style = window.getComputedStyle(textarea);
        const fontSize = parseFloat(style.fontSize);
        const lineHeight = parseFloat(style.lineHeight) || fontSize * 1.5;
        
        // Approximate position (simplified)
        setCursorPosition({ top: lineHeight * 2, left: 16 });
      }
    } else {
      setShowSuggestions(false);
      setSearchQuery("");
    }
  }, [message]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim()) {
      // Remove @video from the message before sending
      const cleanMessage = message.replace(/@video\s*/gi, "").trim();
      onSend(cleanMessage, "default", [], hasVideoMention);
      setMessage("");
      setShowSuggestions(false);
    }
  };

  const acceptSuggestion = () => {
    if (!currentSuggestion) return;
    
    const cursorPos = textareaRef.current?.selectionStart || 0;
    const textBeforeCursor = message.slice(0, cursorPos);
    const textAfterCursor = message.slice(cursorPos);
    const lastAtIndex = textBeforeCursor.lastIndexOf("@");
    
    // Replace from @ to cursor with the full suggestion
    const newMessage = 
      message.slice(0, lastAtIndex) + 
      currentSuggestion.label + " " + 
      textAfterCursor;
    
    setMessage(newMessage);
    setShowSuggestions(false);
    
    // Set cursor after the inserted mention
    setTimeout(() => {
      if (textareaRef.current) {
        const newCursorPos = lastAtIndex + currentSuggestion.label.length + 1;
        textareaRef.current.selectionStart = newCursorPos;
        textareaRef.current.selectionEnd = newCursorPos;
        textareaRef.current.focus();
      }
    }, 0);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (showSuggestions) {
      if (e.key === "Tab" || (e.key === "Enter" && filteredSuggestions.length > 0)) {
        e.preventDefault();
        acceptSuggestion();
        return;
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setSuggestionIndex((prev) => (prev + 1) % filteredSuggestions.length);
        return;
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSuggestionIndex((prev) => (prev - 1 + filteredSuggestions.length) % filteredSuggestions.length);
        return;
      } else if (e.key === "Escape") {
        e.preventDefault();
        setShowSuggestions(false);
        return;
      }
    }
    
    if (e.key === "Enter" && !e.shiftKey && !showSuggestions) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const modelDisplayNames: Record<string, string> = {
    "claude-3-5-opus": "Claude 3.5 Opus",
    "claude-3-5-sonnet": "Claude 3.5 Sonnet",
    "claude-3-5-haiku": "Claude 3.5 Haiku",
    "claude-3-opus": "Claude 3 Opus",
    "claude-3-sonnet": "Claude 3 Sonnet",
    "claude-3-haiku": "Claude 3 Haiku",
    "gpt-4o": "GPT-4o",
    "gpt-4-turbo": "GPT-4 Turbo",
    "gpt-4": "GPT-4",
    "gpt-3.5-turbo": "GPT-3.5 Turbo",
    "o1": "o1",
    "o1-mini": "o1-mini",
  };

  return (
    <div className={centered ? "" : "bg-background"}>
      <div className={`max-w-3xl mx-auto py-4 ${centered ? "" : "px-6"}`}>
        {/* Input Area */}
        <form onSubmit={handleSubmit} className="relative">
          {/* Suggestions - positioned below cursor inline */}
          {showSuggestions && filteredSuggestions.length > 0 && (
            <div className="absolute left-0 bottom-full mb-2 w-[320px] bg-background border border-border rounded-lg shadow-xl z-20 overflow-hidden">
              {filteredSuggestions.map((suggestion, index) => (
                <div
                  key={suggestion.label}
                  className={`flex items-center gap-3 px-3 py-2.5 cursor-pointer transition-colors ${
                    index === suggestionIndex ? 'bg-primary/10' : 'hover:bg-muted/50'
                  }`}
                  onClick={() => {
                    setSuggestionIndex(index);
                    acceptSuggestion();
                  }}
                  onMouseEnter={() => setSuggestionIndex(index)}
                >
                  <Video className="h-4 w-4 text-primary flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-[13px]">{suggestion.label}</div>
                    <div className="text-[11px] text-muted-foreground truncate">{suggestion.description}</div>
                  </div>
                  {index === suggestionIndex && (
                    <kbd className="px-1.5 py-0.5 bg-muted text-[10px] rounded border border-border font-mono flex-shrink-0">↵</kbd>
                  )}
                </div>
              ))}
            </div>
          )}

          <div className="relative border border-border rounded-xl bg-background shadow-sm hover:shadow-md hover:border-primary/30 focus-within:border-primary focus-within:shadow-md transition-all duration-200">
            {/* @video badge */}
            {hasVideoMention && (
              <div className="absolute top-3 left-4 z-10 flex items-center gap-1.5 px-2.5 py-1.5 bg-primary/10 border border-primary/20 rounded-md">
                <Video className="h-3.5 w-3.5 text-primary" />
                <span className="text-[12px] font-medium text-primary">Video Script Mode</span>
              </div>
            )}
            
            {/* Ghost text overlay - inline preview */}
            {showSuggestions && currentSuggestion && getGhostText() && (
              <div 
                className="absolute pointer-events-none z-5"
                style={{
                  top: hasVideoMention ? '56px' : '16px',
                  left: '16px',
                  color: 'transparent',
                }}
              >
                <span className="opacity-0">{message}</span>
                <span className="text-muted-foreground/40">{getGhostText()}</span>
              </div>
            )}
            
            <Textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="How can I help you today?"
              className={`min-h-[100px] border-0 focus-visible:ring-0 resize-none px-4 text-[14px] placeholder:text-muted-foreground/60 bg-transparent ${
                hasVideoMention ? "pt-14 pb-16" : "pt-4 pb-16"
              }`}
              disabled={disabled}
              ref={textareaRef}
            />

            {/* Bottom Row: Model Selector + Submit */}
            <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between px-3 py-3">
              <div className="flex items-center gap-2">
                {/* Placeholder for future attachments/tools */}
              </div>
              
              <div className="flex items-center gap-2">
                {/* Model Selector */}
                {onModelChange && (
                  <Select value={model} onValueChange={onModelChange}>
                    <SelectTrigger className="w-auto h-7 border-0 bg-background/60 hover:bg-background transition-all gap-1.5 px-2.5 text-[12px] rounded-md">
                      <SelectValue>
                        {modelDisplayNames[model] || model}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent align="end" className="w-[280px]">
                      <SelectGroup>
                        <SelectLabel className="text-[11px]">Claude (Anthropic)</SelectLabel>
                        <SelectItem value="claude-3-5-opus">
                          <div className="flex flex-col items-start gap-0.5">
                            <span className="font-medium text-[12px]">Claude 3.5 Opus</span>
                            <span className="text-[11px] text-muted-foreground">Most capable model</span>
                          </div>
                        </SelectItem>
                        <SelectItem value="claude-3-5-sonnet">
                          <div className="flex flex-col items-start gap-0.5">
                            <span className="font-medium text-[12px]">Claude 3.5 Sonnet</span>
                          </div>
                        </SelectItem>
                        <SelectItem value="claude-3-5-haiku">
                          <div className="flex flex-col items-start gap-0.5">
                            <span className="font-medium text-[12px]">Claude 3.5 Haiku</span>
                            <span className="text-[11px] text-muted-foreground">Fastest responses</span>
                          </div>
                        </SelectItem>
                        <SelectItem value="claude-3-opus">
                          <div className="flex flex-col items-start gap-0.5">
                            <span className="font-medium text-[12px]">Claude 3 Opus</span>
                            <span className="text-[11px] text-muted-foreground">Previous generation flagship</span>
                          </div>
                        </SelectItem>
                        <SelectItem value="claude-3-sonnet">
                          <div className="flex flex-col items-start gap-0.5">
                            <span className="font-medium text-[12px]">Claude 3 Sonnet</span>
                            <span className="text-[11px] text-muted-foreground">Balanced performance</span>
                          </div>
                        </SelectItem>
                        <SelectItem value="claude-3-haiku">
                          <div className="flex flex-col items-start gap-0.5">
                            <span className="font-medium text-[12px]">Claude 3 Haiku</span>
                            <span className="text-[11px] text-muted-foreground">Fast and efficient</span>
                          </div>
                        </SelectItem>
                      </SelectGroup>
                      
                      <SelectSeparator />
                      
                      <SelectGroup>
                        <SelectLabel className="text-[11px]">OpenAI</SelectLabel>
                        <SelectItem value="o1">
                          <div className="flex flex-col items-start gap-0.5">
                            <span className="font-medium text-[12px]">o1</span>
                            <span className="text-[11px] text-muted-foreground">Advanced reasoning model</span>
                          </div>
                        </SelectItem>
                        <SelectItem value="o1-mini">
                          <div className="flex flex-col items-start gap-0.5">
                            <span className="font-medium text-[12px]">o1-mini</span>
                            <span className="text-[11px] text-muted-foreground">Faster reasoning model</span>
                          </div>
                        </SelectItem>
                        <SelectItem value="gpt-4o">
                          <div className="flex flex-col items-start gap-0.5">
                            <span className="font-medium text-[12px]">GPT-4o</span>
                            <span className="text-[11px] text-muted-foreground">Multimodal flagship</span>
                          </div>
                        </SelectItem>
                        <SelectItem value="gpt-4-turbo">
                          <div className="flex flex-col items-start gap-0.5">
                            <span className="font-medium text-[12px]">GPT-4 Turbo</span>
                            <span className="text-[11px] text-muted-foreground">Enhanced GPT-4</span>
                          </div>
                        </SelectItem>
                        <SelectItem value="gpt-4">
                          <div className="flex flex-col items-start gap-0.5">
                            <span className="font-medium text-[12px]">GPT-4</span>
                            <span className="text-[11px] text-muted-foreground">Original GPT-4</span>
                          </div>
                        </SelectItem>
                        <SelectItem value="gpt-3.5-turbo">
                          <div className="flex flex-col items-start gap-0.5">
                            <span className="font-medium text-[12px]">GPT-3.5 Turbo</span>
                            <span className="text-[11px] text-muted-foreground">Fast and economical</span>
                          </div>
                        </SelectItem>
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                )}

                {/* Submit Button */}
                <Button
                  type="submit"
                  size="icon"
                  className={`h-7 w-7 rounded-md transition-all duration-200 ${
                    message.trim() 
                      ? 'bg-primary hover:bg-primary/90' 
                      : 'bg-muted-foreground/20 hover:bg-muted-foreground/30 cursor-not-allowed'
                  }`}
                  disabled={disabled || !message.trim()}
                >
                  <Send className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}