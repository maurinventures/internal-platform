/**
 * Login Form Component
 *
 * Updated with Figma Make UI components while preserving API integration logic.
 */

import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Mail, Lock, LogIn } from 'lucide-react';

interface LoginFormProps {
  onSuccess?: () => void;
  onRequire2FA?: () => void;
  onRequire2FASetup?: () => void;
}

export function LoginForm({ onSuccess, onRequire2FA, onRequire2FASetup }: LoginFormProps) {
  const { login, isLoading, error, clearError } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!formData.email || !formData.password) {
      return;
    }

    const result = await login(formData.email, formData.password);

    if (result.success) {
      if (result.requiresVerification === '2fa') {
        onRequire2FA?.();
      } else if (result.requiresVerification === '2fa-setup') {
        onRequire2FASetup?.();
      } else {
        onSuccess?.();
      }
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    clearError(); // Clear error when user types
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-semibold mb-2">Internal Platform</h1>
          <p className="text-muted-foreground">Sign in to your AI-powered workspace</p>
        </div>

        <div className="bg-card border border-border rounded-lg p-8 shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="rounded-md bg-destructive/10 border border-destructive/20 p-4">
                <div className="text-sm text-destructive">{error}</div>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={handleChange}
                  className="pl-10"
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="password"
                  name="password"
                  type="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={handleChange}
                  className="pl-10"
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            <Button
              type="submit"
              className="w-full"
              size="lg"
              disabled={isLoading || !formData.email || !formData.password}
            >
              {isLoading ? (
                <span className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                  Signing in...
                </span>
              ) : (
                <>
                  <LogIn className="mr-2 h-4 w-4" />
                  Sign In
                </>
              )}
            </Button>
          </form>
        </div>

        <div className="flex flex-col items-center gap-2 text-center mt-6">
          <button
            className="text-[12px] text-primary hover:underline active:text-primary/80 transition-colors"
            onClick={() => window.location.href = '/forgot-password'}
          >
            Forgot password?
          </button>
          <button
            onClick={() => window.location.href = '/register'}
            className="text-[12px] text-primary hover:underline active:text-primary/80 transition-colors"
          >
            Create a new account
          </button>
        </div>
      </div>
    </div>
  );
}