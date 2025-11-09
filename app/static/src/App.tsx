import "katex/dist/katex.min.css"
import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from './components/ThemeProvider'
import { ArtifactRenderer } from './components/ArtifactRenderer'
import { DataVisualizationDemo } from './components/DataVisualizationDemo'
import { ThreeDScene } from './components/ThreeDScene'
import { AICodePlayground } from './components/AICodePlayground'
import { MathRenderer } from './components/MathRenderer'
import { InteractiveChart } from './components/InteractiveChart'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function App() {
  const [activeDemo, setActiveDemo] = useState<string>('overview')

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50 dark:from-dark-bg dark:via-dark-bg-alt dark:to-dark-bg-card">
          {/* Navigation */}
          <nav className="nav-glass">
            <div className="container mx-auto px-4 py-4">
              <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold gradient-text">
                  🚀 CogniForge Superhuman UI
                </h1>
                <div className="flex gap-4">
                  {['overview', '3d', 'charts', 'code', 'math'].map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveDemo(tab)}
                      className={`px-4 py-2 rounded-lg font-medium transition-all ${
                        activeDemo === tab
                          ? 'superhuman-button'
                          : 'glass-effect hover:bg-accent-50 dark:hover:bg-dark-bg-card'
                      }`}
                    >
                      {tab.charAt(0).toUpperCase() + tab.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </nav>

          {/* Main Content */}
          <main className="container mx-auto px-4 py-24">
            {activeDemo === 'overview' && <OverviewSection />}
            {activeDemo === '3d' && <ThreeDSection />}
            {activeDemo === 'charts' && <ChartsSection />}
            {activeDemo === 'code' && <CodeSection />}
            {activeDemo === 'math' && <MathSection />}
          </main>
        </div>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

function OverviewSection() {
  return (
    <div className="space-y-8 animate-fade-in">
      <div className="superhuman-card text-center">
        <h2 className="text-4xl font-bold gradient-text mb-4">
          ✨ Advanced UI/UX Technologies
        </h2>
        <p className="text-xl text-gray-600 dark:text-dark-text-dim mb-8">
          Surpassing Claude, ChatGPT, and all tech giants
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
          <FeatureCard
            icon="🎨"
            title="React + TypeScript"
            description="Type-safe components with modern React patterns"
          />
          <FeatureCard
            icon="🎭"
            title="Tailwind CSS"
            description="Utility-first styling with custom design system"
          />
          <FeatureCard
            icon="📊"
            title="D3 + Recharts + Plotly"
            description="Advanced data visualization libraries"
          />
          <FeatureCard
            icon="🎮"
            title="Three.js + R3F"
            description="Stunning 3D graphics and animations"
          />
          <FeatureCard
            icon="🤖"
            title="TensorFlow.js"
            description="Client-side machine learning"
          />
          <FeatureCard
            icon="💻"
            title="Monaco Editor"
            description="VS Code-powered code editing"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DataVisualizationDemo />
        <ArtifactRenderer />
      </div>
    </div>
  )
}

function FeatureCard({ icon, title, description }: { icon: string; title: string; description: string }) {
  return (
    <div className="superhuman-card card-3d group">
      <div className="text-4xl mb-3 transform group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <h3 className="text-lg font-bold mb-2">{title}</h3>
      <p className="text-sm text-gray-600 dark:text-dark-text-dim">{description}</p>
    </div>
  )
}

function ThreeDSection() {
  return (
    <div className="space-y-8 animate-fade-in">
      <div className="superhuman-card">
        <h2 className="text-3xl font-bold gradient-text mb-4">
          🎮 Interactive 3D Graphics with Three.js
        </h2>
        <p className="text-gray-600 dark:text-dark-text-dim mb-6">
          Advanced 3D rendering using React Three Fiber - Drag to rotate, scroll to zoom
        </p>
        <ThreeDScene />
      </div>
    </div>
  )
}

function ChartsSection() {
  return (
    <div className="space-y-8 animate-fade-in">
      <div className="superhuman-card">
        <h2 className="text-3xl font-bold gradient-text mb-4">
          📊 Advanced Data Visualization
        </h2>
        <p className="text-gray-600 dark:text-dark-text-dim mb-6">
          Interactive charts with D3.js, Recharts, and Plotly
        </p>
        <InteractiveChart />
      </div>
    </div>
  )
}

function CodeSection() {
  return (
    <div className="space-y-8 animate-fade-in">
      <div className="superhuman-card">
        <h2 className="text-3xl font-bold gradient-text mb-4">
          💻 AI-Powered Code Playground
        </h2>
        <p className="text-gray-600 dark:text-dark-text-dim mb-6">
          Monaco Editor with syntax highlighting and AI assistance
        </p>
        <AICodePlayground />
      </div>
    </div>
  )
}

function MathSection() {
  return (
    <div className="space-y-8 animate-fade-in">
      <div className="superhuman-card">
        <h2 className="text-3xl font-bold gradient-text mb-4">
          🔢 Advanced Mathematical Rendering
        </h2>
        <p className="text-gray-600 dark:text-dark-text-dim mb-6">
          LaTeX rendering with KaTeX and Math.js calculations
        </p>
        <MathRenderer />
      </div>
    </div>
  )
}

export default App
