import React, { useState } from 'react'
import Editor from '@monaco-editor/react'
import { Play, Copy, Check } from 'lucide-react'

const initialCode = `// 🚀 AI-Powered Code Playground
// Try editing this code and run it!

function fibonacci(n) {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}

function calculatePrimes(max) {
  const primes = [];
  for (let i = 2; i <= max; i++) {
    let isPrime = true;
    for (let j = 2; j <= Math.sqrt(i); j++) {
      if (i % j === 0) {
        isPrime = false;
        break;
      }
    }
    if (isPrime) primes.push(i);
  }
  return primes;
}

// Run examples
console.log('Fibonacci(10):', fibonacci(10));
console.log('Primes up to 20:', calculatePrimes(20));

// AI can help you write complex algorithms!
const result = {
  fibonacci: fibonacci(10),
  primes: calculatePrimes(20),
  message: '✨ Code executed successfully!'
};

result;
`

export function AICodePlayground() {
  const [code, setCode] = useState(initialCode)
  const [output, setOutput] = useState<string>('')
  const [copied, setCopied] = useState(false)

  const runCode = () => {
    try {
      // Capture console.log output
      const logs: string[] = []
      const originalLog = console.log
      console.log = (...args) => {
        logs.push(args.map(arg => 
          typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
        ).join(' '))
      }

      // Execute code
      const result = eval(code)
      console.log = originalLog

      // Display output
      const outputText = [
        ...logs,
        '\n--- Result ---',
        typeof result === 'object' ? JSON.stringify(result, null, 2) : String(result)
      ].join('\n')
      
      setOutput(outputText)
    } catch (error) {
      setOutput(`❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  const copyCode = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <button
            onClick={runCode}
            className="superhuman-button flex items-center gap-2"
          >
            <Play className="w-4 h-4" />
            Run Code
          </button>
          <button
            onClick={copyCode}
            className="glass-effect px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-accent-50"
          >
            {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="code-block">
          <div className="bg-gray-800 text-white px-4 py-2 text-sm font-mono">
            💻 Editor (Monaco - VS Code Engine)
          </div>
          <Editor
            height="400px"
            defaultLanguage="javascript"
            value={code}
            onChange={(value) => setCode(value || '')}
            theme="vs-dark"
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              lineNumbers: 'on',
              roundedSelection: true,
              scrollBeyondLastLine: false,
              automaticLayout: true,
            }}
          />
        </div>

        <div className="code-block">
          <div className="bg-gray-800 text-white px-4 py-2 text-sm font-mono">
            📤 Output
          </div>
          <div className="bg-gray-900 text-green-400 font-mono text-sm p-4 h-[400px] overflow-auto">
            {output || '👆 Click "Run Code" to see the output'}
          </div>
        </div>
      </div>

      <div className="glass-effect p-4 rounded-lg">
        <h4 className="font-semibold mb-2">✨ Features:</h4>
        <ul className="text-sm text-gray-600 dark:text-dark-text-dim space-y-1">
          <li>• Monaco Editor - Same engine as VS Code</li>
          <li>• Syntax highlighting and IntelliSense</li>
          <li>• Real-time code execution</li>
          <li>• Console output capture</li>
          <li>• Error handling with detailed messages</li>
        </ul>
      </div>
    </div>
  )
}
