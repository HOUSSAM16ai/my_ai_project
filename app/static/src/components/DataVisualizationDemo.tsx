import { useMemo, useState } from 'react'
import {
  ResponsiveContainer,
  LineChart, Line,
  BarChart, Bar,
  AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from 'recharts'
import { Activity, BarChart3, TrendingUp } from 'lucide-react'

type Point = {
  name: string
  users: number
  sessions: number
  revenue: number
}

const RAW_DATA: ReadonlyArray<Point> = Object.freeze([
  { name: 'Jan', users: 400,  sessions: 240, revenue: 2400 },
  { name: 'Feb', users: 300,  sessions: 139, revenue: 2210 },
  { name: 'Mar', users: 600,  sessions: 980, revenue: 2290 },
  { name: 'Apr', users: 800,  sessions: 390, revenue: 2000 },
  { name: 'May', users: 1189, sessions: 480, revenue: 2181 },
  { name: 'Jun', users: 2390, sessions: 380, revenue: 2500 },
  { name: 'Jul', users: 3490, sessions: 430, revenue: 2100 },
])

type ChartKind = 'line' | 'bar' | 'area'

const CHART_TABS: ReadonlyArray<{ type: ChartKind; icon: React.ComponentType<{ className?: string }> }> = [
  { type: 'line', icon: TrendingUp },
  { type: 'bar',  icon: BarChart3 },
  { type: 'area', icon: Activity },
] as const

const ChartContainer = ({ children }: { children: React.ReactNode }) => (
  <>
    <CartesianGrid strokeDasharray="3 3" stroke="#e0e3e8" />
    <XAxis dataKey="name" stroke="#6c757d" />
    <YAxis stroke="#6c757d" />
    <Tooltip
      contentStyle={{
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        border: '1px solid #e0e3e8',
        borderRadius: 8,
      }}
    />
    <Legend />
    {children}
  </>
);

const LineChartContent = () => (
  <ChartContainer>
    <Line type="monotone" dataKey="users" stroke="#2196f3" strokeWidth={2} dot={false} />
    <Line type="monotone" dataKey="sessions" stroke="#4fc3f7" strokeWidth={2} dot={false} />
    <Line type="monotone" dataKey="revenue" stroke="#66bb6a" strokeWidth={2} dot={false} />
  </ChartContainer>
);

const BarChartContent = () => (
  <ChartContainer>
    <Bar dataKey="users" fill="#2196f3" />
    <Bar dataKey="sessions" fill="#4fc3f7" />
    <Bar dataKey="revenue" fill="#66bb6a" />
  </ChartContainer>
);

const AreaChartContent = () => (
  <ChartContainer>
    <defs>
      <linearGradient id="colorUsers" x1="0" y1="0" x2="0" y2="1">
        <stop offset="5%" stopColor="#2196f3" stopOpacity={0.8} />
        <stop offset="95%" stopColor="#2196f3" stopOpacity={0} />
      </linearGradient>
      <linearGradient id="colorSessions" x1="0" y1="0" x2="0" y2="1">
        <stop offset="5%" stopColor="#4fc3f7" stopOpacity={0.8} />
        <stop offset="95%" stopColor="#4fc3f7" stopOpacity={0} />
      </linearGradient>
      <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
        <stop offset="5%" stopColor="#66bb6a" stopOpacity={0.8} />
        <stop offset="95%" stopColor="#66bb6a" stopOpacity={0} />
      </linearGradient>
    </defs>
    <Area type="monotone" dataKey="users" stroke="#2196f3" fillOpacity={1} fill="url(#colorUsers)" />
    <Area type="monotone" dataKey="sessions" stroke="#4fc3f7" fillOpacity={1} fill="url(#colorSessions)" />
    <Area type="monotone" dataKey="revenue" stroke="#66bb6a" fillOpacity={1} fill="url(#colorRevenue)" />
  </ChartContainer>
);


export function DataVisualizationDemo() {
  const [chartType, setChartType] = useState<ChartKind>('line')

  const data = useMemo(() => [...RAW_DATA], [])

  const renderChart = (): JSX.Element => {
    switch (chartType) {
      case 'line':
        return <LineChart data={data}><LineChartContent /></LineChart>;
      case 'bar':
        return <BarChart data={data}><BarChartContent /></BarChart>;
      case 'area':
        return <AreaChart data={data}><AreaChartContent /></AreaChart>;
      default:
        return <></>;
    }
  }

  return (
    <section className="superhuman-card" role="region" aria-label="Real-time analytics chart">
      <header className="flex items-center justify-between mb-6">
        <h3 className="text-2xl font-bold gradient-text flex items-center gap-2">
          <Activity className="w-6 h-6" aria-hidden="true" />
          Real-time Analytics
        </h3>

        <nav aria-label="Chart type" className="flex gap-2">
          {CHART_TABS.map(({ type, icon: Icon }) => (
            <button
              key={type}
              type="button"
              onClick={() => setChartType(type)}
              aria-pressed={chartType === type}
              aria-label={`Show ${type} chart`}
              className={`p-2 rounded-lg transition-all ${
                chartType === type
                  ? 'bg-accent-500 text-white'
                  : 'glass-effect hover:bg-accent-50'
              }`}
            >
              <Icon className="w-5 h-5" aria-hidden="true" />
            </button>
          ))}
        </nav>
      </header>

      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </section>
  )
}
