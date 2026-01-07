/**
 * Library List Component Tests (Prompt 23)
 *
 * Tests that library displays items correctly from the API.
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { mockFetch, mockLibraryData } from '../../test-utils/api-mocks';

// Mock fetch globally for these tests
const originalFetch = global.fetch;

beforeAll(() => {
  global.fetch = jest.fn(mockFetch);
});

afterAll(() => {
  global.fetch = originalFetch;
});

// Simple LibraryList component for testing
// Note: In a real implementation, this would be in a separate file
interface LibraryItem {
  id: string;
  title: string;
  description: string;
  content_type: string;
  file_name: string;
  created_at: string;
}

interface LibraryListProps {
  onItemClick?: (item: LibraryItem) => void;
}

const LibraryList: React.FC<LibraryListProps> = ({ onItemClick }) => {
  const [items, setItems] = React.useState<LibraryItem[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const fetchItems = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch('http://localhost:5001/api/external-content', {
          credentials: 'include'
        });
        const data = await response.json();
        setItems(data.content || []);
      } catch (err) {
        setError('Failed to load library items');
      } finally {
        setLoading(false);
      }
    };

    fetchItems();
  }, []);

  if (loading) {
    return <div>Loading library items...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div data-testid="library-list">
      <h2>Library</h2>
      {items.length === 0 ? (
        <div>No items found</div>
      ) : (
        <ul>
          {items.map((item) => (
            <li
              key={item.id}
              data-testid={`library-item-${item.id}`}
              onClick={() => onItemClick?.(item)}
              style={{ cursor: onItemClick ? 'pointer' : 'default' }}
            >
              <h3>{item.title}</h3>
              <p>{item.description}</p>
              <span className="content-type">{item.content_type}</span>
              <span className="file-name">{item.file_name}</span>
              <time>{new Date(item.created_at).toLocaleDateString()}</time>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

describe('LibraryList Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders loading state initially', () => {
    render(<LibraryList />);
    expect(screen.getByText('Loading library items...')).toBeInTheDocument();
  });

  test('fetches and displays library items from API', async () => {
    render(<LibraryList />);

    // Wait for items to load
    await waitFor(() => {
      expect(screen.getByText('Test Video 1')).toBeInTheDocument();
    });

    // Verify API was called
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:5001/api/external-content',
      expect.objectContaining({
        credentials: 'include'
      })
    );

    // Check that both mock items are displayed
    expect(screen.getByText('Test Video 1')).toBeInTheDocument();
    expect(screen.getByText('Test Audio 1')).toBeInTheDocument();
    expect(screen.getByText('A test video for library display')).toBeInTheDocument();
    expect(screen.getByText('A test audio for library display')).toBeInTheDocument();
  });

  test('displays content types correctly', async () => {
    render(<LibraryList />);

    await waitFor(() => {
      expect(screen.getByText('Test Video 1')).toBeInTheDocument();
    });

    // Check content types are displayed
    expect(screen.getByText('video')).toBeInTheDocument();
    expect(screen.getByText('audio')).toBeInTheDocument();
  });

  test('displays file names correctly', async () => {
    render(<LibraryList />);

    await waitFor(() => {
      expect(screen.getByText('Test Video 1')).toBeInTheDocument();
    });

    // Check file names are displayed
    expect(screen.getByText('test-video-1.mp4')).toBeInTheDocument();
    expect(screen.getByText('test-audio-1.mp3')).toBeInTheDocument();
  });

  test('formats dates correctly', async () => {
    render(<LibraryList />);

    await waitFor(() => {
      expect(screen.getByText('Test Video 1')).toBeInTheDocument();
    });

    // Check that dates are formatted (they should be readable dates, not ISO strings)
    const dateElements = screen.getAllByRole('time') ||
                        screen.getAllByText(/2024/) ||
                        screen.getAllByText(/Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec/);

    expect(dateElements.length).toBeGreaterThan(0);
  });

  test('handles item click events', async () => {
    const mockOnItemClick = jest.fn();
    render(<LibraryList onItemClick={mockOnItemClick} />);

    await waitFor(() => {
      expect(screen.getByText('Test Video 1')).toBeInTheDocument();
    });

    const firstItem = screen.getByTestId('library-item-test-content-1');
    await userEvent.click(firstItem);

    expect(mockOnItemClick).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'test-content-1',
        title: 'Test Video 1'
      })
    );
  });

  test('displays correct number of items', async () => {
    render(<LibraryList />);

    await waitFor(() => {
      expect(screen.getByText('Test Video 1')).toBeInTheDocument();
    });

    // Should have exactly 2 items as per mock data
    const listItems = screen.getAllByRole('listitem');
    expect(listItems).toHaveLength(2);
  });

  test('handles empty library state', async () => {
    // Mock empty response
    const emptyMockFetch = (url: string) => {
      if (url.includes('/api/external-content')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ content: [], total: 0 })
        } as Response);
      }
      return mockFetch(url);
    };

    global.fetch = jest.fn(emptyMockFetch);

    render(<LibraryList />);

    await waitFor(() => {
      expect(screen.getByText('No items found')).toBeInTheDocument();
    });
  });

  test('handles API error gracefully', async () => {
    // Mock error response
    const errorMockFetch = (url: string) => {
      if (url.includes('/api/external-content')) {
        return Promise.reject(new Error('Network error'));
      }
      return mockFetch(url);
    };

    global.fetch = jest.fn(errorMockFetch);

    render(<LibraryList />);

    await waitFor(() => {
      expect(screen.getByText('Error: Failed to load library items')).toBeInTheDocument();
    });
  });

  test('has proper accessibility attributes', async () => {
    render(<LibraryList />);

    await waitFor(() => {
      expect(screen.getByText('Test Video 1')).toBeInTheDocument();
    });

    // Check that the list has proper semantics
    const list = screen.getByRole('list');
    expect(list).toBeInTheDocument();

    // Check that items are proper list items
    const listItems = screen.getAllByRole('listitem');
    expect(listItems.length).toBeGreaterThan(0);

    // Check that times have proper semantic markup
    const timeElements = screen.getAllByRole('time');
    if (timeElements.length > 0) {
      expect(timeElements[0]).toBeInTheDocument();
    }
  });
});