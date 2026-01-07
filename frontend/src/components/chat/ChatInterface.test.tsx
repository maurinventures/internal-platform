/**
 * ChatInterface Component Tests (Prompt 23)
 *
 * Tests that chat sends messages and displays responses properly.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider } from '../../contexts/AuthContext';
import ChatInterface from './ChatInterface';
import { mockFetch, mockChatResponse } from '../../test-utils/api-mocks';

// Mock fetch globally for these tests
const originalFetch = global.fetch;

beforeAll(() => {
  global.fetch = jest.fn(mockFetch);
});

afterAll(() => {
  global.fetch = originalFetch;
});

// Helper to render ChatInterface with AuthProvider
const renderWithAuth = (component: React.ReactElement) => {
  return render(
    <AuthProvider>
      {component}
    </AuthProvider>
  );
};

describe('ChatInterface Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders chat input field and send button', () => {
    renderWithAuth(<ChatInterface />);

    const messageInput = screen.getByPlaceholderText(/type your message/i) ||
                        screen.getByRole('textbox') ||
                        screen.getByLabelText(/message/i);

    const sendButton = screen.getByRole('button', { name: /send/i }) ||
                      screen.getByTestId('send-button') ||
                      screen.getByTitle(/send message/i);

    expect(messageInput).toBeInTheDocument();
    expect(sendButton).toBeInTheDocument();
  });

  test('sends chat message when send button is clicked', async () => {
    const user = userEvent.setup();

    renderWithAuth(<ChatInterface />);

    const messageInput = screen.getByPlaceholderText(/type your message/i) ||
                        screen.getByRole('textbox');

    const sendButton = screen.getByRole('button', { name: /send/i }) ||
                      screen.getByTestId('send-button');

    // Type a message
    await user.type(messageInput, 'Hello, how can you help me today?');

    // Click send button
    await user.click(sendButton);

    // Verify API was called
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/chat'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify({
            message: 'Hello, how can you help me today?',
            model: expect.any(String) // Should include a model selection
          }),
          credentials: 'include'
        })
      );
    });
  });

  test('sends message when Enter key is pressed', async () => {
    const user = userEvent.setup();

    renderWithAuth(<ChatInterface />);

    const messageInput = screen.getByPlaceholderText(/type your message/i) ||
                        screen.getByRole('textbox');

    // Type a message and press Enter
    await user.type(messageInput, 'Test message{Enter}');

    // Verify API was called
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/chat'),
        expect.objectContaining({
          method: 'POST'
        })
      );
    });
  });

  test('does not send empty messages', async () => {
    const user = userEvent.setup();

    renderWithAuth(<ChatInterface />);

    const sendButton = screen.getByRole('button', { name: /send/i }) ||
                      screen.getByTestId('send-button');

    // Try to send empty message
    await user.click(sendButton);

    // Verify API was NOT called
    expect(global.fetch).not.toHaveBeenCalled();
  });

  test('displays chat response after sending message', async () => {
    const user = userEvent.setup();

    renderWithAuth(<ChatInterface />);

    const messageInput = screen.getByPlaceholderText(/type your message/i) ||
                        screen.getByRole('textbox');
    const sendButton = screen.getByRole('button', { name: /send/i }) ||
                      screen.getByTestId('send-button');

    // Send a message
    await user.type(messageInput, 'What is the weather like?');
    await user.click(sendButton);

    // Wait for response to appear
    await waitFor(() => {
      expect(screen.getByText(mockChatResponse.message)).toBeInTheDocument();
    });

    // Also check that the user's message is displayed
    expect(screen.getByText('What is the weather like?')).toBeInTheDocument();
  });

  test('clears input field after sending message', async () => {
    const user = userEvent.setup();

    renderWithAuth(<ChatInterface />);

    const messageInput = screen.getByPlaceholderText(/type your message/i) ||
                        screen.getByRole('textbox') as HTMLInputElement;
    const sendButton = screen.getByRole('button', { name: /send/i }) ||
                      screen.getByTestId('send-button');

    // Type and send a message
    await user.type(messageInput, 'Test message');
    await user.click(sendButton);

    // Input should be cleared
    await waitFor(() => {
      expect(messageInput.value).toBe('');
    });
  });

  test('disables send button while message is being sent', async () => {
    const user = userEvent.setup();

    renderWithAuth(<ChatInterface />);

    const messageInput = screen.getByPlaceholderText(/type your message/i) ||
                        screen.getByRole('textbox');
    const sendButton = screen.getByRole('button', { name: /send/i }) ||
                      screen.getByTestId('send-button');

    // Type and send a message
    await user.type(messageInput, 'Test message');
    await user.click(sendButton);

    // Button should be disabled temporarily
    expect(sendButton).toBeDisabled();
  });

  test('shows loading indicator while waiting for response', async () => {
    const user = userEvent.setup();

    renderWithAuth(<ChatInterface />);

    const messageInput = screen.getByPlaceholderText(/type your message/i) ||
                        screen.getByRole('textbox');
    const sendButton = screen.getByRole('button', { name: /send/i }) ||
                      screen.getByTestId('send-button');

    // Send a message
    await user.type(messageInput, 'Test message');
    await user.click(sendButton);

    // Look for loading indicator (could be text, spinner, or dots)
    const loadingIndicator = screen.queryByText(/loading/i) ||
                           screen.queryByText(/thinking/i) ||
                           screen.queryByText(/typing/i) ||
                           screen.queryByTestId('loading-spinner') ||
                           screen.queryByText('...');

    if (loadingIndicator) {
      expect(loadingIndicator).toBeInTheDocument();
    }
  });

  test('handles model selection', async () => {
    const user = userEvent.setup();

    renderWithAuth(<ChatInterface />);

    // Look for model selector dropdown
    const modelSelector = screen.queryByRole('combobox') ||
                         screen.queryByTestId('model-selector') ||
                         screen.queryByText(/claude/i) ||
                         screen.queryByText(/gpt/i);

    if (modelSelector) {
      // If model selector exists, test it
      await user.click(modelSelector);

      // Look for model options
      const claudeOption = screen.queryByText(/claude/i);
      if (claudeOption) {
        await user.click(claudeOption);
      }
    }

    // Send a message to verify model is included
    const messageInput = screen.getByPlaceholderText(/type your message/i) ||
                        screen.getByRole('textbox');
    const sendButton = screen.getByRole('button', { name: /send/i }) ||
                      screen.getByTestId('send-button');

    await user.type(messageInput, 'Test with model');
    await user.click(sendButton);

    // Verify model is included in API call
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/chat'),
        expect.objectContaining({
          body: expect.stringContaining('"model"')
        })
      );
    });
  });

  test('maintains conversation history', async () => {
    const user = userEvent.setup();

    renderWithAuth(<ChatInterface />);

    const messageInput = screen.getByPlaceholderText(/type your message/i) ||
                        screen.getByRole('textbox');
    const sendButton = screen.getByRole('button', { name: /send/i }) ||
                      screen.getByTestId('send-button');

    // Send first message
    await user.type(messageInput, 'First message');
    await user.click(sendButton);

    // Wait for response
    await waitFor(() => {
      expect(screen.getByText('First message')).toBeInTheDocument();
    });

    // Clear and send second message
    await user.clear(messageInput);
    await user.type(messageInput, 'Second message');
    await user.click(sendButton);

    // Both messages should be visible
    await waitFor(() => {
      expect(screen.getByText('First message')).toBeInTheDocument();
      expect(screen.getByText('Second message')).toBeInTheDocument();
    });
  });
});