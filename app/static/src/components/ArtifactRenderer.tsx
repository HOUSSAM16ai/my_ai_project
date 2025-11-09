import { useState } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Code2, Sparkles } from 'lucide-react'

const codeExamples = [
  {
    language: 'python',
    title: 'Python - Machine Learning',
    code: `import tensorflow as tf
import numpy as np

# Create a simple neural network
model = tf.keras.Sequential([
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(10, activation='softmax')
])

# Compile the model
model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

# Train with sample data
X_train = np.random.random((1000, 20))
y_train = np.random.randint(10, size=1000)
model.fit(X_train, y_train, epochs=5)`,
  },
  {
    language: 'javascript',
    title: 'JavaScript - React Component',
    code: `import React, { useState, useEffect } from 'react';

function SuperhumanComponent() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const response = await fetch('/api/v1/data');
        const json = await response.json();
        setData(json.data);
      } catch (error) {
        console.error('Error:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) return <Spinner />;
  
  return (
    <div className="superhuman-card">
      {data.map(item => (
        <Card key={item.id} {...item} />
      ))}
    </div>
  );
}`,
  },
  {
    language: 'typescript',
    title: 'TypeScript - Advanced Types',
    code: `interface User {
  id: number;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'moderator';
}

type ApiResponse<T> = {
  data: T;
  error: string | null;
  meta: {
    page: number;
    total: number;
  };
};

async function fetchUsers(): Promise<ApiResponse<User[]>> {
  const response = await fetch('/api/users');
  return response.json();
}

// Generic repository pattern
class Repository<T extends { id: number }> {
  constructor(private endpoint: string) {}
  
  async findById(id: number): Promise<T | null> {
    const response = await fetch(\`\${this.endpoint}/\${id}\`);
    return response.ok ? response.json() : null;
  }
  
  async findAll(): Promise<T[]> {
    const response = await fetch(this.endpoint);
    return response.json();
  }
}`,
  },
]

export function ArtifactRenderer() {
  const [selectedExample, setSelectedExample] = useState(0)

  const example = codeExamples[selectedExample]

  return (
    <div className="artifact-container">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-accent-500" />
          <h3 className="text-xl font-bold">Code Artifacts (Claude-style)</h3>
        </div>
        <div className="flex gap-2">
          {codeExamples.map((_, index) => (
            <button
              key={index}
              onClick={() => setSelectedExample(index)}
              className={`w-8 h-8 rounded-full transition-all ${
                selectedExample === index
                  ? 'bg-accent-500 text-white'
                  : 'glass-effect hover:bg-accent-50'
              }`}
            >
              {index + 1}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-3 flex items-center gap-2">
        <Code2 className="w-4 h-4 text-accent-500" />
        <span className="text-sm font-semibold text-gray-700 dark:text-dark-text">
          {example.title}
        </span>
        <span className="text-xs px-2 py-1 rounded-full bg-accent-100 text-accent-700 dark:bg-accent-900 dark:text-accent-300">
          {example.language}
        </span>
      </div>

      <div className="code-block">
        <SyntaxHighlighter
          language={example.language}
          style={vscDarkPlus}
          customStyle={{
            margin: 0,
            borderRadius: '0.5rem',
            fontSize: '0.875rem',
          }}
          showLineNumbers
        >
          {example.code}
        </SyntaxHighlighter>
      </div>

      <div className="mt-4 p-3 bg-blue-50 dark:bg-dark-bg-alt rounded-lg">
        <p className="text-sm text-gray-600 dark:text-dark-text-dim">
          ✨ <strong>Artifact Features:</strong> Syntax highlighting with Prism.js, 
          multiple language support, line numbers, and beautiful themes!
        </p>
      </div>
    </div>
  )
}
