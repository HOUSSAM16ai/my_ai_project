import type { Data } from 'plotly.js'
import { useState, useCallback, useMemo } from 'react'
import Plot from 'react-plotly.js'
import { RefreshCw } from 'lucide-react'

type ChartKind = 'scatter3d' | 'surface' | 'heatmap'

export function InteractiveChart() {
  const [chartType, setChartType] = useState<ChartKind>('scatter3d')
  const [dataVersion, setDataVersion] = useState(0)

  // توليد بيانات عشوائية لكل نوع — مربوطة بالإصدار لضمان إعادة الرسم
  const generateData = useCallback(() => {
    const scatter3dData: Data = {
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
      type: 'scatter3d',
    }

    const surfaceData: Data = {
      z: Array.from({ length: 30 }, (_, i) =>
        Array.from({ length: 30 }, (_, j) => {
          const x = (i - 15) / 5
          const y = (j - 15) / 5
          return Math.sin(Math.sqrt(x * x + y * y))
        })
      ),
      type: 'surface',
      colorscale: 'Portland',
    }

    const heatmapData: Data = {
      z: Array.from({ length: 20 }, () =>
        Array.from({ length: 20 }, () => Math.random() * 100)
      ),
      type: 'heatmap',
      colorscale: 'Hot',
    }

    return { scatter3dData, surfaceData, heatmapData }
  }, [dataVersion])

  const { scatter3dData, surfaceData, heatmapData } = generateData()

  // حدد بيانات الرسم حسب النوع (مُحسّبة بـ memo لتقليل إعادة الحساب)
  const chartData = useMemo<Data[]>(() => {
    switch (chartType) {
      case 'scatter3d': return [scatter3dData]
      case 'surface':   return [surfaceData]
      case 'heatmap':   return [heatmapData]
    }
  }, [chartType, scatter3dData, surfaceData, heatmapData])

  // تخطيط متكيّف مع النوع: نضيف scene فقط للأنواع ثلاثية الأبعاد
  const layout = useMemo(() => {
    const base = {
      autosize: true,
      height: 500,
      margin: { l: 0, r: 0, t: 0, b: 0 },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
    } as const

    if (chartType === 'scatter3d' || chartType === 'surface') {
      return {
        ...base,
        scene: {
          xaxis: { backgroundcolor: 'rgba(0,0,0,0)', gridcolor: '#e0e3e8' },
          yaxis: { backgroundcolor: 'rgba(0,0,0,0)', gridcolor: '#e0e3e8' },
          zaxis: { backgroundcolor: 'rgba(0,0,0,0)', gridcolor: '#e0e3e8' },
        },
      }
    }
    return base
  }, [chartType])

  const refreshData = () => setDataVersion(v => v + 1)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          {([
            { type: 'scatter3d', label: '3D Scatter' },
            { type: 'surface',   label: '3D Surface' },
            { type: 'heatmap',   label: 'Heatmap'   },
          ] as const).map(({ type, label }) => (
            <button
              key={type}
              onClick={() => setChartType(type)}
              className={`px-4 py-2 rounded-lg transition-all ${
                chartType === type ? 'superhuman-button' : 'glass-effect hover:bg-accent-50'
              }`}
              aria-pressed={chartType === type}
            >
              {label}
            </button>
          ))}
        </div>

        <button
          onClick={refreshData}
          className="glass-effect p-2 rounded-lg hover:bg-accent-50"
          title="Refresh data"
          aria-label="Refresh data"
        >
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>

      <div className="glass-effect p-4 rounded-xl">
        <Plot
          key={`${chartType}-${dataVersion}`}     // يضمن إعادة بناء الرسم عند تغيير النوع/البيانات
          data={chartData}
          layout={layout as any}                  // تخفيف صارم لأن Layout union مع scene اختياري
          config={{ responsive: true, displayModeBar: true, displaylogo: false }}
          style={{ width: '100%', height: '100%' }}
          useResizeHandler
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
