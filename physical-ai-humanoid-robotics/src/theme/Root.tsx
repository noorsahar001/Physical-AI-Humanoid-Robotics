import React from 'react';
import ChatbotWidget from './ChatbotWidget';

// Default implementation that wraps children with the ChatbotWidget
export default function Root({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <ChatbotWidget />
    </>
  );
}
