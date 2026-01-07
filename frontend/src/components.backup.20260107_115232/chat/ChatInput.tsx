/**
 * Chat Input Component
 *
 * Updated with Figma Make UI components while preserving API integration logic.
 */

import React, { useState, useRef, useEffect } from 'react';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { Send, ChevronDown } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  SelectGroup,
  SelectLabel,
  SelectSeparator,
} from '../ui/select';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  selectedModel?: string;
  onModelChange?: (model: string) => void;
  models?: Array<{
    id: string;
    name: string;
    provider: string;
    description?: string;
  }>;
}

export function ChatInput({
  onSendMessage,
  disabled,
  placeholder = "Type your message...",
  selectedModel = "",
  onModelChange,
  models = []
}: ChatInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`;
    }
  }, [message]);

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

  const getModelsByProvider = () => {
    const grouped = models.reduce((acc, model) => {
      if (!acc[model.provider]) {
        acc[model.provider] = [];
      }
      acc[model.provider].push(model);
      return acc;
    }, {} as Record<string, typeof models>);

    return grouped;
  };

  const modelsByProvider = getModelsByProvider();

  return (
    <div className="bg-background border-t border-border">
      <div className="max-w-3xl mx-auto py-4 px-6">
        <form onSubmit={handleSubmit} className="relative">
          <div className="relative border border-border rounded-xl bg-background shadow-sm hover:shadow-md hover:border-primary/30 focus-within:border-primary focus-within:shadow-md transition-all duration-200">
            <Textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              className="min-h-[100px] max-h-[150px] border-0 focus-visible:ring-0 resize-none px-4 pt-4 pb-16 text-[14px] placeholder:text-muted-foreground/60 bg-transparent"
              disabled={disabled}
            />

            {/* Bottom Row: Model Selector + Submit */}
            <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between px-3 py-3">
              <div className="flex items-center gap-2">
                {/* Placeholder for future attachments/tools */}
              </div>

              <div className="flex items-center gap-2">
                {/* Model Selector */}
                {onModelChange && models.length > 0 && (
                  <Select value={selectedModel} onValueChange={onModelChange}>
                    <SelectTrigger className="w-auto h-7 border-0 bg-background/60 hover:bg-background transition-all gap-1.5 px-2.5 text-[12px] rounded-md">
                      <SelectValue>
                        {modelDisplayNames[selectedModel] || selectedModel || "Select model"}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent align="end" className="w-[280px]">
                      {Object.entries(modelsByProvider).map(([provider, providerModels]) => (
                        <SelectGroup key={provider}>
                          <SelectLabel className="text-[11px]">
                            {provider === 'anthropic' ? 'Claude (Anthropic)' :
                             provider === 'openai' ? 'OpenAI' :
                             provider.charAt(0).toUpperCase() + provider.slice(1)}
                          </SelectLabel>
                          {providerModels.map((model) => (
                            <SelectItem key={model.id} value={model.id}>
                              <div className="flex flex-col items-start gap-0.5">
                                <span className="font-medium text-[12px]">{model.name}</span>
                                {model.description && (
                                  <span className="text-[11px] text-muted-foreground">{model.description}</span>
                                )}
                              </div>
                            </SelectItem>
                          ))}
                          {provider !== Object.keys(modelsByProvider)[Object.keys(modelsByProvider).length - 1] && (
                            <SelectSeparator />
                          )}
                        </SelectGroup>
                      ))}
                    </SelectContent>
                  </Select>
                )}

                {/* Submit Button */}
                <Button
                  type="submit"
                  size="icon"
                  className={`h-7 w-7 rounded-md transition-all duration-200 ${
                    message.trim() && !disabled
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