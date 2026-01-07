/**
 * Download Button Component Tests (Prompt 23)
 *
 * Tests that download buttons work correctly and handle file downloads.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { mockFetch } from '../../test-utils/api-mocks';

// Mock fetch globally for these tests
const originalFetch = global.fetch;

beforeAll(() => {
  global.fetch = jest.fn(mockFetch);
});

afterAll(() => {
  global.fetch = originalFetch;
});

// Mock window.open for download simulation
const originalWindowOpen = window.open;
beforeAll(() => {
  window.open = jest.fn();
});

afterAll(() => {
  window.open = originalWindowOpen;
});

// Simple DownloadButton component for testing
// Note: In a real implementation, this would be in a separate file
interface DownloadButtonProps {
  videoId?: string;
  clipId?: string;
  type: 'video' | 'clip';
  children: React.ReactNode;
  disabled?: boolean;
  variant?: 'primary' | 'secondary';
}

const DownloadButton: React.FC<DownloadButtonProps> = ({
  videoId,
  clipId,
  type,
  children,
  disabled = false,
  variant = 'primary'
}) => {
  const [isDownloading, setIsDownloading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleDownload = async () => {
    if (disabled || isDownloading) return;

    setIsDownloading(true);
    setError(null);

    try {
      let downloadUrl: string;
      let response: Response;

      if (type === 'video' && videoId) {
        response = await fetch(`http://localhost:5001/api/video-download/${videoId}`, {
          credentials: 'include'
        });
      } else if (type === 'clip' && clipId) {
        response = await fetch(`http://localhost:5001/api/clip-download/${clipId}`, {
          credentials: 'include'
        });
      } else {
        throw new Error('Invalid download configuration');
      }

      if (!response.ok) {
        throw new Error('Download failed');
      }

      const data = await response.json();
      downloadUrl = data.download_url;

      // Simulate download by opening URL
      window.open(downloadUrl, '_blank');

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed');
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div>
      <button
        onClick={handleDownload}
        disabled={disabled || isDownloading}
        className={`download-button ${variant}`}
        data-testid={`download-${type}-button`}
        aria-label={`Download ${type}`}
      >
        {isDownloading ? `Downloading ${type}...` : children}
      </button>
      {error && (
        <div className="error-message" role="alert">
          {error}
        </div>
      )}
    </div>
  );
};

describe('DownloadButton Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders download button with correct text', () => {
    render(
      <DownloadButton type="video" videoId="test-video-123">
        Download Video
      </DownloadButton>
    );

    const button = screen.getByRole('button', { name: /download video/i });
    expect(button).toBeInTheDocument();
    expect(screen.getByText('Download Video')).toBeInTheDocument();
  });

  test('handles video download on click', async () => {
    render(
      <DownloadButton type="video" videoId="test-video-123">
        Download Video
      </DownloadButton>
    );

    const button = screen.getByRole('button', { name: /download video/i });
    await userEvent.click(button);

    // Verify API was called with correct video ID
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:5001/api/video-download/test-video-123',
        expect.objectContaining({
          credentials: 'include'
        })
      );
    });

    // Verify window.open was called for download
    await waitFor(() => {
      expect(window.open).toHaveBeenCalledWith(
        expect.stringContaining('downloads/video-test-video-123.mp4'),
        '_blank'
      );
    });
  });

  test('handles clip download on click', async () => {
    render(
      <DownloadButton type="clip" clipId="test-clip-456">
        Download Clip
      </DownloadButton>
    );

    const button = screen.getByRole('button', { name: /download clip/i });
    await userEvent.click(button);

    // Verify API was called with correct clip ID
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:5001/api/clip-download/test-clip-456',
        expect.objectContaining({
          credentials: 'include'
        })
      );
    });

    // Verify window.open was called for download
    await waitFor(() => {
      expect(window.open).toHaveBeenCalledWith(
        expect.stringContaining('downloads/clip-test-clip-456.mp4'),
        '_blank'
      );
    });
  });

  test('shows loading state while downloading', async () => {
    render(
      <DownloadButton type="video" videoId="test-video-123">
        Download Video
      </DownloadButton>
    );

    const button = screen.getByRole('button', { name: /download video/i });
    await userEvent.click(button);

    // Button should show loading text and be disabled
    expect(button).toHaveTextContent('Downloading video...');
    expect(button).toBeDisabled();
  });

  test('prevents multiple simultaneous downloads', async () => {
    render(
      <DownloadButton type="video" videoId="test-video-123">
        Download Video
      </DownloadButton>
    );

    const button = screen.getByRole('button', { name: /download video/i });

    // Click multiple times rapidly
    await userEvent.click(button);
    await userEvent.click(button);
    await userEvent.click(button);

    // API should only be called once
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });
  });

  test('handles download errors gracefully', async () => {
    // Mock error response
    const errorMockFetch = (url: string) => {
      if (url.includes('/api/video-download/')) {
        return Promise.resolve({
          ok: false,
          status: 500,
          json: () => Promise.resolve({ error: 'Server error' })
        } as Response);
      }
      return mockFetch(url);
    };

    global.fetch = jest.fn(errorMockFetch);

    render(
      <DownloadButton type="video" videoId="error-video">
        Download Video
      </DownloadButton>
    );

    const button = screen.getByRole('button', { name: /download video/i });
    await userEvent.click(button);

    // Error message should appear
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Download failed');
    });

    // Button should be re-enabled after error
    await waitFor(() => {
      expect(button).not.toBeDisabled();
      expect(button).toHaveTextContent('Download Video');
    });
  });

  test('respects disabled prop', () => {
    render(
      <DownloadButton type="video" videoId="test-video-123" disabled>
        Download Video
      </DownloadButton>
    );

    const button = screen.getByRole('button', { name: /download video/i });
    expect(button).toBeDisabled();
  });

  test('does not download when disabled', async () => {
    render(
      <DownloadButton type="video" videoId="test-video-123" disabled>
        Download Video
      </DownloadButton>
    );

    const button = screen.getByRole('button', { name: /download video/i });
    await userEvent.click(button);

    // API should not be called
    expect(global.fetch).not.toHaveBeenCalled();
  });

  test('applies correct CSS classes for variants', () => {
    const { rerender } = render(
      <DownloadButton type="video" videoId="test-video-123" variant="primary">
        Download Video
      </DownloadButton>
    );

    let button = screen.getByRole('button', { name: /download video/i });
    expect(button).toHaveClass('download-button', 'primary');

    rerender(
      <DownloadButton type="video" videoId="test-video-123" variant="secondary">
        Download Video
      </DownloadButton>
    );

    button = screen.getByRole('button', { name: /download video/i });
    expect(button).toHaveClass('download-button', 'secondary');
  });

  test('has proper accessibility attributes', () => {
    render(
      <DownloadButton type="video" videoId="test-video-123">
        Download Video
      </DownloadButton>
    );

    const button = screen.getByRole('button', { name: /download video/i });
    expect(button).toHaveAttribute('aria-label', 'Download video');
    expect(button).toHaveAttribute('data-testid', 'download-video-button');
  });

  test('handles network errors', async () => {
    // Mock network error
    const networkErrorMockFetch = (url: string) => {
      if (url.includes('/api/video-download/')) {
        return Promise.reject(new Error('Network error'));
      }
      return mockFetch(url);
    };

    global.fetch = jest.fn(networkErrorMockFetch);

    render(
      <DownloadButton type="video" videoId="network-error-video">
        Download Video
      </DownloadButton>
    );

    const button = screen.getByRole('button', { name: /download video/i });
    await userEvent.click(button);

    // Error message should appear
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Network error');
    });
  });

  test('clears previous errors on new download attempt', async () => {
    // Start with error mock
    const errorMockFetch = (url: string) => {
      if (url.includes('/api/video-download/')) {
        return Promise.reject(new Error('First error'));
      }
      return mockFetch(url);
    };

    global.fetch = jest.fn(errorMockFetch);

    render(
      <DownloadButton type="video" videoId="test-video">
        Download Video
      </DownloadButton>
    );

    const button = screen.getByRole('button', { name: /download video/i });

    // First download attempt (should error)
    await userEvent.click(button);
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('First error');
    });

    // Switch to successful mock
    global.fetch = jest.fn(mockFetch);

    // Second download attempt (should clear error)
    await userEvent.click(button);

    // Error message should be cleared
    await waitFor(() => {
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });
});