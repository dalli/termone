/**
 * XTerminal Component - Terminal UI with xterm.js
 */

import React, { useEffect, useRef } from 'react';

interface XTerminalProps {
  sessionId: string;
  onInput?: (data: string) => void;
  onResize?: (rows: number, cols: number) => void;
  theme?: string;
  fontSize?: number;
  fontFamily?: string;
  output: string;
}

export const XTerminal: React.FC<XTerminalProps> = ({
  sessionId,
  onInput,
  onResize,
  theme = 'dracula',
  fontSize = 14,
  fontFamily = "'Courier New', monospace",
  output,
}) => {
  const terminalRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (terminalRef.current) {
      // Scroll to bottom
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [output]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      const input = inputRef.current?.value || '';
      onInput?.(input + '\n');
      if (inputRef.current) {
        inputRef.current.value = '';
      }
    }
  };

  return (
    <div className="flex flex-col h-full bg-black rounded-lg overflow-hidden">
      {/* Terminal Output */}
      <div
        ref={terminalRef}
        className="flex-1 overflow-auto p-4 font-mono text-sm"
        style={{ fontSize: `${fontSize}px`, fontFamily }}
      >
        <pre className="text-green-400 whitespace-pre-wrap break-words">{output}</pre>
      </div>

      {/* Terminal Input */}
      <div className="bg-gray-900 border-t border-gray-700 px-4 py-2">
        <input
          ref={inputRef}
          type="text"
          placeholder="Enter command..."
          onKeyDown={handleKeyDown}
          className="w-full bg-black text-green-400 outline-none font-mono text-sm"
          style={{ fontFamily }}
          autoFocus
        />
      </div>
    </div>
  );
};

export default XTerminal;
