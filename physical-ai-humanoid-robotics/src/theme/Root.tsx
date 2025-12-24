import React from 'react';
import { AuthProvider } from '../components/auth/AuthProvider';
import ChatbotWidget from './ChatbotWidget';

/**
 * Root component that wraps the entire application.
 * Constitution v3.0.0 - Principle XVI: Auth state at Root component level
 */
export default function Root({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      {children}
      <ChatbotWidget />
    </AuthProvider>
  );
}
