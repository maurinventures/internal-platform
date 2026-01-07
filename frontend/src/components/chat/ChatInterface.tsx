/**
 * Chat Interface Component
 *
 * Updated with Figma Make UI components while preserving API integration logic.
 * Main chat interface that integrates model selection, message display, and message input.
 */

import React, { useEffect, useState } from 'react';
import { useChat } from '../../hooks/useChat';
import { useModels } from '../../hooks/useModels';
import { ModelSelector } from './ModelSelector';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { Card, CardHeader, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { X } from 'lucide-react';

interface ChatInterfaceProps {
  conversationId?: string;
  className?: string;
}

export function ChatInterface({ conversationId, className = '' }: ChatInterfaceProps) {
  const {
    conversation,
    messages,
    loading,
    error,
    isGenerating,
    sendMessage,
    createNewConversation,
    loadConversation,
    updateConversationModel,
    clearError,
  } = useChat();

  const { models, defaultModel, loading: modelsLoading, getModelById } = useModels();

  const [selectedModel, setSelectedModel] = useState<string>('');

  // Initialize conversation and selected model
  useEffect(() => {
    if (conversationId) {
      loadConversation(conversationId);
    } else {
      // Set default model for new conversations
      setSelectedModel(defaultModel);
    }
  }, [conversationId, defaultModel, loadConversation]);

  // Update selected model when conversation loads
  useEffect(() => {
    if (conversation?.preferred_model) {
      setSelectedModel(conversation.preferred_model);
    }
  }, [conversation?.preferred_model]);

  const handleModelChange = async (modelId: string) => {
    setSelectedModel(modelId);

    if (conversation) {
      // Update existing conversation's model preference
      await updateConversationModel(modelId);
    }
  };

  const handleSendMessage = async (message: string) => {
    if (!conversation && !conversationId) {
      // Create a new conversation if one doesn't exist
      await createNewConversation(undefined, selectedModel);
    }

    await sendMessage(message, selectedModel);
  };

  const selectedModelInfo = getModelById(selectedModel);

  return (
    <div className={`flex flex-col h-full bg-background rounded-lg shadow-sm border border-border ${className}`}>
      {/* Header with model selector and conversation info */}
      <CardHeader className="flex-shrink-0 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-foreground">
              {conversation?.title || 'New Conversation'}
            </h2>
            {conversation && (
              <p className="text-sm text-muted-foreground mt-1">
                Created {new Date(conversation.created_at).toLocaleDateString()}
              </p>
            )}
          </div>

          {/* Model Selector */}
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <label className="block text-sm font-medium text-foreground mb-1">
                AI Model
              </label>
              <ModelSelector
                selectedModel={selectedModel}
                onModelChange={handleModelChange}
                disabled={modelsLoading || isGenerating}
                size="sm"
              />
            </div>
          </div>
        </div>

        {/* Model info display */}
        {selectedModelInfo && (
          <Card className="mt-3 bg-muted/50 border-muted">
            <CardContent className="p-3">
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                    selectedModelInfo.provider === 'anthropic' ? 'bg-anthropic-500' : 'bg-openai-500'
                  }`}>
                    <span className="text-white text-xs font-bold">
                      {selectedModelInfo.provider === 'anthropic' ? 'A' : 'O'}
                    </span>
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground">
                    {selectedModelInfo.name}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {selectedModelInfo.description}
                  </p>
                </div>
                <div className="flex-shrink-0">
                  <Badge variant="secondary" className="text-xs">
                    {(selectedModelInfo.context_window / 1000).toFixed(0)}K context
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Error display */}
        {error && (
          <Card className="mt-3 border-destructive bg-destructive/5">
            <CardContent className="p-3">
              <div className="flex">
                <div className="flex-shrink-0">
                  <X className="h-5 w-5 text-destructive" />
                </div>
                <div className="ml-3 flex-1">
                  <h3 className="text-sm font-medium text-destructive">Error</h3>
                  <div className="mt-1 text-sm text-destructive/80">{error}</div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={clearError}
                    className="mt-2 text-destructive hover:text-destructive/80"
                  >
                    Dismiss
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </CardHeader>

      {/* Messages area */}
      <div className="flex-1 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="flex items-center space-x-3">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              <span className="text-muted-foreground">Loading conversation...</span>
            </div>
          </div>
        ) : (
          <MessageList messages={messages} isGenerating={isGenerating} />
        )}
      </div>

      {/* Message input */}
      <div className="flex-shrink-0">
        <MessageInput
          onSendMessage={handleSendMessage}
          disabled={isGenerating || loading || modelsLoading || !selectedModel}
          placeholder={
            !selectedModel
              ? 'Please select a model first...'
              : isGenerating
              ? 'AI is responding...'
              : 'Type your message...'
          }
        />
      </div>
    </div>
  );
}

/**
 * Chat Page Component
 *
 * Full-page layout for the chat interface with updated styling.
 */
export function ChatPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-card shadow-sm border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-xl font-bold text-foreground">Internal Platform Chat</h1>
          </div>
        </div>
      </div>

      {/* Main chat area */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="h-[calc(100vh-12rem)]">
          <ChatInterface className="h-full" />
        </div>
      </div>
    </div>
  );
}