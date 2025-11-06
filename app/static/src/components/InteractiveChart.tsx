import React, { useState, useCallback } from 'react'
import Plot from 'react-plotly.js'
import { RefreshCw } from 'lucide-react'

export function InteractiveChart() {
  const [chartType, setChartType] = useState<'scatter3d' | 'surface' | 'heatmap'>('scatter3d')
  const [dataVersion, setDataVersion] = useState(0)

  // Generate data with version for proper re-rendering
  const generateData = useCallback(() => {
    const scatter3dData = {
      x: Array.from({ length: 100 }, () => Math.random() * 10),
      y: Array.from({ length: 100 }, () => Math.random() * 10),
      z: Array.from({ length: 100 }, () => Math.random() * 10),
      mode: 'markers',
      marker: {
        size: 5,
        color: Array.from({ length: 100 }, () => Math.random()),
        colorscale: 'Viridis',
        showscale: true,
      },
      type: 'scatter3d' as const,
    }

    const surfaceData = {
      z: Array.from({ length: 30 }, (_, i) =>
        Array.from({ length: 30 }, (_, j) => {
          const x = (i - 15) / 5
          const y = (j - 15) / 5
          return Math.sin(Math.sqrt(x * x + y * y))
        })
      ),
      type: 'surface' as const,
      colorscale: 'Portland',
    }

    const heatmapData = {
      z: Array.from({ length: 20 }, () =>
        Array.from({ length: 20 }, () => Math.random() * 100)
      ),
      type: 'heatmap' as const,
      colorscale: 'Hot',
    }

    return { scatter3dData, surfaceData, heatmapData }
  }, [dataVersion])

  const { scatter3dData, surfaceData, heatmapData } = generateData()

  const getChartData = () => {
    switch (chartType) {
      case 'scatter3d':
        return [scatter3dData]
      case 'surface':
        return [surfaceData]
      case 'heatmap':
        return [heatmapData]
    }
  }

  const refreshData = () => {
    setDataVersion(v => v + 1)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          {[
            { type: 'scatter3d' as const, label: '3D Scatter' },
            { type: 'surface' as const, label: '3D Surface' },
            { type: 'heatmap' as const, label: 'Heatmap' },
          ].map(({ type, label }) => (
            <button
              key={type}
              onClick={() => setChartType(type)}
              className={`px-4 py-2 rounded-lg transition-all ${
                chartType === type
                  ? 'superhuman-button'
                  : 'glass-effect hover:bg-accent-50'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        <button
          onClick={refreshData}
          className="glass-effect p-2 rounded-lg hover:bg-accent-50"
          title="Refresh data"
        >
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>

      <div className="glass-effect p-4 rounded-xl">
        <Plot
          data={getChartData()}
          layout={{
            autosize: true,
            height: 500,
            margin: { l: 0, r: 0, t: 0, b: 0 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            scene: {
              xaxis: { 
                backgroundcolor: 'rgba(0,0,0,0)',
                gridcolor: '#e0e3e8',
              },
              yaxis: { 
                backgroundcolor: 'rgba(0,0,0,0)',
                gridcolor: '#e0e3e8',
              },
              zaxis: { 
                backgroundcolor: 'rgba(0,0,0,0)',
                gridcolor: '#e0e3e8',
              },
            },
          }}
          config={{
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
          }}
          style={{ width: '100%', height: '100%' }}
        />
      </div>

      <div className="glass-effect p-4 rounded-lg">
        <h4 className="font-semibold mb-2">✨ Plotly.js Features:</h4>
        <ul className="text-sm text-gray-600 dark:text-dark-text-dim space-y-1">
          <li>• Interactive 3D visualizations with zoom and rotation</li>
          <li>• Multiple chart types: scatter, surface, heatmap, and more</li>
          <li>• Scientific-grade plotting capabilities</li>
          <li>• Real-time data updates and animations</li>
          <li>• Export to PNG, SVG, and other formats</li>
        </ul>
      </div>
    </div>
  )
}
