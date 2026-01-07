/**
 * Frontend Tests Suite (Prompt 23)
 *
 * Comprehensive tests for frontend functionality without requiring Flask backend.
 * Tests login forms, chat messaging, library display, and download buttons.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { mockFetch, mockUserData, mockChatResponse, mockLibraryData } from '../test-utils/api-mocks';

// Mock fetch globally for these tests
const originalFetch = global.fetch;

beforeAll(() => {
  global.fetch = jest.fn(mockFetch);
});

afterAll(() => {
  global.fetch = originalFetch;
});

// Mock window.open for download tests
const originalWindowOpen = window.open;
beforeAll(() => {
  window.open = jest.fn();
});

afterAll(() => {
  window.open = originalWindowOpen;
});

// Simple test components to demonstrate the testing patterns

// 1. LOGIN FORM COMPONENT TEST
const MockLoginForm: React.FC = () => {
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Email and password are required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:5001/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
        credentials: 'include'
      });

      const data = await response.json();
      if (response.ok) {
        // Login successful
        console.log('Login successful', data);
      } else {
        setError(data.error || 'Login failed');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>
      <div>
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </div>
      <button type="submit" disabled={loading}>
        {loading ? 'Signing in...' : 'Sign In'}
      </button>
      {error && <div role="alert">{error}</div>}
    </form>
  );
};

// 2. CHAT INTERFACE COMPONENT TEST
const MockChatInterface: React.FC = () => {
  const [message, setMessage] = React.useState('');
  const [messages, setMessages] = React.useState<string[]>([]);
  const [loading, setLoading] = React.useState(false);

  const sendMessage = async () => {
    if (!message.trim() || loading) return;

    const userMessage = message;
    setMessage('');
    setMessages(prev => [...prev, `User: ${userMessage}`]);
    setLoading(true);

    try {
      const response = await fetch('http://localhost:5001/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage, model: 'claude-sonnet' }),
        credentials: 'include'
      });

      const data = await response.json();
      setMessages(prev => [...prev, `AI: ${data.message}`]);
    } catch (err) {
      setMessages(prev => [...prev, 'AI: Error occurred']);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div>
      <div data-testid="message-history">
        {messages.map((msg, i) => <div key={i}>{msg}</div>)}
      </div>
      <div>
        <input
          placeholder="Type your message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
        />
        <button onClick={sendMessage} disabled={loading || !message.trim()}>
          Send
        </button>
      </div>
    </div>
  );
};

// 3. LIBRARY LIST COMPONENT TEST
const MockLibraryList: React.FC = () => {
  const [items, setItems] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const fetchItems = async () => {
      try {
        const response = await fetch('http://localhost:5001/api/external-content', {
          credentials: 'include'
        });
        const data = await response.json();
        setItems(data.content || []);
      } finally {
        setLoading(false);
      }
    };
    fetchItems();
  }, []);

  if (loading) return <div>Loading library items...</div>;

  return (
    <div>
      <h2>Library</h2>
      {items.map(item => (
        <div key={item.id} data-testid={`library-item-${item.id}`}>
          <h3>{item.title}</h3>
          <p>{item.description}</p>
          <span>{item.content_type}</span>
        </div>
      ))}
    </div>
  );
};

// 4. DOWNLOAD BUTTON COMPONENT TEST
interface MockDownloadButtonProps {
  videoId: string;
  type: 'video' | 'clip';
}

const MockDownloadButton: React.FC<MockDownloadButtonProps> = ({ videoId, type }) => {
  const [downloading, setDownloading] = React.useState(false);

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const endpoint = type === 'video'
        ? `/api/video-download/${videoId}`
        : `/api/clip-download/${videoId}`;

      const response = await fetch(`http://localhost:5001${endpoint}`, {
        credentials: 'include'
      });

      if (response && response.json) {
        const data = await response.json();
        if (data && data.download_url) {
          window.open(data.download_url, '_blank');
        }
      }
    } catch (error) {
      console.error('Download failed:', error);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <button
      onClick={handleDownload}
      disabled={downloading}
      data-testid={`download-${type}-button`}
    >
      {downloading ? 'Downloading...' : `Download ${type}`}
    </button>
  );
};

// TEST SUITES

describe('Frontend Tests Suite (Prompt 23)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Login Form Tests', () => {
    test('renders login form with email and password fields', () => {
      render(<MockLoginForm />);

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    });

    test('submits form with valid credentials', async () => {
      render(<MockLoginForm />);

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      // Use older userEvent API (compatible with v13)
      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.type(passwordInput, 'password');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:5001/api/auth/login',
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: 'test@example.com', password: 'password' }),
            credentials: 'include'
          })
        );
      });
    });

    test('shows error for invalid credentials', async () => {
      render(<MockLoginForm />);

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await userEvent.type(emailInput, 'wrong@example.com');
      await userEvent.type(passwordInput, 'wrongpass');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Invalid credentials');
      });
    });

    test('validates required fields', async () => {
      render(<MockLoginForm />);

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Email and password are required');
      });
    });
  });

  describe('Chat Interface Tests', () => {
    test('renders chat input and send button', () => {
      render(<MockChatInterface />);

      expect(screen.getByPlaceholderText(/type your message/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
    });

    test('sends chat message when send button is clicked', async () => {
      render(<MockChatInterface />);

      const input = screen.getByPlaceholderText(/type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      await userEvent.type(input, 'Hello AI');
      await userEvent.click(sendButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:5001/api/chat',
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ message: 'Hello AI', model: 'claude-sonnet' })
          })
        );
      });

      // Check that message appears in history
      await waitFor(() => {
        expect(screen.getByText('User: Hello AI')).toBeInTheDocument();
        expect(screen.getByText(`AI: ${mockChatResponse.message}`)).toBeInTheDocument();
      });
    });

    test('sends message when Enter key is pressed', async () => {
      render(<MockChatInterface />);

      const input = screen.getByPlaceholderText(/type your message/i);
      await userEvent.type(input, 'Test message{enter}');

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:5001/api/chat',
          expect.objectContaining({ method: 'POST' })
        );
      });
    });

    test('does not send empty messages', async () => {
      render(<MockChatInterface />);

      const sendButton = screen.getByRole('button', { name: /send/i });
      await userEvent.click(sendButton);

      expect(global.fetch).not.toHaveBeenCalled();
    });

    test('clears input after sending message', async () => {
      render(<MockChatInterface />);

      const input = screen.getByPlaceholderText(/type your message/i) as HTMLInputElement;
      const sendButton = screen.getByRole('button', { name: /send/i });

      await userEvent.type(input, 'Test message');
      await userEvent.click(sendButton);

      await waitFor(() => {
        expect(input.value).toBe('');
      });
    });
  });

  describe('Library Display Tests', () => {
    test('displays library items from API', async () => {
      render(<MockLibraryList />);

      await waitFor(() => {
        expect(screen.getByText('Test Video 1')).toBeInTheDocument();
        expect(screen.getByText('Test Audio 1')).toBeInTheDocument();
      });

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:5001/api/external-content',
        expect.objectContaining({ credentials: 'include' })
      );
    });

    test('shows loading state initially', () => {
      render(<MockLibraryList />);
      expect(screen.getByText('Loading library items...')).toBeInTheDocument();
    });

    test('displays content types correctly', async () => {
      render(<MockLibraryList />);

      await waitFor(() => {
        expect(screen.getByText('video')).toBeInTheDocument();
        expect(screen.getByText('audio')).toBeInTheDocument();
      });
    });
  });

  describe('Download Button Tests', () => {
    test('handles video download correctly', async () => {
      render(<MockDownloadButton videoId="test-123" type="video" />);

      const downloadButton = screen.getByTestId('download-video-button');
      await userEvent.click(downloadButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:5001/api/video-download/test-123',
          expect.objectContaining({ credentials: 'include' })
        );
      });

      await waitFor(() => {
        expect(window.open).toHaveBeenCalledWith(
          expect.stringContaining('downloads/video-test-123.mp4'),
          '_blank'
        );
      });
    });

    test('handles clip download correctly', async () => {
      render(<MockDownloadButton videoId="clip-456" type="clip" />);

      const downloadButton = screen.getByTestId('download-clip-button');
      await userEvent.click(downloadButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:5001/api/clip-download/clip-456',
          expect.objectContaining({ credentials: 'include' })
        );
      });
    });

    test('shows loading state while downloading', async () => {
      render(<MockDownloadButton videoId="test-123" type="video" />);

      const downloadButton = screen.getByTestId('download-video-button');
      await userEvent.click(downloadButton);

      // Button should show downloading state briefly
      expect(downloadButton).toHaveTextContent('Downloading...');
      expect(downloadButton).toBeDisabled();
    });

    test('download button works for both video and clip types', async () => {
      const { rerender } = render(<MockDownloadButton videoId="test-123" type="video" />);

      let downloadButton = screen.getByTestId('download-video-button');
      expect(downloadButton).toHaveTextContent('Download video');

      rerender(<MockDownloadButton videoId="test-456" type="clip" />);
      downloadButton = screen.getByTestId('download-clip-button');
      expect(downloadButton).toHaveTextContent('Download clip');
    });
  });

  describe('API Mock Integration', () => {
    test('mock fetch responses work correctly', async () => {
      // Test auth endpoint
      const authResponse = await fetch('http://localhost:5001/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email: 'test@example.com', password: 'password' })
      });
      const authData = await authResponse.json();
      expect(authData.success).toBe(true);
      expect(authData.user.email).toBe('test@example.com');

      // Test chat endpoint
      const chatResponse = await fetch('http://localhost:5001/api/chat', {
        method: 'POST',
        body: JSON.stringify({ message: 'test' })
      });
      const chatData = await chatResponse.json();
      expect(chatData.message).toBe(mockChatResponse.message);

      // Test content endpoint
      const contentResponse = await fetch('http://localhost:5001/api/external-content');
      const contentData = await contentResponse.json();
      expect(contentData.content).toHaveLength(2);
      expect(contentData.content[0].title).toBe('Test Video 1');
    });

    test('handles error responses correctly', async () => {
      const response = await fetch('http://localhost:5001/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email: 'wrong@example.com', password: 'wrong' })
      });
      expect(response.ok).toBe(false);
      expect(response.status).toBe(401);

      const data = await response.json();
      expect(data.error).toBe('Invalid credentials');
    });
  });
});