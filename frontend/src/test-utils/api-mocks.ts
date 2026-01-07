/**
 * API Mock Setup for Frontend Tests (Prompt 23)
 *
 * Provides mock implementations of the API client for testing without Flask backend.
 */

// Mock data for testing
export const mockUserData = {
  id: 'test-user-id',
  email: 'test@example.com',
  name: 'Test User'
};

export const mockChatResponse = {
  message: 'Mock AI response to your question',
  clips: [],
  has_script: false
};

export const mockLibraryData = {
  content: [
    {
      id: 'test-content-1',
      title: 'Test Video 1',
      description: 'A test video for library display',
      content_type: 'video',
      file_name: 'test-video-1.mp4',
      created_at: '2024-01-01T00:00:00Z'
    },
    {
      id: 'test-content-2',
      title: 'Test Audio 1',
      description: 'A test audio for library display',
      content_type: 'audio',
      file_name: 'test-audio-1.mp3',
      created_at: '2024-01-02T00:00:00Z'
    }
  ],
  total: 2,
  page: 1,
  per_page: 20
};

export const mockModels = [
  {
    id: 'claude-sonnet',
    name: 'Claude Sonnet 4',
    description: 'Balanced performance and capability',
    provider: 'anthropic'
  },
  {
    id: 'gpt-4o',
    name: 'GPT-4o',
    description: 'OpenAI\'s most capable model',
    provider: 'openai'
  }
];

export const mockDownloadOptions = {
  video_id: 'test-video',
  title: 'Test Video',
  clips: [
    {
      id: 'clip-1',
      start_time: 0,
      end_time: 30,
      text: 'Test clip content',
      size_mb: 5.2
    }
  ],
  full_video: {
    size_mb: 150.8,
    duration: 300
  }
};

// Mock fetch function for testing
export const mockFetch = jest.fn((url: string, options?: RequestInit): Promise<Response> => {
  try {
    const urlObj = new URL(url);
    const path = urlObj.pathname;
    const method = options?.method || 'GET';

    // Mock responses based on endpoint
    if (method === 'POST' && path === '/api/auth/login') {
      const body = JSON.parse((options?.body as string) || '{}');
      if (body.email === 'test@example.com' && body.password === 'password') {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: jest.fn().mockResolvedValue({
            success: true,
            user: mockUserData,
            requires_2fa: false
          })
        } as any);
      }
      return Promise.resolve({
        ok: false,
        status: 401,
        json: jest.fn().mockResolvedValue({ error: 'Invalid credentials' })
      } as any);
    }

    if (method === 'GET' && path === '/api/auth/me') {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue({ user: mockUserData })
      } as any);
    }

    if (method === 'POST' && path === '/api/auth/logout') {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue({ success: true })
      } as any);
    }

    if (method === 'POST' && path === '/api/chat') {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue(mockChatResponse)
      } as any);
    }

    if (method === 'GET' && path === '/api/models') {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue(mockModels)
      } as any);
    }

    if (method === 'GET' && path === '/api/external-content') {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue(mockLibraryData)
      } as any);
    }

    if (method === 'GET' && path.includes('/api/video/') && path.includes('/download-options')) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue(mockDownloadOptions)
      } as any);
    }

    if (method === 'GET' && path.includes('/api/video-download/')) {
      const videoId = path.split('/').pop();
      return Promise.resolve({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue({
          download_url: `http://localhost:5001/downloads/video-${videoId}.mp4`,
          filename: `video-${videoId}.mp4`,
          size_mb: 150.8
        })
      } as any);
    }

    if (method === 'GET' && path.includes('/api/clip-download/')) {
      const videoId = path.split('/').pop();
      return Promise.resolve({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue({
          download_url: `http://localhost:5001/downloads/clip-${videoId}.mp4`,
          filename: `clip-${videoId}.mp4`,
          size_mb: 5.2
        })
      } as any);
    }

    // Default fallback
    return Promise.resolve({
      ok: false,
      status: 404,
      json: jest.fn().mockResolvedValue({ error: 'Not found' })
    } as any);

  } catch (error) {
    // If URL parsing fails, return error response
    return Promise.resolve({
      ok: false,
      status: 500,
      json: jest.fn().mockResolvedValue({ error: 'Invalid URL' })
    } as any);
  }
});

// Mock API client factory for component testing
export const createMockApi = () => ({
  auth: {
    login: jest.fn().mockResolvedValue({
      success: true,
      user: { id: 'test-user-id', email: 'test@example.com', name: 'Test User' },
      requires_2fa: false
    }),
    me: jest.fn().mockResolvedValue({
      user: { id: 'test-user-id', email: 'test@example.com', name: 'Test User' }
    }),
    logout: jest.fn().mockResolvedValue({ success: true })
  },
  chat: {
    send: jest.fn().mockResolvedValue({
      message: 'Mock AI response',
      clips: [],
      has_script: false
    }),
    getModels: jest.fn().mockResolvedValue([
      { id: 'claude-sonnet', name: 'Claude Sonnet 4' },
      { id: 'gpt-4o', name: 'GPT-4o' }
    ])
  },
  content: {
    list: jest.fn().mockResolvedValue({
      content: [
        {
          id: 'test-content-1',
          title: 'Test Video 1',
          description: 'A test video',
          content_type: 'video'
        }
      ],
      total: 1
    })
  },
  downloads: {
    getClip: jest.fn().mockResolvedValue({
      download_url: 'http://localhost:5001/downloads/test-clip.mp4',
      filename: 'test-clip.mp4',
      size_mb: 5.2
    }),
    getVideo: jest.fn().mockResolvedValue({
      download_url: 'http://localhost:5001/downloads/test-video.mp4',
      filename: 'test-video.mp4',
      size_mb: 150.8
    }),
    getOptions: jest.fn().mockResolvedValue({
      video_id: 'test-video',
      title: 'Test Video',
      clips: [{ id: 'clip-1', text: 'Test clip' }],
      full_video: { size_mb: 150.8 }
    })
  }
});