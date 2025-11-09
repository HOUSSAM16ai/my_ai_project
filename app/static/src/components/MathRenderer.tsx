import { useState } from 'react'
import * as math from 'mathjs'
import 'katex/dist/katex.min.css'
import { InlineMath, BlockMath } from 'react-katex'
import { Calculator, BookOpen } from 'lucide-react'

export function MathRenderer() {
  const [expression, setExpression] = useState('x^2 + 2x + 1')
  const [result, setResult] = useState('')

  const calculateExpression = () => {
    try {
      const scope = { x: 5 }
      const evaluated = math.evaluate(expression, scope)
      setResult(`For x = 5: ${evaluated}`)
    } catch (error) {
      setResult(`Error: ${error instanceof Error ? error.message : 'Invalid expression'}`)
    }
  }

  const examples = [
    {
      title: 'Quadratic Formula',
      latex: 'x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}',
    },
    {
      title: "Euler's Identity",
      latex: 'e^{i\\pi} + 1 = 0',
    },
    {
      title: 'Taylor Series',
      latex: 'e^x = \\sum_{n=0}^{\\infty} \\frac{x^n}{n!}',
    },
    {
      title: 'Fourier Transform',
      latex: 'F(\\omega) = \\int_{-\\infty}^{\\infty} f(t) e^{-i\\omega t} dt',
    },
    {
      title: 'Maxwell Equations',
      latex: '\\nabla \\cdot \\vec{E} = \\frac{\\rho}{\\epsilon_0}',
    },
    {
      title: 'Schrödinger Equation',
      latex: 'i\\hbar\\frac{\\partial}{\\partial t}\\Psi = \\hat{H}\\Psi',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Interactive Calculator */}
      <div className="glass-effect p-6 rounded-xl">
        <div className="flex items-center gap-2 mb-4">
          <Calculator className="w-5 h-5 text-accent-500" />
          <h3 className="text-lg font-bold">Interactive Math Calculator</h3>
        </div>
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={expression}
            onChange={(e) => setExpression(e.target.value)}
            placeholder="Enter expression (e.g., x^2 + 2x + 1)"
            className="superhuman-input flex-1"
          />
          <button
            onClick={calculateExpression}
            className="superhuman-button"
          >
            Calculate
          </button>
        </div>
        {result && (
          <div className="p-4 bg-accent-50 dark:bg-dark-bg-card rounded-lg">
            <p className="font-mono text-accent-700 dark:text-accent-300">{result}</p>
          </div>
        )}
        <div className="mt-4 p-4 bg-blue-50 dark:bg-dark-bg-alt rounded-lg">
          <p className="text-sm text-gray-600 dark:text-dark-text-dim">
            <strong>Try:</strong> sqrt(16), sin(pi/2), log(100), 2^10, factorial(5)
          </p>
        </div>
      </div>

      {/* LaTeX Examples */}
      <div className="glass-effect p-6 rounded-xl">
        <div className="flex items-center gap-2 mb-4">
          <BookOpen className="w-5 h-5 text-accent-500" />
          <h3 className="text-lg font-bold">LaTeX Mathematical Equations</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {examples.map((example, index) => (
            <div
              key={index}
              className="p-4 bg-white dark:bg-dark-bg-card rounded-lg border border-gray-200 dark:border-dark-border"
            >
              <h4 className="text-sm font-semibold text-gray-700 dark:text-dark-text mb-2">
                {example.title}
              </h4>
              <div className="overflow-x-auto">
                <BlockMath math={example.latex} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Inline Math Examples */}
      <div className="glass-effect p-6 rounded-xl">
        <h3 className="text-lg font-bold mb-4">Inline Math Examples</h3>
        <div className="space-y-3 text-gray-700 dark:text-dark-text">
          <p>
            The area of a circle is <InlineMath math="A = \pi r^2" /> where{' '}
            <InlineMath math="r" /> is the radius.
          </p>
          <p>
            The Pythagorean theorem states that{' '}
            <InlineMath math="a^2 + b^2 = c^2" /> for a right triangle.
          </p>
          <p>
            Einstein's famous equation is <InlineMath math="E = mc^2" />.
          </p>
          <p>
            The derivative of <InlineMath math="f(x) = x^2" /> is{' '}
            <InlineMath math="f'(x) = 2x" />.
          </p>
        </div>
      </div>

      {/* Feature List */}
      <div className="glass-effect p-4 rounded-lg">
        <h4 className="font-semibold mb-2">✨ Mathematical Capabilities:</h4>
        <ul className="text-sm text-gray-600 dark:text-dark-text-dim space-y-1">
          <li>• KaTeX for beautiful LaTeX rendering</li>
          <li>• Math.js for advanced calculations</li>
          <li>• Support for complex equations and formulas</li>
          <li>• Interactive calculator with variable evaluation</li>
          <li>• Scientific, trigonometric, and algebraic functions</li>
          <li>• Matrix operations and linear algebra</li>
        </ul>
      </div>
    </div>
  )
}
