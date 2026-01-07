/**
 * LoginForm Component Tests (Prompt 23)
 *
 * Tests that the login form submits properly and handles authentication.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider } from '../../contexts/AuthContext';
import LoginForm from './LoginForm';
import { mockFetch, mockUserData } from '../../test-utils/api-mocks';

// Mock fetch globally for these tests
const originalFetch = global.fetch;

beforeAll(() => {
  global.fetch = jest.fn(mockFetch);
});

afterAll(() => {
  global.fetch = originalFetch;
});

// Helper to render LoginForm with AuthProvider
const renderWithAuth = (component: React.ReactElement) => {
  return render(
    <AuthProvider>
      {component}
    </AuthProvider>
  );
};

describe('LoginForm Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders login form with email and password fields', () => {
    renderWithAuth(<LoginForm />);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  test('submits form with valid credentials successfully', async () => {
    const user = userEvent.setup();

    renderWithAuth(<LoginForm />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    // Fill in the form
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password');

    // Submit the form
    await user.click(submitButton);

    // Verify fetch was called with correct parameters
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/login'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify({
            email: 'test@example.com',
            password: 'password'
          }),
          credentials: 'include'
        })
      );
    });
  });

  test('displays error message for invalid credentials', async () => {
    const user = userEvent.setup();

    renderWithAuth(<LoginForm />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    // Fill in the form with invalid credentials
    await user.type(emailInput, 'wrong@example.com');
    await user.type(passwordInput, 'wrongpassword');

    // Submit the form
    await user.click(submitButton);

    // Check for error message
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });

  test('disables submit button while form is submitting', async () => {
    const user = userEvent.setup();

    renderWithAuth(<LoginForm />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    // Fill in the form
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password');

    // Submit the form
    await user.click(submitButton);

    // Check that button is disabled during submission
    expect(submitButton).toBeDisabled();
  });

  test('validates required fields', async () => {
    const user = userEvent.setup();

    renderWithAuth(<LoginForm />);

    const submitButton = screen.getByRole('button', { name: /sign in/i });

    // Try to submit empty form
    await user.click(submitButton);

    // Check for validation messages
    await waitFor(() => {
      expect(screen.getByText(/email is required/i) || screen.getByText(/required/i)).toBeInTheDocument();
    });
  });

  test('shows and hides password when toggle is clicked', async () => {
    const user = userEvent.setup();

    renderWithAuth(<LoginForm />);

    const passwordInput = screen.getByLabelText(/password/i) as HTMLInputElement;

    // Check initial state (password should be hidden)
    expect(passwordInput.type).toBe('password');

    // Look for password toggle button (eye icon)
    const toggleButton = screen.getByRole('button', { name: /toggle password visibility/i }) ||
                        screen.getByTestId('password-toggle') ||
                        passwordInput.parentElement?.querySelector('[data-testid="password-toggle"]');

    if (toggleButton) {
      // Click to show password
      await user.click(toggleButton);
      expect(passwordInput.type).toBe('text');

      // Click to hide password again
      await user.click(toggleButton);
      expect(passwordInput.type).toBe('password');
    }
  });

  test('handles form submission with keyboard (Enter key)', async () => {
    const user = userEvent.setup();

    renderWithAuth(<LoginForm />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);

    // Fill in the form
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password');

    // Press Enter in password field
    await user.type(passwordInput, '{Enter}');

    // Verify form was submitted
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/login'),
        expect.objectContaining({
          method: 'POST'
        })
      );
    });
  });

  test('clears error message when user starts typing', async () => {
    const user = userEvent.setup();

    renderWithAuth(<LoginForm />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    // Submit with invalid credentials to show error
    await user.type(emailInput, 'wrong@example.com');
    await user.type(passwordInput, 'wrongpassword');
    await user.click(submitButton);

    // Wait for error to appear
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });

    // Start typing in email field
    await user.clear(emailInput);
    await user.type(emailInput, 'test@example.com');

    // Error should be cleared (or at least not visible)
    await waitFor(() => {
      expect(screen.queryByText(/invalid credentials/i)).not.toBeInTheDocument();
    });
  });
});