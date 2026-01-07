/**
 * Test Setup and Configuration for Frontend Tests (Prompt 23)
 *
 * Provides common test utilities and setup for all component tests.
 */

import '@testing-library/jest-dom';
import { TextEncoder, TextDecoder } from 'util';

// Setup global TextEncoder/TextDecoder for tests
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder as any;

// Mock window.matchMedia for tests that use responsive components
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // Deprecated
    removeListener: jest.fn(), // Deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock window.ResizeObserver for components that use resize detection
global.ResizeObserver = class ResizeObserver {
  observe() {
    // Mock implementation
  }
  unobserve() {
    // Mock implementation
  }
  disconnect() {
    // Mock implementation
  }
};

// Mock IntersectionObserver for components that use intersection detection
global.IntersectionObserver = class IntersectionObserver {
  observe() {
    // Mock implementation
  }
  unobserve() {
    // Mock implementation
  }
  disconnect() {
    // Mock implementation
  }
};

// Mock window.scrollTo for scroll-related tests
Object.defineProperty(window, 'scrollTo', {
  writable: true,
  value: jest.fn(),
});

// Mock localStorage for components that use local storage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock as any;

// Mock sessionStorage for components that use session storage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.sessionStorage = sessionStorageMock as any;

// Mock console methods to reduce test output noise
const originalError = console.error;
const originalWarn = console.warn;

beforeEach(() => {
  // Reset all mocks before each test
  jest.clearAllMocks();
  localStorageMock.getItem.mockClear();
  localStorageMock.setItem.mockClear();
  localStorageMock.removeItem.mockClear();
  localStorageMock.clear.mockClear();
  sessionStorageMock.getItem.mockClear();
  sessionStorageMock.setItem.mockClear();
  sessionStorageMock.removeItem.mockClear();
  sessionStorageMock.clear.mockClear();

  // Suppress console errors/warnings that are expected in tests
  console.error = jest.fn();
  console.warn = jest.fn();
});

afterEach(() => {
  // Restore console methods after each test
  console.error = originalError;
  console.warn = originalWarn;
});

// Custom test utilities
export const waitForLoadingToFinish = async () => {
  await waitFor(() => {
    expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
  });
};

export const expectElementToBeVisible = (element: HTMLElement) => {
  expect(element).toBeInTheDocument();
  expect(element).toBeVisible();
};

export const expectElementToBeHidden = (element: HTMLElement) => {
  expect(element).not.toBeVisible();
};

// Import necessary testing utilities so they're available in all test files
import { waitFor, screen } from '@testing-library/react';

// Export testing utilities for convenience
export { waitFor, screen };