import React, { useState } from 'react'
import { LineChart, Line, BarChart, Bar, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Activity, BarChart3, TrendingUp } from 'lucide-react'

const data = [
  { name: 'Jan', users: 400, sessions: 240, revenue: 2400 },
  { name: 'Feb', users: 300, sessions: 139, revenue: 2210 },
  { name: 'Mar', users: 600, sessions: 980, revenue: 2290 },
  { name: 'Apr', users: 800, sessions: 390, revenue: 2000 },
  { name: 'May', users: 1189, sessions: 480, revenue: 2181 },
  { name: 'Jun', users: 2390, sessions: 380, revenue: 2500 },
  { name: 'Jul', users: 3490, sessions: 430, revenue: 2100 },
]

export function DataVisualizationDemo() {
  const [chartType, setChartType] = useState<'line' | 'bar' | 'area'>('line')

  return (
    <div className="superhuman-card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-2xl font-bold gradient-text flex items-center gap-2">
          <Activity className="w-6 h-6" />
          Real-time Analytics
        </h3>
        <div className="flex gap-2">
          {[
            { type: 'line' as const, icon: TrendingUp },
            { type: 'bar' as const, icon: BarChart3 },
            { type: 'area' as const, icon: Activity },
          ].map(({ type, icon: Icon }) => (
            <button
              key={type}
              onClick={() => setChartType(type)}
              className={`p-2 rounded-lg transition-all ${
                chartType === type
                  ? 'bg-accent-500 text-white'
                  : 'glass-effect hover:bg-accent-50'
              }`}
            >
              <Icon className="w-5 h-5" />
            </button>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        {chartType === 'line' && (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e3e8" />
            <XAxis dataKey="name" stroke="#6c757d" />
            <YAxis stroke="#6c757d" />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                border: '1px solid #e0e3e8',
                borderRadius: '8px',
              }}
            />
            <Legend />
            <Line type="monotone" dataKey="users" stroke="#2196f3" strokeWidth={2} />
            <Line type="monotone" dataKey="sessions" stroke="#4fc3f7" strokeWidth={2} />
            <Line type="monotone" dataKey="revenue" stroke="#66bb6a" strokeWidth={2} />
          </LineChart>
        )}
        
        {chartType === 'bar' && (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e3e8" />
            <XAxis dataKey="name" stroke="#6c757d" />
            <YAxis stroke="#6c757d" />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                border: '1px solid #e0e3e8',
                borderRadius: '8px',
              }}
            />
            <Legend />
            <Bar dataKey="users" fill="#2196f3" />
            <Bar dataKey="sessions" fill="#4fc3f7" />
            <Bar dataKey="revenue" fill="#66bb6a" />
          </BarChart>
        )}
        
        {chartType === 'area' && (
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorUsers" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2196f3" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#2196f3" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorSessions" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#4fc3f7" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#4fc3f7" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e3e8" />
            <XAxis dataKey="name" stroke="#6c757d" />
            <YAxis stroke="#6c757d" />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                border: '1px solid #e0e3e8',
                borderRadius: '8px',
              }}
            />
            <Legend />
            <Area type="monotone" dataKey="users" stroke="#2196f3" fillOpacity={1} fill="url(#colorUsers)" />
            <Area type="monotone" dataKey="sessions" stroke="#4fc3f7" fillOpacity={1} fill="url(#colorSessions)" />
          </AreaChart>
        )}
      </ResponsiveContainer>
    </div>
  )
}
