import React from 'react'

interface HintBubbleProps {
  hint: string
  level: 1 | 2 | 3
}

const formatMathHint = (hint: string): string => {
  let text = hint

  // Remove LaTeX delimiters and display math wrappers.
  text = text.replace(/\\+\(|\\+\)|\\+\[|\\+\]/g, '')

  // Replace common LaTeX commands with more readable math notation.
  text = text.replace(/\\left|\\right/g, '')
  text = text.replace(/\\cdot/g, '·')
  text = text.replace(/\\times/g, '×')
  text = text.replace(/\\pm/g, '±')

  // Convert LaTeX fractions to inline a/b form.
  while (/\\frac\{([^}]*)\}\{([^}]*)\}/.test(text)) {
    text = text.replace(/\\frac\{([^}]*)\}\{([^}]*)\}/g, '$1/$2')
  }

  // Clean up escaped characters and extra whitespace.
  text = text.replace(/\\n/g, ' ')
  text = text.replace(/\\/g, '')
  text = text.replace(/\s+/g, ' ').trim()

  return text
}

export const HintBubble: React.FC<HintBubbleProps> = ({ hint, level }) => {
  const levelDescriptions = {
    1: 'Socratic Question',
    2: 'Concept & Formula',
    3: 'Near Answer',
  }

  return (
    <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-lg">
      <div className="flex items-start gap-3">
        <span className="text-2xl">💡</span>
        <div className="flex-1">
          <p className="text-sm font-semibold text-blue-900 mb-2">
            {levelDescriptions[level]} - Level {level}/3
          </p>
          <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
            {formatMathHint(hint)}
          </p>
        </div>
      </div>
    </div>
  )
}

export default HintBubble
