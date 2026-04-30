import React, { useState } from 'react'
import { api } from '../api/studyowl'
import HintBubble from '../components/HintBubble'

interface LearningResource {
  title: string
  url?: string
  summary?: string
}

export const StudentChat: React.FC = () => {
  const [question, setQuestion] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [hint, setHint] = useState<string | null>(null)
  const [hintLevel, setHintLevel] = useState<1 | 2 | 3>(1)
  const [attempt, setAttempt] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'answered'>('idle')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [reviewMode, setReviewMode] = useState(false)
  const [learningResources, setLearningResources] = useState<LearningResource[]>([])
  const [sessionStage, setSessionStage] = useState<'start' | 'inProgress' | 'complete'>('start')

  const handleStartSession = async () => {
    if (!question.trim()) {
      setError('Please enter a homework question')
      return
    }

    setStatus('loading')
    setError(null)
    setReviewMode(false)
    setLearningResources([])

    try {
      const result = await api.startSession({ question })
      setSessionId(result.session_id)
      setSessionStage('inProgress')
      setHint(result.hint)
      setHintLevel(result.hint_level)
      setAttempt('')
      setStatus('idle')
      setMessage(null)
    } catch (err) {
      setError((err as Error).message)
      setStatus('idle')
    }
  }

  const handleSubmitAttempt = async () => {
    if (!sessionId || !attempt.trim()) return

    setStatus('loading')
    setError(null)

    try {
      const result = await api.submitAttempt(sessionId, { attempt_text: attempt })

      if (result.status === 'correct') {
        setMessage('You got it! Great work!')
        setReviewMode(false)
        setLearningResources([])
        setSessionStage('complete')
        setAttempt('')
      } else {
        setHint(result.hint ?? null)
        setHintLevel(result.hint_level ?? hintLevel)
        setMessage(result.message ?? null)
        setReviewMode(result.review_mode ?? false)
        setLearningResources(result.learning_resources ?? [])
        setAttempt('')
      }
      setStatus('idle')
    } catch (err) {
      setError((err as Error).message)
      setStatus('idle')
    }
  }

  const handleNextProblem = () => {
    setSessionId(null)
    setSessionStage('start')
    setQuestion('')
    setHint(null)
    setHintLevel(1)
    setAttempt('')
    setMessage(null)
    setError(null)
    setReviewMode(false)
    setLearningResources([])
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-2xl mx-auto">
        <header className="text-center mb-8 pt-8">
          <h1 className="text-4xl font-bold text-indigo-900 mb-2">
            🦉 StudyOwl
          </h1>
          <p className="text-gray-600">Your AI Homework Assistant</p>
        </header>

        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          {sessionStage === 'start' ? (
            <>
              <h2 className="text-2xl font-bold text-gray-800 mb-4">
                What are you working on?
              </h2>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Type or paste your homework question here..."
                className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 mb-4"
              />
              <button
                onClick={handleStartSession}
                disabled={status === 'loading'}
                className="w-full bg-indigo-600 text-white py-2 rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-50 transition"
              >
                {status === 'loading' ? 'Loading...' : 'Get First Hint'}
              </button>
            </>
          ) : sessionStage === 'inProgress' ? (
            <>
              <div className="mb-6">
                <p className="text-gray-600 mb-2">Question:</p>
                <p className="text-gray-900 bg-gray-50 p-3 rounded-lg">
                  {question}
                </p>
              </div>

              {hint && <HintBubble hint={hint} level={hintLevel} />}

              {reviewMode && (
                <div className="relative overflow-hidden rounded-lg p-6 bg-gradient-to-br from-orange-50 via-white to-amber-50 border border-orange-200 mb-4">
                  <div className="celebration-wrapper pointer-events-none">
                    {Array.from({ length: 10 }).map((_, index) => (
                      <span
                        key={index}
                        className="confetti-piece"
                        style={{
                          left: `${8 + index * 8}%`,
                          animationDelay: `${index * 0.08}s`,
                          backgroundColor: ['#f59e0b', '#ea580c', '#d97706', '#f97316'][index % 4],
                        }}
                      />
                    ))}
                  </div>
                  <div className="relative">
                    <h2 className="text-3xl font-bold text-orange-900 mb-3 text-center">
                      😞 Review Needed
                    </h2>
                    <p className="text-orange-800 mb-6 text-lg text-center">
                      You've used all 3 attempts. It's time to learn more before trying again.
                    </p>

                    {learningResources && learningResources.length > 0 ? (
                      <>
                        <p className="text-orange-900 font-semibold mb-4 text-center">
                          Here are some resources to help you understand this topic better:
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                          {learningResources.map((resource, index) => (
                            <div
                              key={index}
                              className="bg-white rounded-lg p-4 border border-orange-200 hover:shadow-md transition-shadow"
                            >
                              <h3 className="font-semibold text-orange-900 mb-2 line-clamp-2">
                                {resource.title || 'Learning Resource'}
                              </h3>
                              {resource.summary && (
                                <p className="text-sm text-gray-700 mb-3 line-clamp-3">
                                  {resource.summary}
                                </p>
                              )}
                              {resource.url ? (
                                <a
                                  href={resource.url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="inline-flex items-center text-sm font-semibold text-indigo-700 hover:text-indigo-900 underline"
                                >
                                  Open resource →
                                </a>
                              ) : (
                                <p className="text-sm text-gray-500">No direct link available</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </>
                    ) : (
                      <p className="text-sm text-orange-800 mb-6 text-center">
                        Review a related website article or textbook example about the topic, then return and try a new question.
                      </p>
                    )}

                    <div className="text-center">
                      <button
                        onClick={handleNextProblem}
                        className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition"
                      >
                        Back to new question
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {message && (
                <div className="bg-green-50 border-l-4 border-green-500 p-4 mb-4 rounded">
                  <p className="text-gray-800">{message}</p>
                </div>
              )}

              {!reviewMode && sessionId && (
                <>
                  <input
                    type="text"
                    value={attempt}
                    onChange={(e) => setAttempt(e.target.value)}
                    placeholder="Your answer..."
                    className="w-full mb-3 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    onKeyPress={(e) => e.key === 'Enter' && handleSubmitAttempt()}
                  />
                  <button
                    onClick={handleSubmitAttempt}
                    disabled={status === 'loading' || !attempt.trim()}
                    className="w-full bg-green-600 text-white py-2 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50 transition"
                  >
                    {status === 'loading' ? 'Checking...' : 'Submit Answer'}
                  </button>
                </>
              )}
            </>
          ) : (
            <div className="relative overflow-hidden rounded-lg p-6 bg-gradient-to-br from-emerald-50 via-white to-lime-50 border border-emerald-200 mb-4">
              <div className="celebration-wrapper pointer-events-none">
                {Array.from({ length: 12 }).map((_, index) => (
                  <span
                    key={index}
                    className="confetti-piece"
                    style={{
                      left: `${8 + index * 7}%`,
                      animationDelay: `${index * 0.1}s`,
                      backgroundColor: ['#84cc16', '#22c55e', '#14b8a6', '#0ea5e9'][index % 4],
                    }}
                  />
                ))}
              </div>
              <div className="relative text-center">
                <h2 className="text-3xl font-bold text-emerald-900 mb-3">
                  🎉 Congratulations!
                </h2>
                <p className="text-gray-700 mb-6 text-lg">
                  {message ?? 'That was the right answer! Great job.'}
                </p>
                <button
                  onClick={handleNextProblem}
                  className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition"
                >
                  Next problem
                </button>
              </div>
            </div>
          )}

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
            </div>
          )}
        </div>

        <div className="bg-indigo-50 rounded-lg p-4 text-center text-sm text-gray-600">
          <p>
            📚 StudyOwl uses Socratic questioning to help you learn, not spoil the answers!
          </p>
        </div>
      </div>
    </div>
  )
}

export default StudentChat
